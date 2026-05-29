"""Baseline DDMRP (Demand-Driven Material Requirements Planning).

Reference : Ptak & Smith (2016), *Demand-Driven Material Requirements Planning*.

Pipeline :
1. Strategic Inventory Positioning : top N articles (Pareto sur train).
2. Buffer Profiles & Levels : Red / Yellow / Green Zones par article.
3. Net Flow Position (NFP) = On-Hand + On-Order - Qualified Demand.
4. Decision de reappro : NFP < TOY -> commander (TOG - NFP).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class DDMRPBuffer:
    code_article_freq: float
    adu: float
    lt_jours: float
    variability_factor: float
    order_cycle_jours: int
    red_zone: float
    yellow_zone: float
    green_zone: float

    @property
    def top_of_red(self) -> float:
        return self.red_zone

    @property
    def top_of_yellow(self) -> float:
        return self.red_zone + self.yellow_zone

    @property
    def top_of_green(self) -> float:
        return self.red_zone + self.yellow_zone + self.green_zone


def select_strategic_articles(
    df_train: pd.DataFrame,
    coverage_pct: float = 0.80,
    article_col: str = "code_article_freq",
    qte_col: str = "qte_demandee",
) -> list[float]:
    """Renvoie la liste des articles cumulant `coverage_pct` du volume total (Pareto)."""
    volumes = df_train.groupby(article_col)[qte_col].sum().sort_values(ascending=False)
    cumul = volumes.cumsum() / volumes.sum()
    seuil_idx = (cumul <= coverage_pct).sum() + 1
    return volumes.index[: max(1, seuil_idx)].tolist()


def _coef_variation(s: pd.Series) -> float:
    mean = s.mean()
    if mean <= 0:
        return 0.0
    return s.std(ddof=0) / mean


def compute_buffers(
    df_train: pd.DataFrame,
    articles: list[float],
    order_cycle_jours: int = 7,
    window_days: int = 90,
    date_col: str = "date_cmd",
    article_col: str = "code_article_freq",
    qte_col: str = "qte_demandee",
    lt_col: str = "delai_demande_jours",
) -> pd.DataFrame:
    """Calcule les buffers DDMRP par article."""
    end_date = df_train[date_col].max()
    start_date = end_date - pd.Timedelta(days=window_days)
    recent = df_train.loc[df_train[date_col] >= start_date]
    nb_jours = max((recent[date_col].max() - recent[date_col].min()).days, 1)
    rows = []
    for art in articles:
        sub = recent.loc[recent[article_col] == art]
        if sub.empty:
            sub = df_train.loc[df_train[article_col] == art]
            if sub.empty:
                continue
            local_days = max((sub[date_col].max() - sub[date_col].min()).days, 1)
        else:
            local_days = nb_jours
        adu = sub[qte_col].sum() / local_days
        lt = max(float(np.median(sub[lt_col])), 1.0)
        cv = _coef_variation(sub[qte_col])
        if cv < 0.5:
            variability_factor = 0.25
        elif cv < 1.0:
            variability_factor = 0.5
        else:
            variability_factor = 0.75
        red = adu * lt * variability_factor
        yellow = adu * lt
        green = adu * lt * (order_cycle_jours / max(lt, 1.0))
        rows.append({
            "code_article_freq": art,
            "adu": adu,
            "lt_jours": lt,
            "variability_factor": variability_factor,
            "order_cycle_jours": order_cycle_jours,
            "red_zone": red,
            "yellow_zone": yellow,
            "green_zone": green,
            "top_of_red": red,
            "top_of_yellow": red + yellow,
            "top_of_green": red + yellow + green,
        })
    return pd.DataFrame(rows)


def compute_nfp(
    on_hand: float,
    on_order: float,
    qualified_demand: float,
) -> float:
    """Net Flow Position = On-Hand + On-Order - Qualified Demand."""
    return on_hand + on_order - qualified_demand


def decide_replenishment(
    nfp: float,
    buffer: DDMRPBuffer | pd.Series,
) -> float:
    """Si NFP < top_of_yellow -> commander (top_of_green - NFP). Sinon 0."""
    if isinstance(buffer, pd.Series):
        toy = buffer["top_of_yellow"]
        tog = buffer["top_of_green"]
    else:
        toy = buffer.top_of_yellow
        tog = buffer.top_of_green
    if nfp < toy:
        return max(tog - nfp, 0.0)
    return 0.0


def simulate_ddmrp_week(
    df_week: pd.DataFrame,
    buffers: pd.DataFrame,
    stock: pd.DataFrame,
    qte_col: str = "qte_demandee",
    article_col: str = "code_article_freq",
) -> pd.DataFrame:
    """Simule une semaine DDMRP : evalue NFP, decide reappro, retourne ruptures + cmds.

    Approximation : on agrege la demande par article sur la semaine, on compare
    au stock initial, on emet une commande si NFP < TOY.
    """
    weekly_demand = df_week.groupby(article_col)[qte_col].sum().rename("qualified_demand")
    merged = (
        buffers.merge(stock, on=article_col, how="left")
        .merge(weekly_demand, on=article_col, how="left")
    )
    merged["qualified_demand"] = merged["qualified_demand"].fillna(0.0)
    merged["on_hand"] = merged["on_hand"].fillna(0.0)
    merged["on_order"] = merged["on_order"].fillna(0.0)
    merged["nfp"] = merged["on_hand"] + merged["on_order"] - merged["qualified_demand"]
    merged["ordered_qte"] = np.where(
        merged["nfp"] < merged["top_of_yellow"],
        np.maximum(merged["top_of_green"] - merged["nfp"], 0.0),
        0.0,
    )
    # Rupture si stock disponible < demande
    merged["rupture"] = np.maximum(merged["qualified_demand"] - merged["on_hand"], 0.0)
    return merged[[
        article_col,
        "qualified_demand",
        "on_hand",
        "nfp",
        "top_of_yellow",
        "top_of_green",
        "ordered_qte",
        "rupture",
    ]]
