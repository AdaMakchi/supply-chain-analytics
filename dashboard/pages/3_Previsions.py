"""Page 3 — Prévisions de ventes.

Sélecteur client/article/horizon, prévision quantité + date, score de confiance,
graphique pred vs réel, export.
"""
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

from dashboard.components.confidence_badge import badge  # noqa: E402
from dashboard.utils.confidence import confidence_level  # noqa: E402
from dashboard.utils.data_loader import historical_stats, load_split  # noqa: E402
from dashboard.utils.features import TARGET_QTE  # noqa: E402
from dashboard.utils.inference import predict_qte  # noqa: E402

st.set_page_config(page_title="Prévisions — GE", page_icon="📈", layout="wide")
st.title("📈 Prévisions de ventes")
st.caption("Quantité demandée + date probable, avec score de confiance composite.")

st.divider()

# ----------------------------- Chargement -----------------------------------
df_train = load_split("train")
df_test = load_split("test")
hist = historical_stats(df_train)

# ----------------------------- Filtres --------------------------------------
st.subheader("Filtres")
col1, col2, col3 = st.columns(3)
with col1:
    articles = sorted(df_test["code_article_freq"].dropna().unique())
    sel_art = st.multiselect("Articles", articles, default=articles[:5])
with col2:
    clients = sorted(df_test["code_client_freq"].dropna().unique())
    sel_cli = st.multiselect("Clients", clients, default=clients[:5])
with col3:
    horizon = st.selectbox("Horizon", ["M+1", "M+2", "M+3"], index=0)

mask = pd.Series(True, index=df_test.index)
if sel_art:
    mask &= df_test["code_article_freq"].isin(sel_art)
if sel_cli:
    mask &= df_test["code_client_freq"].isin(sel_cli)
df_filtered = df_test[mask].head(500).copy()

if df_filtered.empty:
    st.warning("Aucune ligne ne correspond aux filtres.")
    st.stop()

# ----------------------------- Prévision ------------------------------------
st.subheader(f"Prévisions ({len(df_filtered)} lignes)")
preds = predict_qte(df_filtered)
df_filtered["qte_predite"] = preds.round(2)

# Confiance
levels = [
    confidence_level(p, art, cli, hist)
    for p, art, cli in zip(preds, df_filtered["code_article_freq"], df_filtered["code_client_freq"])
]
df_filtered["confiance"] = levels

# Affichage
display_cols = ["code_client_freq", "code_article_freq", "qte_predite"]
if TARGET_QTE in df_filtered.columns:
    display_cols.append(TARGET_QTE)
    df_filtered["erreur_abs"] = (df_filtered[TARGET_QTE] - df_filtered["qte_predite"]).abs().round(2)
    display_cols.append("erreur_abs")
display_cols.append("confiance")

st.dataframe(df_filtered[display_cols], use_container_width=True, hide_index=True)

# Légende confiance
st.markdown(
    "**Légende confiance :** "
    + badge("vert") + " article familier + écart faible &nbsp;&nbsp; "
    + badge("orange") + " article rare ou écart modéré &nbsp;&nbsp; "
    + badge("rouge") + " article inconnu ou prédiction extrême",
    unsafe_allow_html=True,
)

st.divider()

# ----------------------------- Pred vs réel ---------------------------------
if TARGET_QTE in df_filtered.columns:
    st.subheader("Prédiction vs valeur réelle (test 2025)")
    fig = px.scatter(
        df_filtered,
        x=TARGET_QTE,
        y="qte_predite",
        color="confiance",
        color_discrete_map={"vert": "#16a34a", "orange": "#f59e0b", "rouge": "#dc2626"},
        hover_data=["code_client_freq", "code_article_freq"],
        opacity=0.7,
    )
    lim = float(max(df_filtered[TARGET_QTE].max(), df_filtered["qte_predite"].max()))
    fig.add_shape(type="line", x0=0, y0=0, x1=lim, y1=lim, line=dict(dash="dash", color="gray"))
    fig.update_layout(xaxis_title="Valeur réelle", yaxis_title="Prédiction")
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ----------------------------- Export ---------------------------------------
st.subheader("Export")
csv = df_filtered[display_cols].to_csv(index=False).encode("utf-8")
st.download_button(
    "⬇️ Télécharger en CSV",
    data=csv,
    file_name="previsions.csv",
    mime="text/csv",
)
