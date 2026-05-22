"""Carte KPI réutilisable."""
from __future__ import annotations

import streamlit as st


def kpi_card(label: str, value: str, delta: str | None = None, help_text: str | None = None) -> None:
    st.metric(label=label, value=value, delta=delta, help=help_text)
