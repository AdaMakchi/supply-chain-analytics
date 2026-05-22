"""Page 4 — Analyse & Storytelling.

IA vs baseline, top erreurs, saisonnalité (figures Phase 2), limites.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dashboard.utils.data_loader import load_rapport_modelisation, load_split  # noqa: E402
from dashboard.utils.features import TARGET_QTE  # noqa: E402
from dashboard.utils.inference import predict_qte  # noqa: E402

st.set_page_config(page_title="Analyse — GE", page_icon="🔍", layout="wide")
st.title("🔍 Analyse & Storytelling")
st.caption("IA vs baseline historique, cas d'erreurs, saisonnalité, limites identifiées.")

st.divider()

# ----------------------------- IA vs baseline -------------------------------
st.subheader("IA bat-elle la baseline ?")
rapport = load_rapport_modelisation()
xgb_best = rapport["xgboost_optuna_final"]
baseline = rapport["baseline"]

col1, col2, col3 = st.columns(3)
col1.metric("MAE baseline", f"{baseline['mae']:.2f}")
col2.metric("MAE XGBoost Optuna", f"{xgb_best['mae']:.2f}", f"{xgb_best['mae']-baseline['mae']:+.2f}")
col3.metric("Gain relatif", f"{(baseline['mae']-xgb_best['mae'])/baseline['mae']*100:.1f}%")

st.markdown(
    f"""
    Le modèle XGBoost Optuna réduit la **MAE de {baseline['mae']:.2f} à {xgb_best['mae']:.2f}**
    sur le test set 2025, soit un gain de **{(baseline['mae']-xgb_best['mae'])/baseline['mae']*100:.1f}%**
    par rapport à la moyenne historique client × article.
    """
)

st.divider()

# ----------------------------- Top erreurs ----------------------------------
st.subheader("Top 10 erreurs (où l'IA se trompe le plus)")
df_test = load_split("test")
preds = predict_qte(df_test)
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

# ----------------------------- Saisonnalité ---------------------------------
st.subheader("Saisonnalité observée (Phase 2)")
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
       le format Phase 2bis (Mode A imposé).
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
