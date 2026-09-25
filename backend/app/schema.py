from pydantic import BaseModel, Field

from .defaults import DEFAULT_STORE_BRAND


class SocialPost(BaseModel):
    caption: str = Field(..., min_length=1, max_length=500)
    offer: str = Field(..., min_length=1, max_length=200)
    cta: str = Field(..., min_length=1, max_length=120)
    hashtags: list[str] = Field(..., min_length=3, max_length=6)


class OptimizedPrompt(BaseModel):
    optimized_prompt: str = Field(..., min_length=1, max_length=1200)


class GenerateRequest(BaseModel):
    brief: str = Field(default="", max_length=2000)
    variation: bool = False
    store_brand: str = Field(default=DEFAULT_STORE_BRAND, max_length=120)
    # Optional poster for vision caption (Regenerate / vision path).
    image_base64: str | None = None
    mime_type: str | None = Field(default=None, max_length=64)


class UsageInfo(BaseModel):
    prompt_tokens: int
    output_tokens: int
    thoughts_tokens: int
    total_tokens: int
    estimated_usd: float
    model: str


class GenerateResponse(SocialPost):
    usage: UsageInfo | None = None
    store_brand: str = DEFAULT_STORE_BRAND


class PipelineUsage(BaseModel):
    optimize: UsageInfo | None = None
    image: dict | None = None
    caption: UsageInfo | None = None


class PipelineTotals(BaseModel):
    """Aggregated metrics for one complete Generate (or Regenerate) run."""

    total_estimated_usd: float = 0.0
    total_tokens: int = 0
    wall_seconds: float = 0.0
    api_calls: int = 0
    models: list[str] = Field(default_factory=list)
    steps: dict | None = None


class PipelineResponse(BaseModel):
    """Full Generate pipeline: optimized prompt → poster → vision caption."""

    optimized_prompt: str = ""
    # Poster fields (always present on image success)
    image_base64: str | None = None
    mime_type: str | None = None
    filename: str | None = None
    person_generation: str | None = None
    # Caption fields (null if caption step failed after image OK)
    caption: str | None = None
    offer: str | None = None
    cta: str | None = None
    hashtags: list[str] | None = None
    text_error: str | None = None
    store_brand: str = DEFAULT_STORE_BRAND
    usage: PipelineUsage | None = None
    totals: PipelineTotals | None = None
    api_calls: int = 0
