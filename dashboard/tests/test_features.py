"""Tests sur la liste de features et leur coherence avec le modele."""
from __future__ import annotations

from pathlib import Path

import joblib
import pytest

from dashboard.utils.features import FEATURES, FEATURES_V2, TARGET_QTE


def test_features_v1_length():
    assert len(FEATURES) == 28


def test_features_v2_length():
    assert len(FEATURES_V2) == 47


def test_features_v2_includes_v1():
    for f in FEATURES:
        assert f in FEATURES_V2


def test_target_qte_string():
    assert TARGET_QTE == "qte_demandee"


@pytest.mark.skipif(
    not (Path(__file__).resolve().parents[2] / "models" / "xgboost_optuna_v2.pkl").exists(),
    reason="modele v2 absent (run preflight notebook)",
)
def test_features_v2_match_model():
    model_path = Path(__file__).resolve().parents[2] / "models" / "xgboost_optuna_v2.pkl"
    model = joblib.load(model_path)
    booster_features = model.get_booster().feature_names
    assert booster_features == FEATURES_V2, "FEATURES_V2 desync avec le modele entraine"
