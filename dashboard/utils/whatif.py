"""Simulation what-if : modifier les inputs d'une ligne et re-predire.

Utilise le modele v2 (47 features) + intervalle quantile LightGBM si disponible.
"""
from __future__ import annotations

from copy import deepcopy

import numpy as np
import pandas as pd

from dashboard.utils.features import FEATURES_V2
from dashboard.utils.inference import predict_qte_v2, predict_qte_intervals


def simulate_prediction(
    row: pd.Series,
    overrides: dict[str, float],
) -> dict:
    """Re-predit pour `row` avec les overrides appliques sur les features numeriques.

    Retourne dict avec :
      - pred_actuelle : prediction sans modification
      - pred_simulee : prediction avec overrides
      - delta_pct : variation relative
      - p10 / p90 : intervalle si LGBM quantile dispo, sinon None
    """
    base_df = pd.DataFrame([row[FEATURES_V2].to_dict()])
    pred_actuelle = float(predict_qte_v2(base_df)[0])

    sim_df = base_df.copy()
    for k, v in overrides.items():
        if k in sim_df.columns:
            sim_df.at[0, k] = v
    pred_simulee = float(predict_qte_v2(sim_df)[0])

    intervals = predict_qte_intervals(sim_df)
    if intervals is not None:
        p10 = float(intervals["p10"][0])
        p90 = float(intervals["p90"][0])
    else:
        p10 = None
        p90 = None

    delta_pct = (pred_simulee - pred_actuelle) / max(pred_actuelle, 1e-3) * 100
    return {
        "pred_actuelle": pred_actuelle,
        "pred_simulee": pred_simulee,
        "delta_pct": delta_pct,
        "p10": p10,
        "p90": p90,
    }
