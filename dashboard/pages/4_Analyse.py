"""Page 4 — Analyse & Storytelling.

IA vs baseline, top erreurs, saisonnalité, limites identifiées,
et architectures complémentaires (Stacking Ridge, baseline DDMRP).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dashboard.utils.data_loader import load_rapport_modelisation, load_split_v3  # noqa: E402
from dashboard.utils.features import TARGET_QTE  # noqa: E402
from dashboard.utils.inference import predict_qte_v2  # noqa: E402


@st.cache_data(ttl=3600)
def _load_json(path: Path) -> dict | None:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


st.set_page_config(page_title="Analyse — GE", page_icon="🔍", layout="wide")
st.title("🔍 Analyse & Storytelling")
st.caption("IA vs baseline historique, cas d'erreurs, saisonnalité, limites identifiées, Stacking Ridge et baseline DDMRP.")

st.divider()

# ----------------------------- IA vs baseline -------------------------------
st.subheader("IA bat-elle la baseline ?")
rapport = load_rapport_modelisation()
baseline = rapport["baseline"]
sprint_a = _load_json(ROOT / "reports" / "sprint_a_chantier1_metrics.json")

if sprint_a:
    mae_v2 = sprint_a["test_metrics_v2"]["MAE"]
    model_label = "XGBoost Optuna v2"
else:
    mae_v2 = rapport["xgboost_optuna_final"]["mae"]
    model_label = "XGBoost Optuna"

gain_pct = (baseline['mae'] - mae_v2) / baseline['mae'] * 100

col1, col2, col3 = st.columns(3)
col1.metric("MAE baseline", f"{baseline['mae']:.2f}")
col2.metric(f"MAE {model_label}", f"{mae_v2:.2f}", f"{mae_v2-baseline['mae']:+.2f}")
col3.metric("Gain relatif", f"{gain_pct:.1f}%")

st.markdown(
    f"""
    Le modèle **{model_label}** (47 features) réduit la
    **MAE de {baseline['mae']:.2f} à {mae_v2:.2f}** sur le test set 2025,
    soit un gain de **{gain_pct:.1f} %** vs la moyenne historique client × article.
    """
)

st.divider()

# ----------------------------- Top erreurs ----------------------------------
st.subheader("Top 10 erreurs (où l'IA se trompe le plus) — XGBoost v2")
df_test = load_split_v3("test")
preds = predict_qte_v2(df_test)
df_err = pd.DataFrame({
    "code_client_freq": df_test["code_client_freq"].values,
    "code_article_freq": df_test["code_article_freq"].values,
    "qte_reelle": df_test[TARGET_QTE].values,
    "qte_predite": preds.round(2),
})
df_err["erreur_abs"] = (df_err["qte_reelle"] - df_err["qte_predite"]).abs().round(2)
top_err = df_err.nlargest(10, "erreur_abs")
st.dataframe(top_err, use_container_width=True, hide_index=True)

st.markdown(
    "**Lecture :** ces cas extrêmes correspondent généralement à des commandes "
    "de gros volume sur des articles ou clients peu représentés dans le train. "
    "Le badge confiance ROUGE/ORANGE doit signaler ces situations à l'utilisateur."
)

st.divider()

# ----------------------------- Stacking + DDMRP ----------------------------
st.subheader("Architectures complémentaires — Stacking Ridge et baseline DDMRP")

sprint_b_stack = _load_json(ROOT / "reports" / "sprint_b_chantier1_stacking.json")
sprint_b_ddmrp = _load_json(ROOT / "reports" / "sprint_b_chantier3_ddmrp.json")

tab_stack, tab_ddmrp = st.tabs(["📐 Stacking Ridge", "📦 DDMRP vs IA"])

with tab_stack:
    if sprint_b_stack:
        df_stack = pd.DataFrame(sprint_b_stack["results"])
        df_stack["MAE"] = df_stack["MAE"].round(2)
        df_stack["RMSE"] = df_stack["RMSE"].round(2)
        df_stack["R2"] = df_stack["R2"].round(3)
        df_stack["WAPE"] = (df_stack["WAPE"] * 100).round(1).astype(str) + " %"
        st.dataframe(df_stack, use_container_width=True, hide_index=True)
        st.markdown(
            "**Lecture** : le Stacking Ridge (XGB v2 + LGBM P50 + CatBoost) gagne sur **RMSE** "
            "(97.55 vs 101.83) et **R²** (0.694 vs 0.666) — il corrige les grandes erreurs. "
            "Mais XGBoost v2 garde le meilleur MAE → on **garde XGB v2 en production** (Occam)."
        )
    else:
        st.info("Lancez `notebooks/10_catboost_stacking.ipynb` pour générer les résultats.")

with tab_ddmrp:
    if sprint_b_ddmrp:
        df_ddmrp = pd.DataFrame(sprint_b_ddmrp["comparison_mae"])
        df_ddmrp["MAE"] = df_ddmrp["MAE"].round(2)
        df_ddmrp["Biais"] = df_ddmrp["Biais"].round(2)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**MAE et biais (agrégé hebdo, articles stratégiques)**")
            st.dataframe(df_ddmrp, use_container_width=True, hide_index=True)
        with c2:
            df_cout = pd.DataFrame(sprint_b_ddmrp["comparison_cout"])
            df_cout["cout_total"] = df_cout["cout_total"].round(0)
            st.markdown(f"**Coût total (α={sprint_b_ddmrp['alpha']}, β={sprint_b_ddmrp['beta']})**")
            st.dataframe(df_cout, use_container_width=True, hide_index=True)
        st.markdown(
            f"""
            - **{sprint_b_ddmrp['n_articles_strategiques']} articles stratégiques** sélectionnés (Pareto 80 %)
            - **IA gagne en précision** (MAE 260) ET en coût (α élevé pénalise les ruptures)
            - **DDMRP gagne en sécurité opérationnelle** (taux rupture {sprint_b_ddmrp['taux_rupture_ddmrp']*100:.1f} %)
            - **Hybride 50/50** = meilleur compromis (MAE 242, biais ~0) → recommandation production

            *Référence : Ptak & Smith (2016), Demand-Driven Material Requirements Planning.*
            """
        )
    else:
        st.info("Lancez `notebooks/09_baseline_ddmrp.ipynb` pour générer les résultats.")

st.divider()

# ----------------------------- Saisonnalité ---------------------------------
st.subheader("Saisonnalité observée")
reports_dir = ROOT / "reports"
figures = sorted(reports_dir.glob("decomposition_*.png")) + sorted(reports_dir.glob("cycles_*.png"))
if figures:
    cols = st.columns(2)
    for i, fig in enumerate(figures[:6]):
        cols[i % 2].image(str(fig), caption=fig.stem, use_container_width=True)
else:
    st.info("Aucune figure de décomposition trouvée dans `reports/`.")

st.divider()

# ----------------------------- Limites --------------------------------------
st.subheader("Limites identifiées")
lstm = rapport["lstm_time_to_event"]
st.markdown(
    f"""
    1. **Prédiction de date faible** — LSTM time-to-event :
       MAE **{lstm['mae_jours']:.1f} jours**, précision ±7j seulement **{lstm['precision_7j']*100:.1f}%**.
       Le dashboard signale cette incertitude (badge ROUGE par défaut sur la date).

    2. **Facteurs géopolitiques non modélisés** — guerres, crises matières premières,
       grèves logistiques : ces ruptures sont invisibles aux features actuelles.

    3. **Articles inconnus du train** — fallback médiane, prédiction peu fiable
       → badge ROUGE systématique.

    4. **Données 2025 = test only** — pas de retraining incrémental dans le MVP.

    5. **Pipeline d'encodage figé** — modifications du dataset doivent suivre
       le format d'encodage de référence (Mode A imposé).
    """
)

st.divider()

# ----------------------------- Perspectives ---------------------------------
st.subheader("Perspectives")
st.markdown(
    """
    - **Court terme** : intégrer des features géopolitiques (indices commodités, indicateurs supply chain)
    - **Moyen terme** : architecture transformer pour la date (TFT, N-BEATS)
    - **Production** : déploiement FastAPI + base PostgreSQL + monitoring drift (Evidently, Whylogs)
    - **Validation humaine continue** : feedback loop utilisateur → fine-tuning hebdomadaire
    """
)
