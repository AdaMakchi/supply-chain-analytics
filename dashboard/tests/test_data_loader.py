"""Tests historical_stats : la fonction renvoie un dict structure correctement."""
from __future__ import annotations

from dashboard.utils.data_loader import historical_stats


def test_historical_stats_keys(tiny_split_train):
    stats = historical_stats.__wrapped__(tiny_split_train)
    assert set(stats.keys()) >= {"art_count", "couple_median", "quantiles", "global_median"}


def test_historical_stats_quantiles_in_dict(tiny_split_train):
    stats = historical_stats.__wrapped__(tiny_split_train)
    for q in (0.1, 0.5, 0.9, 0.95):
        assert q in stats["quantiles"]
