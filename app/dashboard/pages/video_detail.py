"""Dashboard page: Détail d'une vidéo."""

from __future__ import annotations

import streamlit as st

from app.storage import get_repo


def render() -> None:
    st.title("🔍 Détail d'une vidéo")

    repo = get_repo()
    videos = repo.list_videos(limit=500)

    if not videos:
        st.warning("Aucune vidéo disponible.")
        return

    video_options = {v.video_id: v.title for v in videos}
    default_id = st.session_state.get("detail_video_id", list(video_options.keys())[0])

    selected_id = st.selectbox(
        "Choisir une vidéo",
        options=list(video_options.keys()),
        format_func=lambda vid: video_options.get(vid, vid),
        index=list(video_options.keys()).index(default_id) if default_id in video_options else 0,
    )

    video = repo.get_video(selected_id)
    if not video:
        st.error("Vidéo introuvable.")
        return

    # --- Metadata ---
    st.subheader("📋 Métadonnées")
    col1, col2, col3 = st.columns(3)
    col1.metric("👁 Vues", f"{video.view_count:,}" if video.view_count else "—")
    col2.metric("👍 Likes", f"{video.like_count:,}" if video.like_count else "—")
    col3.metric("📅 Date", str(video.publish_date)[:10] if video.publish_date else "—")

    st.markdown(f"🔗 **URL:** [{video.video_url}]({video.video_url})")
    st.markdown(f"🌐 **Langue:** `{video.language}` | **Statut:** `{video.status}`")

    if video.description:
        with st.expander("Description"):
            st.write(video.description)

    st.divider()

    # --- Transcript ---
    st.subheader("📝 Transcript")
    transcript = repo.get_transcript(selected_id)
    if transcript and transcript.raw_text:
        st.caption(f"Statut: `{transcript.status}` | Langue détectée: `{transcript.language_detected}` | {transcript.char_count} caractères")
        st.text_area("Texte brut", transcript.raw_text, height=200)

        if transcript.segments:
            with st.expander(f"Segments horodatés ({len(transcript.segments)})"):
                for seg in transcript.segments:
                    st.markdown(f"**{seg.start:.1f}s** – {seg.text}")
    else:
        st.info("Transcript non disponible pour cette vidéo.")

    st.divider()

    # --- Predictions ---
    st.subheader("🎯 Pronostics extraits")
    predictions = repo.get_predictions_for_video(selected_id)
    if not predictions:
        st.info("Aucun pronostic extrait pour cette vidéo.")
        if st.button("Extraire les pronostics maintenant"):
            if transcript and transcript.raw_text:
                from app.extraction.predictions import extract_predictions
                from app.models.domain import VideoStatus
                pred = extract_predictions(transcript.raw_text, video.video_id, video.channel_id, video.language or "en")
                repo.save_prediction(pred)
                repo.update_video_status(video.video_id, VideoStatus.PREDICTIONS_EXTRACTED)
                st.success("Pronostics extraits ! Actualisez.")
            else:
                st.warning("Pas de transcript disponible.")
        return

    pred = predictions[0]  # Latest version

    c1, c2, c3 = st.columns(3)
    c1.metric("🏆 Vainqueur prédit", pred.tournament_winner or "—")
    c2.metric("📊 Confiance globale", f"{pred.overall_confidence:.0%}" if pred.overall_confidence else "—")
    c3.metric("📦 Version", pred.version)

    if pred.key_arguments:
        st.markdown("**Arguments clés:**")
        for arg in pred.key_arguments:
            st.markdown(f"- {arg}")

    if pred.key_quotes:
        st.markdown("**Citations:**")
        for quote in pred.key_quotes:
            st.markdown(f"> {quote}")

    st.markdown("**Items de prédiction:**")
    import pandas as pd
    items_df = pd.DataFrame([
        {
            "Type": i.prediction_type,
            "Équipe": i.team or "—",
            "Adversaire": i.opponent or "—",
            "Score": f"{i.score_team}-{i.score_opponent}" if i.score_team is not None else "—",
            "Phase": i.stage or "—",
            "Confiance": f"{i.confidence:.0%}" if i.confidence else "—",
            "Citation": (i.raw_text[:80] + "…") if i.raw_text and len(i.raw_text) > 80 else (i.raw_text or "—"),
        }
        for i in pred.items
    ])
    if not items_df.empty:
        st.dataframe(items_df, use_container_width=True, hide_index=True)
