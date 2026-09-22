"""Vertex AI client for Nano Banana image poster generation (lite by default)."""

from __future__ import annotations

import os
import time
from io import BytesIO
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image as PILImage

from guardrails import (
    SafetyBlockedError,
    default_safety_settings,
    person_generation_block_message,
    raise_if_safety_blocked,
)
from image_usage import format_usage, log_usage, usage_from_response
from prompt import role_label_for_part

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}
MAX_REFS = 3


def get_settings() -> dict[str, str]:
    project = os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not project:
        raise RuntimeError("Missing GOOGLE_CLOUD_PROJECT in .env")
    return {
        "project": project,
        "location": os.getenv("IMAGE_LOCATION", "global"),
        "model": os.getenv("IMAGE_MODEL", "gemini-3.1-flash-lite-image"),
        "aspect_ratio": os.getenv("IMAGE_ASPECT_RATIO", "9:16"),
        # Lite model supports 1K only; Pro/Flash support 2K/4K.
        "image_size": os.getenv("IMAGE_SIZE", "1K"),
    }


def get_client() -> genai.Client:
    s = get_settings()
    return genai.Client(
        vertexai=True,
        project=s["project"],
        location=s["location"],
    )


def prepare_jpeg_bytes(path: Path, max_side: int = 1600) -> tuple[bytes, str]:
    """Load image, convert to RGB JPEG under size limits for Vertex inline refs."""
    img = PILImage.open(path)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    elif img.mode != "RGB":
        img = img.convert("RGB")

    w, h = img.size
    scale = min(1.0, max_side / max(w, h))
    if scale < 1.0:
        img = img.resize((int(w * scale), int(h * scale)), PILImage.Resampling.LANCZOS)

    buf = BytesIO()
    img.save(buf, format="JPEG", quality=90, optimize=True)
    return buf.getvalue(), "image/jpeg"


def list_reference_images(folder: Path) -> list[Path]:
    if not folder.is_dir():
        return []
    return [
        p
        for p in sorted(folder.iterdir())
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS
    ]


def load_role_reference_parts(
    role_refs: list[dict[str, Any]],
    *,
    max_refs: int = MAX_REFS,
) -> list[types.Part]:
    """Build interleaved text-label + image parts for up to max_refs role refs.

    Each item: {"path": Path, "role": str, "name": str}.
    Empty list is valid (text-only generation).
    """
    if not role_refs:
        return []
    if len(role_refs) > max_refs:
        raise ValueError(f"At most {max_refs} reference images allowed, got {len(role_refs)}")

    parts: list[types.Part] = []
    for i, item in enumerate(role_refs[:max_refs], start=1):
        path = Path(item["path"])
        role = (item.get("role") or "auto").strip().lower()
        name = item.get("name") or path.name
        label = (
            f"REFERENCE {i} — file: {name} — {role_label_for_part(role)}"
        )
        parts.append(types.Part.from_text(text=label))
        data, mime = prepare_jpeg_bytes(path)
        parts.append(types.Part.from_bytes(data=data, mime_type=mime))
    return parts


def load_reference_parts(paths: list[Path], *, max_refs: int = MAX_REFS) -> list[types.Part]:
    """Backward-compatible loader: unlabeled images as role=auto."""
    role_refs = [{"path": p, "role": "auto", "name": p.name} for p in paths[:max_refs]]
    return load_role_reference_parts(role_refs, max_refs=max_refs)


def extract_image_bytes(response: Any) -> bytes | None:
    if not response.candidates:
        return None
    content = response.candidates[0].content
    if not content or not content.parts:
        return None
    for part in content.parts:
        inline = getattr(part, "inline_data", None)
        if inline is not None:
            data = getattr(inline, "data", None)
            if data:
                return data if isinstance(data, (bytes, bytearray)) else bytes(data)
        as_image = getattr(part, "as_image", None)
        if callable(as_image):
            try:
                img = as_image()
                if img is not None:
                    buf = BytesIO()
                    img.save(buf, format="PNG")
                    return buf.getvalue()
            except Exception:
                pass
    return None


def extract_text(response: Any) -> str:
    chunks: list[str] = []
    if not response.candidates:
        return ""
    content = response.candidates[0].content
    if not content or not content.parts:
        return ""
    for part in content.parts:
        if getattr(part, "thought", None) is True and not getattr(part, "text", None):
            continue
        text = getattr(part, "text", None)
        if text:
            chunks.append(text)
    return "\n".join(chunks).strip()


def _response_debug(response: Any) -> str:
    bits: list[str] = []
    pf = getattr(response, "prompt_feedback", None)
    if pf is not None:
        bits.append(f"prompt_feedback={pf}")
    cands = response.candidates or []
    bits.append(f"n_candidates={len(cands)}")
    for i, c in enumerate(cands):
        bits.append(f"cand[{i}].finish_reason={getattr(c, 'finish_reason', None)}")
        content = getattr(c, "content", None)
        parts = getattr(content, "parts", None) if content else None
        if not parts:
            bits.append(f"cand[{i}].parts=empty")
            continue
        for j, p in enumerate(parts):
            has_text = bool(getattr(p, "text", None))
            inline = getattr(p, "inline_data", None)
            data_len = 0
            if inline is not None and getattr(inline, "data", None) is not None:
                data_len = len(inline.data)
            bits.append(
                f"cand[{i}].part[{j}] text={has_text} inline_len={data_len} "
                f"thought={getattr(p, 'thought', None)}"
            )
    return "; ".join(bits)


def generate_poster_image(
    *,
    prompt: str,
    reference_parts: list[types.Part] | None = None,
    source: str = "generate_poster",
    person_generation: str = "ALLOW_NONE",
) -> tuple[bytes, dict, str]:
    """Generate one poster; returns (png_or_jpeg_bytes, usage_record, model_text)."""
    s = get_settings()
    client = get_client()
    user_parts: list[types.Part] = [types.Part.from_text(text=prompt)]
    if reference_parts:
        user_parts.extend(reference_parts)
    contents = [types.Content(role="user", parts=user_parts)]

    config = types.GenerateContentConfig(
        response_modalities=["TEXT", "IMAGE"],
        candidate_count=1,
        safety_settings=default_safety_settings(),
        image_config=types.ImageConfig(
            aspect_ratio=s["aspect_ratio"],
            image_size=s["image_size"],
            person_generation=person_generation,
        ),
    )

    started = time.perf_counter()
    response = client.models.generate_content(
        model=s["model"],
        contents=contents,
        config=config,
    )
    wall = time.perf_counter() - started

    pf = getattr(response, "prompt_feedback", None)
    block_msg = str(getattr(pf, "block_reason_message", "") or "")
    if (
        person_generation == "ALLOW_NONE"
        and pf is not None
        and getattr(pf, "block_reason", None) is not None
        and "PersonGeneration" in block_msg
    ):
        raise SafetyBlockedError(person_generation_block_message(block_msg))

    raise_if_safety_blocked(response)

    image_bytes = extract_image_bytes(response)
    if not image_bytes:
        raise RuntimeError(
            "Model returned no image. "
            + (extract_text(response) or "(no text)")
            + " | "
            + _response_debug(response)
        )

    record = usage_from_response(
        response,
        model=s["model"],
        source=source,
        image_size=s["image_size"],
        aspect_ratio=s["aspect_ratio"],
        wall_seconds=wall,
    )
    log_usage(record)
    print(format_usage(record))
    return image_bytes, record, extract_text(response)


def edit_poster_image(
    *,
    edit_prompt: str,
    previous_image: bytes,
    previous_mime: str = "image/png",
    source: str = "edit_poster",
    person_generation: str = "ALLOW_NONE",
) -> tuple[bytes, dict, str]:
    """One edit turn: previous image + fix instructions."""
    s = get_settings()
    client = get_client()
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=edit_prompt),
                types.Part.from_bytes(data=previous_image, mime_type=previous_mime),
            ],
        )
    ]
    config = types.GenerateContentConfig(
        response_modalities=["TEXT", "IMAGE"],
        candidate_count=1,
        safety_settings=default_safety_settings(),
        image_config=types.ImageConfig(
            aspect_ratio=s["aspect_ratio"],
            image_size=s["image_size"],
            person_generation=person_generation,
        ),
    )
    started = time.perf_counter()
    response = client.models.generate_content(
        model=s["model"],
        contents=contents,
        config=config,
    )
    wall = time.perf_counter() - started

    pf = getattr(response, "prompt_feedback", None)
    block_msg = str(getattr(pf, "block_reason_message", "") or "")
    if (
        person_generation == "ALLOW_NONE"
        and pf is not None
        and getattr(pf, "block_reason", None) is not None
        and "PersonGeneration" in block_msg
    ):
        raise SafetyBlockedError(person_generation_block_message(block_msg))

    raise_if_safety_blocked(response)

    image_bytes = extract_image_bytes(response)
    if not image_bytes:
        raise RuntimeError(
            "Edit returned no image. "
            + (extract_text(response) or "(no text)")
            + " | "
            + _response_debug(response)
        )
    record = usage_from_response(
        response,
        model=s["model"],
        source=source,
        image_size=s["image_size"],
        aspect_ratio=s["aspect_ratio"],
        wall_seconds=wall,
    )
    log_usage(record)
    print(format_usage(record))
    return image_bytes, record, extract_text(response)
