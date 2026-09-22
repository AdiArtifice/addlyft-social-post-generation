"""Input/output guardrails for the social-post image workflow."""

from __future__ import annotations

import re
from typing import Any

from google.genai.types import HarmBlockThreshold, HarmCategory, SafetySetting

MAX_PROMPT_CHARS = 2000
VALID_ROLES = frozenset({"product", "brand", "background", "style", "auto"})

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
    """Raised when input fails application guardrails."""


def default_safety_settings() -> list[SafetySetting]:
    threshold = HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
    # Use the four configurable Vertex categories (same as text). IMAGE_* enums
    # are not reliably accepted by all Gemini image models on Vertex.
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


def validate_prompt(prompt: str) -> str:
    text = (prompt or "").strip()
    if not text:
        raise GuardrailError("Enter a prompt before generating.")
    if len(text) > MAX_PROMPT_CHARS:
        raise GuardrailError(
            f"Prompt is too long ({len(text)} chars). Keep it under {MAX_PROMPT_CHARS}."
        )
    for pat in _BLOCKED_PATTERNS:
        if pat.search(text):
            raise GuardrailError(
                "This prompt looks unsafe or abusive for an ad demo. "
                "Please revise the request."
            )
    return text


def parse_roles(raw: str | None, *, n_refs: int) -> list[str]:
    """Parse roles JSON or comma list; pad/trim to n_refs with 'auto'."""
    if n_refs <= 0:
        return []
    text = (raw or "").strip()
    roles: list[str] = []
    if text:
        if text.startswith("["):
            import json

            try:
                parsed = json.loads(text)
            except json.JSONDecodeError as exc:
                raise GuardrailError("Invalid roles JSON.") from exc
            if not isinstance(parsed, list):
                raise GuardrailError("roles must be a JSON array of strings.")
            roles = [str(r).strip().lower() for r in parsed]
        else:
            roles = [r.strip().lower() for r in text.split(",") if r.strip()]

    while len(roles) < n_refs:
        roles.append("auto")
    roles = roles[:n_refs]
    for r in roles:
        if r not in VALID_ROLES:
            raise GuardrailError(
                f"Invalid role '{r}'. Expected one of: {sorted(VALID_ROLES)}"
            )
    return roles


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
            "Please revise the prompt or references."
        )

    candidates = getattr(response, "candidates", None) or []
    if not candidates:
        # Empty candidates often means a safety block; still distinguish PersonGeneration.
        if pf is not None and "PersonGeneration" in str(
            getattr(pf, "block_reason_message", "") or ""
        ):
            raise SafetyBlockedError(
                "Blocked because a reference appears to contain people. "
                "Enable 'Allow people in poster' to retry, or use refs without faces."
            )
        raise SafetyBlockedError(
            "Blocked by safety filter (no candidates returned). "
            "Please revise the prompt or references."
        )

    finish = getattr(candidates[0], "finish_reason", None)
    finish_name = getattr(finish, "name", None) or str(finish or "")
    finish_upper = finish_name.upper()
    if any(reason in finish_upper for reason in _SAFETY_BLOCK_REASONS):
        raise SafetyBlockedError(
            f"Blocked by safety filter ({finish_name}). "
            "Please revise the prompt or references."
        )


def person_generation_block_message(block_msg: str) -> str:
    return (
        "Input blocked under ALLOW_NONE (people detected in a reference). "
        "Enable 'Allow people in poster' (UI) or pass --allow-people (CLI) to opt in. "
        f"Details: {block_msg or 'PersonGeneration'}"
    )
