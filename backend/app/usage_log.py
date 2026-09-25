"""Thin wrapper so the backend can log token usage without path hacks."""

from __future__ import annotations

import sys
from datetime import datetime, timezone

from .config import PROJECT_ROOT, settings

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from usage import log_usage, read_generation_reports, usage_from_response  # noqa: E402

__all__ = [
    "log_generation_usage",
    "log_pipeline_totals",
    "read_generation_reports",
]


def log_generation_usage(response, *, source: str) -> dict:
    record = usage_from_response(response, model=settings.gemini_model, source=source)
    log_usage(record)
    return record


def log_pipeline_totals(record: dict) -> dict:
    """Persist a combined Generate/Regenerate totals row (source set by caller)."""
    payload = dict(record)
    payload.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
    log_usage(payload)
    return payload
