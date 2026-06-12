"""Tests for the storage layer (uses an in-memory/temp SQLite DB)."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from app.models.domain import Channel, Creator, Prediction, PredictionItem, PredictionType, Team, Video
from app.storage.database import Database
from app.storage.repository import Repository


@pytest.fixture()
def repo() -> Repository:
    with tempfile.TemporaryDirectory() as tmpdir:
        db = Database(Path(tmpdir) / "test.db")
        yield Repository(db)


class TestChannelRepository:
    def test_upsert_and_get(self, repo: Repository):
        ch = Channel(channel_id="UC_TEST_1", name="TestChannel", url="https://youtube.com/@test", language="en")
        repo.upsert_channel(ch)
        retrieved = repo.get_channel("UC_TEST_1")
        assert retrieved is not None
        assert retrieved.name == "TestChannel"

    def test_list_channels(self, repo: Repository):
        repo.upsert_channel(Channel(channel_id="UC_A", name="A", url="https://a.com", language="fr"))
        repo.upsert_channel(Channel(channel_id="UC_B", name="B", url="https://b.com", language="en"))
        channels = repo.list_channels()
        assert len(channels) == 2

    def test_upsert_updates_existing(self, repo: Repository):
        ch = Channel(channel_id="UC_UPDATE", name="Old Name", url="https://x.com", language="en")
        repo.upsert_channel(ch)
        ch2 = Channel(channel_id="UC_UPDATE", name="New Name", url="https://x.com", language="en")
        repo.upsert_channel(ch2)
        result = repo.get_channel("UC_UPDATE")
        assert result.name == "New Name"


class TestVideoRepository:
    def _channel(self, repo: Repository, cid: str = "UC_TEST") -> None:
        repo.upsert_channel(Channel(channel_id=cid, name="Test", url="https://t.com", language="en"))

    def test_upsert_and_get(self, repo: Repository):
        self._channel(repo)
        v = Video(channel_id="UC_TEST", video_id="VID1", video_url="https://yt.com/watch?v=VID1", title="Test Video", language="en")
        repo.upsert_video(v)
        result = repo.get_video("VID1")
        assert result is not None
        assert result.title == "Test Video"

    def test_list_videos_filter_language(self, repo: Repository):
        self._channel(repo, "UC_FR")
        self._channel(repo, "UC_EN")
        repo.upsert_video(Video(channel_id="UC_FR", video_id="VFR", video_url="u", title="FR", language="fr"))
        repo.upsert_video(Video(channel_id="UC_EN", video_id="VEN", video_url="u", title="EN", language="en"))
        fr_vids = repo.list_videos(language="fr")
        assert len(fr_vids) == 1
        assert fr_vids[0].video_id == "VFR"


class TestPredictionRepository:
    def _setup(self, repo: Repository):
        repo.upsert_channel(Channel(channel_id="UC_P", name="P", url="https://p.com", language="fr"))
        repo.upsert_video(Video(channel_id="UC_P", video_id="VPRED", video_url="u", title="T", language="fr"))

    def test_save_and_get(self, repo: Repository):
        self._setup(repo)
        pred = Prediction(
            video_id="VPRED", channel_id="UC_P",
            tournament_winner="France",
            items=[PredictionItem(prediction_type=PredictionType.TOURNAMENT_WINNER, team="France", confidence=0.8)],
        )
        repo.save_prediction(pred)
        results = repo.get_predictions_for_video("VPRED")
        assert len(results) == 1
        assert results[0].tournament_winner == "France"
        assert len(results[0].items) == 1

    def test_version_increments(self, repo: Repository):
        self._setup(repo)
        pred = Prediction(video_id="VPRED", channel_id="UC_P", items=[])
        repo.save_prediction(pred)
        repo.save_prediction(pred)
        results = repo.get_predictions_for_video("VPRED")
        versions = sorted(r.version for r in results)
        assert versions == [1, 2]


class TestStatsRepository:
    def test_stats_returns_counts(self, repo: Repository):
        repo.upsert_channel(Channel(channel_id="UC_S", name="S", url="u", language="en"))
        stats = repo.stats()
        assert stats["channels"] == 1
        assert stats["videos"] == 0
