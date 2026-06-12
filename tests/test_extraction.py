"""Tests for the extraction module."""

from __future__ import annotations

import pytest

from app.extraction.predictions import (
    _canonical,
    _detect_confidence,
    _detect_exact_scores,
    _detect_tournament_winner,
    extract_predictions,
)
from app.extraction.transcript import _stub_transcript
from app.models.domain import PredictionType, TranscriptStatus


class TestTranscript:
    def test_stub_returns_transcript(self):
        t = _stub_transcript("test_vid")
        assert t.video_id == "test_vid"
        assert t.status == TranscriptStatus.AUTO_GENERATED
        assert t.raw_text
        assert t.segments

    def test_stub_char_count(self):
        t = _stub_transcript("abc")
        assert t.char_count == len(t.raw_text)


class TestPredictionExtraction:
    FRENCH_TEXT = (
        "Je pense que la France va gagner la Coupe du Monde 2026. "
        "En finale, je vois France 2-1 Brésil. "
        "L'Espagne peut créer la surprise. "
        "Je suis très confiant à 80%."
    )

    def test_extract_returns_prediction(self):
        pred = extract_predictions(self.FRENCH_TEXT, "vid1", "ch1", "fr")
        assert pred.video_id == "vid1"
        assert pred.channel_id == "ch1"

    def test_tournament_winner_detected(self):
        winner = _detect_tournament_winner(self.FRENCH_TEXT.lower())
        assert winner == "France"

    def test_exact_score_detected(self):
        items = _detect_exact_scores(self.FRENCH_TEXT, self.FRENCH_TEXT.lower())
        assert any(i.prediction_type == PredictionType.EXACT_SCORE for i in items)

    def test_confidence_detected(self):
        conf = _detect_confidence(self.FRENCH_TEXT.lower())
        assert conf is not None
        assert 0.0 <= conf <= 1.0

    def test_canonical_mapping(self):
        assert _canonical("brésil") == "Brazil"
        assert _canonical("france") == "France"
        assert _canonical("espagne") == "Spain"

    def test_no_false_positive_on_empty(self):
        pred = extract_predictions("", "vid2", "ch1", "en")
        assert pred.tournament_winner is None
        assert pred.items == []
