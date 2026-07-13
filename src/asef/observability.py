from __future__ import annotations

import json
import logging
import re
from datetime import UTC, datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any


_OPENAI_KEY = re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{8,}\b")
_ASSIGNMENT = re.compile(
    r"(?i)\b(api[_-]?key|password|access[_-]?token|private[_-]?key|secret)\b[\"']?\s*[:=]\s*[\"']?[^\s,;\"'}]+"
)
_EXTRA_FIELDS = (
    "run_id",
    "operation",
    "component",
    "status",
    "classification",
    "duration_ms",
    "exit_code",
)


def configure_operational_logging(log_dir: Path, level: str = "INFO") -> logging.Logger:
    """Configure local JSONL logs without changing machine-readable CLI stdout."""
    log_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("asef")
    logger.setLevel(getattr(logging, level.upper()))
    logger.propagate = False
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()
    handler = RotatingFileHandler(
        log_dir / "asef.jsonl",
        maxBytes=1_048_576,
        backupCount=2,
        encoding="utf-8",
    )
    handler.setFormatter(SafeJsonFormatter())
    logger.addHandler(handler)
    return logger


def close_operational_logging(logger: logging.Logger) -> None:
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()


class SafeJsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "schema_version": "1.0.0",
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": sanitize_text(record.getMessage()),
        }
        for field in _EXTRA_FIELDS:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = sanitize_text(str(value)) if isinstance(value, str) else value
        if record.exc_info:
            payload["exception_type"] = record.exc_info[0].__name__
        return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def sanitize_text(value: str) -> str:
    value = _OPENAI_KEY.sub("[REDACTED_OPENAI_KEY]", value)
    return _ASSIGNMENT.sub(lambda match: f"{match.group(1)}=[REDACTED]", value)
