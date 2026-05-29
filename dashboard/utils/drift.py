"""Drift detection via Population Stability Index (PSI).

Interpretation :
- PSI < 0.10  : pas de drift significatif
- 0.10-0.25  : drift modere, surveillance recommandee
- > 0.25     : drift important, modele potentiellement obsolete
"""
from __future__ import annotations

import numpy as np
import pandas as pd

PSI_THRESHOLDS = {
    "stable": 0.10,
    "moderate": 0.25,
}

# Top 6 features par importance permutation (cf sprint_a_permutation_importance.csv)
DEFAULT_DRIFT_FEATURES = [
    "qte_roll_mean_7",
    "qte_roll_mean_30_article",
    "qte_roll_mean_30",
    "qte_roll_mean_30_client",
    "prix",
    "ipi_valeur",
]


def psi(reference: np.ndarray, current: np.ndarray, bins: int = 10) -> float:
    """Population Stability Index entre une distribution de reference et une distribution actuelle.

    Les bins sont definis par quantiles sur la reference puis appliques aux deux echantillons.
    """
    reference = np.asarray(reference, dtype=float)
    current = np.asarray(current, dtype=float)
    reference = reference[~np.isnan(reference)]
    current = current[~np.isnan(current)]
    if reference.size == 0 or current.size == 0:
        return float("nan")
    quantiles = np.linspace(0.0, 1.0, bins + 1)
    edges = np.quantile(reference, quantiles)
    edges = np.unique(edges)
    if edges.size < 2:
        return 0.0
    edges[0] = -np.inf
    edges[-1] = np.inf
    ref_counts, _ = np.histogram(reference, bins=edges)
    cur_counts, _ = np.histogram(current, bins=edges)
    eps = 1e-6
    ref_pct = ref_counts / max(ref_counts.sum(), 1) + eps
    cur_pct = cur_counts / max(cur_counts.sum(), 1) + eps
    return float(np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct)))


def classify_psi(value: float) -> str:
    if np.isnan(value):
        return "inconnu"
    if value < PSI_THRESHOLDS["stable"]:
        return "stable"
    if value < PSI_THRESHOLDS["moderate"]:
        return "modere"
    return "significatif"


def compute_drift_report(
    df_reference: pd.DataFrame,
    df_current: pd.DataFrame,
    features: list[str] | None = None,
    bins: int = 10,
) -> pd.DataFrame:
    """Calcule PSI par feature et retourne un DataFrame trie par PSI decroissant."""
    if features is None:
        features = DEFAULT_DRIFT_FEATURES
    rows = []
    for f in features:
        if f not in df_reference.columns or f not in df_current.columns:
            rows.append({"feature": f, "psi": float("nan"), "classification": "absent"})
            continue
        val = psi(df_reference[f].values, df_current[f].values, bins=bins)
        rows.append({"feature": f, "psi": val, "classification": classify_psi(val)})
    return pd.DataFrame(rows).sort_values("psi", ascending=False, na_position="last").reset_index(drop=True)
