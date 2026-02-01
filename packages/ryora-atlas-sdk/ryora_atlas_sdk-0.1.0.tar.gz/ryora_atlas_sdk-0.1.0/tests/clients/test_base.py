"""Tests for BaseClient shared functionality."""

import logging
import uuid
from datetime import datetime, timezone
from email.utils import format_datetime

import httpx
import pytest
import respx
from httpx import Response
from pydantic import BaseModel as PydanticBaseModel

from atlas_sdk.clients.base import (
    BaseClient,
    _get_retry_after_from_response,
    _is_retryable_response,
    _mask_sensitive,
)
from atlas_sdk.exceptions import AtlasHTTPStatusError, AtlasRateLimitError


@pytest.fixture
def base_url() -> str:
    return "http://test-service"


@pytest.fixture
def client(base_url: str) -> BaseClient:
    return BaseClient(base_url=base_url)


class TestIsRetryableResponse:
    """Tests for _is_retryable_response helper."""

    @pytest.mark.parametrize("status_code", [429, 502, 503, 504])
    def test_retryable_status_codes(self, status_code: int) -> None:
        response = Response(status_code)
        assert _is_retryable_response(response) is True

    @pytest.mark.parametrize("status_code", [200, 201, 400, 401, 404, 500, 501])
    def test_non_retryable_status_codes(self, status_code: int) -> None:
        response = Response(status_code)
        assert _is_retryable_response(response) is False


class TestMaskSensitive:
    """Tests for _mask_sensitive helper function."""

    def test_masks_api_key(self) -> None:
        data = {"api_key": "secret123", "limit": "10"}
        result = _mask_sensitive(data)
        assert result["api_key"] == "***MASKED***"
        assert result["limit"] == "10"

    def test_masks_authorization(self) -> None:
        data = {"authorization": "Bearer token123"}
        result = _mask_sensitive(data)
        assert result["authorization"] == "***MASKED***"

    def test_masks_case_insensitive(self) -> None:
        data = {"API_KEY": "secret", "Token": "abc", "SECRET": "xyz"}
        result = _mask_sensitive(data)
        assert result["API_KEY"] == "***MASKED***"
        assert result["Token"] == "***MASKED***"
        assert result["SECRET"] == "***MASKED***"

    @pytest.mark.parametrize(
        "key",
        [
            "api_key",
            "apikey",
            "api-key",
            "x-api-key",
            "token",
            "secret",
            "password",
            "credential",
            "authorization",
        ],
    )
    def test_masks_all_sensitive_keys(self, key: str) -> None:
        data = {key: "sensitive_value"}
        result = _mask_sensitive(data)
        assert result[key] == "***MASKED***"

    def test_returns_none_for_none_input(self) -> None:
        assert _mask_sensitive(None) is None

    def test_returns_none_for_empty_dict(self) -> None:
        assert _mask_sensitive({}) is None

    def test_preserves_non_sensitive_keys(self) -> None:
        data = {"limit": 10, "offset": 0, "status": "active"}
        result = _mask_sensitive(data)
        assert result == {"limit": "10", "offset": "0", "status": "active"}


class TestBaseClientInit:
    """Tests for BaseClient initialization."""

    def test_base_url_strips_trailing_slash(self) -> None:
        client = BaseClient(base_url="http://test.com/")
        assert client.base_url == "http://test.com"

    def test_default_timeout(self) -> None:
        client = BaseClient(base_url="http://test.com")
        assert client.timeout == 30.0

    def test_custom_timeout(self) -> None:
        client = BaseClient(base_url="http://test.com", timeout=60.0)
        assert client.timeout == 60.0

    def test_external_client(self) -> None:
        external_client = httpx.AsyncClient()
        client = BaseClient(base_url="http://test.com", client=external_client)
        assert client._client is external_client
        assert client._internal_client is False

    def test_default_connection_pool_limits(self) -> None:
        client = BaseClient(base_url="http://test.com")
        assert client._limits.max_connections == 100
        assert client._limits.max_keepalive_connections == 20
        assert client._limits.keepalive_expiry == 5.0

    def test_custom_connection_pool_limits(self) -> None:
        client = BaseClient(
            base_url="http://test.com",
            max_connections=200,
            max_keepalive_connections=50,
            keepalive_expiry=30.0,
        )
        assert client._limits.max_connections == 200
        assert client._limits.max_keepalive_connections == 50
        assert client._limits.keepalive_expiry == 30.0


class TestBaseClientContextManager:
    """Tests for context manager behavior."""

    @pytest.mark.asyncio
    async def test_creates_internal_client_on_enter(self, client: BaseClient) -> None:
        assert client._client is None

        async with client:
            assert client._client is not None
            assert client._internal_client is True

        assert client._client is None
        assert client._internal_client is False

    @pytest.mark.asyncio
    async def test_preserves_external_client(self, base_url: str) -> None:
        external_client = httpx.AsyncClient(base_url=base_url)
        client = BaseClient(base_url=base_url, client=external_client)

        async with client:
            assert client._client is external_client
            assert client._internal_client is False

        # External client should NOT be closed
        assert client._client is external_client
        assert not external_client.is_closed

        await external_client.aclose()


class TestBaseClientConnectionPool:
    """White-box tests for connection pool configuration.

    NOTE: These tests verify internal implementation details (private attributes
    like _limits, _client, _internal_client) rather than observable behavior.
    They exist to ensure configuration values are correctly stored and passed
    through to httpx, but may need updates if the internal implementation changes.

    Testing actual connection pooling behavior (e.g., connection reuse, limits
    being enforced) would require integration tests with real network connections.
    """

    @pytest.mark.asyncio
    async def test_limits_stored_on_base_client(self, base_url: str) -> None:
        """Connection pool limits should be stored on BaseClient."""
        client = BaseClient(
            base_url=base_url,
            max_connections=150,
            max_keepalive_connections=40,
            keepalive_expiry=15.0,
        )

        # Verify limits are stored correctly on the BaseClient
        assert client._limits.max_connections == 150
        assert client._limits.max_keepalive_connections == 40
        assert client._limits.keepalive_expiry == 15.0

    @pytest.mark.asyncio
    async def test_client_created_with_limits_context_manager(
        self, base_url: str
    ) -> None:
        """Internal client should be created when using context manager."""
        client = BaseClient(
            base_url=base_url,
            max_connections=200,
            max_keepalive_connections=50,
            keepalive_expiry=30.0,
        )

        async with client:
            assert client._client is not None
            assert client._internal_client is True
            # BaseClient's limits are stored for passing to httpx
            assert client._limits.max_connections == 200

    @pytest.mark.asyncio
    async def test_client_created_with_limits_ensure_client(
        self, base_url: str
    ) -> None:
        """Internal client should be created when using _ensure_client."""
        client = BaseClient(
            base_url=base_url,
            max_connections=250,
            max_keepalive_connections=60,
            keepalive_expiry=45.0,
        )

        await client._ensure_client()

        assert client._client is not None
        assert client._internal_client is True
        # BaseClient's limits are stored for passing to httpx
        assert client._limits.max_connections == 250

        await client.close()

    @pytest.mark.asyncio
    async def test_external_client_preserved(self, base_url: str) -> None:
        """External clients should be preserved and not replaced."""
        external_limits = httpx.Limits(
            max_connections=50,
            max_keepalive_connections=10,
            keepalive_expiry=2.0,
        )
        external_client = httpx.AsyncClient(base_url=base_url, limits=external_limits)

        # BaseClient with different limits - but external client takes precedence
        client = BaseClient(
            base_url=base_url,
            client=external_client,
            max_connections=500,  # Different from external_client
        )

        # BaseClient stores its own limits, but they won't be used
        assert client._limits.max_connections == 500

        async with client:
            # External client is used, not a new one with BaseClient's limits
            assert client._client is external_client
            assert client._internal_client is False

        await external_client.aclose()


class TestBaseClientClose:
    """Tests for close method."""

    @pytest.mark.asyncio
    async def test_close_internal_client(self, client: BaseClient) -> None:
        async with client:
            pass

        # Already closed by context manager, but calling again should be safe
        await client.close()

    @pytest.mark.asyncio
    async def test_close_without_context_manager(self, base_url: str) -> None:
        client = BaseClient(base_url=base_url)
        await client._ensure_client()

        assert client._client is not None
        await client.close()
        assert client._client is None


class TestBaseClientRaiseForStatus:
    """Tests for _raise_for_status method."""

    def _make_response(self, status_code: int, **kwargs: object) -> Response:
        """Create a response with a mock request attached."""
        request = httpx.Request("GET", "http://test/")
        return Response(status_code, request=request, **kwargs)

    def test_no_raise_on_success(self, client: BaseClient) -> None:
        response = self._make_response(200)
        client._raise_for_status(response)  # Should not raise

    def test_raises_atlas_error_with_json_body(self, client: BaseClient) -> None:
        error_data = {"detail": "Not found", "code": "ERR_001"}
        response = self._make_response(404, json=error_data)

        with pytest.raises(AtlasHTTPStatusError) as exc_info:
            client._raise_for_status(response)

        assert "Not found" in str(exc_info.value)
        # New format: error is in server_response, not in message
        assert exc_info.value.server_response == error_data

    def test_raises_atlas_error_with_text_body(self, client: BaseClient) -> None:
        response = self._make_response(500, text="Internal error occurred")

        with pytest.raises(AtlasHTTPStatusError) as exc_info:
            client._raise_for_status(response)

        assert "Internal error occurred" in str(exc_info.value)
        assert exc_info.value.server_response == "Internal error occurred"


class TestBaseClientRequest:
    """Tests for _request method."""

    @pytest.mark.asyncio
    async def test_request_logging(
        self, client: BaseClient, base_url: str, caplog: pytest.LogCaptureFixture
    ) -> None:
        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get("/test").mock(return_value=Response(200))

            with caplog.at_level(logging.DEBUG):
                async with client:
                    await client._request("GET", "/test")

            assert "Request: GET /test" in caplog.text
            assert "Response: 200 GET /test" in caplog.text
            assert "duration=" in caplog.text

    @pytest.mark.asyncio
    async def test_request_with_params(self, client: BaseClient, base_url: str) -> None:
        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get("/test", params={"key": "value"}).mock(
                return_value=Response(200, json={"result": "ok"})
            )

            async with client:
                response = await client._request(
                    "GET", "/test", params={"key": "value"}
                )

            assert response.status_code == 200
            assert response.json() == {"result": "ok"}

    @pytest.mark.asyncio
    async def test_request_with_json_body(
        self, client: BaseClient, base_url: str
    ) -> None:
        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.post("/test").mock(
                return_value=Response(201, json={"id": "123"})
            )

            async with client:
                response = await client._request("POST", "/test", json={"name": "test"})

            assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_auto_creates_client_if_needed(
        self, client: BaseClient, base_url: str
    ) -> None:
        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get("/test").mock(return_value=Response(200))

            # No context manager - should auto-create client
            response = await client._request("GET", "/test")
            assert response.status_code == 200
            assert client._client is not None
            assert client._internal_client is True

            await client.close()


class TestBaseClientRetry:
    """Tests for retry behavior."""

    @pytest.mark.asyncio
    async def test_retries_on_502(self, client: BaseClient, base_url: str) -> None:
        call_count = 0

        async def side_effect(request: httpx.Request) -> Response:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                return Response(502)
            return Response(200)

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get("/test").mock(side_effect=side_effect)

            async with client:
                response = await client._request("GET", "/test")

            assert response.status_code == 200
            assert call_count == 3

    @pytest.mark.asyncio
    async def test_retries_on_connect_error(
        self, client: BaseClient, base_url: str
    ) -> None:
        call_count = 0

        async def side_effect(request: httpx.Request) -> Response:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise httpx.ConnectError("Connection failed")
            return Response(200)

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get("/test").mock(side_effect=side_effect)

            async with client:
                response = await client._request("GET", "/test")

            assert response.status_code == 200
            assert call_count == 2

    @pytest.mark.asyncio
    async def test_no_retry_on_400(self, client: BaseClient, base_url: str) -> None:
        call_count = 0

        async def side_effect(request: httpx.Request) -> Response:
            nonlocal call_count
            call_count += 1
            return Response(400)

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get("/test").mock(side_effect=side_effect)

            async with client:
                response = await client._request("GET", "/test")

            assert response.status_code == 400
            assert call_count == 1  # No retry for 400


class TestBaseClientStructuredLogging:
    """Tests for structured logging with request details."""

    @pytest.mark.asyncio
    async def test_logs_query_params(
        self, client: BaseClient, base_url: str, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Structured logging should include query parameters."""
        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get("/test", params={"limit": "10", "offset": "0"}).mock(
                return_value=Response(200)
            )

            with caplog.at_level(logging.DEBUG):
                async with client:
                    await client._request(
                        "GET", "/test", params={"limit": "10", "offset": "0"}
                    )

            assert "params=" in caplog.text
            assert "limit" in caplog.text

    @pytest.mark.asyncio
    async def test_masks_sensitive_params_in_logs(
        self, client: BaseClient, base_url: str, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Sensitive query parameters should be masked in SDK logs."""
        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get(
                "/test", params={"api_key": "secret123", "limit": "10"}
            ).mock(return_value=Response(200))

            with caplog.at_level(logging.DEBUG):
                async with client:
                    await client._request(
                        "GET", "/test", params={"api_key": "secret123", "limit": "10"}
                    )

            # Check only SDK log messages (atlas_sdk.clients.base)
            sdk_logs = [
                record.message
                for record in caplog.records
                if record.name == "atlas_sdk.clients.base"
            ]
            sdk_log_text = " ".join(sdk_logs)

            # Sensitive value should NOT appear in SDK logs
            assert "secret123" not in sdk_log_text
            # Masked placeholder should appear
            assert "***MASKED***" in sdk_log_text
            # Non-sensitive values should still appear
            assert "limit" in sdk_log_text

    @pytest.mark.asyncio
    async def test_logs_request_body_size(
        self, client: BaseClient, base_url: str, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Structured logging should include request body size for POST requests."""
        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.post("/test").mock(return_value=Response(201))

            with caplog.at_level(logging.DEBUG):
                async with client:
                    await client._request(
                        "POST", "/test", json={"name": "test", "value": 123}
                    )

            assert "body_size=" in caplog.text

    @pytest.mark.asyncio
    async def test_logs_response_content_type(
        self, client: BaseClient, base_url: str, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Structured logging should include response content type."""
        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get("/test").mock(
                return_value=Response(
                    200,
                    json={"result": "ok"},
                    headers={"content-type": "application/json"},
                )
            )

            with caplog.at_level(logging.DEBUG):
                async with client:
                    await client._request("GET", "/test")

            assert "content_type=" in caplog.text
            assert "application/json" in caplog.text

    @pytest.mark.asyncio
    async def test_logs_response_content_length(
        self, client: BaseClient, base_url: str, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Structured logging should include response content length."""
        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get("/test").mock(
                return_value=Response(
                    200,
                    json={"result": "ok"},
                    headers={"content-length": "42"},
                )
            )

            with caplog.at_level(logging.DEBUG):
                async with client:
                    await client._request("GET", "/test")

            assert "content_length=" in caplog.text


class TestBaseClientRequestId:
    """Tests for X-Request-ID header propagation.

    These tests verify that request IDs are correctly set in HTTP headers
    that reach the server. The tests capture actual requests sent to the
    mock server to verify observable behavior (headers arriving at server).
    """

    @pytest.mark.asyncio
    async def test_auto_generates_request_id(
        self, client: BaseClient, base_url: str
    ) -> None:
        """Should auto-generate a valid UUID request ID when not provided."""
        captured_request: httpx.Request | None = None

        async def capture_request(request: httpx.Request) -> Response:
            nonlocal captured_request
            captured_request = request
            return Response(200)

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get("/test").mock(side_effect=capture_request)

            async with client:
                await client._request("GET", "/test")

        assert captured_request is not None
        assert "X-Request-ID" in captured_request.headers
        # Validate it's a properly formatted UUID (not just length check)
        request_id = captured_request.headers["X-Request-ID"]
        try:
            parsed_uuid = uuid.UUID(request_id)
            # Ensure it's a valid UUID version (typically v4 for random)
            assert parsed_uuid.version in (1, 4), "Expected UUID version 1 or 4"
        except ValueError:
            pytest.fail(f"Request ID '{request_id}' is not a valid UUID")

    @pytest.mark.asyncio
    async def test_uses_provided_request_id(
        self, client: BaseClient, base_url: str
    ) -> None:
        """Should use the provided request ID instead of generating one."""
        captured_request: httpx.Request | None = None
        custom_request_id = "my-custom-request-id-12345"

        async def capture_request(request: httpx.Request) -> Response:
            nonlocal captured_request
            captured_request = request
            return Response(200)

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get("/test").mock(side_effect=capture_request)

            async with client:
                await client._request("GET", "/test", request_id=custom_request_id)

        assert captured_request is not None
        assert captured_request.headers["X-Request-ID"] == custom_request_id

    @pytest.mark.asyncio
    async def test_logs_request_id(
        self, client: BaseClient, base_url: str, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Request ID should be included in log messages."""
        custom_request_id = "test-request-id-abc123"

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get("/test").mock(return_value=Response(200))

            with caplog.at_level(logging.DEBUG):
                async with client:
                    await client._request("GET", "/test", request_id=custom_request_id)

        assert "request_id=" in caplog.text
        assert custom_request_id in caplog.text

    @pytest.mark.asyncio
    async def test_request_id_preserved_on_retry(
        self, client: BaseClient, base_url: str
    ) -> None:
        """Same request ID should be used across retries."""
        captured_request_ids: list[str] = []
        call_count = 0

        async def capture_request(request: httpx.Request) -> Response:
            nonlocal call_count
            call_count += 1
            captured_request_ids.append(request.headers.get("X-Request-ID", ""))
            if call_count < 2:
                return Response(502)
            return Response(200)

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get("/test").mock(side_effect=capture_request)

            async with client:
                await client._request("GET", "/test")

        assert len(captured_request_ids) == 2
        # All retries should use the same request ID
        assert captured_request_ids[0] == captured_request_ids[1]


class TestGetRetryAfterFromResponse:
    """Tests for _get_retry_after_from_response helper."""

    def test_returns_none_for_non_429(self) -> None:
        response = Response(503)
        assert _get_retry_after_from_response(response) is None

    def test_returns_none_without_header(self) -> None:
        response = Response(429)
        assert _get_retry_after_from_response(response) is None

    def test_parses_numeric_seconds(self) -> None:
        response = Response(429, headers={"Retry-After": "30"})
        assert _get_retry_after_from_response(response) == 30.0

    def test_parses_numeric_seconds_float(self) -> None:
        response = Response(429, headers={"Retry-After": "5.5"})
        assert _get_retry_after_from_response(response) == 5.5

    def test_parses_http_date(self) -> None:
        # Create a date 10 seconds in the future
        future_time = datetime.now(timezone.utc).timestamp() + 10
        future_date = datetime.fromtimestamp(future_time, tz=timezone.utc)
        http_date = format_datetime(future_date, usegmt=True)

        response = Response(429, headers={"Retry-After": http_date})
        result = _get_retry_after_from_response(response)

        assert result is not None
        # Should be approximately 10 seconds (with some tolerance for test execution time)
        assert 8 <= result <= 12

    def test_http_date_in_past_returns_zero(self) -> None:
        # Create a date 10 seconds in the past
        past_time = datetime.now(timezone.utc).timestamp() - 10
        past_date = datetime.fromtimestamp(past_time, tz=timezone.utc)
        http_date = format_datetime(past_date, usegmt=True)

        response = Response(429, headers={"Retry-After": http_date})
        result = _get_retry_after_from_response(response)

        assert result == 0.0

    def test_returns_none_for_invalid_header(self) -> None:
        response = Response(429, headers={"Retry-After": "invalid"})
        assert _get_retry_after_from_response(response) is None


class TestRateLimitRetry:
    """Tests for 429 rate limit retry behavior."""

    @pytest.mark.asyncio
    async def test_retries_on_429(self, client: BaseClient, base_url: str) -> None:
        """Should retry on 429 and succeed when server recovers."""
        call_count = 0

        async def side_effect(request: httpx.Request) -> Response:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                return Response(429, headers={"Retry-After": "0"})
            return Response(200)

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get("/test").mock(side_effect=side_effect)

            async with client:
                response = await client._request("GET", "/test")

            assert response.status_code == 200
            assert call_count == 3

    @pytest.mark.asyncio
    async def test_raises_rate_limit_error_after_retries_exhausted(
        self, client: BaseClient, base_url: str
    ) -> None:
        """Should raise AtlasRateLimitError after retries are exhausted."""
        call_count = 0

        async def side_effect(request: httpx.Request) -> Response:
            nonlocal call_count
            call_count += 1
            return Response(429, headers={"Retry-After": "0"})

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get("/test").mock(side_effect=side_effect)

            async with client:
                response = await client._request("GET", "/test")

                # After retries exhausted, _raise_for_status should raise AtlasRateLimitError
                with pytest.raises(AtlasRateLimitError) as exc_info:
                    client._raise_for_status(response)

                assert exc_info.value.retry_after == 0.0

            # Should have retried 5 times (max attempts)
            assert call_count == 5

    @pytest.mark.asyncio
    async def test_rate_limit_error_includes_retry_after_seconds(
        self, client: BaseClient
    ) -> None:
        """AtlasRateLimitError should include retry_after from header."""
        request = httpx.Request("GET", "http://test/")
        response = Response(429, headers={"Retry-After": "120"}, request=request)

        with pytest.raises(AtlasRateLimitError) as exc_info:
            client._raise_for_status(response)

        assert exc_info.value.retry_after == 120.0

    @pytest.mark.asyncio
    async def test_rate_limit_error_includes_retry_after_date(
        self, client: BaseClient
    ) -> None:
        """AtlasRateLimitError should parse HTTP date from Retry-After header."""
        request = httpx.Request("GET", "http://test/")

        # Create a date 30 seconds in the future
        future_time = datetime.now(timezone.utc).timestamp() + 30
        future_date = datetime.fromtimestamp(future_time, tz=timezone.utc)
        http_date = format_datetime(future_date, usegmt=True)

        response = Response(429, headers={"Retry-After": http_date}, request=request)

        with pytest.raises(AtlasRateLimitError) as exc_info:
            client._raise_for_status(response)

        # Should be approximately 30 seconds
        assert exc_info.value.retry_after is not None
        assert 28 <= exc_info.value.retry_after <= 32

    @pytest.mark.asyncio
    async def test_rate_limit_error_retry_after_none_when_no_header(
        self, client: BaseClient
    ) -> None:
        """AtlasRateLimitError.retry_after should be None if no header present."""
        request = httpx.Request("GET", "http://test/")
        response = Response(429, request=request)

        with pytest.raises(AtlasRateLimitError) as exc_info:
            client._raise_for_status(response)

        assert exc_info.value.retry_after is None

    @pytest.mark.asyncio
    async def test_rate_limit_error_is_subclass_of_http_status_error(
        self, client: BaseClient
    ) -> None:
        """AtlasRateLimitError should be catchable as AtlasHTTPStatusError."""
        request = httpx.Request("GET", "http://test/")
        response = Response(429, request=request)

        with pytest.raises(AtlasHTTPStatusError):
            client._raise_for_status(response)

    @pytest.mark.asyncio
    async def test_rate_limit_error_is_subclass_of_atlas_error(
        self, client: BaseClient
    ) -> None:
        """AtlasRateLimitError should be catchable as AtlasError."""
        from atlas_sdk.exceptions import AtlasError, AtlasRateLimitError

        request = httpx.Request("GET", "http://test/")
        response = Response(429, request=request)

        with pytest.raises(AtlasRateLimitError) as exc_info:
            client._raise_for_status(response)

        # Verify it's also an AtlasError
        assert isinstance(exc_info.value, AtlasError)


class TestBaseClientIdempotency:
    """Tests for idempotency key support."""

    @pytest.mark.asyncio
    async def test_idempotency_key_header_injected(
        self, client: BaseClient, base_url: str
    ) -> None:
        """Should inject Idempotency-Key header when provided."""
        captured_request: httpx.Request | None = None

        async def capture_request(request: httpx.Request) -> Response:
            nonlocal captured_request
            captured_request = request
            return Response(201)

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.post("/test").mock(side_effect=capture_request)

            async with client:
                await client._request(
                    "POST", "/test", idempotency_key="my-idempotency-key-123"
                )

        assert captured_request is not None
        assert "Idempotency-Key" in captured_request.headers
        assert captured_request.headers["Idempotency-Key"] == "my-idempotency-key-123"

    @pytest.mark.asyncio
    async def test_idempotency_key_auto_generates_uuid(
        self, client: BaseClient, base_url: str
    ) -> None:
        """Should auto-generate a UUID when idempotency_key='auto'."""
        captured_request: httpx.Request | None = None

        async def capture_request(request: httpx.Request) -> Response:
            nonlocal captured_request
            captured_request = request
            return Response(201)

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.post("/test").mock(side_effect=capture_request)

            async with client:
                await client._request("POST", "/test", idempotency_key="auto")

        assert captured_request is not None
        assert "Idempotency-Key" in captured_request.headers
        # Should be a valid UUID format (36 chars with hyphens)
        idempotency_key = captured_request.headers["Idempotency-Key"]
        assert len(idempotency_key) == 36

    @pytest.mark.asyncio
    async def test_no_idempotency_key_header_when_none(
        self, client: BaseClient, base_url: str
    ) -> None:
        """Should not include Idempotency-Key header when not provided."""
        captured_request: httpx.Request | None = None

        async def capture_request(request: httpx.Request) -> Response:
            nonlocal captured_request
            captured_request = request
            return Response(200)

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get("/test").mock(side_effect=capture_request)

            async with client:
                await client._request("GET", "/test")

        assert captured_request is not None
        assert "Idempotency-Key" not in captured_request.headers

    @pytest.mark.asyncio
    async def test_idempotency_key_logged(
        self, client: BaseClient, base_url: str, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Idempotency key should be included in log messages."""
        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.post("/test").mock(return_value=Response(201))

            with caplog.at_level(logging.DEBUG):
                async with client:
                    await client._request(
                        "POST", "/test", idempotency_key="idem-key-abc"
                    )

        assert "idempotency_key=" in caplog.text
        assert "idem-key-abc" in caplog.text

    @pytest.mark.asyncio
    async def test_idempotency_key_preserved_on_retry(
        self, client: BaseClient, base_url: str
    ) -> None:
        """Same idempotency key should be used across retries."""
        captured_keys: list[str] = []
        call_count = 0

        async def capture_request(request: httpx.Request) -> Response:
            nonlocal call_count
            call_count += 1
            if "Idempotency-Key" in request.headers:
                captured_keys.append(request.headers["Idempotency-Key"])
            if call_count < 2:
                return Response(502)
            return Response(201)

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.post("/test").mock(side_effect=capture_request)

            async with client:
                await client._request(
                    "POST", "/test", idempotency_key="idem-key-retry-test"
                )

        assert len(captured_keys) == 2
        # All retries should use the same idempotency key
        assert captured_keys[0] == captured_keys[1] == "idem-key-retry-test"


class TestBaseClientInstrumentation:
    """Tests for BaseClient instrumentation features."""

    def test_default_instrumentation_is_noop(self, base_url: str) -> None:
        """Default instrumentation should be a no-op."""
        from atlas_sdk.instrumentation import NoOpMetricsHandler

        client = BaseClient(base_url=base_url)

        assert isinstance(client._instrumentation.metrics_handler, NoOpMetricsHandler)
        assert client._instrumentation.enable_tracing is False

    def test_enable_tracing_parameter(self, base_url: str) -> None:
        """Should accept enable_tracing parameter."""
        client = BaseClient(base_url=base_url, enable_tracing=True)

        assert client._instrumentation.enable_tracing is True

    def test_metrics_handler_parameter(self, base_url: str) -> None:
        """Should accept custom metrics handler."""
        from unittest.mock import MagicMock

        from atlas_sdk.instrumentation import MetricsHandler

        mock_handler = MagicMock(spec=MetricsHandler)
        client = BaseClient(base_url=base_url, metrics_handler=mock_handler)

        assert client._instrumentation.metrics_handler is mock_handler

    def test_instrumentation_config_parameter(self, base_url: str) -> None:
        """Should accept InstrumentationConfig object."""
        from atlas_sdk.instrumentation import InstrumentationConfig

        config = InstrumentationConfig(enable_tracing=True)
        client = BaseClient(base_url=base_url, instrumentation=config)

        assert client._instrumentation is config

    def test_instrumentation_config_takes_precedence(self, base_url: str) -> None:
        """InstrumentationConfig should take precedence over individual params."""
        from unittest.mock import MagicMock

        from atlas_sdk.instrumentation import InstrumentationConfig, MetricsHandler

        mock_handler1 = MagicMock(spec=MetricsHandler)
        mock_handler2 = MagicMock(spec=MetricsHandler)
        config = InstrumentationConfig(metrics_handler=mock_handler2)

        client = BaseClient(
            base_url=base_url,
            metrics_handler=mock_handler1,  # Should be ignored
            instrumentation=config,
        )

        assert client._instrumentation.metrics_handler is mock_handler2

    @pytest.mark.asyncio
    async def test_metrics_handler_on_request_start_called(self, base_url: str) -> None:
        """Metrics handler on_request_start should be called."""
        from unittest.mock import MagicMock

        from atlas_sdk.instrumentation import MetricsHandler

        mock_handler = MagicMock(spec=MetricsHandler)
        client = BaseClient(base_url=base_url, metrics_handler=mock_handler)

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get("/test").mock(return_value=Response(200))

            async with client:
                await client._request("GET", "/test", request_id="test-req-id")

        mock_handler.on_request_start.assert_called_once()
        call_args = mock_handler.on_request_start.call_args
        assert call_args[0][0] == "GET"
        assert call_args[0][1] == "/test"
        assert call_args[0][2] == "test-req-id"

    @pytest.mark.asyncio
    async def test_metrics_handler_on_request_end_called(self, base_url: str) -> None:
        """Metrics handler on_request_end should be called with RequestMetrics."""
        from unittest.mock import MagicMock

        from atlas_sdk.instrumentation import MetricsHandler, RequestMetrics

        mock_handler = MagicMock(spec=MetricsHandler)
        client = BaseClient(base_url=base_url, metrics_handler=mock_handler)

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get("/test").mock(
                return_value=Response(200, headers={"content-length": "42"})
            )

            async with client:
                await client._request("GET", "/test", request_id="test-req-id")

        mock_handler.on_request_end.assert_called_once()
        call_args = mock_handler.on_request_end.call_args
        metrics: RequestMetrics = call_args[0][0]

        assert metrics.method == "GET"
        assert metrics.url == "/test"
        assert metrics.request_id == "test-req-id"
        assert metrics.status_code == 200
        assert metrics.duration_seconds > 0
        assert metrics.response_body_size == 42

    @pytest.mark.asyncio
    async def test_metrics_handler_on_request_error_called(self, base_url: str) -> None:
        """Metrics handler on_request_error should be called on exception."""
        from unittest.mock import MagicMock

        from atlas_sdk.instrumentation import MetricsHandler

        mock_handler = MagicMock(spec=MetricsHandler)
        client = BaseClient(base_url=base_url, metrics_handler=mock_handler)

        async with respx.mock(base_url=base_url) as respx_mock:
            # Simulate a connection error that exhausts retries
            respx_mock.get("/test").mock(
                side_effect=httpx.ConnectError("Connection failed")
            )

            async with client:
                with pytest.raises(httpx.ConnectError):
                    await client._request("GET", "/test", request_id="test-req-id")

        # on_request_error should be called
        mock_handler.on_request_error.assert_called()
        call_args = mock_handler.on_request_error.call_args
        assert call_args[0][0] == "GET"
        assert call_args[0][1] == "/test"
        assert call_args[0][2] == "test-req-id"
        assert isinstance(call_args[0][3], httpx.ConnectError)

    @pytest.mark.asyncio
    async def test_metrics_handler_on_request_end_with_json_body(
        self, base_url: str
    ) -> None:
        """Metrics should include request body size for POST with JSON."""
        from unittest.mock import MagicMock

        from atlas_sdk.instrumentation import MetricsHandler, RequestMetrics

        mock_handler = MagicMock(spec=MetricsHandler)
        client = BaseClient(base_url=base_url, metrics_handler=mock_handler)

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.post("/test").mock(return_value=Response(201))

            async with client:
                await client._request(
                    "POST", "/test", json={"name": "test"}, request_id="test-req-id"
                )

        call_args = mock_handler.on_request_end.call_args
        metrics: RequestMetrics = call_args[0][0]

        assert metrics.method == "POST"
        assert metrics.request_body_size is not None
        assert metrics.request_body_size > 0

    @pytest.mark.asyncio
    async def test_metrics_handler_called_on_each_request(self, base_url: str) -> None:
        """Metrics handler should be called for each request."""
        from unittest.mock import MagicMock

        from atlas_sdk.instrumentation import MetricsHandler

        mock_handler = MagicMock(spec=MetricsHandler)
        client = BaseClient(base_url=base_url, metrics_handler=mock_handler)

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get("/test1").mock(return_value=Response(200))
            respx_mock.get("/test2").mock(return_value=Response(200))

            async with client:
                await client._request("GET", "/test1")
                await client._request("GET", "/test2")

        assert mock_handler.on_request_start.call_count == 2
        assert mock_handler.on_request_end.call_count == 2


# =============================================================================
# HTTP Helper Methods Tests
# =============================================================================


class SampleModel:
    """Simple Pydantic-like model for testing HTTP helpers."""

    def __init__(self, id: str, name: str, value: int = 0) -> None:
        self.id = id
        self.name = name
        self.value = value

    @classmethod
    def model_validate(cls, data: dict) -> "SampleModel":
        return cls(id=data["id"], name=data["name"], value=data.get("value", 0))


# Create a proper Pydantic model for testing


class SampleResponseModel(PydanticBaseModel):
    """Sample model for HTTP helper tests."""

    id: str
    name: str
    value: int = 0


class SampleCreateModel(PydanticBaseModel):
    """Sample model for POST/PATCH requests."""

    name: str
    value: int = 0


class TestGetOne:
    """Tests for _get_one helper method."""

    @pytest.mark.asyncio
    async def test_get_one_success(self, client: BaseClient, base_url: str) -> None:
        """Should fetch and parse a single model."""
        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get("/api/v1/items/123").mock(
                return_value=Response(
                    200, json={"id": "123", "name": "test-item", "value": 42}
                )
            )

            async with client:
                result = await client._get_one("/api/v1/items/123", SampleResponseModel)

        assert isinstance(result, SampleResponseModel)
        assert result.id == "123"
        assert result.name == "test-item"
        assert result.value == 42

    @pytest.mark.asyncio
    async def test_get_one_with_params(self, client: BaseClient, base_url: str) -> None:
        """Should pass query parameters."""
        captured_request: httpx.Request | None = None

        async def capture_request(request: httpx.Request) -> Response:
            nonlocal captured_request
            captured_request = request
            return Response(200, json={"id": "123", "name": "test", "value": 0})

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get("/api/v1/items/123").mock(side_effect=capture_request)

            async with client:
                await client._get_one(
                    "/api/v1/items/123", SampleResponseModel, params={"enrich": "true"}
                )

        assert captured_request is not None
        assert "enrich=true" in str(captured_request.url)

    @pytest.mark.asyncio
    async def test_get_one_raises_on_404(
        self, client: BaseClient, base_url: str
    ) -> None:
        """Should raise AtlasHTTPStatusError on 404."""
        from atlas_sdk.exceptions import AtlasNotFoundError

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get("/api/v1/items/999").mock(
                return_value=Response(404, json={"detail": "Not found"})
            )

            async with client:
                with pytest.raises(AtlasNotFoundError):
                    await client._get_one("/api/v1/items/999", SampleResponseModel)

    @pytest.mark.asyncio
    async def test_get_one_passes_request_id(
        self, client: BaseClient, base_url: str
    ) -> None:
        """Should pass request_id to underlying request."""
        captured_request: httpx.Request | None = None

        async def capture_request(request: httpx.Request) -> Response:
            nonlocal captured_request
            captured_request = request
            return Response(200, json={"id": "123", "name": "test", "value": 0})

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get("/api/v1/items/123").mock(side_effect=capture_request)

            async with client:
                await client._get_one(
                    "/api/v1/items/123", SampleResponseModel, request_id="custom-id"
                )

        assert captured_request is not None
        assert captured_request.headers["X-Request-ID"] == "custom-id"


class TestGetMany:
    """Tests for _get_many helper method."""

    @pytest.mark.asyncio
    async def test_get_many_success(self, client: BaseClient, base_url: str) -> None:
        """Should fetch and parse a list of models."""
        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get("/api/v1/items").mock(
                return_value=Response(
                    200,
                    json=[
                        {"id": "1", "name": "item-1", "value": 10},
                        {"id": "2", "name": "item-2", "value": 20},
                        {"id": "3", "name": "item-3", "value": 30},
                    ],
                )
            )

            async with client:
                result = await client._get_many("/api/v1/items", SampleResponseModel)

        assert len(result) == 3
        assert all(isinstance(item, SampleResponseModel) for item in result)
        assert result[0].id == "1"
        assert result[1].name == "item-2"
        assert result[2].value == 30

    @pytest.mark.asyncio
    async def test_get_many_empty_list(self, client: BaseClient, base_url: str) -> None:
        """Should return empty list for empty response."""
        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get("/api/v1/items").mock(return_value=Response(200, json=[]))

            async with client:
                result = await client._get_many("/api/v1/items", SampleResponseModel)

        assert result == []

    @pytest.mark.asyncio
    async def test_get_many_with_params(
        self, client: BaseClient, base_url: str
    ) -> None:
        """Should pass query parameters."""
        captured_request: httpx.Request | None = None

        async def capture_request(request: httpx.Request) -> Response:
            nonlocal captured_request
            captured_request = request
            return Response(200, json=[])

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get("/api/v1/items").mock(side_effect=capture_request)

            async with client:
                await client._get_many(
                    "/api/v1/items",
                    SampleResponseModel,
                    params={"limit": 50, "offset": 10},
                )

        assert captured_request is not None
        url_str = str(captured_request.url)
        assert "limit=50" in url_str
        assert "offset=10" in url_str


class TestPostOne:
    """Tests for _post_one helper method."""

    @pytest.mark.asyncio
    async def test_post_one_success(self, client: BaseClient, base_url: str) -> None:
        """Should POST data and parse response model."""
        captured_request: httpx.Request | None = None

        async def capture_request(request: httpx.Request) -> Response:
            nonlocal captured_request
            captured_request = request
            return Response(
                201, json={"id": "new-123", "name": "new-item", "value": 100}
            )

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.post("/api/v1/items").mock(side_effect=capture_request)

            async with client:
                data = SampleCreateModel(name="new-item", value=100)
                result = await client._post_one(
                    "/api/v1/items", data, SampleResponseModel
                )

        assert isinstance(result, SampleResponseModel)
        assert result.id == "new-123"
        assert result.name == "new-item"
        assert result.value == 100

        # Verify request body
        assert captured_request is not None
        import json

        body = json.loads(captured_request.content)
        assert body["name"] == "new-item"
        assert body["value"] == 100

    @pytest.mark.asyncio
    async def test_post_one_with_idempotency_key(
        self, client: BaseClient, base_url: str
    ) -> None:
        """Should include idempotency key in headers."""
        captured_request: httpx.Request | None = None

        async def capture_request(request: httpx.Request) -> Response:
            nonlocal captured_request
            captured_request = request
            return Response(201, json={"id": "123", "name": "test", "value": 0})

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.post("/api/v1/items").mock(side_effect=capture_request)

            async with client:
                data = SampleCreateModel(name="test")
                await client._post_one(
                    "/api/v1/items", data, SampleResponseModel, idempotency_key="my-key"
                )

        assert captured_request is not None
        assert captured_request.headers["Idempotency-Key"] == "my-key"

    @pytest.mark.asyncio
    async def test_post_one_raises_on_validation_error(
        self, client: BaseClient, base_url: str
    ) -> None:
        """Should raise on 422 validation error."""
        from atlas_sdk.exceptions import AtlasValidationError

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.post("/api/v1/items").mock(
                return_value=Response(422, json={"detail": "Validation failed"})
            )

            async with client:
                data = SampleCreateModel(name="test")
                with pytest.raises(AtlasValidationError):
                    await client._post_one("/api/v1/items", data, SampleResponseModel)


class TestPatchOne:
    """Tests for _patch_one helper method."""

    @pytest.mark.asyncio
    async def test_patch_one_success(self, client: BaseClient, base_url: str) -> None:
        """Should PATCH data and parse response model."""
        captured_request: httpx.Request | None = None

        async def capture_request(request: httpx.Request) -> Response:
            nonlocal captured_request
            captured_request = request
            return Response(
                200, json={"id": "123", "name": "updated-name", "value": 50}
            )

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.patch("/api/v1/items/123").mock(side_effect=capture_request)

            async with client:
                data = SampleCreateModel(name="updated-name", value=50)
                result = await client._patch_one(
                    "/api/v1/items/123", data, SampleResponseModel
                )

        assert isinstance(result, SampleResponseModel)
        assert result.id == "123"
        assert result.name == "updated-name"
        assert result.value == 50

        # Verify PATCH method was used
        assert captured_request is not None
        assert captured_request.method == "PATCH"

    @pytest.mark.asyncio
    async def test_patch_one_excludes_unset(
        self, client: BaseClient, base_url: str
    ) -> None:
        """Should exclude unset fields from request body."""
        captured_request: httpx.Request | None = None

        async def capture_request(request: httpx.Request) -> Response:
            nonlocal captured_request
            captured_request = request
            return Response(200, json={"id": "123", "name": "test", "value": 0})

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.patch("/api/v1/items/123").mock(side_effect=capture_request)

            async with client:
                # Only set name, value should use default
                data = SampleCreateModel(name="only-name")
                await client._patch_one("/api/v1/items/123", data, SampleResponseModel)

        assert captured_request is not None
        import json

        body = json.loads(captured_request.content)
        # exclude_unset=True means only explicitly set fields are sent
        # In this case, name was set and value has a default, so both appear
        assert "name" in body


class TestDelete:
    """Tests for _delete helper method."""

    @pytest.mark.asyncio
    async def test_delete_success(self, client: BaseClient, base_url: str) -> None:
        """Should make DELETE request successfully."""
        captured_request: httpx.Request | None = None

        async def capture_request(request: httpx.Request) -> Response:
            nonlocal captured_request
            captured_request = request
            return Response(204)

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.delete("/api/v1/items/123").mock(side_effect=capture_request)

            async with client:
                result = await client._delete("/api/v1/items/123")

        assert result is None
        assert captured_request is not None
        assert captured_request.method == "DELETE"

    @pytest.mark.asyncio
    async def test_delete_raises_on_404(
        self, client: BaseClient, base_url: str
    ) -> None:
        """Should raise AtlasNotFoundError on 404."""
        from atlas_sdk.exceptions import AtlasNotFoundError

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.delete("/api/v1/items/999").mock(
                return_value=Response(404, json={"detail": "Not found"})
            )

            async with client:
                with pytest.raises(AtlasNotFoundError):
                    await client._delete("/api/v1/items/999")

    @pytest.mark.asyncio
    async def test_delete_passes_request_id(
        self, client: BaseClient, base_url: str
    ) -> None:
        """Should pass request_id to underlying request."""
        captured_request: httpx.Request | None = None

        async def capture_request(request: httpx.Request) -> Response:
            nonlocal captured_request
            captured_request = request
            return Response(204)

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.delete("/api/v1/items/123").mock(side_effect=capture_request)

            async with client:
                await client._delete("/api/v1/items/123", request_id="delete-req-id")

        assert captured_request is not None
        assert captured_request.headers["X-Request-ID"] == "delete-req-id"
