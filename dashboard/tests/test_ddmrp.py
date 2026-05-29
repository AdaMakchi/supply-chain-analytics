"""Tests DDMRP : buffers, NFP, decision de reappro."""
from __future__ import annotations

import numpy as np
import pandas as pd

from dashboard.utils.ddmrp import (
    compute_buffers,
    compute_nfp,
    decide_replenishment,
    select_strategic_articles,
    simulate_ddmrp_week,
)


def test_select_strategic_articles_pareto(tiny_split_train):
    arts = select_strategic_articles(tiny_split_train, coverage_pct=0.8)
    assert len(arts) >= 1
    assert len(arts) <= tiny_split_train["code_article_freq"].nunique()


def test_compute_buffers_columns(tiny_split_train):
    arts = select_strategic_articles(tiny_split_train, coverage_pct=1.0)
    buffers = compute_buffers(tiny_split_train, arts, order_cycle_jours=7, window_days=365)
    for col in ("red_zone", "yellow_zone", "green_zone", "top_of_red", "top_of_yellow", "top_of_green"):
        assert col in buffers.columns
    assert (buffers["top_of_yellow"] > buffers["top_of_red"]).all()
    assert (buffers["top_of_green"] > buffers["top_of_yellow"]).all()


def test_compute_nfp_formula():
    assert compute_nfp(on_hand=100, on_order=50, qualified_demand=30) == 120
    assert compute_nfp(on_hand=0, on_order=0, qualified_demand=10) == -10


def test_decide_replenishment_under_yellow():
    buf = pd.Series({"top_of_yellow": 100.0, "top_of_green": 150.0})
    # NFP=50 < TOY=100 -> commande TOG-NFP=100
    assert decide_replenishment(50, buf) == 100.0


def test_decide_replenishment_above_yellow():
    buf = pd.Series({"top_of_yellow": 100.0, "top_of_green": 150.0})
    assert decide_replenishment(120, buf) == 0.0


def test_simulate_ddmrp_week(tiny_split_train):
    arts = select_strategic_articles(tiny_split_train, coverage_pct=1.0)
    buffers = compute_buffers(tiny_split_train, arts, window_days=365)
    stock = pd.DataFrame({
        "code_article_freq": buffers["code_article_freq"],
        "on_hand": np.zeros(len(buffers)),
        "on_order": np.zeros(len(buffers)),
    })
    week = tiny_split_train.iloc[:10]
    sim = simulate_ddmrp_week(week, buffers, stock)
    assert "ordered_qte" in sim.columns
    assert "rupture" in sim.columns
    assert (sim["ordered_qte"] >= 0).all()
