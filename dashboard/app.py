"""Dashboard GE — Page d'accueil.

Lancement : `streamlit run dashboard/app.py` depuis la racine du projet.
"""
from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dashboard.components.kpi_card import kpi_card  # noqa: E402
from dashboard.utils.data_loader import load_rapport_modelisation  # noqa: E402

st.set_page_config(
    page_title="Prévision Demande GE",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Système de Prévision et d'Optimisation des Stocks")
st.caption(
    "Approche Demand-Driven s'appuyant sur l'IA pour prédire la demande client réelle "
    "et optimiser la chaîne d'approvisionnement — Mémoire Master GE 2026."
)

st.divider()

rapport = load_rapport_modelisation()
xgb_best = rapport["xgboost_optuna_final"]
baseline = rapport["baseline"]
gain_mae = (baseline["mae"] - xgb_best["mae"]) / baseline["mae"] * 100

col1, col2, col3, col4 = st.columns(4)
with col1:
    kpi_card("MAE modèle final", f"{xgb_best['mae']:.2f}", f"-{gain_mae:.1f}% vs baseline")
with col2:
    kpi_card("R² test (2025)", f"{xgb_best['r2']:.3f}", help_text="Coefficient de détermination")
with col3:
    kpi_card("WAPE", f"{xgb_best['wape']*100:.1f}%", help_text="Weighted Absolute Percentage Error")
with col4:
    kpi_card("Dataset", "349 390", help_text="Lignes après nettoyage (2021-2025)")

st.divider()

st.subheader("Pipeline du projet")
st.markdown(
    """
    ```
    Phase 1            Phase 2 / 2bis       Phase 3            Phase 4
    Data Engineering → Études stats + EDA → Modélisation IA → Dashboard
    ```
    """
)

col_left, col_right = st.columns([2, 1])
with col_left:
    st.subheader("Problématique")
    st.markdown(
        "> Comment une approche **Demand-Driven** s'appuyant sur l'IA peut-elle "
        "prédire la demande client réelle (Quantité + Date) pour optimiser la "
        "chaîne d'approvisionnement ?"
    )
    st.subheader("Architecture des modèles")
    st.markdown(
        f"""
        - **Architecture 1 — Quantité** : XGBoost + Optuna (50 essais)
          — MAE **{xgb_best['mae']:.2f}** (baseline {baseline['mae']:.2f})
        - **Architecture 2 — Date** : LSTM time-to-event
          — MAE **{rapport['lstm_time_to_event']['mae_jours']:.1f} j**,
          précision ±7j **{rapport['lstm_time_to_event']['precision_7j']*100:.1f}%**
        """
    )

with col_right:
    st.subheader("Navigation")
    st.markdown(
        """
        - 📂 **Données** — import, révision, sauvegarde
        - 🤖 **IA** — modèle actif, ré-entraînement
        - 📈 **Prévisions** — quantité, date, confiance
        - 🔍 **Analyse** — IA vs baseline, limites
        """
    )
    st.info("Sélectionnez une page dans la barre latérale.")

st.divider()
st.caption(
    f"Dataset enrichi : 349 390 lignes × 35 colonnes  •  "
    f"Splits temporels 2021-2023 / 2024 / 2025  •  "
    f"Cible North Star : précision > 60% (WAPE actuelle {(1-xgb_best['wape'])*100:.1f}%)"
)
