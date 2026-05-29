"""Page Backtest interactif — slider temporel sur 2025."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dashboard.utils.data_loader import load_backtest_2025  # noqa: E402

st.set_page_config(page_title="Backtest 2025", page_icon=":bar_chart:", layout="wide")
st.title("Backtest interactif — Si on avait utilise le modele en 2025...")
st.caption(
    "Cumul des predictions hebdomadaires vs realite. Choisir le(s) modele(s) "
    "a comparer et la semaine d'arret."
)

backtest = load_backtest_2025()
if backtest is None:
    st.error(
        "`data/processed/backtest_2025.parquet` absent. "
        "Lancez d'abord le notebook `11_backtest_2025_precompute.ipynb`."
    )
    st.stop()

available_models = []
labels = {
    "pred_xgb_v2": "XGBoost v2",
    "pred_lgbm_p50": "LightGBM P50",
    "pred_catboost": "CatBoost",
    "pred_stacking": "Stacking Ridge",
    "pred_baseline": "Baseline (mediane)",
}
for col, lab in labels.items():
    if col in backtest.columns and backtest[col].notna().any():
        available_models.append((col, lab))

with st.sidebar:
    st.header("Configuration")
    weeks = sorted(backtest["semaine_iso"].unique())
    week_max = st.slider("Semaine d'arret (ISO)", int(min(weeks)), int(max(weeks)), int(max(weeks)))
    selected = st.multiselect(
        "Modeles a comparer",
        [m[1] for m in available_models],
        default=[m[1] for m in available_models[:3]],
    )
    alpha = st.number_input("Cout unitaire rupture (alpha)", value=50.0, step=10.0)
    beta = st.number_input("Cout unitaire sur-stock (beta)", value=1.0, step=1.0)

selected_cols = [c for c, lab in available_models if lab in selected]
if not selected_cols:
    st.warning("Selectionnez au moins un modele.")
    st.stop()

window = backtest[backtest["semaine_iso"] <= week_max].copy()

# Metriques rolling 4 semaines (sur fenetre [week_max-3, week_max])
rolling_low = max(int(min(weeks)), week_max - 3)
rolling = backtest[(backtest["semaine_iso"] >= rolling_low) & (backtest["semaine_iso"] <= week_max)]

st.subheader(f"Cumul jusqu'a la semaine {week_max}")
weekly = window.groupby("semaine_iso").agg(
    qte_reelle_cumul=("qte_reelle", "sum"),
    **{f"{c}_cumul": (c, "sum") for c in selected_cols},
).cumsum().reset_index()

fig = px.line(weekly, x="semaine_iso", y=["qte_reelle_cumul"] + [f"{c}_cumul" for c in selected_cols],
              labels={"value": "Quantite cumulee", "semaine_iso": "Semaine ISO"})
fig.for_each_trace(lambda t: t.update(name=labels.get(t.name.replace("_cumul", ""), t.name).replace("_cumul", "")))
st.plotly_chart(fig, use_container_width=True)

st.divider()

st.subheader(f"Metriques rolling 4 semaines (sem. {rolling_low} -> {week_max})")
y_true = rolling["qte_reelle"].values
cols_metric = st.columns(len(selected_cols) + 1)
cols_metric[0].metric("Nb lignes fenetre", len(rolling))
for i, col in enumerate(selected_cols):
    y_pred = rolling[col].values
    mae = float(np.mean(np.abs(y_true - y_pred)))
    wape = float(np.sum(np.abs(y_true - y_pred)) / max(np.sum(np.abs(y_true)), 1e-6))
    cols_metric[i + 1].metric(labels[col], f"MAE {mae:.2f}", f"WAPE {wape*100:.1f}%")

st.divider()

st.subheader("Cout cumule (alpha x ruptures + beta x sur-stock)")
cost_rows = []
for col in selected_cols:
    err_under = np.maximum(window["qte_reelle"].values - window[col].values, 0)
    err_over = np.maximum(window[col].values - window["qte_reelle"].values, 0)
    cost = alpha * err_under.sum() + beta * err_over.sum()
    cost_rows.append({"modele": labels[col], "cout_total": float(cost),
                      "ruptures (unites)": float(err_under.sum()),
                      "surstock (unites)": float(err_over.sum())})
st.dataframe(pd.DataFrame(cost_rows), use_container_width=True, hide_index=True)

st.divider()

st.subheader("Top 10 erreurs absolues (semaine d'arret)")
last_week = window[window["semaine_iso"] == week_max].copy()
if not last_week.empty:
    main_col = selected_cols[0]
    last_week["err_abs"] = (last_week["qte_reelle"] - last_week[main_col]).abs()
    top = last_week.nlargest(10, "err_abs")[
        ["code_client_freq", "code_article_freq", "qte_reelle", main_col, "err_abs"]
    ].rename(columns={main_col: labels[main_col]})
    st.dataframe(top, use_container_width=True, hide_index=True)
else:
    st.info(f"Aucune ligne pour la semaine {week_max}")
