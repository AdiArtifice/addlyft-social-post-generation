"""Thin wrapper so the backend can log token usage without path hacks."""

from __future__ import annotations

import sys

from .config import PROJECT_ROOT, settings

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from usage import log_usage, usage_from_response  # noqa: E402


def log_generation_usage(response, *, source: str) -> dict:
    record = usage_from_response(response, model=settings.gemini_model, source=source)
    log_usage(record)
    return record
