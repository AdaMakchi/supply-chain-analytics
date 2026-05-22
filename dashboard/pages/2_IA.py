"""Page 2 — Intelligence Artificielle.

Carte modèle actif, métriques, feature importance, historique versions,
bouton ré-entraînement.
"""
from __future__ import annotations

import os
import sys
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

rapport = load_rapport_modelisation()
xgb_best = rapport["xgboost_optuna_final"]
baseline = rapport["baseline"]

# ----------------------------- Carte modèle ---------------------------------
st.subheader("Modèle actif")
col1, col2 = st.columns([2, 1])
with col1:
    st.markdown(
        f"""
        **Nom** : XGBoost Optuna (final)
        **Version** : 1.0 — {rapport['date']}
        **Cible** : `qte_demandee` (transformation `log1p`)
        **Split** : Train 2021-2023 / Val 2024 / Test 2025
        **Features** : {len(rapport['features'])} (cf. notebook 03)
        """
    )
with col2:
    st.json(xgb_best["best_params"])

st.divider()

# ----------------------------- Métriques ------------------------------------
st.subheader("Performances test (2025)")
c1, c2, c3, c4 = st.columns(4)
c1.metric("MAE", f"{xgb_best['mae']:.2f}", f"{xgb_best['mae']-baseline['mae']:+.2f} vs baseline")
c2.metric("RMSE", f"{xgb_best['rmse']:.2f}", f"{xgb_best['rmse']-baseline['rmse']:+.2f}")
c3.metric("R²", f"{xgb_best['r2']:.3f}")
c4.metric("WAPE", f"{xgb_best['wape']*100:.1f}%")

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
st.subheader("Comparaison des architectures testées")
rows = []
for key, label in [
    ("xgboost_log", "XGBoost (log + MSE)"),
    ("xgboost_tweedie", "XGBoost (Tweedie)"),
    ("lightgbm_log", "LightGBM (log)"),
    ("xgboost_optuna_final", "XGBoost Optuna ⭐"),
]:
    m = rapport[key]
    rows.append({"Modèle": label, "MAE": m["mae"], "RMSE": m["rmse"], "R²": m["r2"], "WAPE": f"{m['wape']*100:.1f}%"})
rows.insert(0, {"Modèle": "Baseline (moy. hist.)", "MAE": baseline["mae"], "RMSE": baseline["rmse"], "R²": "—", "WAPE": "—"})
st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

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
if st.button("🔄 Ré-entraîner XGBoost Optuna", type="secondary"):
    retrain_script = ROOT / "src" / "retrain.py"
    if not retrain_script.exists():
        st.error(f"Script absent : `{retrain_script.relative_to(ROOT)}` — à créer en J7.")
    else:
        st.info("Lancement en arrière-plan… (fonctionnalité à compléter J7)")
        # TODO J7 : subprocess.Popen + log streaming
