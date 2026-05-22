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
    FEATURES_LSTM,
    SEQ_LEN,
    TARGET_QTE,
)

__all__ = [
    "FEATURES",
    "FEATURES_LSTM",
    "SEQ_LEN",
    "TARGET_QTE",
    "load_xgb_optuna",
    "load_lstm",
    "predict_qte",
    "predict_date_offset",
]

ROOT = Path(__file__).resolve().parents[2]
MODELS_DIR = ROOT / "models"


@st.cache_resource
def load_xgb_optuna():
    return joblib.load(MODELS_DIR / "xgboost_optuna_final.pkl")


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


def predict_date_offset(sequences: np.ndarray) -> np.ndarray:
    """Prédit le délai (jours) avant la prochaine commande à partir de séquences (N, SEQ_LEN, F)."""
    import torch  # lazy

    if sequences.ndim != 3 or sequences.shape[1] != SEQ_LEN or sequences.shape[2] != len(FEATURES_LSTM):
        raise ValueError(f"Shape attendue (N, {SEQ_LEN}, {len(FEATURES_LSTM)}), reçu {sequences.shape}")
    model = load_lstm()
    with torch.no_grad():
        return model(torch.tensor(sequences, dtype=torch.float32)).cpu().numpy()
