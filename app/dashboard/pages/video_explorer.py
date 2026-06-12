"""Dashboard page: Explorateur de vidéos."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from app.storage import get_repo


def render() -> None:
    st.title("🎬 Explorateur de vidéos")

    repo = get_repo()
    channels = repo.list_channels()
    videos = repo.list_videos(limit=500)

    if not videos:
        st.warning("Aucune vidéo disponible. Chargez les données démo depuis la Vue d'ensemble.")
        return

    # Build a DataFrame
    channel_map = {c.channel_id: c.name for c in channels}
    df = pd.DataFrame([
        {
            "video_id": v.video_id,
            "Titre": v.title,
            "Chaîne": channel_map.get(v.channel_id, v.channel_id),
            "channel_id": v.channel_id,
            "Langue": v.language,
            "Date": str(v.publish_date)[:10] if v.publish_date else "—",
            "Vues": v.view_count or 0,
            "Likes": v.like_count or 0,
            "Statut": v.status,
            "URL": v.video_url,
        }
        for v in videos
    ])

    # --- Filters ---
    with st.sidebar:
        st.subheader("Filtres")
        lang_options = ["Toutes"] + sorted(df["Langue"].unique().tolist())
        sel_lang = st.selectbox("Langue", lang_options)

        ch_options = ["Toutes"] + sorted(df["Chaîne"].unique().tolist())
        sel_ch = st.selectbox("Chaîne", ch_options)

        status_options = ["Tous"] + sorted(df["Statut"].unique().tolist())
        sel_status = st.selectbox("Statut", status_options)

        search = st.text_input("🔍 Recherche dans le titre")

    filtered = df.copy()
    if sel_lang != "Toutes":
        filtered = filtered[filtered["Langue"] == sel_lang]
    if sel_ch != "Toutes":
        filtered = filtered[filtered["Chaîne"] == sel_ch]
    if sel_status != "Tous":
        filtered = filtered[filtered["Statut"] == sel_status]
    if search:
        filtered = filtered[filtered["Titre"].str.contains(search, case=False, na=False)]

    st.caption(f"{len(filtered)} vidéo(s) trouvée(s)")

    display_cols = ["Titre", "Chaîne", "Langue", "Date", "Vues", "Likes", "Statut"]
    st.dataframe(
        filtered[display_cols].reset_index(drop=True),
        use_container_width=True,
        hide_index=True,
    )

    # Allow drilling into a video
    if not filtered.empty:
        st.divider()
        sel_vid = st.selectbox(
            "Sélectionner une vidéo pour voir les détails",
            options=filtered["video_id"].tolist(),
            format_func=lambda vid: filtered[filtered["video_id"] == vid]["Titre"].values[0],
        )
        if sel_vid:
            row = filtered[filtered["video_id"] == sel_vid].iloc[0]
            st.markdown(f"**URL:** [{row['URL']}]({row['URL']})")
            if st.button("Voir le détail complet →"):
                st.session_state["detail_video_id"] = sel_vid
                st.info("Naviguez vers 'Détail d'une vidéo' dans le menu.")
