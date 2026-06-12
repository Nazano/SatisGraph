"""Structured logging utility for SatisGraph."""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class JSONFormatter(logging.Formatter):
    """Emit log records as JSON lines."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "extra"):
            payload.update(record.extra)
        return json.dumps(payload, ensure_ascii=False)


def get_logger(name: str, level: str = "INFO", fmt: str = "text", log_file: str | None = None) -> logging.Logger:
    """Return a configured logger.

    Args:
        name: Logger name (typically ``__name__``).
        level: Log level string (``"INFO"``, ``"DEBUG"`` …).
        fmt: ``"json"`` for structured JSON output, ``"text"`` for human-readable.
        log_file: Optional path to write logs to a file in addition to stdout.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # already configured

    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    handler = logging.StreamHandler(sys.stdout)
    if fmt == "json":
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s – %(message)s")
        )
    logger.addHandler(handler)

    if log_file:
        path = Path(log_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(path)
        fh.setFormatter(JSONFormatter())
        logger.addHandler(fh)

    logger.propagate = False
    return logger
