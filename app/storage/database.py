"""SQLite database initialisation and connection management."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from app.utils.logger import get_logger

logger = get_logger(__name__)

_DDL = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS channels (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id  TEXT NOT NULL UNIQUE,
    name        TEXT NOT NULL,
    url         TEXT NOT NULL,
    language    TEXT NOT NULL DEFAULT 'other',
    country     TEXT,
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    updated_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

CREATE TABLE IF NOT EXISTS teams (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL UNIQUE,
    aliases         TEXT,           -- JSON array
    confederation   TEXT,
    fifa_ranking    INTEGER
);

CREATE TABLE IF NOT EXISTS matches (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    team_a          TEXT NOT NULL,
    team_b          TEXT NOT NULL,
    stage           TEXT NOT NULL DEFAULT 'group',
    grp             TEXT,           -- group label A-F etc.
    scheduled_date  TEXT,
    venue           TEXT,
    UNIQUE(team_a, team_b, stage)
);

CREATE TABLE IF NOT EXISTS videos (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id          TEXT NOT NULL REFERENCES channels(channel_id) ON DELETE CASCADE,
    video_id            TEXT NOT NULL UNIQUE,
    video_url           TEXT NOT NULL,
    title               TEXT NOT NULL,
    description         TEXT,
    publish_date        TEXT,
    language            TEXT NOT NULL DEFAULT 'other',
    duration_seconds    INTEGER,
    view_count          INTEGER,
    like_count          INTEGER,
    status              TEXT NOT NULL DEFAULT 'pending',
    created_at          TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    updated_at          TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

CREATE TABLE IF NOT EXISTS transcripts (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id            TEXT NOT NULL UNIQUE REFERENCES videos(video_id) ON DELETE CASCADE,
    raw_text            TEXT,
    segments            TEXT,       -- JSON array of {start, duration, text}
    status              TEXT NOT NULL DEFAULT 'unavailable',
    language_detected   TEXT,
    char_count          INTEGER,
    fetched_at          TEXT
);

CREATE TABLE IF NOT EXISTS predictions (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id            TEXT NOT NULL REFERENCES videos(video_id) ON DELETE CASCADE,
    channel_id          TEXT NOT NULL,
    version             INTEGER NOT NULL DEFAULT 1,
    tournament_winner   TEXT,
    key_arguments       TEXT,       -- JSON array
    key_quotes          TEXT,       -- JSON array
    overall_confidence  REAL,
    extracted_at        TEXT,
    extractor_version   TEXT NOT NULL DEFAULT '0.1.0',
    UNIQUE(video_id, version)
);

CREATE TABLE IF NOT EXISTS prediction_items (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    prediction_id   INTEGER NOT NULL REFERENCES predictions(id) ON DELETE CASCADE,
    prediction_type TEXT NOT NULL,
    team            TEXT,
    opponent        TEXT,
    score_team      INTEGER,
    score_opponent  INTEGER,
    match_id        INTEGER REFERENCES matches(id),
    stage           TEXT,
    confidence      REAL,
    raw_text        TEXT
);

CREATE TABLE IF NOT EXISTS creators (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id          TEXT NOT NULL UNIQUE REFERENCES channels(channel_id) ON DELETE CASCADE,
    accuracy_score      REAL,
    total_predictions   INTEGER NOT NULL DEFAULT 0,
    correct_predictions INTEGER NOT NULL DEFAULT 0,
    weight              REAL NOT NULL DEFAULT 1.0,
    updated_at          TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_videos_channel  ON videos(channel_id);
CREATE INDEX IF NOT EXISTS idx_videos_language ON videos(language);
CREATE INDEX IF NOT EXISTS idx_videos_date     ON videos(publish_date);
CREATE INDEX IF NOT EXISTS idx_videos_status   ON videos(status);
CREATE INDEX IF NOT EXISTS idx_pred_items_type ON prediction_items(prediction_type);
CREATE INDEX IF NOT EXISTS idx_pred_items_team ON prediction_items(team);
CREATE INDEX IF NOT EXISTS idx_pred_video      ON predictions(video_id);
"""


class Database:
    """Thin wrapper around a SQLite connection."""

    def __init__(self, db_path: Path) -> None:
        self._path = db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _init_schema(self) -> None:
        with self.connection() as conn:
            conn.executescript(_DDL)
        logger.info("Schema initialised", extra={"db": str(self._path)})

    @contextmanager
    def connection(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(self._path, detect_types=sqlite3.PARSE_DECLTYPES)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
