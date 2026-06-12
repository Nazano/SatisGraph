"""Pydantic models for SatisGraph domain objects."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class Language(str, Enum):
    FR = "fr"
    EN = "en"
    ES = "es"
    OTHER = "other"


# ---------------------------------------------------------------------------
# Channel
# ---------------------------------------------------------------------------


class Channel(BaseModel):
    id: Optional[int] = None
    channel_id: str = Field(..., description="YouTube channel ID")
    name: str
    url: str
    language: Language = Language.OTHER
    country: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(use_enum_values=True)


# ---------------------------------------------------------------------------
# Video
# ---------------------------------------------------------------------------


class VideoStatus(str, Enum):
    PENDING = "pending"
    TRANSCRIPT_FETCHED = "transcript_fetched"
    TRANSCRIPT_UNAVAILABLE = "transcript_unavailable"
    PREDICTIONS_EXTRACTED = "predictions_extracted"
    ERROR = "error"


class Video(BaseModel):
    id: Optional[int] = None
    channel_id: str
    video_id: str = Field(..., description="YouTube video ID")
    video_url: str
    title: str
    description: Optional[str] = None
    publish_date: Optional[datetime] = None
    language: Language = Language.OTHER
    duration_seconds: Optional[int] = None
    view_count: Optional[int] = None
    like_count: Optional[int] = None
    status: VideoStatus = VideoStatus.PENDING
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(use_enum_values=True)

    @property
    def youtube_url(self) -> str:
        return f"https://www.youtube.com/watch?v={self.video_id}"


# ---------------------------------------------------------------------------
# Transcript
# ---------------------------------------------------------------------------


class TranscriptSegment(BaseModel):
    start: float = Field(..., description="Start time in seconds")
    duration: float = Field(..., description="Duration in seconds")
    text: str


class TranscriptStatus(str, Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    AUTO_GENERATED = "auto_generated"
    ERROR = "error"


class Transcript(BaseModel):
    id: Optional[int] = None
    video_id: str
    raw_text: Optional[str] = None
    segments: Optional[list[TranscriptSegment]] = None
    status: TranscriptStatus = TranscriptStatus.UNAVAILABLE
    language_detected: Optional[str] = None
    char_count: Optional[int] = None
    fetched_at: Optional[datetime] = None
    model_config = ConfigDict(use_enum_values=True)


# ---------------------------------------------------------------------------
# Team
# ---------------------------------------------------------------------------


class Team(BaseModel):
    id: Optional[int] = None
    name: str
    aliases: Optional[list[str]] = None
    confederation: Optional[str] = None
    fifa_ranking: Optional[int] = None


# ---------------------------------------------------------------------------
# Match
# ---------------------------------------------------------------------------


class MatchStage(str, Enum):
    GROUP = "group"
    ROUND_OF_32 = "round_of_32"
    ROUND_OF_16 = "round_of_16"
    QUARTER_FINAL = "quarter_final"
    SEMI_FINAL = "semi_final"
    THIRD_PLACE = "third_place"
    FINAL = "final"


class Match(BaseModel):
    id: Optional[int] = None
    team_a: str
    team_b: str
    stage: MatchStage = MatchStage.GROUP
    group: Optional[str] = None
    scheduled_date: Optional[datetime] = None
    venue: Optional[str] = None
    model_config = ConfigDict(use_enum_values=True)

    @property
    def label(self) -> str:
        return f"{self.team_a} vs {self.team_b}"


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------


class PredictionType(str, Enum):
    TOURNAMENT_WINNER = "tournament_winner"
    MATCH_WINNER = "match_winner"
    EXACT_SCORE = "exact_score"
    QUALIFIED_TEAM = "qualified_team"
    GROUP_ORDER = "group_order"
    DARK_HORSE = "dark_horse"
    ELIMINATED_TEAM = "eliminated_team"
    TOP_SCORER = "top_scorer"
    OTHER = "other"


class PredictionItem(BaseModel):
    id: Optional[int] = None
    prediction_id: Optional[int] = None
    prediction_type: PredictionType
    team: Optional[str] = None
    opponent: Optional[str] = None
    score_team: Optional[int] = None
    score_opponent: Optional[int] = None
    match_id: Optional[int] = None
    stage: Optional[str] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    raw_text: Optional[str] = None
    model_config = ConfigDict(use_enum_values=True)


class Prediction(BaseModel):
    id: Optional[int] = None
    video_id: str
    channel_id: str
    version: int = 1
    tournament_winner: Optional[str] = None
    key_arguments: Optional[list[str]] = None
    key_quotes: Optional[list[str]] = None
    overall_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    items: list[PredictionItem] = Field(default_factory=list)
    extracted_at: Optional[datetime] = None
    extractor_version: str = "0.1.0"
    model_config = ConfigDict(use_enum_values=True)


# ---------------------------------------------------------------------------
# Creator / scoring
# ---------------------------------------------------------------------------


class Creator(BaseModel):
    id: Optional[int] = None
    channel_id: str
    accuracy_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    total_predictions: int = 0
    correct_predictions: int = 0
    weight: float = 1.0
    updated_at: Optional[datetime] = None
