"""Tests du generateur de stock mock."""
from __future__ import annotations

import numpy as np

from dashboard.utils.stock_mock import compute_adu, compute_lt, generate_stock_mock


def test_compute_adu_positive(tiny_split_train):
    adu = compute_adu(tiny_split_train, window_days=365)
    assert (adu >= 0).all()


def test_compute_lt_min_1(tiny_split_train):
    lt = compute_lt(tiny_split_train)
    assert (lt >= 1.0).all()


def test_generate_stock_mock_shape(tiny_split_train):
    stock = generate_stock_mock(tiny_split_train, coverage_days=30, seed=42)
    expected_cols = {"code_article_freq", "on_hand", "on_order", "adu", "lt_jours"}
    assert expected_cols.issubset(set(stock.columns))
    n_articles = tiny_split_train["code_article_freq"].nunique()
    assert len(stock) == n_articles


def test_generate_stock_mock_reproducible(tiny_split_train):
    s1 = generate_stock_mock(tiny_split_train, seed=42)
    s2 = generate_stock_mock(tiny_split_train, seed=42)
    np.testing.assert_array_equal(s1["on_hand"].values, s2["on_hand"].values)
