"""Dashboard GE — Page d'accueil."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dashboard.components.kpi_card import kpi_card  # noqa: E402
from dashboard.utils.data_loader import load_rapport_modelisation  # noqa: E402


@st.cache_data(ttl=3600)
def _load_sprint_a_v2() -> dict | None:
    p = ROOT / "reports" / "sprint_a_chantier1_metrics.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


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
baseline_v1 = rapport["baseline"]
sprint_a = _load_sprint_a_v2()

if sprint_a:
    v2 = sprint_a["test_metrics_v2"]
    mae = v2["MAE"]
    rmse = v2["RMSE"]
    r2 = v2["R2"]
    wape = v2["WAPE"]
    n_features = sprint_a["n_features"]
    n_trials = sprint_a["n_trials_optuna"]
    gain_mae = (baseline_v1["mae"] - mae) / baseline_v1["mae"] * 100
else:
    xgb_best = rapport["xgboost_optuna_final"]
    mae, rmse, r2, wape = xgb_best["mae"], xgb_best["rmse"], xgb_best["r2"], xgb_best["wape"]
    n_features = len(rapport["features"])
    n_trials = 50
    gain_mae = (baseline_v1["mae"] - mae) / baseline_v1["mae"] * 100

col1, col2, col3, col4 = st.columns(4)
with col1:
    kpi_card("MAE XGBoost v2", f"{mae:.2f}", f"-{gain_mae:.1f}% vs baseline")
with col2:
    kpi_card("R² test (2025)", f"{r2:.3f}", help_text="Coefficient de détermination")
with col3:
    kpi_card("WAPE", f"{wape*100:.1f}%", help_text="Weighted Absolute Percentage Error")
with col4:
    kpi_card("Précision (1 − WAPE)", f"{(1-wape)*100:.1f}%", help_text="Cible North Star : > 60 %")

st.divider()

st.subheader("Pipeline du projet")
st.markdown(
    """
    ```
    Data Engineering → EDA & études statistiques → Modélisation IA → Industrialisation → Dashboard
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
        - **XGBoost v2** (production) — {n_features} features, Optuna {n_trials} essais
          — MAE **{mae:.2f}** (baseline {baseline_v1['mae']:.2f}, −{gain_mae:.1f} %)
        - **LightGBM Quantile** P10/P50/P90 — intervalles de confiance
        - **CatBoost + Stacking Ridge** — meilleur RMSE/R²
        - **Baseline DDMRP** (Ptak & Smith 2016) — comparaison opérationnelle
        - **LSTM time-to-event** — date probable, MAE **{rapport['lstm_time_to_event']['mae_jours']:.1f} j**
        """
    )

with col_right:
    st.subheader("Navigation")
    st.markdown(
        """
        - 📂 **Données** — import, révision, sauvegarde
        - 🤖 **IA** — modèle actif, re-train
        - 📈 **Prévisions** — quantité + what-if
        - 🔍 **Analyse** — IA vs baseline, limites
        - 📉 **Drift** — PSI features
        - 📊 **Backtest 2025** — slider semaine
        """
    )
    st.info("Sélectionnez une page dans la barre latérale.")

st.divider()
st.caption(
    f"Dataset enrichi : 349 390 lignes × 35 colonnes  •  "
    f"Splits temporels 2021-2023 / 2024 / 2025  •  "
    f"Cible North Star : précision > 60 % (actuel **{(1-wape)*100:.1f} %**)"
)
