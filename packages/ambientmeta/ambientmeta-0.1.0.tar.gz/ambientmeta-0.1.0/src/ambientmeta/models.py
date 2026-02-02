"""Response models for the AmbientMeta SDK."""

from dataclasses import dataclass, field


@dataclass
class EntityResult:
    """A detected entity with its placeholder, type, and confidence."""

    placeholder: str
    type: str
    confidence: float


@dataclass
class SanitizeResponse:
    """Response from the sanitize endpoint."""

    sanitized: str
    session_id: str
    entities_found: int
    entities: list[EntityResult]
    processing_ms: float


@dataclass
class RehydrateResponse:
    """Response from the rehydrate endpoint."""

    text: str
    entities_restored: int
    processing_ms: float


@dataclass
class PatternResponse:
    """Response from the patterns endpoint."""

    pattern_id: str
    name: str
    status: str = "active"


@dataclass
class FeedbackResponse:
    """Response from the feedback endpoint."""

    status: str = "recorded"
