"""Page 2 — Intelligence Artificielle.

Carte modèle actif, métriques, feature importance, historique versions,
bouton ré-entraînement.
"""
from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dashboard.utils.data_loader import load_rapport_modelisation  # noqa: E402

st.set_page_config(page_title="IA — GE", page_icon="🤖", layout="wide")
st.title("🤖 Intelligence Artificielle")
st.caption("Modèle actif, performances, feature importance et historique des versions.")

st.divider()


@st.cache_data(ttl=3600)
def _load_json(path: Path) -> dict | None:
    import json
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


rapport = load_rapport_modelisation()
baseline = rapport["baseline"]
sprint_a = _load_json(ROOT / "reports" / "sprint_a_chantier1_metrics.json")
sprint_b_stack = _load_json(ROOT / "reports" / "sprint_b_chantier1_stacking.json")

# ----------------------------- Carte modèle (v2) ----------------------------
st.subheader("Modèle actif — XGBoost v2")
col1, col2 = st.columns([2, 1])
with col1:
    if sprint_a:
        n_feat = sprint_a["n_features"]
        n_trials = sprint_a["n_trials_optuna"]
        date_str = sprint_a["date"][:10]
    else:
        n_feat = len(rapport["features"])
        n_trials = 300
        date_str = rapport["date"]
    st.markdown(
        f"""
        **Nom** : XGBoost Optuna v2
        **Version** : 2.0 — {date_str}
        **Cible** : `qte_demandee` (transformation `log1p`)
        **Split** : Train 2021-2023 / Val 2024 / Test 2025
        **Features** : {n_feat} (cf. `dashboard/utils/features.py` → `FEATURES_V2`)
        **Optuna** : {n_trials} essais
        """
    )
with col2:
    if sprint_a:
        st.json(sprint_a["best_params"])
    else:
        st.json(rapport["xgboost_optuna_final"]["best_params"])

st.divider()

# ----------------------------- Métriques v2 ---------------------------------
st.subheader("Performances test (2025) — XGBoost v2")
if sprint_a:
    v2 = sprint_a["test_metrics_v2"]
    mae, rmse, r2, wape = v2["MAE"], v2["RMSE"], v2["R2"], v2["WAPE"]
else:
    xgb_best = rapport["xgboost_optuna_final"]
    mae, rmse, r2, wape = xgb_best["mae"], xgb_best["rmse"], xgb_best["r2"], xgb_best["wape"]

c1, c2, c3, c4 = st.columns(4)
c1.metric("MAE", f"{mae:.2f}", f"{mae-baseline['mae']:+.2f} vs baseline")
c2.metric("RMSE", f"{rmse:.2f}", f"{rmse-baseline['rmse']:+.2f}")
c3.metric("R²", f"{r2:.3f}")
c4.metric("WAPE", f"{wape*100:.1f}%")

st.divider()

# ----------------------------- Feature importance ---------------------------
st.subheader("Feature importance — Top 15")
fi_path = ROOT / "reports" / "feature_importance_xgb.png"
if fi_path.exists():
    st.image(str(fi_path), use_container_width=True)
else:
    st.warning(f"Figure non trouvée : `{fi_path.relative_to(ROOT)}`")

st.divider()

# ----------------------------- Comparaison modèles --------------------------
st.subheader("Benchmark des architectures testées")
rows = [
    {"Modèle": "Baseline (moy. hist.)", "MAE": baseline["mae"], "RMSE": baseline["rmse"], "R²": "—", "WAPE": "—"},
]
for key, label in [
    ("xgboost_log", "XGBoost v1 (log + MSE)"),
    ("xgboost_tweedie", "XGBoost v1 (Tweedie)"),
    ("lightgbm_log", "LightGBM v1 (log)"),
    ("xgboost_optuna_final", "XGBoost Optuna v1 (28 feat.)"),
]:
    m = rapport[key]
    rows.append({"Modèle": label, "MAE": round(m["mae"], 2), "RMSE": round(m["rmse"], 2),
                 "R²": round(m["r2"], 3), "WAPE": f"{m['wape']*100:.1f}%"})

# Ligne v2 + modèles avancés
rows.append({"Modèle": "**XGBoost Optuna v2 (47 feat.)** ⭐ MAE",
             "MAE": round(mae, 2), "RMSE": round(rmse, 2), "R²": round(r2, 3), "WAPE": f"{wape*100:.1f}%"})

if sprint_b_stack:
    for r in sprint_b_stack["results"]:
        name = r["modele"]
        if name == "XGBoost v2":
            continue  # déjà ajouté ci-dessus
        suffix = " ⭐ RMSE/R²" if name == "Stacking Ridge" else ""
        rows.append({"Modèle": f"{name}{suffix}", "MAE": round(r["MAE"], 2),
                     "RMSE": round(r["RMSE"], 2), "R²": round(r["R2"], 3),
                     "WAPE": f"{r['WAPE']*100:.1f}%"})

st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
st.caption("**Décision de production** : XGBoost v2 conservé (meilleur MAE, simplicité). Stacking Ridge documenté comme amélioration RMSE/R².")

st.divider()

# ----------------------------- Historique versions --------------------------
st.subheader("Historique des modèles sauvegardés")
models_dir = ROOT / "models"
files = sorted(models_dir.glob("*.pkl")) + sorted(models_dir.glob("*.pt"))
hist = []
for f in files:
    hist.append({
        "Fichier": f.name,
        "Taille (KB)": round(f.stat().st_size / 1024, 1),
        "Modifié le": pd.to_datetime(f.stat().st_mtime, unit="s").strftime("%Y-%m-%d %H:%M"),
    })
st.dataframe(pd.DataFrame(hist), use_container_width=True, hide_index=True)

st.divider()

# ----------------------------- Ré-entraînement ------------------------------
st.subheader("Ré-entraînement du modèle")
st.markdown(
    "Lance le script `src/retrain.py` qui ré-exécute l'étape Optuna + fit final. "
    "Opération longue (~10-30 min selon machine)."
)
retrain_script = ROOT / "src" / "retrain.py"
logs_dir = ROOT / "logs"
logs_dir.mkdir(exist_ok=True)

mode = st.radio(
    "Mode",
    ["quick", "full"],
    horizontal=True,
    help="quick = 30 essais (~5 min) • full = 100 essais (~30 min)",
)

if "retrain_pid" not in st.session_state:
    st.session_state["retrain_pid"] = None
    st.session_state["retrain_log"] = None

col_btn, col_status = st.columns([1, 2])
with col_btn:
    if st.button("🔄 Lancer le re-entraînement", type="primary"):
        if not retrain_script.exists():
            st.error(f"Script absent : `{retrain_script.relative_to(ROOT)}`")
        else:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_path = logs_dir / f"retrain_{ts}.streamlit.log"
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(f"=== retrain --{mode} lance le {ts} ===\n")
            proc = subprocess.Popen(
                [sys.executable, str(retrain_script), f"--{mode}"],
                stdout=open(log_path, "a", encoding="utf-8"),
                stderr=subprocess.STDOUT,
                cwd=str(ROOT),
            )
            st.session_state["retrain_pid"] = proc.pid
            st.session_state["retrain_log"] = str(log_path)
            st.success(f"Lance en arriere-plan (PID {proc.pid}). Log : `{log_path.name}`")

with col_status:
    if st.session_state.get("retrain_log"):
        log_path = Path(st.session_state["retrain_log"])
        if log_path.exists():
            try:
                content = log_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                content = log_path.read_text(encoding="utf-8", errors="replace")
            with st.expander(f"📜 Log en cours — {log_path.name}", expanded=True):
                st.code(content[-2000:] if len(content) > 2000 else content)
