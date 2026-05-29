"""Generateur de stock initial fictif par article.

Utilise:
- Couverture cible (par defaut 30 jours de demande moyenne)
- ADU (Average Daily Usage) calcule sur train

Fournit egalement un generateur de commandes en cours (on_order) optionnel.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class StockProfile:
    code_article_freq: float
    on_hand: float
    on_order: float
    adu: float
    lt_jours: float


def compute_adu(
    df_train: pd.DataFrame,
    date_col: str = "date_cmd",
    target_col: str = "qte_demandee",
    article_col: str = "code_article_freq",
    window_days: int = 90,
) -> pd.Series:
    """ADU = moyenne `qte_demandee/jour` sur les `window_days` derniers jours du train.

    Si l'article n'a pas d'observation dans la fenetre, on retombe sur l'ADU global.
    """
    end_date = df_train[date_col].max()
    start_date = end_date - pd.Timedelta(days=window_days)
    mask = df_train[date_col] >= start_date
    recent = df_train.loc[mask].copy()
    if recent.empty:
        recent = df_train.copy()
        nb_jours = max((df_train[date_col].max() - df_train[date_col].min()).days, 1)
    else:
        nb_jours = max((recent[date_col].max() - recent[date_col].min()).days, 1)
    sum_by_article = recent.groupby(article_col)[target_col].sum()
    adu = sum_by_article / nb_jours
    return adu.replace([np.inf, -np.inf], np.nan).fillna(adu.median())


def compute_lt(
    df_train: pd.DataFrame,
    article_col: str = "code_article_freq",
    lt_col: str = "delai_demande_jours",
) -> pd.Series:
    """LT (lead time) median par article. Fallback global si valeur manquante."""
    lt = df_train.groupby(article_col)[lt_col].median()
    return lt.fillna(df_train[lt_col].median()).clip(lower=1)


def generate_stock_mock(
    df_train: pd.DataFrame,
    coverage_days: int = 30,
    seed: int = 42,
) -> pd.DataFrame:
    """Genere un stock initial fictif par article.

    Hypothese de travail (documentee dans le rapport) : pour chaque article,
    le stock initial vaut `coverage_days * ADU * facteur_aleatoire(0.7, 1.3)`.

    Returns
    -------
    DataFrame `(code_article_freq, on_hand, on_order, adu, lt_jours)`.
    """
    rng = np.random.default_rng(seed)
    adu = compute_adu(df_train)
    lt = compute_lt(df_train).reindex(adu.index).fillna(7.0)
    noise = rng.uniform(0.7, 1.3, size=len(adu))
    on_hand = (coverage_days * adu.values) * noise
    # Quelques articles en rupture initiale (~5%)
    rupture_mask = rng.random(len(adu)) < 0.05
    on_hand[rupture_mask] = 0.0
    # On_order = pour ~10% des articles, une commande en cours egale a ~LT * ADU
    on_order = np.zeros(len(adu))
    cmd_mask = rng.random(len(adu)) < 0.1
    on_order[cmd_mask] = (lt.values[cmd_mask] * adu.values[cmd_mask])

    return pd.DataFrame({
        "code_article_freq": adu.index,
        "on_hand": np.round(on_hand, 2),
        "on_order": np.round(on_order, 2),
        "adu": np.round(adu.values, 4),
        "lt_jours": np.round(lt.values, 1),
    }).reset_index(drop=True)
