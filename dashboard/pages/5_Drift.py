"""Page Drift detection — PSI sur features cles vs reference train."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dashboard.utils.drift import (  # noqa: E402
    DEFAULT_DRIFT_FEATURES,
    PSI_THRESHOLDS,
    compute_drift_report,
)

st.set_page_config(page_title="Drift Detection", page_icon=":chart_with_downwards_trend:", layout="wide")
st.title("Drift Detection — Population Stability Index")
st.caption(
    "Compare la distribution des features clees entre le train (reference) et "
    "une distribution actuelle (par defaut : test 2025)."
)

DATA = ROOT / "data" / "processed"

@st.cache_data(ttl=3600)
def load_split_v3(name: str) -> pd.DataFrame:
    return pd.read_parquet(DATA / f"split_{name}_v3_features.parquet")

with st.sidebar:
    st.header("Configuration")
    bins = st.slider("Nombre de bins (quantiles)", 5, 20, 10)
    upload = st.file_uploader("Upload CSV optionnel (current)", type=["csv", "parquet"])
    st.markdown(f"""
    **Seuils PSI**
    - < {PSI_THRESHOLDS['stable']:.2f} : stable
    - {PSI_THRESHOLDS['stable']:.2f} - {PSI_THRESHOLDS['moderate']:.2f} : modere
    - > {PSI_THRESHOLDS['moderate']:.2f} : significatif
    """)

df_ref = load_split_v3("train")
if upload is not None:
    if upload.name.endswith(".parquet"):
        df_cur = pd.read_parquet(upload)
    else:
        df_cur = pd.read_csv(upload)
    st.info(f"Distribution courante : upload utilisateur ({df_cur.shape[0]} lignes)")
else:
    df_cur = load_split_v3("test")
    st.info(f"Distribution courante : split test ({df_cur.shape[0]} lignes — 2025)")

report = compute_drift_report(df_ref, df_cur, features=DEFAULT_DRIFT_FEATURES, bins=bins)

# Bandeau d'alerte
nb_sig = (report["classification"] == "significatif").sum()
nb_mod = (report["classification"] == "modere").sum()
if nb_sig > 0:
    st.error(f":rotating_light: {nb_sig} feature(s) avec drift significatif (PSI > {PSI_THRESHOLDS['moderate']}). Modele potentiellement obsolete.")
elif nb_mod > 0:
    st.warning(f":warning: {nb_mod} feature(s) en drift modere. Surveillance recommandee.")
else:
    st.success(":white_check_mark: Aucun drift detecte sur les features surveillees.")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Tableau PSI par feature")
    def _color(row):
        c = {"stable": "background-color: #d1fae5", "modere": "background-color: #fef3c7",
             "significatif": "background-color: #fee2e2", "absent": "background-color: #e5e7eb",
             "inconnu": "background-color: #e5e7eb"}
        return [c.get(row["classification"], "")] * len(row)
    st.dataframe(
        report.style.format({"psi": "{:.4f}"}).apply(_color, axis=1),
        use_container_width=True,
    )

with col2:
    st.subheader("PSI par feature (barres)")
    chart_data = report.dropna(subset=["psi"]).set_index("feature")["psi"]
    st.bar_chart(chart_data)

st.divider()
st.markdown("""
**Methode** : PSI = somme sur les bins de `(p_cur - p_ref) * log(p_cur / p_ref)`.
Les bins sont definis par quantiles sur la distribution de reference (train), puis appliques
aux deux echantillons. Reference : Karakoulas (2011), industry standard credit risk monitoring.
""")
