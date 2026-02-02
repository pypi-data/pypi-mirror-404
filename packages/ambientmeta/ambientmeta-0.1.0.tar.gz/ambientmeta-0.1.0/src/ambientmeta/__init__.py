"""AmbientMeta Python SDK — sanitize PII before LLM calls, rehydrate after."""

from ambientmeta.client import AmbientMeta, AsyncAmbientMeta
from ambientmeta.exceptions import (
    AmbientMetaError,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)
from ambientmeta.models import (
    EntityResult,
    FeedbackResponse,
    PatternResponse,
    RehydrateResponse,
    SanitizeResponse,
)

__version__ = "0.1.0"

__all__ = [
    "AmbientMeta",
    "AsyncAmbientMeta",
    "AmbientMetaError",
    "AuthenticationError",
    "NotFoundError",
    "RateLimitError",
    "ValidationError",
    "SanitizeResponse",
    "RehydrateResponse",
    "PatternResponse",
    "FeedbackResponse",
    "EntityResult",
]
