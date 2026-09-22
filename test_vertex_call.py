import os
from google import genai
from google.genai.types import GenerateContentConfig
from pydantic import BaseModel
from dotenv import load_dotenv

from usage import format_usage, log_usage, usage_from_response

load_dotenv()


class SocialPost(BaseModel):
    caption: str
    offer: str
    cta: str
    hashtags: list[str]


client = genai.Client(
    vertexai=True,
    project=os.environ["GOOGLE_CLOUD_PROJECT"],
    location=os.environ["GOOGLE_CLOUD_LOCATION"],
)

response = client.models.generate_content(
    model=os.environ["GEMINI_MODEL"],
    contents="Brief: 20% off all yoga mats this weekend at ZenFit Studio.",
    config=GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=SocialPost,
    ),
)

print(response.parsed)

model = os.environ["GEMINI_MODEL"]
record = usage_from_response(response, model=model, source="test_vertex_call")
log_path = log_usage(record)
print(format_usage(record))
print(f"logged to {log_path}")