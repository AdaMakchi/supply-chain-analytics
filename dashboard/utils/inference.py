"""Chargement des modèles Phase 3 et inférence quantité + date.

`torch` est importé en lazy pour que les pages qui n'utilisent que XGBoost
puissent fonctionner même si l'installation torch est cassée (WinError 1114).
"""
from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import streamlit as st

from dashboard.utils.features import (  # re-export pour rétro-compat
    FEATURES,
    FEATURES_V2,
    FEATURES_LSTM,
    SEQ_LEN,
    TARGET_QTE,
)

__all__ = [
    "FEATURES",
    "FEATURES_V2",
    "FEATURES_LSTM",
    "SEQ_LEN",
    "TARGET_QTE",
    "load_xgb_optuna",
    "load_xgb_optuna_v2",
    "load_lstm",
    "load_lgbm_quantile",
    "predict_qte",
    "predict_qte_v2",
    "predict_qte_intervals",
    "predict_date_offset",
]

ROOT = Path(__file__).resolve().parents[2]
MODELS_DIR = ROOT / "models"


@st.cache_resource
def load_xgb_optuna():
    return joblib.load(MODELS_DIR / "xgboost_optuna_final.pkl")


@st.cache_resource
def load_xgb_optuna_v2():
    return joblib.load(MODELS_DIR / "xgboost_optuna_v2.pkl")


@st.cache_resource
def load_lgbm_quantile() -> dict:
    """Charge les 3 modeles quantile (P10, P50, P90). Retourne un dict ou None si absent."""
    quantiles = {}
    for q in ("p10", "p50", "p90"):
        path = MODELS_DIR / f"lgbm_quantile_{q}.pkl"
        if path.exists():
            quantiles[q] = joblib.load(path)
    return quantiles if len(quantiles) == 3 else None


def _build_lstm_model(input_size: int):
    """Construit le LSTMModel — torch importé en lazy."""
    import torch.nn as nn

    class LSTMModel(nn.Module):
        def __init__(self, input_size: int, hidden_size: int = 64, num_layers: int = 2, dropout: float = 0.2):
            super().__init__()
            self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True, dropout=dropout)
            self.fc = nn.Linear(hidden_size, 1)

        def forward(self, x):
            out, _ = self.lstm(x)
            return self.fc(out[:, -1, :]).squeeze(-1)

    return LSTMModel(input_size=input_size)


@st.cache_resource
def load_lstm():
    import torch  # lazy

    model = _build_lstm_model(len(FEATURES_LSTM))
    state = torch.load(MODELS_DIR / "lstm_time_to_event.pt", map_location="cpu")
    if isinstance(state, dict) and "state_dict" in state:
        model.load_state_dict(state["state_dict"])
    else:
        model.load_state_dict(state)
    model.eval()
    return model


def predict_qte(df: pd.DataFrame) -> np.ndarray:
    """Prédit qte_demandee à partir d'un DataFrame contenant les 28 FEATURES."""
    missing = [f for f in FEATURES if f not in df.columns]
    if missing:
        raise ValueError(f"Features manquantes : {missing}")
    model = load_xgb_optuna()
    y_log = model.predict(df[FEATURES])
    return np.clip(np.expm1(y_log), 0, None)


def predict_qte_v2(df: pd.DataFrame) -> np.ndarray:
    """Predit qte_demandee a partir d'un DataFrame contenant les 47 FEATURES_V2."""
    missing = [f for f in FEATURES_V2 if f not in df.columns]
    if missing:
        raise ValueError(f"Features V2 manquantes : {missing}")
    model = load_xgb_optuna_v2()
    y_log = model.predict(df[FEATURES_V2])
    return np.clip(np.expm1(y_log), 0, None)


def predict_qte_intervals(df: pd.DataFrame) -> dict:
    """Retourne dict {p10, p50, p90} si modeles LGBM quantile dispo, sinon None."""
    models = load_lgbm_quantile()
    if models is None:
        return None
    missing = [f for f in FEATURES_V2 if f not in df.columns]
    if missing:
        raise ValueError(f"Features V2 manquantes : {missing}")
    out = {}
    for q, model in models.items():
        y_log = model.predict(df[FEATURES_V2])
        out[q] = np.clip(np.expm1(y_log), 0, None)
    return out


def predict_date_offset(sequences: np.ndarray) -> np.ndarray:
    """Prédit le délai (jours) avant la prochaine commande à partir de séquences (N, SEQ_LEN, F)."""
    import torch  # lazy

    if sequences.ndim != 3 or sequences.shape[1] != SEQ_LEN or sequences.shape[2] != len(FEATURES_LSTM):
        raise ValueError(f"Shape attendue (N, {SEQ_LEN}, {len(FEATURES_LSTM)}), reçu {sequences.shape}")
    model = load_lstm()
    with torch.no_grad():
        return model(torch.tensor(sequences, dtype=torch.float32)).cpu().numpy()
