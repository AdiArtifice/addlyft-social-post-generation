"""Token usage logging and USD estimates for Nano Banana image models on Vertex AI."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

# Defaults match Nano Banana 2 Lite list rates; override via IMAGE_* env.
DEFAULT_INPUT_USD_PER_MILLION = 0.25
DEFAULT_TEXT_OUTPUT_USD_PER_MILLION = 1.50
DEFAULT_IMAGE_OUTPUT_USD_PER_MILLION = 30.00

# Flash-Lite / Flash Image approximate output tokens by size.
IMAGE_OUTPUT_TOKENS_BY_SIZE = {
    "512": 747,
    "1K": 1120,
    "2K": 1680,
    "4K": 2520,
}

LOG_PATH = Path(__file__).resolve().parent / "logs" / "image_usage.jsonl"


def _rates() -> tuple[float, float, float]:
    return (
        float(os.getenv("IMAGE_INPUT_USD_PER_MILLION", DEFAULT_INPUT_USD_PER_MILLION)),
        float(
            os.getenv(
                "IMAGE_TEXT_OUTPUT_USD_PER_MILLION",
                DEFAULT_TEXT_OUTPUT_USD_PER_MILLION,
            )
        ),
        float(
            os.getenv(
                "IMAGE_OUTPUT_USD_PER_MILLION",
                DEFAULT_IMAGE_OUTPUT_USD_PER_MILLION,
            )
        ),
    )


def estimate_cost_usd(
    *,
    prompt_tokens: int,
    text_output_tokens: int = 0,
    thoughts_tokens: int = 0,
    image_output_tokens: int = 0,
) -> float:
    input_rate, text_out_rate, image_out_rate = _rates()
    billed_text = text_output_tokens + thoughts_tokens
    return (
        (prompt_tokens / 1_000_000) * input_rate
        + (billed_text / 1_000_000) * text_out_rate
        + (image_output_tokens / 1_000_000) * image_out_rate
    )


def _image_tokens_from_response(response, *, image_size: str) -> int:
    """Prefer modality IMAGE details from usage_metadata; else size table / candidates."""
    meta = response.usage_metadata
    details = getattr(meta, "candidates_tokens_details", None) or []
    for detail in details:
        modality = getattr(detail, "modality", None)
        modality_name = getattr(modality, "name", None) or str(modality or "")
        if "IMAGE" in modality_name.upper():
            count = int(getattr(detail, "token_count", None) or 0)
            if count:
                return count
    candidates = int(getattr(meta, "candidates_token_count", None) or 0)
    if candidates >= 700:
        return candidates
    return IMAGE_OUTPUT_TOKENS_BY_SIZE.get(image_size.upper(), 1120)


def usage_from_response(
    response,
    *,
    model: str,
    source: str = "generate_poster",
    image_size: str = "2K",
    aspect_ratio: str = "9:16",
    wall_seconds: float | None = None,
) -> dict:
    meta = response.usage_metadata
    prompt = int(getattr(meta, "prompt_token_count", None) or 0)
    thoughts = int(getattr(meta, "thoughts_token_count", None) or 0)
    candidates = int(getattr(meta, "candidates_token_count", None) or 0)
    total = int(
        getattr(meta, "total_token_count", None) or (prompt + candidates + thoughts)
    )

    image_out = _image_tokens_from_response(response, image_size=image_size)
    # Remaining candidate tokens (if any) treated as text output from the interleaved reply.
    text_out = max(0, candidates - image_out) if candidates >= 700 else candidates

    cost = estimate_cost_usd(
        prompt_tokens=prompt,
        text_output_tokens=text_out,
        thoughts_tokens=thoughts,
        image_output_tokens=image_out,
    )
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "model": model,
        "aspect_ratio": aspect_ratio,
        "image_size": image_size,
        "prompt_tokens": prompt,
        "text_output_tokens": text_out,
        "thoughts_tokens": thoughts,
        "image_output_tokens": image_out,
        "candidates_token_count": candidates,
        "total_tokens": total,
        "estimated_usd": round(cost, 8),
    }
    if wall_seconds is not None:
        record["wall_seconds"] = round(wall_seconds, 2)
    return record


def log_usage(record: dict) -> Path:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    return LOG_PATH


def format_usage(record: dict) -> str:
    wall = ""
    if "wall_seconds" in record:
        wall = f"  |  wall={record['wall_seconds']}s"
    return (
        f"tokens: prompt={record['prompt_tokens']}  "
        f"text_out={record['text_output_tokens']}  "
        f"thoughts={record['thoughts_tokens']}  "
        f"image_out={record['image_output_tokens']}  "
        f"total={record['total_tokens']}  |  "
        f"est. ${record['estimated_usd']:.6f}"
        f"{wall}"
    )
