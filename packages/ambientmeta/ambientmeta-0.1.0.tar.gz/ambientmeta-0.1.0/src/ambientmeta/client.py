"""Sync and async clients for the AmbientMeta Privacy Gateway."""

from __future__ import annotations

from typing import Any

import httpx

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

_DEFAULT_BASE_URL = "https://privacy-gateway.fly.dev"
_DEFAULT_TIMEOUT = 30.0


def _raise_for_error(response: httpx.Response) -> None:
    """Raise an appropriate exception for error responses."""
    if response.status_code < 400:
        return

    try:
        body = response.json()
        err = body.get("error") or body.get("detail", {}).get("error", {})
        code = err.get("code", "unknown_error")
        message = err.get("message", response.text)
        suggestion = err.get("suggestion", "")
    except Exception:
        code = "unknown_error"
        message = response.text
        suggestion = ""

    if response.status_code == 401:
        raise AuthenticationError(code, message, suggestion)
    if response.status_code == 429:
        raise RateLimitError(code, message, suggestion)
    if response.status_code == 404:
        raise NotFoundError(code, message, suggestion)
    if response.status_code == 422:
        raise ValidationError(code, message, suggestion)
    raise AmbientMetaError(code, message, suggestion)


def _parse_sanitize(data: dict[str, Any]) -> SanitizeResponse:
    return SanitizeResponse(
        sanitized=data["sanitized"],
        session_id=data["session_id"],
        entities_found=data["entities_found"],
        entities=[
            EntityResult(
                placeholder=e["placeholder"],
                type=e["type"],
                confidence=e["confidence"],
            )
            for e in data["entities"]
        ],
        processing_ms=data["processing_ms"],
    )


def _parse_rehydrate(data: dict[str, Any]) -> RehydrateResponse:
    return RehydrateResponse(
        text=data["text"],
        entities_restored=data["entities_restored"],
        processing_ms=data["processing_ms"],
    )


def _parse_pattern(data: dict[str, Any]) -> PatternResponse:
    return PatternResponse(
        pattern_id=data["pattern_id"],
        name=data["name"],
        status=data.get("status", "active"),
    )


class AmbientMeta:
    """Synchronous client for the AmbientMeta Privacy Gateway."""

    def __init__(
        self,
        api_key: str,
        base_url: str = _DEFAULT_BASE_URL,
        timeout: float = _DEFAULT_TIMEOUT,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = httpx.Client(
            base_url=self._base_url,
            headers={"X-API-Key": api_key, "Content-Type": "application/json"},
            timeout=timeout,
        )

    def sanitize(
        self,
        text: str,
        entities: list[str] | None = None,
    ) -> SanitizeResponse:
        """Sanitize text by detecting and replacing PII."""
        body: dict[str, Any] = {"text": text}
        if entities is not None:
            body["config"] = {"entities": entities}
        resp = self._client.post("/v1/sanitize", json=body)
        _raise_for_error(resp)
        return _parse_sanitize(resp.json())

    def rehydrate(self, text: str, session_id: str) -> RehydrateResponse:
        """Restore original PII from placeholders using a session ID."""
        resp = self._client.post(
            "/v1/rehydrate",
            json={"text": text, "session_id": session_id},
        )
        _raise_for_error(resp)
        return _parse_rehydrate(resp.json())

    def create_pattern(
        self,
        name: str,
        pattern: str,
        description: str = "",
        examples: list[str] | None = None,
    ) -> PatternResponse:
        """Register a custom detection pattern."""
        resp = self._client.post(
            "/v1/patterns",
            json={
                "name": name,
                "pattern": pattern,
                "description": description,
                "examples": examples or [],
            },
        )
        _raise_for_error(resp)
        return _parse_pattern(resp.json())

    def send_feedback(
        self,
        session_id: str,
        feedback_type: str,
        text_snippet: str,
        expected_type: str = "",
    ) -> FeedbackResponse:
        """Submit feedback on detection accuracy."""
        resp = self._client.post(
            "/v1/feedback",
            json={
                "session_id": session_id,
                "feedback_type": feedback_type,
                "text_snippet": text_snippet,
                "expected_type": expected_type,
            },
        )
        _raise_for_error(resp)
        return FeedbackResponse(status=resp.json().get("status", "recorded"))

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()

    def __enter__(self) -> AmbientMeta:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


class AsyncAmbientMeta:
    """Async client for the AmbientMeta Privacy Gateway."""

    def __init__(
        self,
        api_key: str,
        base_url: str = _DEFAULT_BASE_URL,
        timeout: float = _DEFAULT_TIMEOUT,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers={"X-API-Key": api_key, "Content-Type": "application/json"},
            timeout=timeout,
        )

    async def sanitize(
        self,
        text: str,
        entities: list[str] | None = None,
    ) -> SanitizeResponse:
        """Sanitize text by detecting and replacing PII."""
        body: dict[str, Any] = {"text": text}
        if entities is not None:
            body["config"] = {"entities": entities}
        resp = await self._client.post("/v1/sanitize", json=body)
        _raise_for_error(resp)
        return _parse_sanitize(resp.json())

    async def rehydrate(self, text: str, session_id: str) -> RehydrateResponse:
        """Restore original PII from placeholders using a session ID."""
        resp = await self._client.post(
            "/v1/rehydrate",
            json={"text": text, "session_id": session_id},
        )
        _raise_for_error(resp)
        return _parse_rehydrate(resp.json())

    async def create_pattern(
        self,
        name: str,
        pattern: str,
        description: str = "",
        examples: list[str] | None = None,
    ) -> PatternResponse:
        """Register a custom detection pattern."""
        resp = await self._client.post(
            "/v1/patterns",
            json={
                "name": name,
                "pattern": pattern,
                "description": description,
                "examples": examples or [],
            },
        )
        _raise_for_error(resp)
        return _parse_pattern(resp.json())

    async def send_feedback(
        self,
        session_id: str,
        feedback_type: str,
        text_snippet: str,
        expected_type: str = "",
    ) -> FeedbackResponse:
        """Submit feedback on detection accuracy."""
        resp = await self._client.post(
            "/v1/feedback",
            json={
                "session_id": session_id,
                "feedback_type": feedback_type,
                "text_snippet": text_snippet,
                "expected_type": expected_type,
            },
        )
        _raise_for_error(resp)
        return FeedbackResponse(status=resp.json().get("status", "recorded"))

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> AsyncAmbientMeta:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
