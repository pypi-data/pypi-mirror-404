"""Tests for Atlas SDK exceptions."""

import time
from datetime import datetime, timezone
from email.utils import format_datetime

import httpx
import pytest

from atlas_sdk.exceptions import (
    # Base
    AtlasError,
    # API errors
    AtlasAPIError,
    AtlasAuthenticationError,
    AtlasAuthorizationError,
    AtlasConflictError,
    AtlasNotFoundError,
    AtlasRateLimitError,
    AtlasServerError,
    AtlasValidationError,
    # Domain errors
    AtlasDomainError,
    AgentExecutionError,
    InvalidBlueprintError,
    StateTransitionError,
    # Other errors
    AtlasConnectionError,
    AtlasTimeoutError,
    # Supporting types
    RequestContext,
    ValidationErrorDetail,
    # Legacy aliases
    AtlasHTTPStatusError,
    # Internal helpers (for testing)
    _build_error_message,
)


class TestAtlasError:
    """Tests for AtlasError base exception."""

    def test_inherits_from_exception(self) -> None:
        """Should inherit from Exception."""
        assert issubclass(AtlasError, Exception)

    def test_message_attribute(self) -> None:
        """Should store message in attribute."""
        error = AtlasError("Test error message")
        assert error.message == "Test error message"

    def test_str_representation(self) -> None:
        """Should convert to string properly."""
        error = AtlasError("Test error")
        assert str(error) == "Test error"


class TestRequestContext:
    """Tests for RequestContext dataclass."""

    def test_creation(self) -> None:
        """Should create with all fields."""
        ctx = RequestContext(
            method="POST",
            url="http://example.com/api/test",
            request_id="req-123",
        )
        assert ctx.method == "POST"
        assert ctx.url == "http://example.com/api/test"
        assert ctx.request_id == "req-123"

    def test_default_request_id(self) -> None:
        """Should default request_id to None."""
        ctx = RequestContext(method="GET", url="http://test.com")
        assert ctx.request_id is None

    def test_from_request(self) -> None:
        """Should create from httpx.Request."""
        request = httpx.Request(
            "POST",
            "http://example.com/api/test",
            headers={"X-Request-ID": "req-456"},
        )
        ctx = RequestContext.from_request(request)
        assert ctx.method == "POST"
        assert ctx.url == "http://example.com/api/test"
        assert ctx.request_id == "req-456"

    def test_from_request_without_request_id(self) -> None:
        """Should handle missing X-Request-ID header."""
        request = httpx.Request("GET", "http://example.com/")
        ctx = RequestContext.from_request(request)
        assert ctx.request_id is None


class TestValidationErrorDetail:
    """Tests for ValidationErrorDetail dataclass."""

    def test_creation(self) -> None:
        """Should create with all fields."""
        detail = ValidationErrorDetail(
            loc=("body", "name"),
            msg="Field required",
            type="missing",
        )
        assert detail.loc == ("body", "name")
        assert detail.msg == "Field required"
        assert detail.type == "missing"

    def test_from_dict(self) -> None:
        """Should create from dictionary."""
        data = {
            "loc": ["body", "config", "timeout"],
            "msg": "Value must be positive",
            "type": "value_error.number.not_gt",
        }
        detail = ValidationErrorDetail.from_dict(data)
        assert detail.loc == ("body", "config", "timeout")
        assert detail.msg == "Value must be positive"
        assert detail.type == "value_error.number.not_gt"

    def test_from_dict_with_missing_fields(self) -> None:
        """Should handle missing fields with defaults."""
        detail = ValidationErrorDetail.from_dict({})
        assert detail.loc == ()
        assert detail.msg == "Unknown error"
        assert detail.type == "unknown"

    def test_from_dict_with_integer_in_loc(self) -> None:
        """Should handle integer indices in loc."""
        data = {
            "loc": ["body", "items", 0, "name"],
            "msg": "Invalid value",
            "type": "value_error",
        }
        detail = ValidationErrorDetail.from_dict(data)
        assert detail.loc == ("body", "items", 0, "name")


class TestBuildErrorMessage:
    """Tests for _build_error_message helper function."""

    def test_returns_status_only_when_no_response(self) -> None:
        """Should return only status code when server_response is None."""
        result = _build_error_message(404, None)
        assert result == "HTTP 404"

    def test_returns_status_only_when_empty_response(self) -> None:
        """Should return only status code when server_response is empty string."""
        result = _build_error_message(500, "")
        assert result == "HTTP 500"

    def test_extracts_detail_from_dict(self) -> None:
        """Should extract 'detail' field from dict response."""
        result = _build_error_message(404, {"detail": "Resource not found"})
        assert result == "HTTP 404: Resource not found"

    def test_uses_full_dict_when_no_detail_key(self) -> None:
        """Should use entire dict when 'detail' key is missing."""
        result = _build_error_message(400, {"error": "Bad request"})
        assert result == "HTTP 400: {'error': 'Bad request'}"

    def test_uses_string_response_directly(self) -> None:
        """Should use string response directly in message."""
        result = _build_error_message(500, "Internal Server Error")
        assert result == "HTTP 500: Internal Server Error"

    def test_handles_nested_detail(self) -> None:
        """Should handle nested structures in detail field."""
        response = {"detail": [{"loc": ["body", "name"], "msg": "Required"}]}
        result = _build_error_message(422, response)
        assert "HTTP 422:" in result
        assert "Required" in result

    def test_handles_various_status_codes(self) -> None:
        """Should work with various HTTP status codes."""
        assert _build_error_message(200, None) == "HTTP 200"
        assert _build_error_message(201, None) == "HTTP 201"
        assert _build_error_message(400, None) == "HTTP 400"
        assert _build_error_message(401, None) == "HTTP 401"
        assert _build_error_message(403, None) == "HTTP 403"
        assert _build_error_message(404, None) == "HTTP 404"
        assert _build_error_message(409, None) == "HTTP 409"
        assert _build_error_message(422, None) == "HTTP 422"
        assert _build_error_message(429, None) == "HTTP 429"
        assert _build_error_message(500, None) == "HTTP 500"
        assert _build_error_message(502, None) == "HTTP 502"
        assert _build_error_message(503, None) == "HTTP 503"


class TestAtlasAPIError:
    """Tests for AtlasAPIError exception."""

    def test_inherits_from_atlas_error(self) -> None:
        """Should inherit from AtlasError."""
        assert issubclass(AtlasAPIError, AtlasError)

    def test_all_attributes(self) -> None:
        """Should expose all attributes."""
        request = httpx.Request(
            "POST",
            "http://example.com/api/test",
            headers={"X-Request-ID": "req-789"},
        )
        response = httpx.Response(500, request=request)

        error = AtlasAPIError(
            "Server error",
            status_code=500,
            request=request,
            response=response,
            server_response={"detail": "Internal error"},
        )

        assert error.message == "Server error"
        assert error.status_code == 500
        assert error.request is request
        assert error.response is response
        assert error.server_response == {"detail": "Internal error"}

    def test_request_context_properties(self) -> None:
        """Should expose request context via properties."""
        request = httpx.Request(
            "DELETE",
            "http://example.com/api/resource/123",
            headers={"X-Request-ID": "req-abc"},
        )
        response = httpx.Response(404, request=request)

        error = AtlasAPIError(
            "Not found",
            status_code=404,
            request=request,
            response=response,
        )

        assert error.request_method == "DELETE"
        assert error.request_url == "http://example.com/api/resource/123"
        assert error.request_id == "req-abc"

    def test_from_response_404(self) -> None:
        """Should create AtlasNotFoundError for 404."""
        request = httpx.Request("GET", "http://test/resource/1")
        response = httpx.Response(
            404,
            request=request,
            json={"detail": "Resource not found"},
        )

        error = AtlasAPIError.from_response(response, request)

        assert isinstance(error, AtlasNotFoundError)
        assert error.status_code == 404

    def test_from_response_400(self) -> None:
        """Should create AtlasValidationError for 400."""
        request = httpx.Request("POST", "http://test/resource")
        response = httpx.Response(
            400,
            request=request,
            json={"detail": "Bad request"},
        )

        error = AtlasAPIError.from_response(response, request)

        assert isinstance(error, AtlasValidationError)
        assert error.status_code == 400

    def test_from_response_422(self) -> None:
        """Should create AtlasValidationError for 422."""
        request = httpx.Request("POST", "http://test/resource")
        response = httpx.Response(
            422,
            request=request,
            json={
                "detail": [
                    {"loc": ["body", "name"], "msg": "Required", "type": "missing"}
                ]
            },
        )

        error = AtlasAPIError.from_response(response, request)

        assert isinstance(error, AtlasValidationError)
        assert error.status_code == 422

    def test_from_response_401(self) -> None:
        """Should create AtlasAuthenticationError for 401."""
        request = httpx.Request("GET", "http://test/protected")
        response = httpx.Response(
            401,
            request=request,
            json={"detail": "Not authenticated"},
        )

        error = AtlasAPIError.from_response(response, request)

        assert isinstance(error, AtlasAuthenticationError)
        assert error.status_code == 401

    def test_from_response_403(self) -> None:
        """Should create AtlasAuthorizationError for 403."""
        request = httpx.Request("DELETE", "http://test/admin/resource")
        response = httpx.Response(
            403,
            request=request,
            json={"detail": "Not authorized"},
        )

        error = AtlasAPIError.from_response(response, request)

        assert isinstance(error, AtlasAuthorizationError)
        assert error.status_code == 403

    def test_from_response_409(self) -> None:
        """Should create AtlasConflictError for 409."""
        request = httpx.Request("POST", "http://test/resource")
        response = httpx.Response(
            409,
            request=request,
            json={"detail": "Resource already exists"},
        )

        error = AtlasAPIError.from_response(response, request)

        assert isinstance(error, AtlasConflictError)
        assert error.status_code == 409

    def test_from_response_429(self) -> None:
        """Should create AtlasRateLimitError for 429."""
        request = httpx.Request("GET", "http://test/resource")
        response = httpx.Response(
            429,
            request=request,
            headers={"Retry-After": "30"},
            json={"detail": "Rate limit exceeded"},
        )

        error = AtlasAPIError.from_response(response, request)

        assert isinstance(error, AtlasRateLimitError)
        assert error.status_code == 429
        assert error.retry_after == 30.0

    def test_from_response_500(self) -> None:
        """Should create AtlasServerError for 500."""
        request = httpx.Request("GET", "http://test/resource")
        response = httpx.Response(
            500,
            request=request,
            json={"detail": "Internal server error"},
        )

        error = AtlasAPIError.from_response(response, request)

        assert isinstance(error, AtlasServerError)
        assert error.status_code == 500

    def test_from_response_503(self) -> None:
        """Should create AtlasServerError for 503."""
        request = httpx.Request("GET", "http://test/resource")
        response = httpx.Response(503, request=request)

        error = AtlasAPIError.from_response(response, request)

        assert isinstance(error, AtlasServerError)
        assert error.status_code == 503

    def test_from_response_unknown_status(self) -> None:
        """Should create base AtlasAPIError for unknown status."""
        request = httpx.Request("GET", "http://test/resource")
        response = httpx.Response(418, request=request)  # I'm a teapot

        error = AtlasAPIError.from_response(response, request)

        assert type(error) is AtlasAPIError
        assert error.status_code == 418

    def test_from_response_with_text_body(self) -> None:
        """Should handle non-JSON response body."""
        request = httpx.Request("GET", "http://test/resource")
        response = httpx.Response(
            500,
            request=request,
            content=b"Internal Server Error",
        )

        error = AtlasAPIError.from_response(response, request)

        assert error.server_response == "Internal Server Error"

    def test_from_response_custom_message(self) -> None:
        """Should use custom message when provided."""
        request = httpx.Request("GET", "http://test/resource")
        response = httpx.Response(404, request=request)

        error = AtlasAPIError.from_response(response, request, "Custom message")

        assert error.message == "Custom message"


class TestAtlasValidationError:
    """Tests for AtlasValidationError exception."""

    def test_inherits_from_atlas_api_error(self) -> None:
        """Should inherit from AtlasAPIError."""
        assert issubclass(AtlasValidationError, AtlasAPIError)

    def test_details_property(self) -> None:
        """Should expose details via property."""
        request = httpx.Request("POST", "http://test/")
        response = httpx.Response(422, request=request)
        details = [
            ValidationErrorDetail(loc=("body", "name"), msg="Required", type="missing")
        ]

        error = AtlasValidationError(
            "Validation failed",
            status_code=422,
            request=request,
            response=response,
            details=details,
        )

        assert error.details == details
        assert len(error.details) == 1
        assert error.details[0].loc == ("body", "name")

    def test_from_response_parses_fastapi_format(self) -> None:
        """Should parse FastAPI validation error format."""
        request = httpx.Request("POST", "http://test/")
        response = httpx.Response(
            422,
            request=request,
            json={
                "detail": [
                    {
                        "loc": ["body", "name"],
                        "msg": "field required",
                        "type": "value_error.missing",
                    },
                    {
                        "loc": ["body", "config", "timeout"],
                        "msg": "value is not a valid integer",
                        "type": "type_error.integer",
                    },
                ]
            },
        )

        error = AtlasValidationError.from_response(response, request)

        assert len(error.details) == 2
        assert error.details[0].loc == ("body", "name")
        assert error.details[0].msg == "field required"
        assert error.details[1].loc == ("body", "config", "timeout")
        assert error.details[1].type == "type_error.integer"

    def test_from_response_with_non_list_detail(self) -> None:
        """Should handle non-list detail in response."""
        request = httpx.Request("POST", "http://test/")
        response = httpx.Response(
            400,
            request=request,
            json={"detail": "Invalid request format"},
        )

        error = AtlasValidationError.from_response(response, request)

        # Should have empty details list when detail is not a list
        assert error.details == []


class TestAtlasRateLimitError:
    """Tests for AtlasRateLimitError exception."""

    def test_inherits_from_atlas_api_error(self) -> None:
        """Should inherit from AtlasAPIError."""
        assert issubclass(AtlasRateLimitError, AtlasAPIError)

    def test_retry_after_property(self) -> None:
        """Should expose retry_after through property."""
        request = httpx.Request("GET", "http://test/")
        response = httpx.Response(429, request=request)

        error = AtlasRateLimitError(
            "Rate limited",
            request=request,
            response=response,
            retry_after=30.0,
        )

        assert error.retry_after == 30.0

    def test_retry_after_none_when_not_provided(self) -> None:
        """retry_after should be None when not provided."""
        request = httpx.Request("GET", "http://test/")
        response = httpx.Response(429, request=request)

        error = AtlasRateLimitError(
            "Rate limited",
            request=request,
            response=response,
        )

        assert error.retry_after is None

    def test_from_response_parses_seconds(self) -> None:
        """from_response should parse numeric Retry-After header."""
        request = httpx.Request("GET", "http://test/")
        response = httpx.Response(
            429,
            request=request,
            headers={"Retry-After": "60"},
        )

        error = AtlasRateLimitError.from_response(response, request, "Rate limited")

        assert error.retry_after == 60.0

    def test_from_response_parses_http_date(self) -> None:
        """from_response should parse HTTP date Retry-After header."""
        request = httpx.Request("GET", "http://test/")

        # Create a date 45 seconds in the future
        future_time = time.time() + 45
        future_date = datetime.fromtimestamp(future_time, tz=timezone.utc)
        http_date = format_datetime(future_date, usegmt=True)

        response = httpx.Response(
            429,
            request=request,
            headers={"Retry-After": http_date},
        )

        error = AtlasRateLimitError.from_response(response, request, "Rate limited")

        # Should be approximately 45 seconds
        assert error.retry_after is not None
        assert 43 <= error.retry_after <= 47

    def test_from_response_none_without_header(self) -> None:
        """from_response should set retry_after to None without header."""
        request = httpx.Request("GET", "http://test/")
        response = httpx.Response(429, request=request)

        error = AtlasRateLimitError.from_response(response, request, "Rate limited")

        assert error.retry_after is None

    def test_from_response_none_with_invalid_header(self) -> None:
        """from_response should set retry_after to None with invalid header."""
        request = httpx.Request("GET", "http://test/")
        response = httpx.Response(
            429,
            request=request,
            headers={"Retry-After": "not-a-number-or-date"},
        )

        error = AtlasRateLimitError.from_response(response, request, "Rate limited")

        assert error.retry_after is None

    def test_from_response_past_date_returns_zero(self) -> None:
        """from_response should return 0 for dates in the past."""
        request = httpx.Request("GET", "http://test/")

        # Create a date 10 seconds in the past
        past_time = time.time() - 10
        past_date = datetime.fromtimestamp(past_time, tz=timezone.utc)
        http_date = format_datetime(past_date, usegmt=True)

        response = httpx.Response(
            429,
            request=request,
            headers={"Retry-After": http_date},
        )

        error = AtlasRateLimitError.from_response(response, request, "Rate limited")

        assert error.retry_after == 0.0


class TestAtlasNotFoundError:
    """Tests for AtlasNotFoundError exception."""

    def test_inherits_from_atlas_api_error(self) -> None:
        """Should inherit from AtlasAPIError."""
        assert issubclass(AtlasNotFoundError, AtlasAPIError)


class TestAtlasConflictError:
    """Tests for AtlasConflictError exception."""

    def test_inherits_from_atlas_api_error(self) -> None:
        """Should inherit from AtlasAPIError."""
        assert issubclass(AtlasConflictError, AtlasAPIError)


class TestAtlasAuthenticationError:
    """Tests for AtlasAuthenticationError exception."""

    def test_inherits_from_atlas_api_error(self) -> None:
        """Should inherit from AtlasAPIError."""
        assert issubclass(AtlasAuthenticationError, AtlasAPIError)


class TestAtlasAuthorizationError:
    """Tests for AtlasAuthorizationError exception."""

    def test_inherits_from_atlas_api_error(self) -> None:
        """Should inherit from AtlasAPIError."""
        assert issubclass(AtlasAuthorizationError, AtlasAPIError)


class TestAtlasServerError:
    """Tests for AtlasServerError exception."""

    def test_inherits_from_atlas_api_error(self) -> None:
        """Should inherit from AtlasAPIError."""
        assert issubclass(AtlasServerError, AtlasAPIError)


class TestAtlasDomainError:
    """Tests for AtlasDomainError exception."""

    def test_inherits_from_atlas_error(self) -> None:
        """Should inherit from AtlasError."""
        assert issubclass(AtlasDomainError, AtlasError)


class TestInvalidBlueprintError:
    """Tests for InvalidBlueprintError exception."""

    def test_inherits_from_atlas_domain_error(self) -> None:
        """Should inherit from AtlasDomainError."""
        assert issubclass(InvalidBlueprintError, AtlasDomainError)

    def test_can_be_raised_with_message(self) -> None:
        """Should be raiseable with a message."""
        with pytest.raises(InvalidBlueprintError) as exc_info:
            raise InvalidBlueprintError("Missing required tool: search")

        assert "Missing required tool: search" in str(exc_info.value)


class TestAgentExecutionError:
    """Tests for AgentExecutionError exception."""

    def test_inherits_from_atlas_domain_error(self) -> None:
        """Should inherit from AtlasDomainError."""
        assert issubclass(AgentExecutionError, AtlasDomainError)

    def test_can_be_raised_with_message(self) -> None:
        """Should be raiseable with a message."""
        with pytest.raises(AgentExecutionError) as exc_info:
            raise AgentExecutionError("Agent exceeded memory limit")

        assert "Agent exceeded memory limit" in str(exc_info.value)


class TestStateTransitionError:
    """Tests for StateTransitionError exception."""

    def test_inherits_from_atlas_domain_error(self) -> None:
        """Should inherit from AtlasDomainError."""
        assert issubclass(StateTransitionError, AtlasDomainError)

    def test_can_be_raised_with_message(self) -> None:
        """Should be raiseable with a message."""
        with pytest.raises(StateTransitionError) as exc_info:
            raise StateTransitionError(
                "Cannot transition from 'completed' to 'pending'"
            )

        assert "Cannot transition from 'completed' to 'pending'" in str(exc_info.value)


class TestAtlasTimeoutError:
    """Tests for AtlasTimeoutError exception."""

    def test_inherits_from_atlas_error(self) -> None:
        """Should inherit from AtlasError."""
        assert issubclass(AtlasTimeoutError, AtlasError)

    def test_can_be_raised_with_message(self) -> None:
        """Should be raiseable with a message."""
        with pytest.raises(AtlasTimeoutError) as exc_info:
            raise AtlasTimeoutError("Operation timed out after 30s")

        assert "Operation timed out after 30s" in str(exc_info.value)

    def test_operation_attribute(self) -> None:
        """Should store operation in attribute."""
        error = AtlasTimeoutError(
            "Timeout",
            operation="wait_for_plan_completion",
            timeout_seconds=300.0,
        )

        assert error.operation == "wait_for_plan_completion"
        assert error.timeout_seconds == 300.0

    def test_last_state_attribute(self) -> None:
        """Should store last_state in attribute."""
        error = AtlasTimeoutError(
            "Plan did not complete",
            operation="wait_for_plan_completion",
            timeout_seconds=300.0,
            last_state={"status": "running", "progress": 75},
        )

        assert error.last_state == {"status": "running", "progress": 75}


class TestAtlasConnectionError:
    """Tests for AtlasConnectionError exception."""

    def test_inherits_from_atlas_error(self) -> None:
        """Should inherit from AtlasError."""
        assert issubclass(AtlasConnectionError, AtlasError)

    def test_can_be_raised_with_message(self) -> None:
        """Should be raiseable with a message."""
        with pytest.raises(AtlasConnectionError) as exc_info:
            raise AtlasConnectionError("Connection refused")

        assert "Connection refused" in str(exc_info.value)

    def test_cause_attribute(self) -> None:
        """Should store cause in attribute."""
        original_error = ConnectionRefusedError("Connection refused")
        error = AtlasConnectionError(
            "Failed to connect to server",
            cause=original_error,
        )

        assert error.cause is original_error
        assert error.__cause__ is original_error


class TestLegacyAliases:
    """Tests for backward compatibility aliases."""

    def test_atlas_http_status_error_is_alias(self) -> None:
        """AtlasHTTPStatusError should be alias for AtlasAPIError."""
        assert AtlasHTTPStatusError is AtlasAPIError

    def test_isinstance_works_with_alias(self) -> None:
        """isinstance should work with the legacy alias."""
        request = httpx.Request("GET", "http://test/")
        response = httpx.Response(500, request=request)

        error = AtlasAPIError.from_response(response, request)

        assert isinstance(error, AtlasHTTPStatusError)


class TestExceptionHierarchy:
    """Tests for the exception hierarchy structure."""

    def test_catching_atlas_error_catches_all(self) -> None:
        """Catching AtlasError should catch all Atlas exceptions."""
        request = httpx.Request("GET", "http://test/")
        response = httpx.Response(404, request=request)

        exceptions_to_test = [
            AtlasNotFoundError(
                "Not found", status_code=404, request=request, response=response
            ),
            AtlasValidationError(
                "Invalid", status_code=422, request=request, response=response
            ),
            AtlasRateLimitError("Limited", request=request, response=response),
            InvalidBlueprintError("Invalid blueprint"),
            AgentExecutionError("Execution failed"),
            StateTransitionError("Invalid transition"),
            AtlasTimeoutError("Timeout"),
            AtlasConnectionError("Connection failed"),
        ]

        for exc in exceptions_to_test:
            assert isinstance(exc, AtlasError), (
                f"{type(exc).__name__} should be AtlasError"
            )

    def test_catching_atlas_api_error_catches_http_errors(self) -> None:
        """Catching AtlasAPIError should catch all HTTP-related errors."""
        request = httpx.Request("GET", "http://test/")
        response = httpx.Response(500, request=request)

        http_exceptions = [
            AtlasNotFoundError(
                "Not found", status_code=404, request=request, response=response
            ),
            AtlasValidationError(
                "Invalid", status_code=422, request=request, response=response
            ),
            AtlasConflictError(
                "Conflict", status_code=409, request=request, response=response
            ),
            AtlasAuthenticationError(
                "Unauthenticated", status_code=401, request=request, response=response
            ),
            AtlasAuthorizationError(
                "Unauthorized", status_code=403, request=request, response=response
            ),
            AtlasRateLimitError("Limited", request=request, response=response),
            AtlasServerError(
                "Server error", status_code=500, request=request, response=response
            ),
        ]

        for exc in http_exceptions:
            assert isinstance(exc, AtlasAPIError), (
                f"{type(exc).__name__} should be AtlasAPIError"
            )

    def test_catching_atlas_domain_error_catches_domain_errors(self) -> None:
        """Catching AtlasDomainError should catch all domain-specific errors."""
        domain_exceptions = [
            InvalidBlueprintError("Invalid blueprint"),
            AgentExecutionError("Execution failed"),
            StateTransitionError("Invalid transition"),
        ]

        for exc in domain_exceptions:
            assert isinstance(exc, AtlasDomainError), (
                f"{type(exc).__name__} should be AtlasDomainError"
            )
