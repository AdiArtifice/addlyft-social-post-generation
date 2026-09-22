"""Build a role-aware social-media ad poster prompt from promotion + optional refs."""

from __future__ import annotations

from typing import Any

STORE_BRAND_DEFAULT = "AMPM Woodstock"

ROLE_INSTRUCTIONS = {
    "product": (
        "Preserve exact product appearance, packaging, colors, logos, and labeling. "
        "Do not invent a new SKU or redesign logos."
    ),
    "brand": (
        "Use only as visual cues for AMPM Woodstock store identity (signage, colors, "
        "retail look). Do not copy unrelated logos from the image."
    ),
    "background": (
        "Use as store / shelf / cooler / retail environment context and inspiration. "
        "Create a coherent new scene; do not require a pixel-perfect clone unless the "
        "image clearly is the intended photo base."
    ),
    "style": (
        "Use ONLY for composition, typography hierarchy, lighting, color treatment, "
        "and advertising style. Do NOT copy products, logos, offers, or on-image text "
        "from this reference."
    ),
    "auto": (
        "Inspect the image content and apply it appropriately as product fidelity, "
        "store/environment context, brand cue, and/or style inspiration. Never copy "
        "foreign offers, prices, or competitor logos into the poster."
    ),
}


def _orientation_label(aspect_ratio: str) -> str:
    ar = (aspect_ratio or "").strip()
    if ar in {"9:16", "2:3", "3:4", "4:5"}:
        return "portrait / vertical"
    if ar in {"16:9", "3:2", "4:3", "21:9"}:
        return "landscape / horizontal"
    return "as specified"


def _store_brand(promotion: dict[str, Any]) -> str:
    return (promotion.get("store_brand") or STORE_BRAND_DEFAULT).strip() or STORE_BRAND_DEFAULT


def _exact_text_block(promotion: dict[str, Any]) -> str:
    headline = (promotion.get("headline") or "").strip()
    subhead = (promotion.get("subhead") or "").strip()
    offer = (promotion.get("offer") or "").strip()
    cta = (promotion.get("cta") or "").strip()
    lines: list[str] = []
    if headline:
        lines.append(f"Line {len(lines) + 1} (headline): {headline}")
    if subhead:
        lines.append(f"Line {len(lines) + 1} (subhead): {subhead}")
    if offer:
        lines.append(f"Line {len(lines) + 1} (offer): {offer}")
    if cta:
        lines.append(f"Line {len(lines) + 1} (CTA): {cta}")
    return "\n".join(lines) if lines else "(no on-image text from promotion)"


def _refs_section(role_refs: list[dict[str, Any]]) -> str:
    if not role_refs:
        return (
            "REFERENCE IMAGES\n"
            "- None provided. Compose from the promotion text and AMPM Woodstock "
            "store rules alone. Do not invent product packaging details you cannot "
            "verify."
        )

    lines = [
        "REFERENCE IMAGES",
        "Create a NEW advertisement that combines these inputs. Do not clone any "
        "single reference wholesale.",
    ]
    for i, item in enumerate(role_refs, start=1):
        role = (item.get("role") or "auto").strip().lower()
        name = item.get("name") or f"image_{i}"
        how = ROLE_INSTRUCTIONS.get(role, ROLE_INSTRUCTIONS["auto"])
        lines.append(f"- Reference {i} ({name}) — role: {role}")
        lines.append(f"  How to use: {how}")
    return "\n".join(lines)


def build_poster_prompt(
    promotion: dict[str, Any],
    *,
    aspect_ratio: str = "9:16",
    role_refs: list[dict[str, Any]] | None = None,
) -> str:
    product = (promotion.get("product") or "").strip()
    product_brand = (promotion.get("brand") or product).strip()
    store = _store_brand(promotion)
    must_keep = (promotion.get("must_keep_details") or "").strip()
    scene = (promotion.get("scene_notes") or "").strip()
    style_notes = (promotion.get("style_notes") or "").strip()
    refs = role_refs or []
    orientation = _orientation_label(aspect_ratio)
    exact_block = _exact_text_block(promotion)
    has_product_ref = any((r.get("role") or "").lower() == "product" for r in refs)

    priorities = [
        "1. Exact product/reference fidelity"
        + (" (when a product reference is provided)" if not has_product_ref else ""),
        f"2. Consistent store branding: {store}",
        "3. Correct promotional / on-image text from the promotion only",
        f"4. Professional commercial {aspect_ratio} composition",
        "5. Realistic product placement in a retail context",
        "6. Clean typography and visual hierarchy",
        "7. Coherent use of whatever store/background/style references were provided",
    ]

    return f"""Create ONE professional social-media advertisement poster image.

FORMAT
- Aspect ratio: {aspect_ratio} ({orientation})
- Output: a NEW finished retail advertisement (not a collage dump of references)
- This is a ONE-SHOT final deliverable — no follow-up edit pass will be applied
- Single best finished poster in this response

STORE IDENTITY (NON-NEGOTIABLE)
- Store brand: {store}
- Show {store} consistently as the retailer (signage, footer, or clear store treatment)
- Do not substitute another store name or invent a different retailer
- Do not invent street addresses, phone numbers, or store details not listed in the promotion

PRODUCT
- Product: {product or "as implied by product references / promotion"}
- Product brand: {product_brand or "as implied by references"}
- {must_keep or "When product references are present, preserve packaging accuracy."}

{_refs_section(refs)}

ON-IMAGE TEXT — SOURCE OF TRUTH (SPELL EXACTLY)
Use ONLY these lines from the promotion. Render each line separately with correct spelling.
Do NOT invent prices, discounts, dates, product claims, slogans, hashtags, or extra offers.
If a promotion field is empty, leave that line off the poster — do not fill gaps with invented copy.
Do NOT merge headline and subhead into one string.
Do NOT duplicate any word (e.g. never "PRICE PRICE"); each word appears once as written.
Do NOT repeat the same promotion line twice.

{exact_block}

COMPOSITION ({aspect_ratio})
- {orientation.capitalize()} commercial social / retail advertisement poster
- Clear hierarchy: product hero + store identity + offer typography
- High-contrast, readable type; leave safe margins
- Realistic retail lighting and product placement

PRIORITIES (in order)
{chr(10).join(priorities)}

NEGATIVES
- Inventing offers, prices, dates, addresses, hashtags, or claims not in the promotion
- Copying products, logos, offers, or text from style references
- Wrong store name (anything other than {store})
- Warped / misspelled / duplicated letters or words
- Merged or repeated promotion lines
- Watermarks, UI chrome, letterboxing

{("STYLE NOTES\n" + style_notes) if style_notes else ""}
{("SCENE NOTES\n" + scene) if scene else ""}

Output: one finished {aspect_ratio} {store} advertisement poster (final, one-shot).
""".strip()


def build_user_prompt_poster(
    user_prompt: str,
    *,
    aspect_ratio: str = "9:16",
    role_refs: list[dict[str, Any]] | None = None,
    store_brand: str | None = None,
) -> str:
    """Build a one-shot poster prompt from a freeform user brief (primary source of truth)."""
    brief = (user_prompt or "").strip()
    if not brief:
        raise ValueError("user_prompt is required")
    store = (store_brand or STORE_BRAND_DEFAULT).strip() or STORE_BRAND_DEFAULT
    refs = role_refs or []
    orientation = _orientation_label(aspect_ratio)

    return f"""Create ONE professional social-media advertisement poster image.

FORMAT
- Aspect ratio: {aspect_ratio} ({orientation})
- Output: a NEW finished retail advertisement (not a collage dump of references)
- This is a ONE-SHOT final deliverable — no follow-up edit pass will be applied
- Single best finished poster in this response

USER PROMPT — PRIMARY SOURCE OF TRUTH
The following natural-language brief is the authoritative source for product,
offer, required on-image text, branding notes, and any other instructions.
Follow it exactly.

FACTS ONLY (NON-NEGOTIABLE)
- Use ONLY prices, discounts, dates, phone numbers, addresses, and product
  claims that appear in this brief, plus the selected store context below.
- If a detail is missing, omit it — never invent offers, prices, dates,
  slogans, hashtags, scarcity claims, or contact details.
- Do not invent limited-time deals or percentages off that are not in the brief.

---
{brief}
---

STORE CONTEXT (selected earlier — do not require it in the brief)
- Store brand: {store}
- Show {store} consistently as the retailer (signage, footer, or clear store treatment)
- Do not invent street addresses or phone numbers unless the user prompt includes them
- Do not substitute a different retailer unless the user prompt clearly names one

{_refs_section(refs)}

ON-IMAGE TEXT
- Extract required headline / offer / CTA wording from the USER PROMPT above
- Spell those lines exactly; do not duplicate words or merge separate lines
- Do not add competitor logos or foreign text from style references

COMPOSITION ({aspect_ratio})
- {orientation.capitalize()} commercial social / retail advertisement poster
- Clear hierarchy: product hero + store identity + offer typography
- High-contrast, readable type; leave safe margins
- Realistic retail lighting and product placement

PRIORITIES (in order)
1. Faithful use of the user prompt (product, offer, text, instructions)
2. Exact product/reference fidelity when a product reference is provided
3. Coherent store / brand / style use of whatever references were provided
4. Professional commercial {aspect_ratio} composition
5. Clean typography and visual hierarchy

NEGATIVES
- Inventing offers, prices, dates, addresses, hashtags, or claims not in the user prompt
- Copying products, logos, offers, or text from style references
- Warped / misspelled / duplicated letters or words
- Watermarks, UI chrome, letterboxing

Output: one finished {aspect_ratio} advertisement poster (final, one-shot).
""".strip()


def build_edit_prompt(
    promotion: dict[str, Any],
    *,
    fix_notes: str = "",
) -> str:
    store = _store_brand(promotion)
    exact = _exact_text_block(promotion)
    extra = f"\nAdditional fix notes: {fix_notes.strip()}" if fix_notes.strip() else ""
    return f"""Keep the product appearance, store identity ({store}), lighting, and overall
layout of the previous poster.

Fix on-image typography so it is fully legible and spelled EXACTLY as follows
(no invented extras):
{exact}
{extra}

Do not redesign the product, change the store name away from {store}, or invent
new logos/offers. Return one corrected poster image.
""".strip()


def role_label_for_part(role: str) -> str:
    role = (role or "auto").strip().lower()
    how = ROLE_INSTRUCTIONS.get(role, ROLE_INSTRUCTIONS["auto"])
    return f"role: {role} — {how}"
