"""Fixtures partagees pour les tests dashboard/utils.

Toutes les fixtures sont synthetiques (pas de chargement parquet lourd)
pour rester executables en CI sans dataset.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(scope="session")
def rng():
    return np.random.default_rng(42)


@pytest.fixture(scope="session")
def tiny_split_train(rng) -> pd.DataFrame:
    """50 lignes synthetiques avec les colonnes minimales utilisees par utils/."""
    n = 50
    dates = pd.date_range("2024-01-01", periods=n, freq="D")
    return pd.DataFrame({
        "date_cmd": dates,
        "code_article_freq": rng.integers(1, 6, n).astype(float),
        "code_client_freq": rng.integers(10, 30, n).astype(float),
        "qte_demandee": rng.gamma(2.0, 5.0, n),
        "delai_demande_jours": rng.integers(1, 15, n).astype(float),
        "prix": rng.uniform(10, 100, n),
        "ipi_valeur": rng.uniform(95, 110, n),
        "qte_lag_1": rng.gamma(2.0, 5.0, n),
        "qte_roll_mean_7": rng.gamma(2.0, 5.0, n),
        "qte_roll_mean_30_article": rng.gamma(2.0, 5.0, n),
        "qte_roll_mean_30_client": rng.gamma(2.0, 5.0, n),
        "qte_roll_mean_30": rng.gamma(2.0, 5.0, n),
    })


@pytest.fixture(scope="session")
def tiny_split_test(rng) -> pd.DataFrame:
    """50 lignes pour simuler la distribution courante (drift)."""
    n = 50
    dates = pd.date_range("2025-01-01", periods=n, freq="D")
    return pd.DataFrame({
        "date_cmd": dates,
        "code_article_freq": rng.integers(1, 6, n).astype(float),
        "code_client_freq": rng.integers(10, 30, n).astype(float),
        "qte_demandee": rng.gamma(2.5, 5.0, n),
        "delai_demande_jours": rng.integers(1, 15, n).astype(float),
        "prix": rng.uniform(10, 100, n) * 1.1,  # leger drift prix
        "ipi_valeur": rng.uniform(95, 110, n),
        "qte_lag_1": rng.gamma(2.5, 5.0, n),
        "qte_roll_mean_7": rng.gamma(2.5, 5.0, n),
        "qte_roll_mean_30_article": rng.gamma(2.5, 5.0, n),
        "qte_roll_mean_30_client": rng.gamma(2.5, 5.0, n),
        "qte_roll_mean_30": rng.gamma(2.5, 5.0, n),
    })
