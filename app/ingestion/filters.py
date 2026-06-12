"""Keyword-based filter to determine if a video is World Cup 2026 related."""

from __future__ import annotations

import re

from app.utils.config import config
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Flatten all keywords for quick matching
_ALL_KEYWORDS: list[str] = []
for _kws in config.world_cup_keywords.values():
    _ALL_KEYWORDS.extend([k.lower() for k in _kws])


def is_world_cup_related(title: str, description: str = "", language: str = "en") -> bool:
    """Return True if the video appears to be about the 2026 World Cup.

    Checks title and description against language-specific keyword lists, then
    falls back to the global list.
    """
    text = f"{title} {description}".lower()

    lang_keywords = [k.lower() for k in config.world_cup_keywords.get(language, [])]
    all_kws = lang_keywords or _ALL_KEYWORDS

    for kw in all_kws:
        # whole-word or phrase match to avoid false positives
        pattern = r"(?<![a-z])" + re.escape(kw) + r"(?![a-z])"
        if re.search(pattern, text):
            logger.debug(f"Matched keyword '{kw}' in: {title!r}")
            return True
    return False
