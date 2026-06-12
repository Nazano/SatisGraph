"""Demo seed script.

Populates the database with realistic-looking fake data so the dashboard
displays something out of the box without needing a YouTube API key.

Run:
    python -m data.demo.seed_data
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Ensure project root is on path when run directly
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.models.domain import (
    Channel, Creator, Prediction, PredictionItem,
    PredictionType, Team, Transcript, TranscriptStatus, Video, VideoStatus,
)
from app.storage import get_repo
from app.utils.logger import get_logger

logger = get_logger(__name__)


def _dt(offset_days: int = 0) -> datetime:
    return datetime.now(tz=timezone.utc) - timedelta(days=offset_days)


CHANNELS = [
    Channel(channel_id="UC_DEMO_FR_1", name="LeFootballExpert", url="https://youtube.com/@LeFootballExpert", language="fr", country="FR"),
    Channel(channel_id="UC_DEMO_EN_1", name="WorldFootballAnalysis", url="https://youtube.com/@WorldFootballAnalysis", language="en", country="US"),
    Channel(channel_id="UC_DEMO_ES_1", name="FutbolMundial2026", url="https://youtube.com/@FutbolMundial2026", language="es", country="AR"),
    Channel(channel_id="UC_DEMO_FR_2", name="PronosticsFoot", url="https://youtube.com/@PronosticsFoot", language="fr", country="FR"),
    Channel(channel_id="UC_DEMO_EN_2", name="SoccerPredictions", url="https://youtube.com/@SoccerPredictions", language="en", country="GB"),
]

VIDEOS = [
    Video(channel_id="UC_DEMO_FR_1", video_id="DEMO_VID_001", video_url="https://youtube.com/watch?v=DEMO_VID_001",
          title="Mes pronostics Coupe du Monde 2026 – France championne ?", language="fr",
          publish_date=_dt(5), view_count=125_000, like_count=4_200, status=VideoStatus.PREDICTIONS_EXTRACTED),
    Video(channel_id="UC_DEMO_EN_1", video_id="DEMO_VID_002", video_url="https://youtube.com/watch?v=DEMO_VID_002",
          title="World Cup 2026 Full Predictions – Who wins?", language="en",
          publish_date=_dt(12), view_count=89_500, like_count=3_100, status=VideoStatus.PREDICTIONS_EXTRACTED),
    Video(channel_id="UC_DEMO_ES_1", video_id="DEMO_VID_003", video_url="https://youtube.com/watch?v=DEMO_VID_003",
          title="Copa del Mundo 2026 – Argentina campeona del mundo", language="es",
          publish_date=_dt(3), view_count=210_000, like_count=9_800, status=VideoStatus.PREDICTIONS_EXTRACTED),
    Video(channel_id="UC_DEMO_FR_2", video_id="DEMO_VID_004", video_url="https://youtube.com/watch?v=DEMO_VID_004",
          title="Pronostics Mundial 2026 – Les 8 équipes qui vont dominer", language="fr",
          publish_date=_dt(20), view_count=45_000, like_count=1_800, status=VideoStatus.TRANSCRIPT_FETCHED),
    Video(channel_id="UC_DEMO_EN_2", video_id="DEMO_VID_005", video_url="https://youtube.com/watch?v=DEMO_VID_005",
          title="2026 World Cup Dark Horses – 5 Teams To Watch", language="en",
          publish_date=_dt(8), view_count=67_000, like_count=2_500, status=VideoStatus.PREDICTIONS_EXTRACTED),
    Video(channel_id="UC_DEMO_FR_1", video_id="DEMO_VID_006", video_url="https://youtube.com/watch?v=DEMO_VID_006",
          title="Analyse groupe B Coupe du Monde 2026 – Qui se qualifie ?", language="fr",
          publish_date=_dt(30), view_count=33_000, like_count=900, status=VideoStatus.PENDING),
]

TRANSCRIPTS = [
    Transcript(video_id="DEMO_VID_001", status=TranscriptStatus.AVAILABLE, language_detected="fr",
               raw_text="Bonjour ! Je pense que la France va gagner la Coupe du Monde 2026. En finale, je vois France 2-1 Brésil. Mbappé sera déterminant. Je suis très confiant à 80%.",
               char_count=150),
    Transcript(video_id="DEMO_VID_002", status=TranscriptStatus.AVAILABLE, language_detected="en",
               raw_text="Hello everyone! I think Brazil will win the World Cup 2026. The final will be Brazil 3-1 France. Vinicius Jr will be the top scorer. Very confident about this.",
               char_count=165),
    Transcript(video_id="DEMO_VID_003", status=TranscriptStatus.AVAILABLE, language_detected="es",
               raw_text="¡Hola! Creo que Argentina ganará el mundial 2026. En la final, Argentina 2-0 France. Messi puede hacer historia. Estoy 90% seguro.",
               char_count=140),
    Transcript(video_id="DEMO_VID_004", status=TranscriptStatus.AVAILABLE, language_detected="fr",
               raw_text="Les 8 équipes favorites: France, Brésil, Argentine, Allemagne, Espagne, Portugal, Angleterre, Pays-Bas. L'Espagne peut créer la surprise.",
               char_count=135),
    Transcript(video_id="DEMO_VID_005", status=TranscriptStatus.AVAILABLE, language_detected="en",
               raw_text="Dark horses: Morocco, Japan, USA, Colombia, Australia. These teams could upset the favorites in the 2026 World Cup.",
               char_count=115),
]

PREDICTIONS = [
    Prediction(
        video_id="DEMO_VID_001", channel_id="UC_DEMO_FR_1",
        tournament_winner="France", overall_confidence=0.80,
        key_arguments=["France a la meilleure équipe du monde", "Mbappé est inarrêtable"],
        key_quotes=["Je pense que la France va gagner la Coupe du Monde 2026"],
        items=[
            PredictionItem(prediction_type=PredictionType.TOURNAMENT_WINNER, team="France", confidence=0.80, raw_text="France va gagner"),
            PredictionItem(prediction_type=PredictionType.EXACT_SCORE, team="France", opponent="Brazil", score_team=2, score_opponent=1, stage="final", confidence=0.55),
        ],
    ),
    Prediction(
        video_id="DEMO_VID_002", channel_id="UC_DEMO_EN_1",
        tournament_winner="Brazil", overall_confidence=0.75,
        key_arguments=["Brazil has the best squad depth", "Vinicius Jr is in top form"],
        key_quotes=["I think Brazil will win the World Cup 2026"],
        items=[
            PredictionItem(prediction_type=PredictionType.TOURNAMENT_WINNER, team="Brazil", confidence=0.75, raw_text="Brazil will win"),
            PredictionItem(prediction_type=PredictionType.EXACT_SCORE, team="Brazil", opponent="France", score_team=3, score_opponent=1, stage="final", confidence=0.45),
        ],
    ),
    Prediction(
        video_id="DEMO_VID_003", channel_id="UC_DEMO_ES_1",
        tournament_winner="Argentina", overall_confidence=0.90,
        key_arguments=["Argentina es el campeón defensor", "Messi puede hacer historia"],
        key_quotes=["Argentina ganará el mundial 2026"],
        items=[
            PredictionItem(prediction_type=PredictionType.TOURNAMENT_WINNER, team="Argentina", confidence=0.90, raw_text="Argentina campeona"),
            PredictionItem(prediction_type=PredictionType.EXACT_SCORE, team="Argentina", opponent="France", score_team=2, score_opponent=0, stage="final", confidence=0.60),
        ],
    ),
    Prediction(
        video_id="DEMO_VID_004", channel_id="UC_DEMO_FR_2",
        tournament_winner="France", overall_confidence=0.65,
        key_arguments=["France possède la meilleure profondeur de banc"],
        key_quotes=["L'Espagne peut créer la surprise"],
        items=[
            PredictionItem(prediction_type=PredictionType.TOURNAMENT_WINNER, team="France", confidence=0.65),
            PredictionItem(prediction_type=PredictionType.DARK_HORSE, team="Spain", confidence=0.70, raw_text="L'Espagne peut créer la surprise"),
            PredictionItem(prediction_type=PredictionType.QUALIFIED_TEAM, team="Germany"),
            PredictionItem(prediction_type=PredictionType.QUALIFIED_TEAM, team="Portugal"),
        ],
    ),
    Prediction(
        video_id="DEMO_VID_005", channel_id="UC_DEMO_EN_2",
        tournament_winner=None, overall_confidence=None,
        key_arguments=["Dark horses can upset the favorites"],
        key_quotes=["Morocco could be the dark horse of the tournament"],
        items=[
            PredictionItem(prediction_type=PredictionType.DARK_HORSE, team="Morocco", confidence=0.65, raw_text="Morocco dark horse"),
            PredictionItem(prediction_type=PredictionType.DARK_HORSE, team="Japan", confidence=0.55),
            PredictionItem(prediction_type=PredictionType.DARK_HORSE, team="USA", confidence=0.50),
        ],
    ),
]

TEAMS = [
    Team(name="France", confederation="UEFA", fifa_ranking=2),
    Team(name="Brazil", confederation="CONMEBOL", fifa_ranking=5),
    Team(name="Argentina", confederation="CONMEBOL", fifa_ranking=1),
    Team(name="Germany", confederation="UEFA", fifa_ranking=16),
    Team(name="Spain", confederation="UEFA", fifa_ranking=8),
    Team(name="England", confederation="UEFA", fifa_ranking=5),
    Team(name="Portugal", confederation="UEFA", fifa_ranking=6),
    Team(name="Belgium", confederation="UEFA", fifa_ranking=4),
    Team(name="Netherlands", confederation="UEFA", fifa_ranking=7),
    Team(name="Morocco", confederation="CAF", fifa_ranking=14),
    Team(name="Japan", confederation="AFC", fifa_ranking=17),
    Team(name="USA", confederation="CONCACAF", fifa_ranking=13),
]

CREATORS = [
    Creator(channel_id="UC_DEMO_FR_1", total_predictions=24, correct_predictions=18, accuracy_score=0.75, weight=1.5),
    Creator(channel_id="UC_DEMO_EN_1", total_predictions=31, correct_predictions=20, accuracy_score=0.65, weight=1.2),
    Creator(channel_id="UC_DEMO_ES_1", total_predictions=18, correct_predictions=14, accuracy_score=0.78, weight=1.3),
    Creator(channel_id="UC_DEMO_FR_2", total_predictions=12, correct_predictions=7, accuracy_score=0.58, weight=1.0),
    Creator(channel_id="UC_DEMO_EN_2", total_predictions=9, correct_predictions=4, accuracy_score=0.44, weight=0.8),
]


def seed() -> None:
    repo = get_repo()
    logger.info("Seeding demo data…")

    for ch in CHANNELS:
        repo.upsert_channel(ch)
    logger.info(f"  {len(CHANNELS)} channels inserted")

    for v in VIDEOS:
        repo.upsert_video(v)
    logger.info(f"  {len(VIDEOS)} videos inserted")

    for t in TRANSCRIPTS:
        repo.upsert_transcript(t)
    logger.info(f"  {len(TRANSCRIPTS)} transcripts inserted")

    for p in PREDICTIONS:
        repo.save_prediction(p)
    logger.info(f"  {len(PREDICTIONS)} predictions inserted")

    for team in TEAMS:
        repo.upsert_team(team)
    logger.info(f"  {len(TEAMS)} teams inserted")

    for c in CREATORS:
        repo.upsert_creator(c)
    logger.info(f"  {len(CREATORS)} creators inserted")

    logger.info("Demo seeding complete ✓")


if __name__ == "__main__":
    seed()
