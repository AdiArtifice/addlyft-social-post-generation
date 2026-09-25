import base64
import time

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .gemini_client import (
    generate_social_post,
    generate_social_post_from_image,
    optimize_brief_for_image,
)
from .guardrails import GuardrailError, SafetyBlockedError, validate_brief
from .image_bridge import generate_image_response
from .schema import (
    GenerateRequest,
    GenerateResponse,
    PipelineResponse,
    PipelineTotals,
    PipelineUsage,
    UsageInfo,
)
from .usage_log import log_pipeline_totals, read_generation_reports

app = FastAPI(title="Social Post Generation", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _usage_info(record: dict | None) -> UsageInfo | None:
    if not record:
        return None
    return UsageInfo(
        prompt_tokens=int(record.get("prompt_tokens") or 0),
        output_tokens=int(record.get("output_tokens") or 0),
        thoughts_tokens=int(record.get("thoughts_tokens") or 0),
        total_tokens=int(record.get("total_tokens") or 0),
        estimated_usd=float(record.get("estimated_usd") or 0.0),
        model=str(record.get("model") or settings.gemini_model),
    )


def _step_tokens(record: dict | None) -> int:
    if not record:
        return 0
    return int(record.get("total_tokens") or 0)


def _step_usd(record: dict | None) -> float:
    if not record:
        return 0.0
    return float(record.get("estimated_usd") or 0.0)


def _step_model(record: dict | None) -> str | None:
    if not record:
        return None
    model = str(record.get("model") or "").strip()
    return model or None


def _resolve_store(store_brand: str | None) -> str:
    store = (store_brand or "").strip()
    if store:
        return store
    from .defaults import DEFAULT_STORE_BRAND

    return DEFAULT_STORE_BRAND


def _compact_step(record: dict | None) -> dict | None:
    if not record:
        return None
    return {
        "model": record.get("model"),
        "total_tokens": int(record.get("total_tokens") or 0),
        "estimated_usd": float(record.get("estimated_usd") or 0.0),
        "prompt_tokens": int(record.get("prompt_tokens") or 0),
        "output_tokens": int(
            record.get("output_tokens")
            or record.get("text_output_tokens")
            or 0
        ),
        "thoughts_tokens": int(record.get("thoughts_tokens") or 0),
        "image_output_tokens": int(record.get("image_output_tokens") or 0)
        if "image_output_tokens" in record
        else None,
        "wall_seconds": record.get("wall_seconds"),
    }


@app.get("/api/health")
def health() -> dict:
    from .defaults import DEFAULT_STORE_BRAND

    return {
        "ok": True,
        "model": settings.gemini_model,
        "store_brand": DEFAULT_STORE_BRAND,
    }


@app.get("/api/generation-reports")
def generation_reports(limit: int = Query(default=20, ge=1, le=200)) -> dict:
    """Return newest-first pipeline / regenerate total records."""
    return {"reports": read_generation_reports(limit)}


@app.post("/api/generate", response_model=GenerateResponse)
def generate(request: GenerateRequest) -> GenerateResponse:
    started = time.perf_counter()
    try:
        brief = validate_brief(request.brief or "")
    except GuardrailError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None

    store = _resolve_store(request.store_brand)
    image_b64 = (request.image_base64 or "").strip()
    mime = (request.mime_type or "image/png").strip() or "image/png"
    is_vision = bool(image_b64)

    try:
        if is_vision:
            try:
                image_bytes = base64.b64decode(image_b64, validate=False)
            except Exception:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid image_base64 for vision caption.",
                ) from None
            if not image_bytes:
                raise HTTPException(
                    status_code=400,
                    detail="Empty image for vision caption.",
                )
            post, usage = generate_social_post_from_image(
                brief,
                image_bytes=image_bytes,
                mime_type=mime,
                variation=request.variation,
                store_brand=store,
            )
        else:
            post, usage = generate_social_post(
                brief,
                variation=request.variation,
                store_brand=store,
            )
    except SafetyBlockedError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None
    except GuardrailError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=502,
            detail="Generation failed. Please try again in a moment.",
        ) from None

    wall = round(time.perf_counter() - started, 3)
    if is_vision and request.variation:
        model = _step_model(usage) or settings.gemini_model
        log_pipeline_totals(
            {
                "source": "api_regenerate",
                "total_estimated_usd": round(_step_usd(usage), 8),
                "total_tokens": _step_tokens(usage),
                "wall_seconds": wall,
                "api_calls": 1,
                "models": [model],
                "steps": {"caption": _compact_step(usage)},
                "store_brand": store,
                "variation": True,
            }
        )

    return GenerateResponse(
        caption=post.caption,
        offer=post.offer,
        cta=post.cta,
        hashtags=post.hashtags,
        store_brand=store,
        usage=_usage_info(usage),
    )


@app.post("/api/generate-image")
async def generate_image(
    prompt: str = Form(...),
    refs: list[UploadFile] | None = File(None),
    roles: str = Form("[]"),
    allow_people: str = Form("false"),
    store_brand: str = Form(""),
) -> dict:
    return await generate_image_response(
        prompt=prompt,
        refs=refs,
        roles=roles,
        allow_people=allow_people,
        store_brand=store_brand,
    )


@app.post("/api/generate-pipeline", response_model=PipelineResponse)
async def generate_pipeline(
    brief: str = Form(...),
    refs: list[UploadFile] | None = File(None),
    roles: str = Form("[]"),
    allow_people: str = Form("false"),
    store_brand: str = Form(""),
) -> PipelineResponse:
    """Optimize brief → image (+ refs) → vision caption/offer/CTA/hashtags."""
    started = time.perf_counter()
    try:
        raw_brief = validate_brief(brief or "")
    except GuardrailError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None

    store = _resolve_store(store_brand)

    try:
        optimized, usage_opt = optimize_brief_for_image(raw_brief, store_brand=store)
    except SafetyBlockedError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None
    except GuardrailError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None
    except Exception:
        raise HTTPException(
            status_code=502,
            detail="Brief optimization failed. Please try again in a moment.",
        ) from None

    # Image step — reuses existing bridge (refs/roles unchanged).
    image_result = await generate_image_response(
        prompt=optimized,
        refs=refs,
        roles=roles,
        allow_people=allow_people,
        store_brand=store,
    )
    usage_image = image_result.get("usage")
    if isinstance(usage_image, dict):
        pass
    else:
        usage_image = None

    image_b64 = image_result.get("image_base64") or ""
    mime = image_result.get("mime_type") or "image/png"
    try:
        image_bytes = base64.b64decode(image_b64, validate=False)
    except Exception:
        raise HTTPException(
            status_code=502,
            detail="Poster generated but could not be decoded for captioning.",
        ) from None

    text_error: str | None = None
    caption = offer = cta = None
    hashtags: list[str] | None = None
    usage_cap: dict | None = None
    caption_ok = False

    try:
        post, usage_cap = generate_social_post_from_image(
            raw_brief,
            image_bytes=image_bytes,
            mime_type=mime,
            variation=False,
            store_brand=store,
        )
        caption = post.caption
        offer = post.offer
        cta = post.cta
        hashtags = post.hashtags
        caption_ok = True
    except SafetyBlockedError as exc:
        text_error = str(exc)
    except GuardrailError as exc:
        text_error = str(exc)
    except Exception:
        text_error = "Caption generation failed. Poster is still available."

    # optimize (1) + image (n) + caption (1 if ok)
    image_calls = int(image_result.get("api_calls") or 1)
    api_calls = 1 + image_calls + (1 if caption_ok else 0)

    wall = round(time.perf_counter() - started, 3)
    total_tokens = (
        _step_tokens(usage_opt) + _step_tokens(usage_image) + _step_tokens(usage_cap)
    )
    total_usd = round(
        _step_usd(usage_opt) + _step_usd(usage_image) + _step_usd(usage_cap),
        8,
    )
    models: list[str] = []
    for rec in (usage_opt, usage_image, usage_cap):
        m = _step_model(rec)
        if m:
            models.append(m)

    steps = {
        "optimize": _compact_step(usage_opt),
        "image": _compact_step(usage_image),
        "caption": _compact_step(usage_cap) if caption_ok else None,
    }
    totals = PipelineTotals(
        total_estimated_usd=total_usd,
        total_tokens=total_tokens,
        wall_seconds=wall,
        api_calls=api_calls,
        models=models,
        steps=steps,
    )
    log_pipeline_totals(
        {
            "source": "api_pipeline",
            "total_estimated_usd": totals.total_estimated_usd,
            "total_tokens": totals.total_tokens,
            "wall_seconds": totals.wall_seconds,
            "api_calls": totals.api_calls,
            "models": totals.models,
            "steps": totals.steps,
            "store_brand": store,
            "filename": image_result.get("filename"),
            "text_error": text_error,
        }
    )

    return PipelineResponse(
        optimized_prompt=optimized,
        image_base64=image_b64,
        mime_type=mime,
        filename=image_result.get("filename"),
        person_generation=image_result.get("person_generation"),
        caption=caption,
        offer=offer,
        cta=cta,
        hashtags=hashtags,
        text_error=text_error,
        store_brand=store,
        usage=PipelineUsage(
            optimize=_usage_info(usage_opt),
            image=usage_image,
            caption=_usage_info(usage_cap),
        ),
        totals=totals,
        api_calls=api_calls,
    )
