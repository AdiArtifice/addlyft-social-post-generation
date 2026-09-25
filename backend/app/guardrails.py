"""Input/output guardrails for the text social-post workflow."""

from __future__ import annotations

import re
from typing import Any

from google.genai.types import HarmBlockThreshold, HarmCategory, SafetySetting

from .schema import SocialPost

MAX_BRIEF_CHARS = 2000
MAX_OPTIMIZED_PROMPT_CHARS = 1200
MAX_CAPTION_CHARS = 500
MAX_OFFER_CHARS = 200
MAX_CTA_CHARS = 120
MIN_HASHTAGS = 3
MAX_HASHTAGS = 6
MAX_HASHTAG_CHARS = 40

# Lightweight intent blocklist — not a full classifier.
_BLOCKED_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in (
        r"\bfake\s+reviews?\b",
        r"\bbuy\s+followers?\b",
        r"\bbuy\s+likes?\b",
        r"\bweapon(?:s)?\s+for\s+sale\b",
        r"\billicit\s+drugs?\b",
        r"\bcounterfeit\b",
        r"\bchild\s+porn\b",
        r"\bcsam\b",
    )
]

# Claim-like tokens that must appear in the brief if used in output.
_CLAIM_RE = re.compile(
    r"(?:\$\s*\d[\d,]*(?:\.\d+)?|\d+(?:\.\d+)?\s*%|\b\d+\s*(?:%?\s*)?off\b)",
    re.IGNORECASE,
)

_SAFETY_BLOCK_REASONS = frozenset(
    {
        "SAFETY",
        "BLOCKLIST",
        "PROHIBITED_CONTENT",
        "SPII",
        "IMAGE_SAFETY",
    }
)


class SafetyBlockedError(RuntimeError):
    """Raised when Vertex blocks a prompt or response for safety."""


class GuardrailError(ValueError):
    """Raised when input/output fails application guardrails."""


def default_safety_settings() -> list[SafetySetting]:
    threshold = HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
    return [
        SafetySetting(category=HarmCategory.HARM_CATEGORY_HARASSMENT, threshold=threshold),
        SafetySetting(category=HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold=threshold),
        SafetySetting(
            category=HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold=threshold
        ),
        SafetySetting(
            category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold=threshold
        ),
    ]


def validate_brief(brief: str) -> str:
    text = (brief or "").strip()
    if not text:
        raise GuardrailError("Please enter an ad brief before generating.")
    if len(text) > MAX_BRIEF_CHARS:
        raise GuardrailError(
            f"Brief is too long ({len(text)} chars). Keep it under {MAX_BRIEF_CHARS}."
        )
    for pat in _BLOCKED_PATTERNS:
        if pat.search(text):
            raise GuardrailError(
                "This brief looks unsafe or abusive for an ad demo. "
                "Please revise the request."
            )
    return text


def enforce_optimized_prompt(text: str) -> str:
    """Normalize and cap the Flash-Lite image-brief rewrite."""
    cleaned = (text or "").strip()
    if not cleaned:
        raise GuardrailError("Optimized prompt came back empty. Please try again.")
    if len(cleaned) > MAX_OPTIMIZED_PROMPT_CHARS:
        cleaned = cleaned[:MAX_OPTIMIZED_PROMPT_CHARS].rstrip()
    for pat in _BLOCKED_PATTERNS:
        if pat.search(cleaned):
            raise GuardrailError(
                "Optimized prompt looks unsafe for an ad demo. Please revise the brief."
            )
    return cleaned


def raise_if_safety_blocked(response: Any) -> None:
    pf = getattr(response, "prompt_feedback", None)
    if pf is not None and getattr(pf, "block_reason", None) is not None:
        msg = (
            getattr(pf, "block_reason_message", None)
            or str(getattr(pf, "block_reason", ""))
            or "blocked"
        )
        raise SafetyBlockedError(
            f"Blocked by safety filter before generation ({msg}). "
            "Please revise the brief."
        )

    candidates = getattr(response, "candidates", None) or []
    if not candidates:
        raise SafetyBlockedError(
            "Blocked by safety filter (no candidates returned). Please revise the brief."
        )

    finish = getattr(candidates[0], "finish_reason", None)
    finish_name = getattr(finish, "name", None) or str(finish or "")
    finish_upper = finish_name.upper()
    if any(reason in finish_upper for reason in _SAFETY_BLOCK_REASONS):
        raise SafetyBlockedError(
            f"Blocked by safety filter ({finish_name}). Please revise the brief."
        )


def _normalize_hashtag(tag: str) -> str:
    t = (tag or "").strip()
    if not t:
        return ""
    if not t.startswith("#"):
        t = f"#{t.lstrip('#')}"
    # Collapse internal spaces for hashtag validity
    t = re.sub(r"\s+", "", t)
    return t[:MAX_HASHTAG_CHARS]


def enforce_output_shape(post: SocialPost, brief: str) -> SocialPost:
    caption = (post.caption or "").strip()[:MAX_CAPTION_CHARS]
    offer = (post.offer or "").strip()[:MAX_OFFER_CHARS]
    cta = (post.cta or "").strip()[:MAX_CTA_CHARS]
    if not caption or not offer or not cta:
        raise GuardrailError(
            "Model returned incomplete fields (caption, offer, and CTA are required)."
        )

    tags = [_normalize_hashtag(t) for t in (post.hashtags or [])]
    tags = [t for t in tags if t and t != "#"]
    # Dedupe preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for t in tags:
        key = t.lower()
        if key not in seen:
            seen.add(key)
            unique.append(t)
    if len(unique) < MIN_HASHTAGS:
        raise GuardrailError(
            f"Expected at least {MIN_HASHTAGS} hashtags; got {len(unique)}."
        )
    unique = unique[:MAX_HASHTAGS]

    combined = f"{caption}\n{offer}\n{cta}"
    brief_norm = re.sub(r"\s+", " ", brief).lower()
    for match in _CLAIM_RE.finditer(combined):
        claim = re.sub(r"\s+", " ", match.group(0)).strip().lower()
        # Normalize $ 20 vs $20
        claim_compact = claim.replace(" ", "")
        brief_compact = brief_norm.replace(" ", "")
        if claim not in brief_norm and claim_compact not in brief_compact:
            raise GuardrailError(
                f"Output invents a claim not in the brief ({match.group(0).strip()}). "
                "Add that fact to the brief, or regenerate with only facts you provided."
            )

    return SocialPost(caption=caption, offer=offer, cta=cta, hashtags=unique)
