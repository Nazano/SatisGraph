"""Streamlit multi-page dashboard entry point.

Run:
    streamlit run app/dashboard/main.py
"""

from __future__ import annotations

import streamlit as st

from app.dashboard.pages import (
    overview,
    video_explorer,
    video_detail,
    creator_comparator,
    match_predictions,
    reliability,
)
from app.utils.config import config

st.set_page_config(
    page_title=config.get("dashboard", "page_title", default="SatisGraph – WC2026"),
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

PAGES = {
    "📊 Vue d'ensemble": overview,
    "🎬 Explorateur de vidéos": video_explorer,
    "🔍 Détail d'une vidéo": video_detail,
    "👥 Comparateur de créateurs": creator_comparator,
    "⚽ Pronos par match": match_predictions,
    "🏆 Fiabilité des créateurs": reliability,
}

st.sidebar.title("⚽ SatisGraph")
st.sidebar.markdown("**World Cup 2026 Predictions**")
st.sidebar.divider()

page_name = st.sidebar.radio("Navigation", list(PAGES.keys()))
st.sidebar.divider()
st.sidebar.caption("v0.1.0 – © 2026 SatisGraph")

PAGES[page_name].render()
