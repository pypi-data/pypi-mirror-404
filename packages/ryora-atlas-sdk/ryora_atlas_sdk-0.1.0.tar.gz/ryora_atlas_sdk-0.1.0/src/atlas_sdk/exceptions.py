"""Atlas SDK exceptions with semantic hierarchy.

This module provides a comprehensive exception hierarchy for the Atlas SDK:

    AtlasError (base)
    ├── AtlasAPIError (all HTTP errors)
    │   ├── AtlasNotFoundError (404)
    │   ├── AtlasValidationError (400, 422)
    │   ├── AtlasConflictError (409)
    │   ├── AtlasAuthenticationError (401)
    │   ├── AtlasAuthorizationError (403)
    │   ├── AtlasRateLimitError (429)
    │   └── AtlasServerError (500-599)
    ├── AtlasDomainError (business logic)
    │   ├── InvalidBlueprintError
    │   ├── AgentExecutionError
    │   └── StateTransitionError
    ├── AtlasTimeoutError (request/polling timeout)
    └── AtlasConnectionError (network failures)

All API errors include request context (method, URL, request_id) for debugging.
ValidationError exposes structured details with field paths.
RateLimitError includes retry_after when available.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from atlas_sdk._internal.http import parse_retry_after


class AtlasError(Exception):
    """Base exception for all Atlas SDK errors.

    This is the root of the Atlas exception hierarchy. Catching this
    exception will catch all Atlas-specific errors.

    Attributes:
        message: Human-readable error message.
    """

    def __init__(self, message: str) -> None:
        """Initialize the error.

        Args:
            message: Human-readable error message.
        """
        self.message = message
        super().__init__(message)


@dataclass
class ValidationErrorDetail:
    """Structured detail for a validation error.

    Follows the standard format used by FastAPI/Pydantic validation errors.

    Attributes:
        loc: Field path as a tuple (e.g., ("body", "name") or ("query", "limit")).
        msg: Human-readable error message.
        type: Error type identifier (e.g., "value_error", "type_error.integer").
    """

    loc: tuple[str | int, ...]
    msg: str
    type: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ValidationErrorDetail:
        """Create a ValidationErrorDetail from a dictionary.

        Args:
            data: Dictionary with 'loc', 'msg', and 'type' keys.

        Returns:
            A ValidationErrorDetail instance.
        """
        loc = data.get("loc", ())
        if isinstance(loc, list):
            loc = tuple(loc)
        return cls(
            loc=loc,
            msg=data.get("msg", "Unknown error"),
            type=data.get("type", "unknown"),
        )


@dataclass
class RequestContext:
    """Context about the HTTP request that triggered an error.

    Attributes:
        method: HTTP method (GET, POST, etc.).
        url: Full request URL.
        request_id: X-Request-ID header value for distributed tracing.
    """

    method: str
    url: str
    request_id: str | None = None

    @classmethod
    def from_request(cls, request: httpx.Request) -> RequestContext:
        """Create RequestContext from an httpx.Request.

        Args:
            request: The HTTP request object.

        Returns:
            A RequestContext instance.
        """
        request_id = request.headers.get("X-Request-ID")
        return cls(
            method=request.method,
            url=str(request.url),
            request_id=request_id,
        )


class AtlasAPIError(AtlasError):
    """Base exception for all HTTP API errors.

    All HTTP errors (4xx, 5xx) are represented by subclasses of this exception.
    Includes request context for debugging and the original httpx objects.

    Attributes:
        message: Human-readable error message.
        status_code: HTTP status code.
        request: The httpx.Request that triggered the error.
        response: The httpx.Response containing the error.
        request_context: Structured request context (method, URL, request_id).
        server_response: Parsed server response body (dict or string).
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        request: httpx.Request,
        response: httpx.Response,
        server_response: dict[str, Any] | str | None = None,
    ) -> None:
        """Initialize the API error.

        Args:
            message: Human-readable error message.
            status_code: HTTP status code.
            request: The httpx.Request that triggered the error.
            response: The httpx.Response containing the error.
            server_response: Parsed server response body.
        """
        self.status_code = status_code
        self.request = request
        self.response = response
        self.request_context = RequestContext.from_request(request)
        self.server_response = server_response
        super().__init__(message)

    @property
    def request_method(self) -> str:
        """HTTP method of the request that triggered this error."""
        return self.request_context.method

    @property
    def request_url(self) -> str:
        """URL of the request that triggered this error."""
        return self.request_context.url

    @property
    def request_id(self) -> str | None:
        """X-Request-ID header value for distributed tracing."""
        return self.request_context.request_id

    @classmethod
    def from_response(
        cls,
        response: httpx.Response,
        request: httpx.Request,
        message: str | None = None,
    ) -> AtlasAPIError:
        """Create an appropriate AtlasAPIError subclass from an HTTP response.

        This factory method inspects the status code and returns the appropriate
        exception subclass (NotFoundError, ValidationError, etc.).

        Args:
            response: The HTTP response containing the error.
            request: The HTTP request that triggered the error.
            message: Optional custom error message. If not provided, a default
                message is generated from the response.

        Returns:
            An appropriate AtlasAPIError subclass instance.
        """
        status_code = response.status_code

        # Parse server response
        server_response: dict[str, Any] | str | None = None
        try:
            server_response = response.json()
        except Exception:
            server_response = response.text or None

        # Build default message if not provided
        if message is None:
            message = _build_error_message(status_code, server_response)

        # Select appropriate exception class based on status code
        exception_class: type[AtlasAPIError]
        if status_code == 401:
            exception_class = AtlasAuthenticationError
        elif status_code == 403:
            exception_class = AtlasAuthorizationError
        elif status_code == 404:
            exception_class = AtlasNotFoundError
        elif status_code == 409:
            exception_class = AtlasConflictError
        elif status_code == 429:
            # RateLimitError has special handling for Retry-After
            return AtlasRateLimitError.from_response(response, request, message)
        elif status_code in (400, 422):
            return AtlasValidationError.from_response(response, request, message)
        elif 500 <= status_code < 600:
            exception_class = AtlasServerError
        else:
            exception_class = AtlasAPIError

        return exception_class(
            message,
            status_code=status_code,
            request=request,
            response=response,
            server_response=server_response,
        )


class AtlasNotFoundError(AtlasAPIError):
    """Raised when the requested resource was not found (HTTP 404).

    This typically occurs when:
    - Requesting a resource by ID that doesn't exist
    - The resource was deleted
    - The URL path is incorrect
    """

    pass


class AtlasValidationError(AtlasAPIError):
    """Raised when request validation fails (HTTP 400 or 422).

    Provides structured access to validation errors via the `details` property,
    which contains a list of ValidationErrorDetail objects with field paths.

    Attributes:
        details: List of ValidationErrorDetail objects describing each error.

    Example:
        try:
            await client.create_agent_class(AgentClassCreate(name=""))
        except AtlasValidationError as e:
            for detail in e.details:
                print(f"Field {'.'.join(str(p) for p in detail.loc)}: {detail.msg}")
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        request: httpx.Request,
        response: httpx.Response,
        server_response: dict[str, Any] | str | None = None,
        details: list[ValidationErrorDetail] | None = None,
    ) -> None:
        """Initialize the validation error.

        Args:
            message: Human-readable error message.
            status_code: HTTP status code (400 or 422).
            request: The httpx.Request that triggered the error.
            response: The httpx.Response containing the error.
            server_response: Parsed server response body.
            details: List of structured validation error details.
        """
        super().__init__(
            message,
            status_code=status_code,
            request=request,
            response=response,
            server_response=server_response,
        )
        self._details = details or []

    @property
    def details(self) -> list[ValidationErrorDetail]:
        """List of structured validation error details.

        Each detail contains:
        - loc: Field path tuple (e.g., ("body", "config", "timeout"))
        - msg: Human-readable error message
        - type: Error type identifier
        """
        return self._details

    @classmethod
    def from_response(
        cls,
        response: httpx.Response,
        request: httpx.Request,
        message: str | None = None,
    ) -> "AtlasValidationError":
        """Create an AtlasValidationError from an HTTP response.

        Parses the FastAPI/Pydantic validation error format to extract
        structured error details.

        Args:
            response: The HTTP response containing the error.
            request: The HTTP request that triggered the error.
            message: Optional error message. If not provided, a default
                message is generated from the response.

        Returns:
            An AtlasValidationError with parsed details.
        """
        # Parse server response
        server_response: dict[str, Any] | str | None = None
        try:
            server_response = response.json()
        except Exception:
            server_response = response.text or None

        # Build default message if not provided
        if message is None:
            message = _build_error_message(response.status_code, server_response)

        details: list[ValidationErrorDetail] = []

        if isinstance(server_response, dict):
            # FastAPI returns validation errors in "detail" field
            detail_data = server_response.get("detail")
            if isinstance(detail_data, list):
                for item in detail_data:
                    if isinstance(item, dict):
                        details.append(ValidationErrorDetail.from_dict(item))

        return cls(
            message,
            status_code=response.status_code,
            request=request,
            response=response,
            server_response=server_response,
            details=details,
        )


class AtlasConflictError(AtlasAPIError):
    """Raised when there's a conflict with the current state (HTTP 409).

    This typically occurs when:
    - Creating a resource that already exists
    - Updating a resource with stale data (optimistic locking)
    - Attempting an operation that violates uniqueness constraints
    """

    pass


class AtlasAuthenticationError(AtlasAPIError):
    """Raised when authentication fails (HTTP 401).

    This typically occurs when:
    - API key is missing or invalid
    - Token has expired
    - Credentials are incorrect
    """

    pass


class AtlasAuthorizationError(AtlasAPIError):
    """Raised when the user lacks permission (HTTP 403).

    This typically occurs when:
    - User doesn't have access to the requested resource
    - Operation is not allowed for the user's role
    - Resource is restricted
    """

    pass


class AtlasRateLimitError(AtlasAPIError):
    """Raised when rate limit is exceeded (HTTP 429).

    Includes the recommended wait time from the Retry-After header when available.

    Attributes:
        retry_after: Number of seconds to wait before retrying, or None if unknown.

    Example:
        try:
            await client.list_deployments()
        except AtlasRateLimitError as e:
            if e.retry_after:
                await asyncio.sleep(e.retry_after)
                # Retry the request
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int = 429,
        request: httpx.Request,
        response: httpx.Response,
        server_response: dict[str, Any] | str | None = None,
        retry_after: float | None = None,
    ) -> None:
        """Initialize the rate limit error.

        Args:
            message: Human-readable error message.
            status_code: HTTP status code (always 429).
            request: The httpx.Request that triggered the error.
            response: The httpx.Response containing the error.
            server_response: Parsed server response body.
            retry_after: Number of seconds to wait before retrying.
        """
        super().__init__(
            message,
            status_code=status_code,
            request=request,
            response=response,
            server_response=server_response,
        )
        self._retry_after = retry_after

    @property
    def retry_after(self) -> float | None:
        """Number of seconds to wait before retrying, or None if unknown."""
        return self._retry_after

    @classmethod
    def from_response(
        cls,
        response: httpx.Response,
        request: httpx.Request,
        message: str | None = None,
    ) -> "AtlasRateLimitError":
        """Create an AtlasRateLimitError from an HTTP response.

        Parses the Retry-After header if present. The header can be either:
        - A number of seconds (e.g., "120")
        - An HTTP date (e.g., "Wed, 21 Oct 2015 07:28:00 GMT")

        Args:
            response: The HTTP response containing the 429 status.
            request: The HTTP request that triggered the error.
            message: Optional error message. If not provided, a default
                message is generated from the response.

        Returns:
            An AtlasRateLimitError with retry_after parsed from the header.
        """
        retry_after = parse_retry_after(response.headers.get("retry-after"))

        # Parse server response
        server_response: dict[str, Any] | str | None = None
        try:
            server_response = response.json()
        except Exception:
            server_response = response.text or None

        # Build default message if not provided
        if message is None:
            message = _build_error_message(response.status_code, server_response)

        return cls(
            message,
            status_code=429,
            request=request,
            response=response,
            server_response=server_response,
            retry_after=retry_after,
        )


class AtlasServerError(AtlasAPIError):
    """Raised when the server encounters an error (HTTP 5xx).

    This typically indicates a problem on the server side:
    - 500: Internal Server Error
    - 502: Bad Gateway
    - 503: Service Unavailable
    - 504: Gateway Timeout

    These errors may be transient and the SDK's retry logic may handle them
    automatically before this exception is raised.
    """

    pass


class AtlasDomainError(AtlasError):
    """Base exception for business logic errors.

    These errors represent domain-specific failures that are not HTTP-related,
    such as invalid agent configurations or state machine violations.
    """

    pass


class InvalidBlueprintError(AtlasDomainError):
    """Raised when an agent blueprint is invalid or incomplete.

    This occurs when:
    - Required blueprint components are missing
    - Blueprint references non-existent resources
    - Blueprint configuration is internally inconsistent
    """

    pass


class AgentExecutionError(AtlasDomainError):
    """Raised when an agent execution fails.

    This occurs when:
    - Agent crashes during execution
    - Agent exceeds resource limits
    - Agent produces invalid output
    """

    pass


class StateTransitionError(AtlasDomainError):
    """Raised when an invalid state transition is attempted.

    This occurs when:
    - Attempting to transition a resource to an invalid state
    - Resource is in a terminal state and cannot be modified
    - State machine constraints are violated
    """

    pass


class AtlasTimeoutError(AtlasError):
    """Raised when an operation times out.

    This can occur during:
    - HTTP request timeout (network level)
    - Polling operations (wait_for_plan_completion, wait_for_task_completion)
    - Long-running operations that exceed configured timeout

    Attributes:
        operation: Description of the operation that timed out.
        timeout_seconds: The timeout value that was exceeded.
        last_state: The last known state before timeout (for polling operations).
    """

    def __init__(
        self,
        message: str,
        *,
        operation: str | None = None,
        timeout_seconds: float | None = None,
        last_state: Any = None,
    ) -> None:
        """Initialize the timeout error.

        Args:
            message: Human-readable error message.
            operation: Description of the operation that timed out.
            timeout_seconds: The timeout value that was exceeded.
            last_state: The last known state before timeout.
        """
        super().__init__(message)
        self.operation = operation
        self.timeout_seconds = timeout_seconds
        self.last_state = last_state


class AtlasConnectionError(AtlasError):
    """Raised when a network connection fails.

    This occurs when:
    - Cannot connect to the server
    - DNS resolution fails
    - Connection is refused
    - Network is unreachable

    Attributes:
        cause: The underlying exception that caused the connection failure.
    """

    def __init__(
        self,
        message: str,
        *,
        cause: Exception | None = None,
    ) -> None:
        """Initialize the connection error.

        Args:
            message: Human-readable error message.
            cause: The underlying exception.
        """
        super().__init__(message)
        self.cause = cause
        if cause:
            self.__cause__ = cause


@dataclass
class InputValidationErrorDetail:
    """Structured detail for an input validation error.

    Used for client-side validation errors that occur before making HTTP requests.

    Attributes:
        loc: Field path as a tuple (e.g., ("agent_class_id",) or ("config", "timeout")).
        msg: Human-readable error message.
        type: Error type identifier (e.g., "uuid_parsing", "enum_invalid", "missing").
        input: The invalid input value (if available).
    """

    loc: tuple[str | int, ...]
    msg: str
    type: str
    input: Any = None

    def __str__(self) -> str:
        """Return a human-readable string representation."""
        path = ".".join(str(p) for p in self.loc) if self.loc else "<root>"
        return f"{path}: {self.msg}"


class AtlasInputValidationError(AtlasError):
    """Raised when client-side input validation fails before making an HTTP request.

    This error is raised immediately when invalid data is detected, without
    making a network round-trip. This enables fail-fast behavior and provides
    clear error messages with field paths pointing to the problematic data.

    Unlike AtlasValidationError (which is raised for HTTP 400/422 responses),
    this error occurs entirely on the client side.

    Attributes:
        details: List of InputValidationErrorDetail objects describing each error.
        model_name: The name of the Pydantic model that failed validation.

    Example:
        try:
            await client.create_agent_definition(AgentDefinitionCreate(
                agent_class_id="not-a-uuid",  # Invalid UUID
                name="test"
            ))
        except AtlasInputValidationError as e:
            for detail in e.details:
                print(f"Field {detail}: {detail.msg}")
            # Output: agent_class_id: Invalid UUID format. Expected a UUID like
            #         '123e4567-e89b-12d3-a456-426614174000', got 'not-a-uuid'.
    """

    def __init__(
        self,
        message: str,
        *,
        details: list[InputValidationErrorDetail] | None = None,
        model_name: str | None = None,
    ) -> None:
        """Initialize the input validation error.

        Args:
            message: Human-readable error message.
            details: List of structured validation error details.
            model_name: The name of the Pydantic model that failed validation.
        """
        super().__init__(message)
        self._details = details or []
        self.model_name = model_name

    @property
    def details(self) -> list[InputValidationErrorDetail]:
        """List of structured validation error details.

        Each detail contains:
        - loc: Field path tuple (e.g., ("config", "timeout"))
        - msg: Human-readable error message
        - type: Error type identifier
        - input: The invalid input value
        """
        return self._details

    @classmethod
    def from_pydantic_error(
        cls,
        error: Exception,
        *,
        model_name: str | None = None,
    ) -> "AtlasInputValidationError":
        """Create an AtlasInputValidationError from a Pydantic ValidationError.

        Transforms Pydantic's validation error format into Atlas's format with
        enhanced error messages for common cases (UUID, enum, required fields).

        Args:
            error: A Pydantic ValidationError instance.
            model_name: Optional name of the model that failed validation.

        Returns:
            An AtlasInputValidationError with parsed details.
        """
        from pydantic import ValidationError

        details: list[InputValidationErrorDetail] = []

        if isinstance(error, ValidationError):
            for err in error.errors():
                loc = tuple(err.get("loc", ()))
                error_type = err.get("type", "unknown")
                original_msg = err.get("msg", "Validation error")
                input_value = err.get("input")

                # Enhance error messages for common cases
                msg = _enhance_validation_message(error_type, original_msg, input_value)

                details.append(
                    InputValidationErrorDetail(
                        loc=loc,
                        msg=msg,
                        type=error_type,
                        input=input_value,
                    )
                )

        # Build summary message
        if details:
            if len(details) == 1:
                message = f"Validation failed: {details[0]}"
            else:
                message = f"Validation failed with {len(details)} errors"
                if model_name:
                    message = (
                        f"{model_name} validation failed with {len(details)} errors"
                    )
        else:
            message = str(error)

        return cls(message, details=details, model_name=model_name)


def _build_error_message(
    status_code: int, server_response: dict[str, Any] | str | None
) -> str:
    """Build a default error message from HTTP status code and server response.

    This helper extracts the 'detail' field from dict responses or uses the
    response text directly for string responses.

    Args:
        status_code: HTTP status code.
        server_response: Parsed server response body (dict, string, or None).

    Returns:
        A formatted error message like "HTTP 404: Resource not found".
    """
    if not server_response:
        return f"HTTP {status_code}"

    if isinstance(server_response, dict):
        detail = server_response.get("detail", server_response)
        return f"HTTP {status_code}: {detail}"

    return f"HTTP {status_code}: {server_response}"


def _enhance_validation_message(
    error_type: str, original_msg: str, input_value: Any
) -> str:
    """Enhance Pydantic error messages with more helpful context.

    Args:
        error_type: The Pydantic error type (e.g., "uuid_parsing", "enum").
        original_msg: The original error message from Pydantic.
        input_value: The invalid input value.

    Returns:
        An enhanced error message with more context.
    """
    # UUID parsing errors
    if error_type == "uuid_parsing":
        if input_value is not None:
            return (
                f"Invalid UUID format. Expected a UUID like "
                f"'123e4567-e89b-12d3-a456-426614174000', got {input_value!r}."
            )
        return "Invalid UUID format. Expected a UUID like '123e4567-e89b-12d3-a456-426614174000'."

    # Enum errors
    if error_type == "enum":
        # Try to extract valid options from the message
        # Pydantic format: "Input should be 'opt1', 'opt2' or 'opt3'"
        return original_msg

    # Missing required field
    if error_type == "missing":
        return "This field is required."

    # String type errors
    if error_type == "string_type":
        if input_value is not None:
            return (
                f"Expected a string, got {type(input_value).__name__}: {input_value!r}."
            )
        return "Expected a string value."

    # Integer type errors
    if error_type == "int_type":
        if input_value is not None:
            return f"Expected an integer, got {type(input_value).__name__}: {input_value!r}."
        return "Expected an integer value."

    # Boolean type errors
    if error_type == "bool_type":
        if input_value is not None:
            return f"Expected a boolean, got {type(input_value).__name__}: {input_value!r}."
        return "Expected a boolean value."

    # List type errors
    if error_type == "list_type":
        if input_value is not None:
            return (
                f"Expected a list, got {type(input_value).__name__}: {input_value!r}."
            )
        return "Expected a list value."

    # Dict type errors
    if error_type == "dict_type":
        if input_value is not None:
            return f"Expected a dictionary, got {type(input_value).__name__}: {input_value!r}."
        return "Expected a dictionary value."

    # Default: return original message
    return original_msg


# Legacy aliases for backward compatibility
# AtlasHTTPStatusError was renamed to AtlasAPIError in 0.2.0
# It will be removed in 0.4.0 (2 minor versions after deprecation)
#
# This is a direct alias for full backward compatibility. Deprecation warnings
# are emitted by the main atlas_sdk package when users import this name.
AtlasHTTPStatusError = AtlasAPIError


__all__ = [
    # Base
    "AtlasError",
    # API errors
    "AtlasAPIError",
    "AtlasNotFoundError",
    "AtlasValidationError",
    "AtlasConflictError",
    "AtlasAuthenticationError",
    "AtlasAuthorizationError",
    "AtlasRateLimitError",
    "AtlasServerError",
    # Domain errors
    "AtlasDomainError",
    "InvalidBlueprintError",
    "AgentExecutionError",
    "StateTransitionError",
    # Other errors
    "AtlasTimeoutError",
    "AtlasConnectionError",
    "AtlasInputValidationError",
    # Supporting types
    "ValidationErrorDetail",
    "RequestContext",
    "InputValidationErrorDetail",
    # Legacy aliases
    "AtlasHTTPStatusError",
]
