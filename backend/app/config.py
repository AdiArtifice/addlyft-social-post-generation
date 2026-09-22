import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


class Settings:
    google_cloud_project: str
    google_cloud_location: str
    gemini_model: str
    cors_origins: list[str]

    def __init__(self) -> None:
        self.google_cloud_project = _require("GOOGLE_CLOUD_PROJECT")
        self.google_cloud_location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
        self.cors_origins = [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]


settings = Settings()
