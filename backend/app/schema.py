from pydantic import BaseModel, Field

from .defaults import DEFAULT_STORE_BRAND


class SocialPost(BaseModel):
    caption: str = Field(..., min_length=1, max_length=500)
    offer: str = Field(..., min_length=1, max_length=200)
    cta: str = Field(..., min_length=1, max_length=120)
    hashtags: list[str] = Field(..., min_length=3, max_length=6)


class GenerateRequest(BaseModel):
    brief: str = Field(default="", max_length=2000)
    variation: bool = False
    store_brand: str = Field(default=DEFAULT_STORE_BRAND, max_length=120)


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
