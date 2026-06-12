"""Dashboard page: Pronos par match."""

from __future__ import annotations

from collections import defaultdict

import pandas as pd
import plotly.express as px
import streamlit as st

from app.models.domain import PredictionType
from app.scoring.aggregator import aggregate_consensus, rank_predictions
from app.storage import get_repo


def render() -> None:
    st.title("⚽ Pronos par match")

    repo = get_repo()
    predictions = repo.list_all_predictions()
    creators = repo.list_creators()
    channels = repo.list_channels()
    videos = repo.list_videos(limit=500)

    if not predictions:
        st.warning("Aucun pronostic disponible.")
        return

    channel_map = {c.channel_id: c.name for c in channels}
    pub_dates = {v.video_id: v.publish_date for v in videos}

    ranked = rank_predictions(predictions, creators, pub_dates)
    consensus = aggregate_consensus(ranked)

    # --- Tournament winner consensus ---
    st.subheader("🏆 Consensus – Vainqueur du tournoi")
    winner_items = [c for c in consensus if c.prediction_type == PredictionType.TOURNAMENT_WINNER]
    if winner_items:
        df_w = pd.DataFrame([
            {
                "Équipe": c.team or "—",
                "Score pondéré": round(c.weighted_score, 3),
                "Nombre de votes": c.vote_count,
                "Supporters": ", ".join(channel_map.get(s, s) for s in set(c.supporters)),
            }
            for c in winner_items
        ])
        st.dataframe(df_w, use_container_width=True, hide_index=True)

        fig = px.bar(
            df_w,
            x="Équipe", y="Score pondéré",
            color="Équipe",
            title="Score de consensus pondéré – Vainqueur du tournoi",
            color_discrete_sequence=px.colors.qualitative.Bold,
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Pas de consensus sur le vainqueur du tournoi.")

    st.divider()

    # --- Match picks ---
    st.subheader("🎯 Picks de matches (scores exacts)")
    score_items = [c for c in consensus if c.prediction_type == PredictionType.EXACT_SCORE]
    if score_items:
        df_s = pd.DataFrame([
            {
                "Match": f"{c.team} vs {c.opponent}",
                "Score": f"{c.score_team}–{c.score_opponent}",
                "Phase": c.stage or "—",
                "Score pondéré": round(c.weighted_score, 3),
                "Votes": c.vote_count,
            }
            for c in score_items
        ])
        st.dataframe(df_s, use_container_width=True, hide_index=True)
    else:
        st.info("Aucun score exact dans le consensus.")

    st.divider()

    # --- Dark horse consensus ---
    st.subheader("⚡ Équipes surprises – Consensus")
    dh_items = [c for c in consensus if c.prediction_type == PredictionType.DARK_HORSE]
    if dh_items:
        teams = [c.team or "—" for c in dh_items]
        scores = [round(c.weighted_score, 3) for c in dh_items]
        fig2 = px.pie(
            names=teams,
            values=scores,
            title="Répartition des équipes surprises (consensus pondéré)",
            color_discrete_sequence=px.colors.qualitative.Pastel1,
        )
        st.plotly_chart(fig2, use_container_width=True)

        df_dh = pd.DataFrame([
            {"Équipe": c.team or "—", "Score pondéré": round(c.weighted_score, 3), "Votes": c.vote_count}
            for c in dh_items
        ])
        st.dataframe(df_dh, use_container_width=True, hide_index=True)
    else:
        st.info("Aucune équipe surprise dans le consensus.")
