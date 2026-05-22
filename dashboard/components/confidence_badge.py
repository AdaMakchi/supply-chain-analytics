"""Badge coloré pour le niveau de confiance d'une prévision."""
from __future__ import annotations

import streamlit as st

from dashboard.utils.confidence import COLORS, LABELS, Level


def badge(level: Level) -> str:
    color = COLORS[level]
    label = LABELS[level]
    return (
        f'<span style="background:{color};color:white;padding:2px 10px;'
        f'border-radius:12px;font-size:0.85em;font-weight:600;">{label}</span>'
    )


def render_badge(level: Level) -> None:
    st.markdown(badge(level), unsafe_allow_html=True)
