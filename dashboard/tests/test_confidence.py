"""Tests des 4 branches du score de confiance (vert / orange / rouge / inconnu)."""
from __future__ import annotations

from dashboard.utils.confidence import confidence_level


def _hist(art_count: dict, couple_med: dict, q90: float = 100.0, q95: float = 200.0) -> dict:
    return {
        "art_count": art_count,
        "couple_median": couple_med,
        "quantiles": {0.5: 30.0, 0.9: q90, 0.95: q95},
    }


def test_confidence_rouge_article_inconnu():
    hist = _hist({}, {})
    assert confidence_level(pred=10, code_article_freq=1.0, code_client_freq=1.0, hist_stats=hist) == "rouge"


def test_confidence_orange_couple_inconnu():
    hist = _hist({5.0: 80}, {})
    assert confidence_level(pred=10, code_article_freq=5.0, code_client_freq=1.0, hist_stats=hist) == "orange"


def test_confidence_vert():
    hist = _hist({5.0: 100}, {(2.0, 5.0): 20.0})
    # ecart = |25-20|/20 = 0.25 < 0.5, pred 25 < q90 (100), art_count=100>=50
    res = confidence_level(pred=25, code_article_freq=5.0, code_client_freq=2.0, hist_stats=hist)
    assert res == "vert"


def test_confidence_rouge_au_dela_p95():
    hist = _hist({5.0: 100}, {(2.0, 5.0): 20.0}, q95=200.0)
    assert confidence_level(pred=250, code_article_freq=5.0, code_client_freq=2.0, hist_stats=hist) == "rouge"


def test_confidence_orange_ecart_important():
    hist = _hist({5.0: 10}, {(2.0, 5.0): 10.0})
    # art_count=10 (>=5), ecart=|20-10|/10=1.0 (<1.5), pred<p90
    res = confidence_level(pred=20, code_article_freq=5.0, code_client_freq=2.0, hist_stats=hist)
    assert res == "orange"
