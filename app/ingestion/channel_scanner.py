"""Channel scanner: orchestrates fetching videos from all configured channels."""

from __future__ import annotations

import time
from datetime import datetime, timezone

from app.ingestion.filters import is_world_cup_related
from app.ingestion.youtube_client import YouTubeClient
from app.models.domain import Channel, Video, VideoStatus
from app.storage.repository import Repository
from app.utils.config import config
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ChannelScanner:
    """Scans all configured channels for new World Cup 2026 videos."""

    def __init__(self, repo: Repository, client: YouTubeClient | None = None) -> None:
        self._repo = repo
        self._client = client or YouTubeClient()

    def sync_channels(self) -> list[Channel]:
        """Ensure all channels from config exist in the DB."""
        channels: list[Channel] = []
        for ch_cfg in config.channels:
            ch = Channel(
                channel_id=ch_cfg["channel_id"],
                name=ch_cfg["name"],
                url=ch_cfg["url"],
                language=ch_cfg.get("language", "other"),
                country=ch_cfg.get("country"),
            )
            ch = self._repo.upsert_channel(ch)
            channels.append(ch)
            logger.info(f"Synced channel: {ch.name}")
        return channels

    def scan_all(self, retry_attempts: int = 3) -> int:
        """Scan all channels and store new World Cup videos. Returns count of new videos."""
        channels = self.sync_channels()
        total = 0
        for channel in channels:
            try:
                total += self._scan_channel(channel, retry_attempts)
            except Exception as exc:
                logger.error(f"Error scanning channel {channel.name}: {exc}")
        logger.info(f"Scan complete. {total} new videos stored.")
        return total

    def _scan_channel(self, channel: Channel, retry_attempts: int) -> int:
        """Fetch and filter videos for a single channel."""
        raw_videos = []
        for attempt in range(1, retry_attempts + 1):
            try:
                raw_videos = self._client.list_channel_videos(channel.channel_id)
                break
            except Exception as exc:
                logger.warning(f"Attempt {attempt} failed for {channel.name}: {exc}")
                if attempt < retry_attempts:
                    time.sleep(config.get("ingestion", "retry_delay_seconds", default=5))

        count = 0
        for raw in raw_videos:
            if not is_world_cup_related(raw.title, raw.description, channel.language):
                continue
            video = Video(
                channel_id=channel.channel_id,
                video_id=raw.video_id,
                video_url=f"https://www.youtube.com/watch?v={raw.video_id}",
                title=raw.title,
                description=raw.description,
                publish_date=raw.publish_date,
                language=channel.language,  # type: ignore[arg-type]
                duration_seconds=raw.duration_seconds,
                view_count=raw.view_count,
                like_count=raw.like_count,
                status=VideoStatus.PENDING,
            )
            self._repo.upsert_video(video)
            count += 1
        return count
