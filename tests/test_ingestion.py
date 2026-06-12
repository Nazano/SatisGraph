"""Tests for the ingestion module."""

from __future__ import annotations

import pytest

from app.ingestion.filters import is_world_cup_related


class TestIsWorldCupRelated:
    def test_fr_keyword_in_title(self):
        assert is_world_cup_related("Mes pronostics Coupe du monde 2026", language="fr")

    def test_en_keyword_in_title(self):
        assert is_world_cup_related("World Cup 2026 Full Predictions", language="en")

    def test_es_keyword_in_title(self):
        assert is_world_cup_related("Copa del mundo 2026 análisis", language="es")

    def test_no_match_returns_false(self):
        assert not is_world_cup_related("Best recipes of the week", language="en")

    def test_keyword_in_description(self):
        assert is_world_cup_related(
            "My football video",
            description="I break down the World Cup 2026 groups",
            language="en",
        )

    def test_case_insensitive(self):
        assert is_world_cup_related("WORLD CUP 2026 ANALYSIS", language="en")

    def test_empty_strings(self):
        assert not is_world_cup_related("", "", language="en")
