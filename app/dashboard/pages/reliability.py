"""Dashboard page: Fiabilité des créateurs."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from app.storage import get_repo


def render() -> None:
    st.title("🏆 Fiabilité des créateurs")

    repo = get_repo()
    creators = repo.list_creators()
    channels = repo.list_channels()
    channel_map = {c.channel_id: c.name for c in channels}

    if not creators:
        st.warning("Aucune donnée de fiabilité disponible.")
        return

    df = pd.DataFrame([
        {
            "Créateur": channel_map.get(c.channel_id, c.channel_id),
            "Score de précision": c.accuracy_score or 0,
            "Total pronostics": c.total_predictions,
            "Corrects": c.correct_predictions,
            "Poids": c.weight,
            "Précision (%)": f"{c.accuracy_score:.1%}" if c.accuracy_score else "—",
        }
        for c in creators
    ]).sort_values("Score de précision", ascending=False)

    # Summary table
    st.subheader("📋 Classement des créateurs")
    st.dataframe(
        df[["Créateur", "Précision (%)", "Total pronostics", "Corrects", "Poids"]].reset_index(drop=True),
        use_container_width=True,
        hide_index=True,
    )

    # Accuracy bar chart
    st.divider()
    st.subheader("📊 Score de précision")
    fig = px.bar(
        df,
        x="Créateur",
        y="Score de précision",
        color="Créateur",
        color_discrete_sequence=px.colors.qualitative.Safe,
        title="Score de précision par créateur",
        range_y=[0, 1],
    )
    fig.update_traces(texttemplate="%{y:.0%}", textposition="outside")
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    # Bubble chart: total vs accuracy
    st.divider()
    st.subheader("📈 Volume vs Précision")
    fig2 = px.scatter(
        df,
        x="Total pronostics",
        y="Score de précision",
        size="Poids",
        color="Créateur",
        text="Créateur",
        title="Volume de pronostics vs Précision (taille = poids)",
        labels={"Score de précision": "Précision (0-1)", "Total pronostics": "Nombre de pronostics"},
    )
    fig2.update_traces(textposition="top center")
    fig2.update_layout(yaxis_range=[0, 1])
    st.plotly_chart(fig2, use_container_width=True)

    # Per-creator details
    st.divider()
    st.subheader("🔍 Détail par créateur")
    selected_creator = st.selectbox(
        "Sélectionner un créateur",
        options=df["Créateur"].tolist(),
    )
    creator_data = df[df["Créateur"] == selected_creator].iloc[0]
    c1, c2, c3 = st.columns(3)
    c1.metric("Précision", creator_data["Précision (%)"])
    c2.metric("Total pronostics", int(creator_data["Total pronostics"]))
    c3.metric("Corrects", int(creator_data["Corrects"]))

    # Show their predictions
    ch_id = next((c.channel_id for c in channels if channel_map.get(c.channel_id) == selected_creator), None)
    if ch_id:
        videos = repo.list_videos(channel_id=ch_id)
        all_preds = []
        for v in videos:
            preds = repo.get_predictions_for_video(v.video_id)
            for p in preds:
                for item in p.items:
                    all_preds.append({
                        "Vidéo": v.title[:60] + "…" if len(v.title) > 60 else v.title,
                        "Type": item.prediction_type,
                        "Équipe": item.team or "—",
                        "Score": f"{item.score_team}–{item.score_opponent}" if item.score_team is not None else "—",
                        "Confiance": f"{item.confidence:.0%}" if item.confidence else "—",
                    })

        if all_preds:
            st.dataframe(pd.DataFrame(all_preds), use_container_width=True, hide_index=True)
        else:
            st.info("Aucun pronostic détaillé pour ce créateur.")
