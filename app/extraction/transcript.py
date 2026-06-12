"""Transcript extraction module.

TODO: Replace stub with real youtube_transcript_api calls:
      1. pip install youtube-transcript-api
      2. from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound
      3. Implement _fetch_real() using YouTubeTranscriptApi.get_transcript(video_id, languages=[lang, 'en'])
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from app.models.domain import Transcript, TranscriptSegment, TranscriptStatus
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Languages to try when fetching transcripts, in order of preference
_LANG_PREFERENCES = ["fr", "en", "es", "a.fr", "a.en", "a.es"]


def extract_transcript(video_id: str, language: str = "en") -> Transcript:
    """Fetch transcript for a YouTube video.

    Returns a :class:`Transcript` object regardless of whether a transcript
    was found (check ``transcript.status`` to know the outcome).

    Args:
        video_id: YouTube video ID (e.g. ``"dQw4w9WgXcQ"``).
        language: Preferred language code.
    """
    try:
        return _fetch_real(video_id, language)
    except ImportError:
        logger.warning(
            "youtube-transcript-api not installed – returning stub transcript. "
            "Run: pip install youtube-transcript-api"
        )
        return _stub_transcript(video_id)
    except Exception as exc:
        logger.error(f"Transcript fetch failed for {video_id}: {exc}")
        return Transcript(
            video_id=video_id,
            status=TranscriptStatus.ERROR,
            fetched_at=datetime.now(tz=timezone.utc),
        )


def _fetch_real(video_id: str, language: str) -> Transcript:
    """Real implementation using youtube-transcript-api.

    TODO: Uncomment when youtube-transcript-api is installed.
    """
    # from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
    #
    # langs = [language] + [l for l in _LANG_PREFERENCES if l != language]
    # try:
    #     raw = YouTubeTranscriptApi.get_transcript(video_id, languages=langs)
    # except (NoTranscriptFound, TranscriptsDisabled):
    #     return Transcript(video_id=video_id, status=TranscriptStatus.UNAVAILABLE,
    #                       fetched_at=datetime.now(tz=timezone.utc))
    #
    # segments = [TranscriptSegment(start=s["start"], duration=s["duration"], text=s["text"]) for s in raw]
    # raw_text = " ".join(s["text"] for s in raw)
    # return Transcript(
    #     video_id=video_id,
    #     raw_text=raw_text,
    #     segments=segments,
    #     status=TranscriptStatus.AVAILABLE,
    #     language_detected=language,
    #     char_count=len(raw_text),
    #     fetched_at=datetime.now(tz=timezone.utc),
    # )
    raise ImportError("youtube-transcript-api")


def _stub_transcript(video_id: str) -> Transcript:
    """Return a plausible stub transcript for demo/testing."""
    sample_segments = [
        TranscriptSegment(start=0.0, duration=4.5, text="Bonjour à tous, bienvenue sur ma chaîne !"),
        TranscriptSegment(start=4.5, duration=6.0, text="Aujourd'hui on parle de la Coupe du Monde 2026."),
        TranscriptSegment(start=10.5, duration=5.0, text="Je pense que la France va gagner le tournoi."),
        TranscriptSegment(start=15.5, duration=7.0, text="Le Brésil et l'Argentine seront leurs adversaires les plus dangereux."),
        TranscriptSegment(start=22.5, duration=5.5, text="En finale, je vois France 2-1 Brésil."),
        TranscriptSegment(start=28.0, duration=6.0, text="Mbappé sera le meilleur buteur du tournoi selon moi."),
        TranscriptSegment(start=34.0, duration=4.0, text="L'Espagne peut créer la surprise, c'est une équipe très technique."),
        TranscriptSegment(start=38.0, duration=5.5, text="Je donne 80% de confiance à mon pronostic France vainqueur."),
    ]
    raw_text = " ".join(s.text for s in sample_segments)
    return Transcript(
        video_id=video_id,
        raw_text=raw_text,
        segments=sample_segments,
        status=TranscriptStatus.AUTO_GENERATED,
        language_detected="fr",
        char_count=len(raw_text),
        fetched_at=datetime.now(tz=timezone.utc),
    )
