"""Prediction scoring and consensus aggregation.

Weights:
  - creator weight (accuracy / reputation)
  - freshness weight (newer videos score higher)
  - prediction confidence
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from app.models.domain import Creator, Prediction, PredictionItem, PredictionType
from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ConsensusItem:
    """Aggregated consensus for a single prediction type + team."""

    prediction_type: str
    team: Optional[str]
    opponent: Optional[str] = None
    score_team: Optional[int] = None
    score_opponent: Optional[int] = None
    stage: Optional[str] = None
    weighted_score: float = 0.0
    vote_count: int = 0
    supporters: list[str] = field(default_factory=list)  # channel_ids


@dataclass
class RankedPrediction:
    """A prediction with its computed overall weight."""

    prediction: Prediction
    channel_weight: float
    freshness_weight: float
    final_weight: float


def _freshness_weight(pub_date: Optional[datetime], max_days: int = 180) -> float:
    """More recent videos get a higher weight (linear decay)."""
    if pub_date is None:
        return 0.5
    now = datetime.now(tz=timezone.utc)
    if pub_date.tzinfo is None:
        pub_date = pub_date.replace(tzinfo=timezone.utc)
    age_days = (now - pub_date).days
    return max(0.1, 1.0 - age_days / max_days)


def rank_predictions(
    predictions: list[Prediction],
    creators: list[Creator],
    video_publish_dates: dict[str, Optional[datetime]] | None = None,
) -> list[RankedPrediction]:
    """Rank predictions by combined weight.

    Args:
        predictions: List of Prediction objects.
        creators: List of Creator objects (for channel weights).
        video_publish_dates: Map of video_id → publish_date for freshness scoring.
    """
    creator_map: dict[str, Creator] = {c.channel_id: c for c in creators}
    video_publish_dates = video_publish_dates or {}

    ranked: list[RankedPrediction] = []
    for pred in predictions:
        creator = creator_map.get(pred.channel_id)
        ch_weight = creator.weight if creator else 1.0
        if creator and creator.accuracy_score is not None:
            ch_weight *= 1 + creator.accuracy_score  # bonus for accurate creators

        pub_date = video_publish_dates.get(pred.video_id)
        fresh_w = _freshness_weight(pub_date)

        final_w = ch_weight * fresh_w * (pred.overall_confidence or 0.7)
        ranked.append(RankedPrediction(pred, ch_weight, fresh_w, final_w))

    ranked.sort(key=lambda r: r.final_weight, reverse=True)
    return ranked


def aggregate_consensus(
    ranked: list[RankedPrediction],
) -> list[ConsensusItem]:
    """Compute a weighted consensus across all ranked predictions.

    Returns one :class:`ConsensusItem` per (prediction_type, team) pair,
    sorted by weighted_score descending.
    """
    bucket: dict[tuple, ConsensusItem] = defaultdict(
        lambda: ConsensusItem(prediction_type="", team=None)
    )

    for rp in ranked:
        for item in rp.prediction.items:
            key = (
                item.prediction_type,
                item.team,
                item.opponent,
                item.score_team,
                item.score_opponent,
            )
            ci = bucket[key]
            ci.prediction_type = item.prediction_type
            ci.team = item.team
            ci.opponent = item.opponent
            ci.score_team = item.score_team
            ci.score_opponent = item.score_opponent
            ci.stage = item.stage
            weight = rp.final_weight * (item.confidence or 0.7)
            ci.weighted_score += weight
            ci.vote_count += 1
            ci.supporters.append(rp.prediction.channel_id)

    result = sorted(bucket.values(), key=lambda c: c.weighted_score, reverse=True)
    return result


def get_tournament_winner_consensus(ranked: list[RankedPrediction]) -> list[ConsensusItem]:
    """Return consensus for tournament winner picks only."""
    all_consensus = aggregate_consensus(ranked)
    return [c for c in all_consensus if c.prediction_type == PredictionType.TOURNAMENT_WINNER]
