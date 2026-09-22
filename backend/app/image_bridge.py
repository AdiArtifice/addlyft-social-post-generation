"""Bridge to social-post-image modules for poster generation on the text backend."""

from __future__ import annotations

import base64
import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from fastapi import File, Form, HTTPException, UploadFile

from .config import PROJECT_ROOT

SPI_DIR = PROJECT_ROOT / "social-post-image"
if str(SPI_DIR) not in sys.path:
    sys.path.insert(0, str(SPI_DIR))

from guardrails import (  # noqa: E402
    GuardrailError,
    SafetyBlockedError,
    parse_roles,
    validate_prompt,
)
from image_client import (  # noqa: E402
    MAX_REFS,
    generate_poster_image,
    get_settings,
    load_role_reference_parts,
)
from .defaults import DEFAULT_STORE_BRAND
from prompt import STORE_BRAND_DEFAULT, build_user_prompt_poster  # noqa: E402

OUT_DIR = SPI_DIR / "outputs"
PROMO_PATH = SPI_DIR / "promotion.json"
UPLOAD_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}


def _parse_allow_people(raw: str | bool | None) -> bool:
    if isinstance(raw, bool):
        return raw
    return str(raw or "").strip().lower() in {"1", "true", "yes", "on"}


async def generate_image_response(
    prompt: str = Form(...),
    refs: list[UploadFile] | None = File(None),
    roles: str = Form("[]"),
    allow_people: str = Form("false"),
    store_brand: str = Form(""),
) -> dict:
    try:
        brief = validate_prompt(prompt)
    except GuardrailError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None

    store = (store_brand or "").strip() or DEFAULT_STORE_BRAND or STORE_BRAND_DEFAULT
    people_ok = _parse_allow_people(allow_people)
    person_generation = "ALLOW_ADULT" if people_ok else "ALLOW_NONE"

    uploads = [f for f in (refs or []) if f is not None and (f.filename or "").strip()]
    if len(uploads) > MAX_REFS:
        raise HTTPException(
            status_code=400,
            detail=f"At most {MAX_REFS} reference images allowed.",
        )

    role_refs: list[dict] = []
    with tempfile.TemporaryDirectory(prefix="spi_refs_") as tmp:
        tmp_dir = Path(tmp)
        saved: list[tuple[Path, str]] = []
        for i, upload in enumerate(uploads):
            name = Path(upload.filename or f"ref_{i}.jpg").name
            suffix = Path(name).suffix.lower() or ".jpg"
            if suffix not in UPLOAD_EXTS:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported file type for {name}. Use jpg/png/webp.",
                )
            dest = tmp_dir / f"ref_{i}{suffix}"
            data = await upload.read()
            if not data:
                continue
            dest.write_bytes(data)
            saved.append((dest, name))

        try:
            role_list = parse_roles(roles, n_refs=len(saved))
        except GuardrailError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from None

        for i, (dest, name) in enumerate(saved):
            role_refs.append({"path": dest, "role": role_list[i], "name": name})

        settings = get_settings()
        model_prompt = build_user_prompt_poster(
            brief,
            aspect_ratio=settings["aspect_ratio"],
            role_refs=role_refs,
            store_brand=store,
        )
        ref_parts = load_role_reference_parts(role_refs, max_refs=MAX_REFS)

        try:
            image_bytes, usage, model_text = generate_poster_image(
                prompt=model_prompt,
                reference_parts=ref_parts,
                source="unified_ui_generate",
                person_generation=person_generation,
            )
        except SafetyBlockedError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from None
        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Generation failed: {exc}",
            ) from None

        OUT_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        stem = f"poster_{stamp}"
        is_png = image_bytes[:8] == b"\x89PNG\r\n\x1a\n"
        suffix = ".png" if is_png else ".jpg"
        mime = "image/png" if is_png else "image/jpeg"
        out_path = OUT_DIR / f"{stem}{suffix}"
        out_path.write_bytes(image_bytes)

        try:
            promo: dict = {}
            if PROMO_PATH.exists():
                promo = json.loads(PROMO_PATH.read_text(encoding="utf-8"))
                if not isinstance(promo, dict):
                    promo = {}
            promo["user_prompt"] = brief
            promo["store_brand"] = store
            PROMO_PATH.write_text(
                json.dumps(promo, indent=2) + "\n", encoding="utf-8"
            )
        except OSError:
            pass

        meta = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "image_file": out_path.name,
            "settings": settings,
            "user_prompt": brief,
            "store_brand": store,
            "references": [{"name": r["name"], "role": r["role"]} for r in role_refs],
            "person_generation": person_generation,
            "prompt": model_prompt,
            "model_text": model_text,
            "usage": usage,
            "api_calls": 1,
        }
        (OUT_DIR / f"{stem}_meta.json").write_text(
            json.dumps(meta, indent=2), encoding="utf-8"
        )

        b64 = base64.b64encode(image_bytes).decode("ascii")
        return {
            "image_base64": b64,
            "mime_type": mime,
            "filename": out_path.name,
            "usage": usage,
            "api_calls": 1,
            "model_text": model_text or "",
            "person_generation": person_generation,
            "store_brand": store,
        }
