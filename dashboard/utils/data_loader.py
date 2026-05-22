"""Chargement et cache des datasets parquet/csv et du rapport modélisation."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"


@st.cache_data(ttl=3600)
def load_split(name: str) -> pd.DataFrame:
    """name ∈ {'train', 'val', 'test'}"""
    path = PROCESSED / f"split_{name}.parquet"
    return pd.read_parquet(path)


@st.cache_data(ttl=3600)
def load_enrichi() -> pd.DataFrame:
    return pd.read_parquet(PROCESSED / "dataset_ml_enrichi.parquet")


@st.cache_data(ttl=3600)
def load_rapport_modelisation() -> dict:
    with open(REPORTS / "rapport_modelisation.json", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(ttl=600)
def historical_stats(df_train: pd.DataFrame) -> dict:
    """Statistiques historiques pour score de confiance + baseline."""
    art_count = df_train["code_article_freq"].value_counts().to_dict()
    couple_median = (
        df_train.groupby(["code_client_freq", "code_article_freq"])["qte_demandee"]
        .median()
        .to_dict()
    )
    quantiles = df_train["qte_demandee"].quantile([0.1, 0.5, 0.9, 0.95]).to_dict()
    return {
        "art_count": art_count,
        "couple_median": couple_median,
        "quantiles": quantiles,
        "global_median": float(df_train["qte_demandee"].median()),
    }
