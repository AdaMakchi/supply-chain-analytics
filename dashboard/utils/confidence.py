"""Score de confiance composite vert / orange / rouge.

Trois facteurs :
- familiarité de l'article (nb de commandes dans le train)
- écart de la prédiction par rapport à la médiane historique du couple
- décile de la prédiction dans la distribution train
"""
from __future__ import annotations

from typing import Literal

Level = Literal["vert", "orange", "rouge"]


def confidence_level(
    pred: float,
    code_article_freq: float,
    code_client_freq: float,
    hist_stats: dict,
) -> Level:
    art_count = hist_stats["art_count"].get(code_article_freq, 0)
    if art_count == 0:
        return "rouge"

    couple_med = hist_stats["couple_median"].get((code_client_freq, code_article_freq))
    if couple_med is None:
        return "orange"

    ecart = abs(pred - couple_med) / max(couple_med, 1.0)
    p90 = hist_stats["quantiles"].get(0.9, float("inf"))
    p95 = hist_stats["quantiles"].get(0.95, float("inf"))

    if pred > p95:
        return "rouge"
    if art_count >= 50 and ecart < 0.5 and pred <= p90:
        return "vert"
    if art_count >= 5 and ecart < 1.5:
        return "orange"
    return "rouge"


COLORS = {
    "vert": "#16a34a",
    "orange": "#f59e0b",
    "rouge": "#dc2626",
}

LABELS = {
    "vert": "Élevée",
    "orange": "Moyenne",
    "rouge": "Faible",
}
