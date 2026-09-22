from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .gemini_client import generate_social_post
from .guardrails import GuardrailError, SafetyBlockedError, validate_brief
from .image_bridge import generate_image_response
from .schema import GenerateRequest, GenerateResponse, UsageInfo

app = FastAPI(title="Social Post Generation", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    from .defaults import DEFAULT_STORE_BRAND

    return {
        "ok": True,
        "model": settings.gemini_model,
        "store_brand": DEFAULT_STORE_BRAND,
    }


@app.post("/api/generate", response_model=GenerateResponse)
def generate(request: GenerateRequest) -> GenerateResponse:
    try:
        brief = validate_brief(request.brief or "")
    except GuardrailError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None

    try:
        post, usage = generate_social_post(
            brief,
            variation=request.variation,
            store_brand=request.store_brand,
        )
    except SafetyBlockedError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None
    except GuardrailError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None
    except Exception:
        raise HTTPException(
            status_code=502,
            detail="Generation failed. Please try again in a moment.",
        ) from None

    store = (request.store_brand or "").strip()
    if not store:
        from .defaults import DEFAULT_STORE_BRAND

        store = DEFAULT_STORE_BRAND
    return GenerateResponse(
        caption=post.caption,
        offer=post.offer,
        cta=post.cta,
        hashtags=post.hashtags,
        store_brand=store,
        usage=UsageInfo(
            prompt_tokens=usage["prompt_tokens"],
            output_tokens=usage["output_tokens"],
            thoughts_tokens=usage["thoughts_tokens"],
            total_tokens=usage["total_tokens"],
            estimated_usd=usage["estimated_usd"],
            model=usage["model"],
        ),
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
