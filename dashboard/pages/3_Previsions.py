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
from dashboard.utils.data_loader import historical_stats, load_split_v3  # noqa: E402
from dashboard.utils.features import TARGET_QTE  # noqa: E402
from dashboard.utils.inference import predict_qte_v2  # noqa: E402

st.set_page_config(page_title="Prévisions — GE", page_icon="📈", layout="wide")
st.title("📈 Prévisions de ventes")
st.caption("Quantité demandée (XGBoost v2 — 47 features) avec score de confiance composite.")

st.divider()

# ----------------------------- Chargement -----------------------------------
df_train = load_split_v3("train")
df_test = load_split_v3("test")
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
st.subheader(f"Prévisions ({len(df_filtered)} lignes) — XGBoost v2")
preds = predict_qte_v2(df_filtered)
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

st.divider()

# ----------------------------- What-If Simulation ---------------------------
st.subheader("🔬 Simulation what-if (modèle v2)")
st.caption(
    "Sélectionnez une ligne du dataset test et modifiez les features pour observer "
    "l'effet sur la prédiction. Modèle XGBoost v2 (47 features) + intervalle quantile P10–P90."
)

try:
    from dashboard.utils.data_loader import load_split_v3
    from dashboard.utils.features import FEATURES_V2
    from dashboard.utils.whatif import simulate_prediction

    df_test_v3 = load_split_v3("test")
    sample_size = min(500, len(df_test_v3))
    sample_v3 = df_test_v3.sample(n=sample_size, random_state=42).reset_index(drop=True)

    sel_idx = st.number_input(
        "Index de la ligne (0 à {})".format(sample_size - 1),
        min_value=0,
        max_value=sample_size - 1,
        value=0,
        step=1,
    )
    row = sample_v3.iloc[int(sel_idx)]

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        prix_factor = st.slider("Prix (× facteur)", 0.5, 1.5, 1.0, 0.05)
    with col_b:
        delai = st.slider(
            "Délai demandé (jours)",
            0, 30, int(row["delai_demande_jours"]),
        )
    with col_c:
        ipi_factor = st.slider("IPI (× facteur)", 0.9, 1.1, 1.0, 0.01)

    col_d, col_e = st.columns(2)
    with col_d:
        peak_toggle = st.toggle("Période peak", value=bool(row.get("est_periode_peak_liv_dem", 0)))
    with col_e:
        ferie_toggle = st.toggle("Jour férié livraison", value=bool(row.get("est_jour_ferie_liv_dem", 0)))

    overrides = {
        "prix": float(row["prix"]) * prix_factor,
        "delai_demande_jours": float(delai),
        "ipi_valeur": float(row["ipi_valeur"]) * ipi_factor,
        "est_periode_peak_liv_dem": int(peak_toggle),
        "est_jour_ferie_liv_dem": int(ferie_toggle),
    }

    result = simulate_prediction(row, overrides)

    col_x, col_y, col_z = st.columns(3)
    col_x.metric("Prédiction actuelle", f"{result['pred_actuelle']:.2f}")
    col_y.metric(
        "Prédiction simulée",
        f"{result['pred_simulee']:.2f}",
        delta=f"{result['delta_pct']:+.1f}%",
    )
    if result["p10"] is not None:
        col_z.metric(
            "Intervalle P10 – P90",
            f"{result['p10']:.1f} – {result['p90']:.1f}",
        )
    else:
        col_z.info("Intervalle indisponible (modèle quantile absent)")

    with st.expander("Voir features modifiées"):
        diff_df = pd.DataFrame({
            "feature": list(overrides.keys()),
            "valeur_initiale": [row[k] for k in overrides],
            "valeur_simulee": list(overrides.values()),
        })
        st.dataframe(diff_df, use_container_width=True, hide_index=True)

except Exception as exc:
    st.warning(f"Simulation what-if indisponible : {exc}")
