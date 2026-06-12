"""Configuration loader for SatisGraph.

Reads ``config/settings.yml`` and ``config/channels.yml``, merges environment
variables for secrets, and exposes typed access helpers.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

_ROOT = Path(__file__).resolve().parents[2]  # project root
_CONFIG_DIR = _ROOT / "config"


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


class AppConfig:
    """Singleton-style config object built from YAML + env vars."""

    def __init__(self) -> None:
        self._settings: dict[str, Any] = _load_yaml(_CONFIG_DIR / "settings.yml")
        self._channels_cfg: dict[str, Any] = _load_yaml(_CONFIG_DIR / "channels.yml")

        # Inject secrets from environment
        self._settings.setdefault("youtube", {})
        self._settings["youtube"]["api_key"] = os.environ.get(
            "YOUTUBE_API_KEY", self._settings["youtube"].get("api_key", "")
        )
        self._settings.setdefault("llm", {})
        self._settings["llm"]["base_url"] = os.environ.get(
            "OLLAMA_BASE_URL", self._settings["llm"].get("base_url", "http://localhost:11434")
        )

    # ------------------------------------------------------------------
    # Convenience accessors
    # ------------------------------------------------------------------

    @property
    def db_path(self) -> Path:
        return _ROOT / self._settings["database"]["path"]

    @property
    def youtube_api_key(self) -> str:
        return self._settings["youtube"]["api_key"]

    @property
    def youtube_max_results(self) -> int:
        return int(self._settings["youtube"].get("max_results_per_channel", 50))

    @property
    def youtube_published_after(self) -> str:
        return self._settings["youtube"].get("published_after", "2025-01-01T00:00:00Z")

    @property
    def llm_enabled(self) -> bool:
        return bool(self._settings["llm"].get("enabled", False))

    @property
    def llm_provider(self) -> str:
        return self._settings["llm"].get("provider", "ollama")

    @property
    def llm_base_url(self) -> str:
        return self._settings["llm"].get("base_url", "http://localhost:11434")

    @property
    def llm_model(self) -> str:
        return self._settings["llm"].get("model", "llama3.2")

    @property
    def log_level(self) -> str:
        return self._settings.get("logging", {}).get("level", "INFO")

    @property
    def log_format(self) -> str:
        return self._settings.get("logging", {}).get("format", "text")

    @property
    def log_file(self) -> str | None:
        return self._settings.get("logging", {}).get("file")

    @property
    def channels(self) -> list[dict[str, Any]]:
        return self._channels_cfg.get("channels", [])

    @property
    def world_cup_keywords(self) -> dict[str, list[str]]:
        return self._channels_cfg.get("world_cup_keywords", {})

    def get(self, *keys: str, default: Any = None) -> Any:
        """Navigate nested config with dot-path keys."""
        node: Any = self._settings
        for key in keys:
            if not isinstance(node, dict):
                return default
            node = node.get(key, default)
        return node


# Module-level singleton
config = AppConfig()
