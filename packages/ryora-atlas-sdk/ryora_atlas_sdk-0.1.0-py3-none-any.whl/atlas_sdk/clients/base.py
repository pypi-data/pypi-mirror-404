"""Base client with shared functionality for Atlas SDK clients."""

from __future__ import annotations

import json
import logging
import uuid
from typing import TYPE_CHECKING, Any, Self, TypeVar

from pydantic import BaseModel

import httpx
from tenacity import (
    RetryCallState,
    retry,
    retry_if_exception_type,
    retry_if_result,
    stop_after_attempt,
)

from atlas_sdk._internal.http import parse_retry_after
from atlas_sdk.exceptions import AtlasAPIError, AtlasInputValidationError
from atlas_sdk.instrumentation import (
    InstrumentationConfig,
    MetricsHandler,
    RequestMetrics,
    RequestTimer,
)

if TYPE_CHECKING:
    from atlas_sdk.instrumentation import TracingContext

logger = logging.getLogger(__name__)

# TypeVar for generic model parsing
ModelT = TypeVar("ModelT", bound=BaseModel)

# Sensitive field names that should be masked in logs (case-insensitive matching)
SENSITIVE_KEYS = frozenset(
    {
        "api_key",
        "apikey",
        "api-key",
        "x-api-key",
        "authorization",
        "token",
        "secret",
        "password",
        "credential",
        "cookie",
        "session",
        "bearer",
    }
)


def _mask_sensitive(data: dict[str, Any] | None) -> dict[str, str] | None:
    """Mask sensitive values in a dictionary for safe logging.

    Args:
        data: Dictionary of key-value pairs to potentially mask.

    Returns:
        A new dictionary with sensitive values replaced by '***MASKED***',
        or None if input is None or empty.
    """
    if not data:
        return None
    masked = {}
    for key, value in data.items():
        if key.lower() in SENSITIVE_KEYS:
            masked[key] = "***MASKED***"
        else:
            masked[key] = str(value)
    return masked


def _is_retryable_response(response: httpx.Response) -> bool:
    """Check if response status code indicates a retryable error.

    Retryable status codes:
    - 429: Too Many Requests (rate limited)
    - 502: Bad Gateway
    - 503: Service Unavailable
    - 504: Gateway Timeout
    """
    return response.status_code in [429, 502, 503, 504]


def _get_retry_after_from_response(response: httpx.Response) -> float | None:
    """Extract Retry-After value from a 429 response.

    Args:
        response: The HTTP response to check.

    Returns:
        The number of seconds to wait, or None if not a 429 or no valid header.
    """
    if response.status_code != 429:
        return None

    return parse_retry_after(response.headers.get("retry-after"))


def _wait_with_retry_after(retry_state: RetryCallState) -> float:
    """Custom wait strategy that respects Retry-After header for 429 responses.

    Falls back to exponential backoff (1-10 seconds) for other retryable errors.

    Args:
        retry_state: The current retry state from tenacity.

    Returns:
        Number of seconds to wait before the next retry.
    """
    # Check if the last result was a response with Retry-After header
    if retry_state.outcome is not None and not retry_state.outcome.failed:
        response = retry_state.outcome.result()
        if isinstance(response, httpx.Response):
            retry_after = _get_retry_after_from_response(response)
            if retry_after is not None:
                # Cap Retry-After at 60 seconds to prevent excessive waits
                return min(retry_after, 60.0)

    # Fall back to exponential backoff: min(2^attempt, 10) seconds
    # With multiplier=1, min=1, max=10
    attempt: int = retry_state.attempt_number
    wait_time: float = min(float(2**attempt), 10.0)
    return wait_time


def _return_last_response(retry_state: RetryCallState) -> httpx.Response:
    """Return the last response or re-raise the last exception when retries are exhausted.

    This callback is called when all retry attempts have been exhausted.
    For result-based retries (429, 502, 503, 504), it extracts and returns
    the last response so that normal error handling can process it.
    For exception-based retries (connection errors, timeouts), it re-raises
    the last exception.

    Args:
        retry_state: The current retry state from tenacity.

    Returns:
        The last HTTP response that triggered the retry.

    Raises:
        Exception: The last exception if the retry was due to an exception.
    """
    if retry_state.outcome is not None:
        if not retry_state.outcome.failed:
            # Result-based retry - return the response
            result: httpx.Response = retry_state.outcome.result()
            return result
        else:
            # Exception-based retry - re-raise the exception
            retry_state.outcome.result()  # This will raise the exception

    # Should not reach here, but handle defensively
    raise RuntimeError("Retry exhausted without a valid outcome")


class BaseClient:
    """Base async client with shared functionality for Atlas SDK clients.

    Provides:
    - HTTP client management (httpx.AsyncClient)
    - Connection pool configuration for high-throughput scenarios
    - Context manager support (__aenter__, __aexit__)
    - Retry logic with tenacity (429, 502, 503, 504, connection errors)
    - Rate limiting support with automatic backoff respecting Retry-After header
    - Structured request logging (DEBUG level) with request/response details
    - Request ID propagation via X-Request-ID header for distributed tracing
    - OpenTelemetry tracing integration (optional)
    - Metrics hooks for custom observability
    - Error handling (_raise_for_status)
    - Configurable timeout

    Connection Pool Settings:
    - max_connections: Total connections allowed (default 100)
    - max_keepalive_connections: Idle connections to keep alive (default 20)
    - keepalive_expiry: Seconds before closing idle connections (default 5.0)

    Recommended settings by deployment pattern:
    - **Single-threaded scripts**: Use defaults (100/20/5.0)
    - **High-throughput services** (100+ concurrent requests):
      max_connections=200, max_keepalive_connections=50, keepalive_expiry=30.0
    - **Serverless/Lambda** (short-lived, bursty):
      max_connections=50, max_keepalive_connections=10, keepalive_expiry=5.0
    - **Long-running background workers**:
      max_connections=100, max_keepalive_connections=30, keepalive_expiry=120.0

    Retry behavior:
    - Retries up to 5 times on transient errors
    - For 429 responses: Uses Retry-After header if present (capped at 60s)
    - For other errors: Uses exponential backoff (2^attempt seconds, max 10s)
    - Raises AtlasRateLimitError for 429 responses after retries exhausted

    Logging includes (at DEBUG level):
    - Request: method, URL, request_id, params (if present), body_size (if JSON body)
    - Response: status, method, URL, request_id, duration, content_type, content_length

    Instrumentation:
    - **OpenTelemetry tracing**: Automatic span creation for HTTP requests when enabled.
      Install `opentelemetry-api` and pass `enable_tracing=True` or use an
      `InstrumentationConfig` object.
    - **Metrics hooks**: Custom handlers receive callbacks for request start, end,
      and errors. Pass a `MetricsHandler` implementation via `metrics_handler` or
      `InstrumentationConfig`.

    Args:
        base_url: The base URL of the service to connect to.
        client: Optional pre-configured httpx.AsyncClient instance. If provided,
            connection pool settings are ignored (use the client's own settings).
        timeout: Request timeout in seconds. Defaults to 30.0.
        max_connections: Maximum number of connections in the pool. Defaults to 100.
        max_keepalive_connections: Maximum number of idle keep-alive connections.
            Defaults to 20.
        keepalive_expiry: Seconds to keep idle connections alive. Defaults to 5.0.
        enable_tracing: Enable OpenTelemetry tracing. Defaults to False.
        metrics_handler: Custom handler for metrics collection.
        instrumentation: Full instrumentation configuration. If provided, takes
            precedence over enable_tracing and metrics_handler.

    Example:
        # High-throughput configuration
        async with ControlPlaneClient(
            base_url="http://control-plane:8000",
            max_connections=200,
            max_keepalive_connections=50,
            keepalive_expiry=30.0,
        ) as client:
            # Make many concurrent requests efficiently
            results = await asyncio.gather(*[client.health() for _ in range(100)])

    Example with tracing:
        # Configure OpenTelemetry first (see opentelemetry docs)
        async with ControlPlaneClient(
            base_url="http://control-plane:8000",
            enable_tracing=True,
        ) as client:
            await client.health()  # Automatically traced

    Example with metrics:
        from atlas_sdk.instrumentation import MetricsHandler, RequestMetrics

        class MyMetrics(MetricsHandler):
            def on_request_end(self, metrics: RequestMetrics) -> None:
                print(f"Request {metrics.method} {metrics.url} took {metrics.duration_seconds}s")

        async with ControlPlaneClient(
            base_url="http://control-plane:8000",
            metrics_handler=MyMetrics(),
        ) as client:
            await client.health()
    """

    def __init__(
        self,
        base_url: str,
        client: httpx.AsyncClient | None = None,
        timeout: float = 30.0,
        max_connections: int = 100,
        max_keepalive_connections: int = 20,
        keepalive_expiry: float = 5.0,
        *,
        enable_tracing: bool = False,
        metrics_handler: MetricsHandler | None = None,
        instrumentation: InstrumentationConfig | None = None,
    ) -> None:
        """Initialize the base client.

        Args:
            base_url: The base URL of the service to connect to.
            client: Optional pre-configured httpx.AsyncClient instance. If provided,
                connection pool settings are ignored.
            timeout: Request timeout in seconds. Defaults to 30.0.
            max_connections: Maximum number of connections in the pool. Defaults to 100.
            max_keepalive_connections: Maximum number of idle keep-alive connections.
                Defaults to 20.
            keepalive_expiry: Seconds to keep idle connections alive. Defaults to 5.0.
            enable_tracing: Enable OpenTelemetry tracing. Defaults to False.
                Requires the opentelemetry-api package to be installed.
            metrics_handler: Custom handler for metrics collection.
            instrumentation: Full instrumentation configuration. If provided, takes
                precedence over enable_tracing and metrics_handler.
        """
        self.base_url = base_url.rstrip("/")
        self._client = client
        self._internal_client = False
        self.timeout = timeout
        self._limits = httpx.Limits(
            max_connections=max_connections,
            max_keepalive_connections=max_keepalive_connections,
            keepalive_expiry=keepalive_expiry,
        )

        # Initialize instrumentation
        if instrumentation is not None:
            self._instrumentation = instrumentation
        else:
            self._instrumentation = InstrumentationConfig(
                enable_tracing=enable_tracing,
                metrics_handler=metrics_handler,
            )

    async def __aenter__(self) -> Self:
        """Enter async context manager, creating internal client if needed."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                limits=self._limits,
            )
            self._internal_client = True
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Exit async context manager, closing internal client if owned."""
        if self._internal_client and self._client:
            await self._client.aclose()
            self._client = None
            self._internal_client = False

    async def _ensure_client(self) -> httpx.AsyncClient:
        """Ensure HTTP client is initialized and return it.

        Creates an internal client if one wasn't provided during initialization.

        Returns:
            The initialized HTTP client.
        """
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                limits=self._limits,
            )
            self._internal_client = True
        return self._client

    async def close(self) -> None:
        """Close the HTTP client if internally managed.

        Should be called when not using the client as a context manager.
        """
        if self._internal_client and self._client:
            await self._client.aclose()
            self._client = None

    def _raise_for_status(self, response: httpx.Response) -> None:
        """Raise appropriate Atlas error if response indicates an error.

        Uses the AtlasAPIError.from_response() factory to automatically select
        the appropriate exception subclass based on HTTP status code:
        - 400, 422: AtlasValidationError
        - 401: AtlasAuthenticationError
        - 403: AtlasAuthorizationError
        - 404: AtlasNotFoundError
        - 409: AtlasConflictError
        - 429: AtlasRateLimitError (with retry_after if available)
        - 5xx: AtlasServerError

        Args:
            response: The HTTP response to check.

        Raises:
            AtlasAPIError: (or appropriate subclass) if the response indicates
                an HTTP error. Includes request context (method, URL, request_id)
                and the server response body.
        """
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise AtlasAPIError.from_response(response, e.request) from e

    async def _request(
        self,
        method: str,
        url: str,
        request_id: str | None = None,
        idempotency_key: str | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make an HTTP request with retry logic and instrumentation.

        Automatically retries on:
        - Connection errors (ConnectError, ConnectTimeout, NetworkError)
        - Read timeouts
        - Rate limiting (429) - respects Retry-After header when present
        - Server errors (502, 503, 504)

        When instrumentation is enabled:
        - OpenTelemetry spans are created for request/response cycles
        - Metrics hooks are invoked at request start, end, and on errors

        Args:
            method: HTTP method (GET, POST, PATCH, DELETE, etc.)
            url: URL path (relative to base_url)
            request_id: Optional request ID for distributed tracing. If not
                provided, a UUID will be auto-generated.
            idempotency_key: Optional idempotency key for safe retries of create
                operations. If provided, an ``Idempotency-Key`` header is added
                to the request. Use the special value ``"auto"`` to generate a
                UUID-based key automatically.
            **kwargs: Additional arguments passed to httpx.request()

        Returns:
            httpx.Response: The HTTP response object.
        """
        # Generate request ID if not provided
        if request_id is None:
            request_id = str(uuid.uuid4())

        # Add X-Request-ID header
        headers = kwargs.pop("headers", {}) or {}
        headers["X-Request-ID"] = request_id

        # Add Idempotency-Key header if provided
        if idempotency_key is not None:
            if idempotency_key == "auto":
                idempotency_key = str(uuid.uuid4())
            headers["Idempotency-Key"] = idempotency_key

        kwargs["headers"] = headers

        # Extract request details for structured logging
        params = kwargs.get("params")
        json_body = kwargs.get("json")
        body_size: int | None = None
        if json_body is not None:
            body_size = len(json.dumps(json_body))

        # Build structured request log (with sensitive data masked)
        log_parts = [f"Request: {method} {url}", f"request_id={request_id}"]
        if idempotency_key is not None:
            log_parts.append(f"idempotency_key={idempotency_key}")
        if params:
            log_parts.append(f"params={_mask_sensitive(params)}")
        if body_size is not None:
            log_parts.append(f"body_size={body_size}")

        logger.debug(" ".join(log_parts))

        # Start instrumentation
        timer = RequestTimer()
        timer.start()

        # Notify metrics handler of request start
        self._instrumentation.metrics_handler.on_request_start(method, url, request_id)

        # Create tracing context
        tracing_ctx: TracingContext = self._instrumentation.create_tracing_context(
            method, url, request_id, body_size
        )

        try:
            with tracing_ctx:
                # Execute request with retry
                response = await self._request_with_retry(method, url, **kwargs)

                # Stop timer and calculate duration
                timer.stop()
                duration = timer.duration_seconds

                # Get response body size
                response_body_size: int | None = None
                content_length_header = response.headers.get("content-length")
                if content_length_header:
                    try:
                        response_body_size = int(content_length_header)
                    except ValueError:
                        pass

                # Update tracing context with response info
                tracing_ctx.set_response(response.status_code, response_body_size)

                # Build structured response log
                content_type = response.headers.get("content-type", "")

                resp_log_parts = [
                    f"Response: {response.status_code} {method} {url}",
                    f"request_id={request_id}",
                    f"duration={duration:.3f}s",
                ]
                if content_type:
                    resp_log_parts.append(f"content_type={content_type}")
                if response_body_size is not None:
                    resp_log_parts.append(f"content_length={response_body_size}")

                logger.debug(" ".join(resp_log_parts))

                # Notify metrics handler of request completion
                metrics = RequestMetrics(
                    method=method,
                    url=url,
                    request_id=request_id,
                    status_code=response.status_code,
                    duration_seconds=duration,
                    request_body_size=body_size,
                    response_body_size=response_body_size,
                )
                self._instrumentation.metrics_handler.on_request_end(metrics)

                return response

        except Exception as e:
            # Stop timer on error
            timer.stop()

            # Notify metrics handler of error
            self._instrumentation.metrics_handler.on_request_error(
                method, url, request_id, e
            )

            # Re-raise the exception
            raise

    @retry(
        retry=retry_if_exception_type(
            (
                httpx.ConnectError,
                httpx.ReadTimeout,
                httpx.ConnectTimeout,
                httpx.NetworkError,
            )
        )
        | retry_if_result(_is_retryable_response),
        wait=_wait_with_retry_after,
        stop=stop_after_attempt(5),
        retry_error_callback=_return_last_response,
    )
    async def _request_with_retry(
        self, method: str, url: str, **kwargs: Any
    ) -> httpx.Response:
        """Internal method that performs the actual HTTP request with retry logic.

        This method is wrapped with retry decorators and called by _request().

        Args:
            method: HTTP method (GET, POST, PATCH, DELETE, etc.)
            url: URL path (relative to base_url)
            **kwargs: Additional arguments passed to httpx.request()

        Returns:
            httpx.Response: The HTTP response object.
        """
        client = await self._ensure_client()
        return await client.request(method, url, **kwargs)

    @staticmethod
    def _validate_model(model: Any) -> None:
        """Validate a Pydantic model and raise AtlasInputValidationError on failure.

        This method re-validates a model instance to ensure it meets all
        constraints. It's called automatically before making HTTP requests
        to fail fast with clear error messages.

        Args:
            model: A Pydantic model instance to validate.

        Raises:
            AtlasInputValidationError: If validation fails, with enhanced
                error messages for common cases (UUID, enum, required fields).

        Note:
            This is a static method that can be used by subclasses to validate
            models before sending them to the API.
        """
        from pydantic import BaseModel, ValidationError

        if not isinstance(model, BaseModel):
            return

        try:
            model.model_validate(model.model_dump())
        except ValidationError as e:
            raise AtlasInputValidationError.from_pydantic_error(
                e, model_name=type(model).__name__
            ) from e

    # -------------------------------------------------------------------------
    # HTTP Helper Methods
    # -------------------------------------------------------------------------

    async def _get_one(
        self,
        path: str,
        model: type[ModelT],
        *,
        request_id: str | None = None,
        **kwargs: Any,
    ) -> ModelT:
        """Make a GET request and parse the response as a single model instance.

        Args:
            path: URL path (relative to base_url).
            model: Pydantic model class to parse the response into.
            request_id: Optional request ID for distributed tracing.
            **kwargs: Additional arguments passed to _request() (e.g., params).

        Returns:
            The parsed model instance.

        Raises:
            AtlasAPIError: If the request fails.
        """
        resp = await self._request("GET", path, request_id=request_id, **kwargs)
        self._raise_for_status(resp)
        return model.model_validate(resp.json())

    async def _get_many(
        self,
        path: str,
        model: type[ModelT],
        *,
        request_id: str | None = None,
        **kwargs: Any,
    ) -> list[ModelT]:
        """Make a GET request and parse the response as a list of model instances.

        Args:
            path: URL path (relative to base_url).
            model: Pydantic model class to parse each item into.
            request_id: Optional request ID for distributed tracing.
            **kwargs: Additional arguments passed to _request() (e.g., params).

        Returns:
            List of parsed model instances.

        Raises:
            AtlasAPIError: If the request fails.
        """
        resp = await self._request("GET", path, request_id=request_id, **kwargs)
        self._raise_for_status(resp)
        return [model.model_validate(item) for item in resp.json()]

    async def _post_one(
        self,
        path: str,
        data: BaseModel,
        model: type[ModelT],
        *,
        request_id: str | None = None,
        idempotency_key: str | None = None,
        **kwargs: Any,
    ) -> ModelT:
        """Make a POST request with data and parse the response as a model instance.

        Args:
            path: URL path (relative to base_url).
            data: Pydantic model to serialize and send as JSON body.
            model: Pydantic model class to parse the response into.
            request_id: Optional request ID for distributed tracing.
            idempotency_key: Optional idempotency key for safe retries.
            **kwargs: Additional arguments passed to _request().

        Returns:
            The parsed model instance.

        Raises:
            AtlasAPIError: If the request fails.
        """
        resp = await self._request(
            "POST",
            path,
            request_id=request_id,
            idempotency_key=idempotency_key,
            json=data.model_dump(exclude_unset=True, mode="json"),
            **kwargs,
        )
        self._raise_for_status(resp)
        return model.model_validate(resp.json())

    async def _patch_one(
        self,
        path: str,
        data: BaseModel,
        model: type[ModelT],
        *,
        request_id: str | None = None,
        **kwargs: Any,
    ) -> ModelT:
        """Make a PATCH request with data and parse the response as a model instance.

        Args:
            path: URL path (relative to base_url).
            data: Pydantic model to serialize and send as JSON body.
            model: Pydantic model class to parse the response into.
            request_id: Optional request ID for distributed tracing.
            **kwargs: Additional arguments passed to _request().

        Returns:
            The parsed model instance.

        Raises:
            AtlasAPIError: If the request fails.
        """
        resp = await self._request(
            "PATCH",
            path,
            request_id=request_id,
            json=data.model_dump(exclude_unset=True, mode="json"),
            **kwargs,
        )
        self._raise_for_status(resp)
        return model.model_validate(resp.json())

    async def _delete(
        self,
        path: str,
        *,
        request_id: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Make a DELETE request.

        Args:
            path: URL path (relative to base_url).
            request_id: Optional request ID for distributed tracing.
            **kwargs: Additional arguments passed to _request().

        Raises:
            AtlasAPIError: If the request fails.
        """
        resp = await self._request("DELETE", path, request_id=request_id, **kwargs)
        self._raise_for_status(resp)
