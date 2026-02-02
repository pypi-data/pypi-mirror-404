"""Tests for the AmbientMeta Python SDK."""

import pytest
import httpx
import respx

from ambientmeta import (
    AmbientMeta,
    AsyncAmbientMeta,
    AmbientMetaError,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)


BASE_URL = "https://test-api.example.com"


# ---------------------------------------------------------------------------
# Sync client tests
# ---------------------------------------------------------------------------


class TestSyncClient:
    def setup_method(self):
        self.client = AmbientMeta(api_key="test-key", base_url=BASE_URL)

    def teardown_method(self):
        self.client.close()

    @respx.mock
    def test_sanitize(self):
        respx.post(f"{BASE_URL}/v1/sanitize").mock(
            return_value=httpx.Response(
                200,
                json={
                    "sanitized": "Email [EMAIL_1]",
                    "session_id": "ses_123",
                    "entities_found": 1,
                    "entities": [
                        {"placeholder": "[EMAIL_1]", "type": "EMAIL", "confidence": 0.99}
                    ],
                    "processing_ms": 5.0,
                },
            )
        )
        result = self.client.sanitize("Email john@acme.com")
        assert result.sanitized == "Email [EMAIL_1]"
        assert result.session_id == "ses_123"
        assert result.entities_found == 1
        assert result.entities[0].type == "EMAIL"
        assert result.entities[0].confidence == 0.99

    @respx.mock
    def test_sanitize_with_entities(self):
        respx.post(f"{BASE_URL}/v1/sanitize").mock(
            return_value=httpx.Response(
                200,
                json={
                    "sanitized": "text",
                    "session_id": "ses_456",
                    "entities_found": 0,
                    "entities": [],
                    "processing_ms": 1.0,
                },
            )
        )
        result = self.client.sanitize("text", entities=["EMAIL", "PHONE"])
        assert result.entities_found == 0

    @respx.mock
    def test_rehydrate(self):
        respx.post(f"{BASE_URL}/v1/rehydrate").mock(
            return_value=httpx.Response(
                200,
                json={
                    "text": "Email john@acme.com",
                    "entities_restored": 1,
                    "processing_ms": 2.0,
                },
            )
        )
        result = self.client.rehydrate("Email [EMAIL_1]", "ses_123")
        assert result.text == "Email john@acme.com"
        assert result.entities_restored == 1

    @respx.mock
    def test_create_pattern(self):
        respx.post(f"{BASE_URL}/v1/patterns").mock(
            return_value=httpx.Response(
                200,
                json={
                    "pattern_id": "pat_abc",
                    "name": "EMPLOYEE_ID",
                    "status": "active",
                },
            )
        )
        result = self.client.create_pattern(
            name="EMPLOYEE_ID",
            pattern=r"EMP-\d{6}",
            description="Employee ID",
            examples=["EMP-123456"],
        )
        assert result.pattern_id == "pat_abc"
        assert result.name == "EMPLOYEE_ID"
        assert result.status == "active"

    @respx.mock
    def test_send_feedback(self):
        respx.post(f"{BASE_URL}/v1/feedback").mock(
            return_value=httpx.Response(200, json={"status": "recorded"})
        )
        result = self.client.send_feedback(
            session_id="ses_123",
            feedback_type="missed_entity",
            text_snippet="Dr. Jane",
            expected_type="PERSON",
        )
        assert result.status == "recorded"

    @respx.mock
    def test_auth_error(self):
        respx.post(f"{BASE_URL}/v1/sanitize").mock(
            return_value=httpx.Response(
                401,
                json={
                    "error": {
                        "code": "invalid_api_key",
                        "message": "Invalid API key",
                        "suggestion": "Check your key",
                    }
                },
            )
        )
        with pytest.raises(AuthenticationError) as exc_info:
            self.client.sanitize("text")
        assert exc_info.value.code == "invalid_api_key"

    @respx.mock
    def test_rate_limit_error(self):
        respx.post(f"{BASE_URL}/v1/sanitize").mock(
            return_value=httpx.Response(
                429,
                json={
                    "error": {
                        "code": "rate_limited",
                        "message": "Rate limit exceeded",
                    }
                },
            )
        )
        with pytest.raises(RateLimitError):
            self.client.sanitize("text")

    @respx.mock
    def test_not_found_error(self):
        respx.post(f"{BASE_URL}/v1/rehydrate").mock(
            return_value=httpx.Response(
                404,
                json={
                    "error": {
                        "code": "session_not_found",
                        "message": "Session not found",
                    }
                },
            )
        )
        with pytest.raises(NotFoundError):
            self.client.rehydrate("[PERSON_1]", "ses_expired")

    @respx.mock
    def test_validation_error(self):
        respx.post(f"{BASE_URL}/v1/sanitize").mock(
            return_value=httpx.Response(
                422,
                json={
                    "error": {
                        "code": "validation_error",
                        "message": "Invalid input",
                    }
                },
            )
        )
        with pytest.raises(ValidationError):
            self.client.sanitize("")

    @respx.mock
    def test_generic_error(self):
        respx.post(f"{BASE_URL}/v1/sanitize").mock(
            return_value=httpx.Response(
                500,
                json={
                    "error": {
                        "code": "internal_error",
                        "message": "Unexpected error",
                    }
                },
            )
        )
        with pytest.raises(AmbientMetaError):
            self.client.sanitize("text")

    def test_context_manager(self):
        with AmbientMeta(api_key="key", base_url=BASE_URL) as client:
            assert client is not None


# ---------------------------------------------------------------------------
# Async client tests
# ---------------------------------------------------------------------------


class TestAsyncClient:
    @respx.mock
    @pytest.mark.asyncio
    async def test_sanitize(self):
        respx.post(f"{BASE_URL}/v1/sanitize").mock(
            return_value=httpx.Response(
                200,
                json={
                    "sanitized": "Email [EMAIL_1]",
                    "session_id": "ses_123",
                    "entities_found": 1,
                    "entities": [
                        {"placeholder": "[EMAIL_1]", "type": "EMAIL", "confidence": 0.99}
                    ],
                    "processing_ms": 5.0,
                },
            )
        )
        async with AsyncAmbientMeta(api_key="test-key", base_url=BASE_URL) as client:
            result = await client.sanitize("Email john@acme.com")
            assert result.sanitized == "Email [EMAIL_1]"
            assert result.session_id == "ses_123"

    @respx.mock
    @pytest.mark.asyncio
    async def test_rehydrate(self):
        respx.post(f"{BASE_URL}/v1/rehydrate").mock(
            return_value=httpx.Response(
                200,
                json={
                    "text": "Email john@acme.com",
                    "entities_restored": 1,
                    "processing_ms": 2.0,
                },
            )
        )
        async with AsyncAmbientMeta(api_key="test-key", base_url=BASE_URL) as client:
            result = await client.rehydrate("Email [EMAIL_1]", "ses_123")
            assert result.text == "Email john@acme.com"

    @respx.mock
    @pytest.mark.asyncio
    async def test_create_pattern(self):
        respx.post(f"{BASE_URL}/v1/patterns").mock(
            return_value=httpx.Response(
                200,
                json={
                    "pattern_id": "pat_abc",
                    "name": "TEST_PAT",
                    "status": "active",
                },
            )
        )
        async with AsyncAmbientMeta(api_key="test-key", base_url=BASE_URL) as client:
            result = await client.create_pattern("TEST_PAT", r"\d+")
            assert result.name == "TEST_PAT"

    @respx.mock
    @pytest.mark.asyncio
    async def test_send_feedback(self):
        respx.post(f"{BASE_URL}/v1/feedback").mock(
            return_value=httpx.Response(200, json={"status": "recorded"})
        )
        async with AsyncAmbientMeta(api_key="test-key", base_url=BASE_URL) as client:
            result = await client.send_feedback("ses_1", "missed_entity", "text")
            assert result.status == "recorded"

    @respx.mock
    @pytest.mark.asyncio
    async def test_auth_error(self):
        respx.post(f"{BASE_URL}/v1/sanitize").mock(
            return_value=httpx.Response(
                401,
                json={"error": {"code": "invalid_api_key", "message": "Bad key"}},
            )
        )
        async with AsyncAmbientMeta(api_key="bad-key", base_url=BASE_URL) as client:
            with pytest.raises(AuthenticationError):
                await client.sanitize("text")
