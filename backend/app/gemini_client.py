from time import sleep

from google import genai
from google.genai.types import GenerateContentConfig

from .config import settings
from .defaults import DEFAULT_STORE_BRAND
from .guardrails import (
    SafetyBlockedError,
    default_safety_settings,
    enforce_output_shape,
    raise_if_safety_blocked,
)
from .schema import SocialPost
from .usage_log import log_generation_usage


def _system_instruction(store_brand: str) -> str:
    return (
        "You are a social media copywriter. Given an ad brief, produce a caption, "
        "the core offer/key message, a clear CTA, and 3–6 relevant hashtags that "
        "each start with #.\n"
        "\n"
        f"SELECTED STORE (already chosen earlier — do not require it in the brief)\n"
        f"- Retailer: {store_brand}\n"
        f"- Reflect {store_brand} as the store identity in the post when natural "
        "(caption, offer, or hashtags).\n"
        "- Do not substitute a different retailer unless the brief explicitly names one.\n"
        "\n"
        "FACTS ONLY (NON-NEGOTIABLE)\n"
        "- Use ONLY prices, discounts, dates, phone numbers, addresses, and product "
        "claims that appear in the brief, plus the selected store above.\n"
        "- If a detail is missing, omit it or say it is not provided — never invent it.\n"
        "- Do not invent limited-time offers, percentages off, free gifts, or "
        "scarcity claims that are not in the brief.\n"
        "- Keep the tone on-brand for the brief, but never sacrifice factual accuracy "
        "for creativity."
    )


_client: genai.Client | None = None


def get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(
            vertexai=True,
            project=settings.google_cloud_project,
            location=settings.google_cloud_location,
        )
    return _client


def generate_social_post(
    brief: str,
    variation: bool = False,
    store_brand: str | None = None,
) -> tuple[SocialPost, dict]:
    store = (store_brand or DEFAULT_STORE_BRAND).strip() or DEFAULT_STORE_BRAND
    temperature = 1.05 if variation else 0.7
    extra = (
        "Write a distinctly different variation from a typical first draft — "
        "same facts from the brief and selected store only, different hook and wording. "
        "Do not invent new offers or numbers.\n\n"
        if variation
        else ""
    )
    # Include store in grounding context so claim checks allow store-related wording.
    grounding_brief = f"{brief.strip()}\nSelected store: {store}"
    contents = (
        f"{extra}"
        f"Selected store: {store}\n"
        f"Brief: {brief.strip()}"
    )
    last_error: Exception | None = None

    for attempt in range(2):
        try:
            response = get_client().models.generate_content(
                model=settings.gemini_model,
                contents=contents,
                config=GenerateContentConfig(
                    system_instruction=_system_instruction(store),
                    response_mime_type="application/json",
                    response_schema=SocialPost,
                    temperature=temperature,
                    safety_settings=default_safety_settings(),
                ),
            )
            raise_if_safety_blocked(response)

            parsed = response.parsed
            if not isinstance(parsed, SocialPost):
                raise RuntimeError("Model did not return a valid SocialPost.")

            post = enforce_output_shape(parsed, grounding_brief)
            record = log_generation_usage(response, source="api_generate")
            return post, record
        except SafetyBlockedError:
            raise
        except Exception as exc:
            last_error = exc
            if attempt == 0:
                sleep(0.6)
                continue
            raise last_error from exc

    raise RuntimeError("Generation failed.")
