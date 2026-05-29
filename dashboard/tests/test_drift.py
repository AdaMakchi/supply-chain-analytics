"""Tests PSI : meme distribution => PSI ~ 0, distribution decalee => PSI > seuil."""
from __future__ import annotations

import numpy as np

from dashboard.utils.drift import classify_psi, compute_drift_report, psi


def test_psi_same_distribution(rng):
    a = rng.normal(0, 1, 5000)
    b = rng.normal(0, 1, 5000)
    val = psi(a, b, bins=10)
    assert val < 0.05, f"Meme distribution -> PSI doit etre proche de 0 (got {val})"


def test_psi_shifted_distribution(rng):
    a = rng.normal(0, 1, 5000)
    b = rng.normal(2, 1, 5000)  # gros decalage
    val = psi(a, b, bins=10)
    assert val > 0.25, f"Distribution decalee -> PSI > 0.25 attendu (got {val})"


def test_psi_handles_nan(rng):
    a = np.concatenate([rng.normal(0, 1, 100), [np.nan, np.nan]])
    b = rng.normal(0, 1, 100)
    val = psi(a, b)
    assert np.isfinite(val)


def test_classify_psi():
    assert classify_psi(0.05) == "stable"
    assert classify_psi(0.15) == "modere"
    assert classify_psi(0.40) == "significatif"
    assert classify_psi(float("nan")) == "inconnu"


def test_compute_drift_report(tiny_split_train, tiny_split_test):
    report = compute_drift_report(
        tiny_split_train,
        tiny_split_test,
        features=["prix", "qte_demandee", "ipi_valeur"],
        bins=5,
    )
    assert set(report.columns) == {"feature", "psi", "classification"}
    assert len(report) == 3
    # Trie decroissant
    psis = report["psi"].dropna().values
    if len(psis) > 1:
        assert all(psis[i] >= psis[i + 1] for i in range(len(psis) - 1))
