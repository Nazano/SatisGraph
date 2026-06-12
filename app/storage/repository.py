"""Repository layer: all DB read/write operations in one place.

Keeping all SQL here makes it easy to swap out the backend later
(e.g. replace sqlite3 calls with SQLAlchemy / asyncpg for PostgreSQL).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Optional

from app.models.domain import (
    Channel,
    Creator,
    Match,
    Prediction,
    PredictionItem,
    Team,
    Transcript,
    Video,
)
from app.storage.database import Database
from app.utils.logger import get_logger

logger = get_logger(__name__)


def _now() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class Repository:
    """Single access point to all persisted data."""

    def __init__(self, db: Database) -> None:
        self._db = db

    # ------------------------------------------------------------------
    # Channels
    # ------------------------------------------------------------------

    def upsert_channel(self, channel: Channel) -> Channel:
        with self._db.connection() as conn:
            conn.execute(
                """
                INSERT INTO channels (channel_id, name, url, language, country, created_at, updated_at)
                VALUES (:channel_id, :name, :url, :language, :country, :now, :now)
                ON CONFLICT(channel_id) DO UPDATE SET
                    name=excluded.name, url=excluded.url,
                    language=excluded.language, country=excluded.country,
                    updated_at=excluded.updated_at
                """,
                {
                    "channel_id": channel.channel_id,
                    "name": channel.name,
                    "url": channel.url,
                    "language": channel.language,
                    "country": channel.country,
                    "now": _now(),
                },
            )
        return self.get_channel(channel.channel_id)  # type: ignore[return-value]

    def get_channel(self, channel_id: str) -> Optional[Channel]:
        with self._db.connection() as conn:
            row = conn.execute(
                "SELECT * FROM channels WHERE channel_id=?", (channel_id,)
            ).fetchone()
        return Channel(**dict(row)) if row else None

    def list_channels(self) -> list[Channel]:
        with self._db.connection() as conn:
            rows = conn.execute("SELECT * FROM channels ORDER BY name").fetchall()
        return [Channel(**dict(r)) for r in rows]

    # ------------------------------------------------------------------
    # Videos
    # ------------------------------------------------------------------

    def upsert_video(self, video: Video) -> Video:
        pub_date = video.publish_date.isoformat() if video.publish_date else None
        with self._db.connection() as conn:
            conn.execute(
                """
                INSERT INTO videos
                    (channel_id, video_id, video_url, title, description, publish_date,
                     language, duration_seconds, view_count, like_count, status, created_at, updated_at)
                VALUES
                    (:channel_id, :video_id, :video_url, :title, :description, :publish_date,
                     :language, :duration_seconds, :view_count, :like_count, :status, :now, :now)
                ON CONFLICT(video_id) DO UPDATE SET
                    title=excluded.title, description=excluded.description,
                    view_count=excluded.view_count, like_count=excluded.like_count,
                    status=excluded.status, updated_at=excluded.updated_at
                """,
                {
                    "channel_id": video.channel_id,
                    "video_id": video.video_id,
                    "video_url": video.video_url,
                    "title": video.title,
                    "description": video.description,
                    "publish_date": pub_date,
                    "language": video.language,
                    "duration_seconds": video.duration_seconds,
                    "view_count": video.view_count,
                    "like_count": video.like_count,
                    "status": video.status,
                    "now": _now(),
                },
            )
        return self.get_video(video.video_id)  # type: ignore[return-value]

    def get_video(self, video_id: str) -> Optional[Video]:
        with self._db.connection() as conn:
            row = conn.execute(
                "SELECT * FROM videos WHERE video_id=?", (video_id,)
            ).fetchone()
        return Video(**dict(row)) if row else None

    def list_videos(
        self,
        channel_id: Optional[str] = None,
        language: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 200,
    ) -> list[Video]:
        clauses: list[str] = []
        params: dict = {}
        if channel_id:
            clauses.append("channel_id=:channel_id")
            params["channel_id"] = channel_id
        if language:
            clauses.append("language=:language")
            params["language"] = language
        if status:
            clauses.append("status=:status")
            params["status"] = status
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        params["limit"] = limit
        with self._db.connection() as conn:
            rows = conn.execute(
                f"SELECT * FROM videos {where} ORDER BY publish_date DESC LIMIT :limit",
                params,
            ).fetchall()
        return [Video(**dict(r)) for r in rows]

    def update_video_status(self, video_id: str, status: str) -> None:
        with self._db.connection() as conn:
            conn.execute(
                "UPDATE videos SET status=?, updated_at=? WHERE video_id=?",
                (status, _now(), video_id),
            )

    # ------------------------------------------------------------------
    # Transcripts
    # ------------------------------------------------------------------

    def upsert_transcript(self, transcript: Transcript) -> None:
        segments_json = (
            json.dumps([s.model_dump() for s in transcript.segments], ensure_ascii=False)
            if transcript.segments
            else None
        )
        with self._db.connection() as conn:
            conn.execute(
                """
                INSERT INTO transcripts
                    (video_id, raw_text, segments, status, language_detected, char_count, fetched_at)
                VALUES (:video_id, :raw_text, :segments, :status, :language_detected, :char_count, :fetched_at)
                ON CONFLICT(video_id) DO UPDATE SET
                    raw_text=excluded.raw_text, segments=excluded.segments,
                    status=excluded.status, language_detected=excluded.language_detected,
                    char_count=excluded.char_count, fetched_at=excluded.fetched_at
                """,
                {
                    "video_id": transcript.video_id,
                    "raw_text": transcript.raw_text,
                    "segments": segments_json,
                    "status": transcript.status,
                    "language_detected": transcript.language_detected,
                    "char_count": transcript.char_count,
                    "fetched_at": transcript.fetched_at.isoformat() if transcript.fetched_at else _now(),
                },
            )

    def get_transcript(self, video_id: str) -> Optional[Transcript]:
        with self._db.connection() as conn:
            row = conn.execute(
                "SELECT * FROM transcripts WHERE video_id=?", (video_id,)
            ).fetchone()
        if not row:
            return None
        d = dict(row)
        if d.get("segments"):
            from app.models.domain import TranscriptSegment
            d["segments"] = [TranscriptSegment(**s) for s in json.loads(d["segments"])]
        return Transcript(**d)

    # ------------------------------------------------------------------
    # Predictions
    # ------------------------------------------------------------------

    def save_prediction(self, prediction: Prediction) -> int:
        """Insert a new prediction (with a new version) and return its id."""
        with self._db.connection() as conn:
            # Determine next version
            row = conn.execute(
                "SELECT MAX(version) as v FROM predictions WHERE video_id=?",
                (prediction.video_id,),
            ).fetchone()
            next_version = (row["v"] or 0) + 1

            cur = conn.execute(
                """
                INSERT INTO predictions
                    (video_id, channel_id, version, tournament_winner, key_arguments,
                     key_quotes, overall_confidence, extracted_at, extractor_version)
                VALUES
                    (:video_id, :channel_id, :version, :tournament_winner, :key_arguments,
                     :key_quotes, :overall_confidence, :extracted_at, :extractor_version)
                """,
                {
                    "video_id": prediction.video_id,
                    "channel_id": prediction.channel_id,
                    "version": next_version,
                    "tournament_winner": prediction.tournament_winner,
                    "key_arguments": json.dumps(prediction.key_arguments or [], ensure_ascii=False),
                    "key_quotes": json.dumps(prediction.key_quotes or [], ensure_ascii=False),
                    "overall_confidence": prediction.overall_confidence,
                    "extracted_at": prediction.extracted_at.isoformat() if prediction.extracted_at else _now(),
                    "extractor_version": prediction.extractor_version,
                },
            )
            pred_id = cur.lastrowid

            for item in prediction.items:
                conn.execute(
                    """
                    INSERT INTO prediction_items
                        (prediction_id, prediction_type, team, opponent, score_team,
                         score_opponent, match_id, stage, confidence, raw_text)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        pred_id,
                        item.prediction_type,
                        item.team,
                        item.opponent,
                        item.score_team,
                        item.score_opponent,
                        item.match_id,
                        item.stage,
                        item.confidence,
                        item.raw_text,
                    ),
                )
        return pred_id  # type: ignore[return-value]

    def get_predictions_for_video(self, video_id: str) -> list[Prediction]:
        with self._db.connection() as conn:
            pred_rows = conn.execute(
                "SELECT * FROM predictions WHERE video_id=? ORDER BY version DESC",
                (video_id,),
            ).fetchall()
            results = []
            for pr in pred_rows:
                items = conn.execute(
                    "SELECT * FROM prediction_items WHERE prediction_id=?", (pr["id"],)
                ).fetchall()
                p = Prediction(
                    id=pr["id"],
                    video_id=pr["video_id"],
                    channel_id=pr["channel_id"],
                    version=pr["version"],
                    tournament_winner=pr["tournament_winner"],
                    key_arguments=json.loads(pr["key_arguments"] or "[]"),
                    key_quotes=json.loads(pr["key_quotes"] or "[]"),
                    overall_confidence=pr["overall_confidence"],
                    extractor_version=pr["extractor_version"],
                    items=[PredictionItem(**dict(i)) for i in items],
                )
                results.append(p)
        return results

    def list_all_predictions(self) -> list[Prediction]:
        with self._db.connection() as conn:
            pred_rows = conn.execute(
                "SELECT * FROM predictions ORDER BY extracted_at DESC"
            ).fetchall()
            results = []
            for pr in pred_rows:
                items = conn.execute(
                    "SELECT * FROM prediction_items WHERE prediction_id=?", (pr["id"],)
                ).fetchall()
                p = Prediction(
                    id=pr["id"],
                    video_id=pr["video_id"],
                    channel_id=pr["channel_id"],
                    version=pr["version"],
                    tournament_winner=pr["tournament_winner"],
                    key_arguments=json.loads(pr["key_arguments"] or "[]"),
                    key_quotes=json.loads(pr["key_quotes"] or "[]"),
                    overall_confidence=pr["overall_confidence"],
                    extractor_version=pr["extractor_version"],
                    items=[PredictionItem(**dict(i)) for i in items],
                )
                results.append(p)
        return results

    # ------------------------------------------------------------------
    # Teams
    # ------------------------------------------------------------------

    def upsert_team(self, team: Team) -> None:
        with self._db.connection() as conn:
            conn.execute(
                """
                INSERT INTO teams (name, aliases, confederation, fifa_ranking)
                VALUES (:name, :aliases, :confederation, :fifa_ranking)
                ON CONFLICT(name) DO UPDATE SET
                    aliases=excluded.aliases, confederation=excluded.confederation,
                    fifa_ranking=excluded.fifa_ranking
                """,
                {
                    "name": team.name,
                    "aliases": json.dumps(team.aliases or [], ensure_ascii=False),
                    "confederation": team.confederation,
                    "fifa_ranking": team.fifa_ranking,
                },
            )

    def list_teams(self) -> list[Team]:
        with self._db.connection() as conn:
            rows = conn.execute("SELECT * FROM teams ORDER BY name").fetchall()
        result = []
        for r in rows:
            d = dict(r)
            if d.get("aliases"):
                d["aliases"] = json.loads(d["aliases"])
            result.append(Team(**d))
        return result

    # ------------------------------------------------------------------
    # Creators
    # ------------------------------------------------------------------

    def upsert_creator(self, creator: Creator) -> None:
        with self._db.connection() as conn:
            conn.execute(
                """
                INSERT INTO creators
                    (channel_id, accuracy_score, total_predictions, correct_predictions, weight, updated_at)
                VALUES (:channel_id, :accuracy_score, :total_predictions, :correct_predictions, :weight, :now)
                ON CONFLICT(channel_id) DO UPDATE SET
                    accuracy_score=excluded.accuracy_score,
                    total_predictions=excluded.total_predictions,
                    correct_predictions=excluded.correct_predictions,
                    weight=excluded.weight, updated_at=excluded.updated_at
                """,
                {
                    "channel_id": creator.channel_id,
                    "accuracy_score": creator.accuracy_score,
                    "total_predictions": creator.total_predictions,
                    "correct_predictions": creator.correct_predictions,
                    "weight": creator.weight,
                    "now": _now(),
                },
            )

    def list_creators(self) -> list[Creator]:
        with self._db.connection() as conn:
            rows = conn.execute("SELECT * FROM creators ORDER BY COALESCE(accuracy_score, -1) DESC").fetchall()
        return [Creator(**dict(r)) for r in rows]

    # ------------------------------------------------------------------
    # Stats helpers
    # ------------------------------------------------------------------

    def stats(self) -> dict:
        with self._db.connection() as conn:
            n_channels = conn.execute("SELECT COUNT(*) FROM channels").fetchone()[0]
            n_videos = conn.execute("SELECT COUNT(*) FROM videos").fetchone()[0]
            n_predictions = conn.execute("SELECT COUNT(*) FROM predictions").fetchone()[0]
            n_items = conn.execute("SELECT COUNT(*) FROM prediction_items").fetchone()[0]
            by_lang = conn.execute(
                "SELECT language, COUNT(*) as cnt FROM videos GROUP BY language"
            ).fetchall()
        return {
            "channels": n_channels,
            "videos": n_videos,
            "predictions": n_predictions,
            "prediction_items": n_items,
            "videos_by_language": {r["language"]: r["cnt"] for r in by_lang},
        }
