"""Token usage logging and USD estimates for Gemini on Vertex AI."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Gemini 2.5 Flash-Lite standard pay-as-you-go (USD per 1M tokens).
# Thinking tokens are billed as output. Override via env if Google changes rates.
DEFAULT_INPUT_USD_PER_MILLION = 0.10
DEFAULT_OUTPUT_USD_PER_MILLION = 0.40

LOG_PATH = Path(__file__).resolve().parent / "logs" / "usage.jsonl"


def _rates() -> tuple[float, float]:
    return (
        float(os.getenv("GEMINI_INPUT_PRICE_PER_MILLION", DEFAULT_INPUT_USD_PER_MILLION)),
        float(os.getenv("GEMINI_OUTPUT_PRICE_PER_MILLION", DEFAULT_OUTPUT_USD_PER_MILLION)),
    )


def estimate_cost_usd(
    *,
    prompt_tokens: int,
    output_tokens: int,
    thoughts_tokens: int = 0,
) -> float:
    input_rate, output_rate = _rates()
    billed_output = output_tokens + thoughts_tokens
    return (prompt_tokens / 1_000_000) * input_rate + (
        billed_output / 1_000_000
    ) * output_rate


def usage_from_response(response, *, model: str, source: str = "generate") -> dict:
    meta = response.usage_metadata
    prompt = int(getattr(meta, "prompt_token_count", None) or 0)
    output = int(getattr(meta, "candidates_token_count", None) or 0)
    thoughts = int(getattr(meta, "thoughts_token_count", None) or 0)
    total = int(
        getattr(meta, "total_token_count", None) or (prompt + output + thoughts)
    )
    cost = estimate_cost_usd(
        prompt_tokens=prompt,
        output_tokens=output,
        thoughts_tokens=thoughts,
    )
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "model": model,
        "prompt_tokens": prompt,
        "output_tokens": output,
        "thoughts_tokens": thoughts,
        "total_tokens": total,
        "estimated_usd": round(cost, 8),
    }


def log_usage(record: dict) -> Path:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    return LOG_PATH


REPORT_SOURCES = frozenset({"api_pipeline", "api_regenerate"})


def read_generation_reports(limit: int = 20) -> list[dict]:
    """Return newest-first pipeline/regenerate total records from usage.jsonl."""
    if limit < 1:
        return []
    if not LOG_PATH.exists():
        return []

    matches: list[dict] = []
    with LOG_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(record, dict):
                continue
            if record.get("source") in REPORT_SOURCES:
                matches.append(record)

    matches.reverse()
    return matches[:limit]


def format_usage(record: dict) -> str:
    return (
        f"tokens: prompt={record['prompt_tokens']}  "
        f"output={record['output_tokens']}  "
        f"thoughts={record['thoughts_tokens']}  "
        f"total={record['total_tokens']}  |  "
        f"est. ${record['estimated_usd']:.8f}"
    )
