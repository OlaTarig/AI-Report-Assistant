from functools import lru_cache

from app.config import get_settings
from app.services.ai.base import AIProvider
from app.services.ai.gemini_provider import GeminiProvider


@lru_cache
def get_ai_provider() -> AIProvider:
    """Single place that decides which provider implementation is active.
    Swapping providers later means adding a branch here (e.g. driven by
    an AI_PROVIDER env var) — nothing else in the app changes."""
    settings = get_settings()
    return GeminiProvider(api_key=settings.gemini_api_key)
