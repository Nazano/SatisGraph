"""YouTube Data API v3 client.

TODO: Replace the stub implementations with real API calls.
      1. Install: google-api-python-client
      2. Build the service:
             from googleapiclient.discovery import build
             youtube = build("youtube", "v3", developerKey=api_key)
      3. Implement list_channel_videos() and get_video_details() using the
         real search.list / videos.list endpoints.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.utils.config import config
from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class RawVideoMetadata:
    """Raw metadata as returned by the YouTube API (or a stub)."""

    video_id: str
    channel_id: str
    title: str
    description: str
    publish_date: datetime
    duration_seconds: Optional[int]
    view_count: Optional[int]
    like_count: Optional[int]


class YouTubeClient:
    """Wrapper around the YouTube Data API v3."""

    def __init__(self, api_key: str = "") -> None:
        self._api_key = api_key or config.youtube_api_key
        self._max_results = config.youtube_max_results
        self._published_after = config.youtube_published_after

        if not self._api_key:
            logger.warning(
                "YOUTUBE_API_KEY not set – YouTubeClient will return stub data only."
            )

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def list_channel_videos(self, channel_id: str) -> list[RawVideoMetadata]:
        """Return recent videos for a channel.

        TODO: Replace stub with real API call:
            response = youtube.search().list(
                part="snippet",
                channelId=channel_id,
                maxResults=self._max_results,
                publishedAfter=self._published_after,
                order="date",
                type="video",
            ).execute()
        """
        if self._api_key:
            return self._fetch_real(channel_id)
        logger.info(f"[STUB] list_channel_videos for {channel_id}")
        return []  # real data fetched in channel_scanner via seed data

    def get_video_details(self, video_id: str) -> Optional[RawVideoMetadata]:
        """Fetch full metadata for a single video.

        TODO: Replace stub with real API call:
            response = youtube.videos().list(
                part="snippet,contentDetails,statistics",
                id=video_id,
            ).execute()
        """
        if self._api_key:
            return self._fetch_video_real(video_id)
        logger.info(f"[STUB] get_video_details for {video_id}")
        return None

    # ------------------------------------------------------------------
    # Private – real API calls (requires valid api_key)
    # ------------------------------------------------------------------

    def _fetch_real(self, channel_id: str) -> list[RawVideoMetadata]:  # pragma: no cover
        """Real implementation – skipped when no API key is present."""
        # TODO: implement using googleapiclient
        raise NotImplementedError("Set YOUTUBE_API_KEY to enable real API calls.")

    def _fetch_video_real(self, video_id: str) -> Optional[RawVideoMetadata]:  # pragma: no cover
        raise NotImplementedError("Set YOUTUBE_API_KEY to enable real API calls.")
