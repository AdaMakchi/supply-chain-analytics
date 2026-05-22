"""Page 1 — Gestion des données.

Upload, validation schéma, aperçu, édition manuelle, sauvegarde.
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dashboard.utils.data_loader import load_enrichi  # noqa: E402
from dashboard.utils.features import FEATURES, TARGET_QTE  # noqa: E402

st.set_page_config(page_title="Données — GE", page_icon="📂", layout="wide")
st.title("📂 Gestion des données")
st.caption("Importez un dataset enrichi (Mode A), révisez les anomalies, sauvegardez.")

st.divider()

# ----------------------------- Upload ---------------------------------------
st.subheader("1. Import")
uploaded = st.file_uploader(
    "Fichier CSV ou Parquet (28 features encodées + qte_demandee)",
    type=["csv", "parquet", "xlsx"],
)

if uploaded is None:
    st.info("Aucun fichier importé — affichage du dataset enrichi de référence.")
    df = load_enrichi()
    source = "dataset_ml_enrichi.parquet"
else:
    suffix = Path(uploaded.name).suffix.lower()
    if suffix == ".csv":
        df = pd.read_csv(uploaded)
    elif suffix == ".parquet":
        df = pd.read_parquet(uploaded)
    elif suffix == ".xlsx":
        df = pd.read_excel(uploaded)
    else:
        st.error(f"Extension non supportée : {suffix}")
        st.stop()
    source = uploaded.name

# ----------------------------- Validation schéma ----------------------------
st.subheader("2. Validation du schéma")
missing = [f for f in FEATURES if f not in df.columns]
has_target = TARGET_QTE in df.columns

if missing:
    st.error(f"❌ Features manquantes : {missing}")
else:
    st.success(f"✅ 28 features présentes dans `{source}`")
if not has_target:
    st.warning(f"⚠️ Colonne cible `{TARGET_QTE}` absente — prévisions impossibles.")

# ----------------------------- Métadonnées ----------------------------------
st.subheader("3. Aperçu du dataset")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Lignes", f"{len(df):,}")
if "date_cmd" in df.columns:
    dmin, dmax = pd.to_datetime(df["date_cmd"]).min(), pd.to_datetime(df["date_cmd"]).max()
    col2.metric("Période", f"{dmin.date()} → {dmax.date()}")
col3.metric("Articles uniques", df.get("code_article_freq", pd.Series()).nunique() if "code_article_freq" in df.columns else "—")
col4.metric("Clients uniques", df.get("code_client_freq", pd.Series()).nunique() if "code_client_freq" in df.columns else "—")

# ----------------------------- Qualité --------------------------------------
st.subheader("4. Contrôles qualité")
nan_pct = (df.isna().mean() * 100).round(2)
nan_pct = nan_pct[nan_pct > 0].sort_values(ascending=False)
if nan_pct.empty:
    st.success("✅ Aucune valeur manquante détectée")
else:
    st.warning("Colonnes avec NaN :")
    st.dataframe(nan_pct.rename("% NaN").to_frame(), use_container_width=False)

if has_target:
    neg = int((df[TARGET_QTE] < 0).sum())
    if neg:
        st.error(f"⚠️ {neg} lignes avec qte_demandee < 0")

# ----------------------------- Édition --------------------------------------
st.subheader("5. Révision manuelle (premières 1 000 lignes)")
edited = st.data_editor(df.head(1000), use_container_width=True, num_rows="dynamic", key="editor")

# ----------------------------- Sauvegarde -----------------------------------
st.subheader("6. Sauvegarde")
if st.button("💾 Sauvegarder les modifications", type="primary", disabled=bool(missing)):
    out_dir = ROOT / "data" / "processed"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"dataset_user_{stamp}.parquet"
    # On sauvegarde le df d'origine avec les éventuelles édits remplacés
    df_final = df.copy()
    df_final.iloc[: len(edited)] = edited.values
    df_final.to_parquet(out_path, index=False)
    st.success(f"✅ Enregistré : `{out_path.relative_to(ROOT)}`")
