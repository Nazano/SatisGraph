"""Dashboard page: Vue d'ensemble (Overview)."""

from __future__ import annotations

import plotly.express as px
import streamlit as st

from app.storage import get_repo


def render() -> None:
    st.title("📊 Vue d'ensemble")

    repo = get_repo()
    stats = repo.stats()

    # KPI row
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🌍 Chaînes suivies", stats["channels"])
    c2.metric("🎬 Vidéos collectées", stats["videos"])
    c3.metric("📋 Pronostics extraits", stats["predictions"])
    c4.metric("🔢 Items de prédiction", stats["prediction_items"])

    st.divider()

    col_left, col_right = st.columns(2)

    # Language breakdown
    with col_left:
        st.subheader("Répartition par langue")
        by_lang = stats.get("videos_by_language", {})
        if by_lang:
            fig = px.pie(
                names=list(by_lang.keys()),
                values=list(by_lang.values()),
                color_discrete_sequence=px.colors.qualitative.Set2,
            )
            fig.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucune donnée disponible.")

    # Channel breakdown
    with col_right:
        st.subheader("Vidéos par chaîne")
        channels = repo.list_channels()
        if channels:
            ch_names = [c.name for c in channels]
            ch_videos = [len(repo.list_videos(channel_id=c.channel_id)) for c in channels]
            fig2 = px.bar(
                x=ch_names,
                y=ch_videos,
                labels={"x": "Chaîne", "y": "Vidéos"},
                color=ch_names,
                color_discrete_sequence=px.colors.qualitative.Pastel,
            )
            fig2.update_layout(showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)

    # Recent videos table
    st.divider()
    st.subheader("Vidéos récentes")
    videos = repo.list_videos(limit=10)
    if videos:
        import pandas as pd
        df = pd.DataFrame([
            {
                "Titre": v.title,
                "Chaîne": v.channel_id,
                "Langue": v.language,
                "Date": str(v.publish_date)[:10] if v.publish_date else "—",
                "Statut": v.status,
                "Vues": f"{v.view_count:,}" if v.view_count else "—",
            }
            for v in videos
        ])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Aucune vidéo en base. Lancez le pipeline ou chargez les données demo.")
        if st.button("🌱 Charger les données démo"):
            with st.spinner("Chargement…"):
                from data.demo.seed_data import seed
                seed()
            st.success("Données démo chargées ! Actualisez la page.")
