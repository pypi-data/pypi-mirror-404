"""Exception classes for the AmbientMeta SDK."""


class AmbientMetaError(Exception):
    """Base exception for all AmbientMeta API errors."""

    def __init__(self, code: str, message: str, suggestion: str = "") -> None:
        self.code = code
        self.message = message
        self.suggestion = suggestion
        super().__init__(f"{code}: {message}")


class AuthenticationError(AmbientMetaError):
    """Raised when the API key is missing or invalid."""

    pass


class RateLimitError(AmbientMetaError):
    """Raised when the rate limit is exceeded."""

    pass


class NotFoundError(AmbientMetaError):
    """Raised when a resource (e.g. session) is not found."""

    pass


class ValidationError(AmbientMetaError):
    """Raised when the request fails validation."""

    pass
