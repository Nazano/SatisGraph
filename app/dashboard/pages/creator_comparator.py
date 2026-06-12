"""Dashboard page: Comparateur de créateurs."""

from __future__ import annotations

from collections import defaultdict

import pandas as pd
import plotly.express as px
import streamlit as st

from app.storage import get_repo


def render() -> None:
    st.title("👥 Comparateur de créateurs")

    repo = get_repo()
    channels = repo.list_channels()
    all_predictions = repo.list_all_predictions()

    if not all_predictions:
        st.warning("Aucun pronostic disponible.")
        return

    channel_map = {c.channel_id: c.name for c in channels}

    # --- Tournament winner comparison ---
    st.subheader("🏆 Qui va gagner le tournoi ?")
    winner_rows = []
    for pred in all_predictions:
        if pred.version != max(p.version for p in all_predictions if p.video_id == pred.video_id):
            continue  # only latest version
        winner_rows.append({
            "Créateur": channel_map.get(pred.channel_id, pred.channel_id),
            "Vainqueur prédit": pred.tournament_winner or "Non précisé",
            "Confiance": f"{pred.overall_confidence:.0%}" if pred.overall_confidence else "—",
        })

    if winner_rows:
        df_winners = pd.DataFrame(winner_rows)
        st.dataframe(df_winners, use_container_width=True, hide_index=True)

        # Aggregated bar chart
        winner_counts: dict[str, int] = defaultdict(int)
        for row in winner_rows:
            winner_counts[row["Vainqueur prédit"]] += 1
        fig = px.bar(
            x=list(winner_counts.keys()),
            y=list(winner_counts.values()),
            labels={"x": "Équipe", "y": "Nombre de créateurs"},
            title="Votes de vainqueur du tournoi",
            color=list(winner_counts.keys()),
            color_discrete_sequence=px.colors.qualitative.Set1,
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # --- Exact score comparison ---
    st.subheader("📊 Pronostics de scores exacts")
    from app.models.domain import PredictionType
    score_rows = []
    for pred in all_predictions:
        for item in pred.items:
            if item.prediction_type == PredictionType.EXACT_SCORE:
                score_rows.append({
                    "Créateur": channel_map.get(pred.channel_id, pred.channel_id),
                    "Match": f"{item.team} vs {item.opponent}",
                    "Score": f"{item.score_team}–{item.score_opponent}",
                    "Phase": item.stage or "—",
                    "Confiance": f"{item.confidence:.0%}" if item.confidence else "—",
                })

    if score_rows:
        df_scores = pd.DataFrame(score_rows)
        st.dataframe(df_scores, use_container_width=True, hide_index=True)
    else:
        st.info("Aucun score exact prédit.")

    st.divider()

    # --- Dark horses ---
    st.subheader("⚡ Équipes surprises (Dark Horses)")
    dh_rows = []
    for pred in all_predictions:
        for item in pred.items:
            if item.prediction_type == PredictionType.DARK_HORSE:
                dh_rows.append({
                    "Créateur": channel_map.get(pred.channel_id, pred.channel_id),
                    "Équipe surprise": item.team or "—",
                    "Confiance": f"{item.confidence:.0%}" if item.confidence else "—",
                    "Citation": (item.raw_text[:60] + "…") if item.raw_text and len(item.raw_text) > 60 else (item.raw_text or "—"),
                })

    if dh_rows:
        st.dataframe(pd.DataFrame(dh_rows), use_container_width=True, hide_index=True)
    else:
        st.info("Aucune équipe surprise mentionnée.")
