"""Instrumentation module for OpenTelemetry integration and metrics hooks.

This module provides optional observability features:
- OpenTelemetry tracing with automatic span creation for HTTP requests
- Metrics hooks for custom metrics collection (request count, latency, errors)

OpenTelemetry Integration:
    The SDK integrates with OpenTelemetry when the optional `opentelemetry-api`
    package is installed. Spans are created automatically for each HTTP request
    with attributes following semantic conventions.

    To enable OpenTelemetry tracing:
    1. Install the optional dependency: `pip install ryora-atlas-sdk[otel]`
    2. Configure your OpenTelemetry tracer provider
    3. Pass `enable_tracing=True` when creating a client

    Example:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import ConsoleSpanExporter

        # Configure OpenTelemetry
        trace.set_tracer_provider(TracerProvider())
        trace.get_tracer_provider().add_span_processor(
            SimpleSpanProcessor(ConsoleSpanExporter())
        )

        # Create client with tracing enabled
        async with ControlPlaneClient(
            base_url="http://control-plane:8000",
            enable_tracing=True,
        ) as client:
            await client.health()  # Automatically traced

Metrics Hooks:
    The SDK exposes hooks for custom metrics collection. Implement the
    `MetricsHandler` protocol to receive callbacks for request lifecycle events.

    Example:
        from atlas_sdk.instrumentation import MetricsHandler, RequestMetrics

        class DatadogMetrics(MetricsHandler):
            def on_request_start(self, method: str, url: str, request_id: str) -> None:
                statsd.increment("atlas_sdk.requests.started")

            def on_request_end(self, metrics: RequestMetrics) -> None:
                statsd.histogram("atlas_sdk.request.duration", metrics.duration_seconds)
                statsd.increment(
                    "atlas_sdk.requests.completed",
                    tags=[f"status:{metrics.status_code}"]
                )

            def on_request_error(
                self, method: str, url: str, request_id: str, error: Exception
            ) -> None:
                statsd.increment("atlas_sdk.requests.errors", tags=[f"error:{type(error).__name__}"])

        # Create client with metrics handler
        async with ControlPlaneClient(
            base_url="http://control-plane:8000",
            metrics_handler=DatadogMetrics(),
        ) as client:
            await client.health()
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from types import TracebackType

# OpenTelemetry imports are optional
_HAS_OPENTELEMETRY = False
try:
    from opentelemetry import context as otel_context  # type: ignore[import-not-found]
    from opentelemetry import trace
    from opentelemetry.trace import SpanKind, Status, StatusCode  # type: ignore[import-not-found]

    _HAS_OPENTELEMETRY = True
except ImportError:
    # OpenTelemetry not installed - tracing will be a no-op
    pass


@dataclass(frozen=True, slots=True)
class RequestMetrics:
    """Metrics collected for a completed HTTP request.

    Attributes:
        method: The HTTP method (GET, POST, etc.).
        url: The request URL path.
        request_id: The X-Request-ID header value.
        status_code: The HTTP response status code.
        duration_seconds: The request duration in seconds.
        request_body_size: Size of the request body in bytes, or None if no body.
        response_body_size: Size of the response body in bytes, or None if unknown.
    """

    method: str
    url: str
    request_id: str
    status_code: int
    duration_seconds: float
    request_body_size: int | None = None
    response_body_size: int | None = None


@runtime_checkable
class MetricsHandler(Protocol):
    """Protocol for custom metrics handlers.

    Implement this protocol to receive callbacks for request lifecycle events.
    All methods are optional - implement only the ones you need.

    The handler methods should be fast and non-blocking. Avoid doing heavy
    I/O or computation in these callbacks as they run synchronously during
    request processing.

    Example:
        class PrometheusMetrics(MetricsHandler):
            def __init__(self) -> None:
                self.request_counter = Counter("atlas_requests_total", "Total requests")
                self.request_duration = Histogram("atlas_request_duration_seconds", "Request duration")

            def on_request_end(self, metrics: RequestMetrics) -> None:
                self.request_counter.labels(
                    method=metrics.method,
                    status=metrics.status_code,
                ).inc()
                self.request_duration.observe(metrics.duration_seconds)
    """

    def on_request_start(self, method: str, url: str, request_id: str) -> None:
        """Called when an HTTP request is about to be sent.

        Args:
            method: The HTTP method (GET, POST, etc.).
            url: The request URL path.
            request_id: The X-Request-ID header value.
        """
        ...

    def on_request_end(self, metrics: RequestMetrics) -> None:
        """Called when an HTTP request completes successfully.

        Args:
            metrics: Metrics collected for the completed request.
        """
        ...

    def on_request_error(
        self, method: str, url: str, request_id: str, error: Exception
    ) -> None:
        """Called when an HTTP request fails with an exception.

        This is called for connection errors, timeouts, and other exceptions
        that prevent the request from completing. It is NOT called for HTTP
        error responses (4xx, 5xx) - those are handled by on_request_end.

        Args:
            method: The HTTP method (GET, POST, etc.).
            url: The request URL path.
            request_id: The X-Request-ID header value.
            error: The exception that caused the failure.
        """
        ...


class NoOpMetricsHandler:
    """A no-op metrics handler that does nothing.

    Used as a default when no metrics handler is configured.
    """

    def on_request_start(self, method: str, url: str, request_id: str) -> None:
        """No-op implementation."""
        pass

    def on_request_end(self, metrics: RequestMetrics) -> None:
        """No-op implementation."""
        pass

    def on_request_error(
        self, method: str, url: str, request_id: str, error: Exception
    ) -> None:
        """No-op implementation."""
        pass


class TracingContext:
    """Context manager for OpenTelemetry span lifecycle.

    Creates and manages a span for an HTTP request. If OpenTelemetry is not
    installed or tracing is disabled, this acts as a no-op context manager.

    The span follows OpenTelemetry HTTP semantic conventions:
    - http.request.method: HTTP method (GET, POST, etc.)
    - url.path: URL path component
    - server.address: Target server host (if available)
    - http.response.status_code: Response status code (set on completion)

    Attributes set on the span:
    - atlas.request_id: The X-Request-ID header value
    - http.request.body.size: Request body size (if present)
    - http.response.body.size: Response body size (if present)

    Example:
        tracer = get_atlas_tracer()
        with TracingContext(tracer, "GET", "/api/health", "req-123") as ctx:
            response = await http_client.get("/api/health")
            ctx.set_response(response.status_code, len(response.content))
    """

    def __init__(
        self,
        tracer: Any,  # Tracer | None - use Any to avoid import errors
        method: str,
        url: str,
        request_id: str,
        request_body_size: int | None = None,
    ) -> None:
        """Initialize the tracing context.

        Args:
            tracer: The OpenTelemetry tracer, or None to disable tracing.
            method: The HTTP method (GET, POST, etc.).
            url: The request URL path.
            request_id: The X-Request-ID header value.
            request_body_size: Size of the request body in bytes, or None.
        """
        self._tracer = tracer
        self._method = method
        self._url = url
        self._request_id = request_id
        self._request_body_size = request_body_size
        self._span: Any = None  # Span | None
        self._token: Any = None  # context token for propagation

    def __enter__(self) -> TracingContext:
        """Start the span."""
        if self._tracer is None or not _HAS_OPENTELEMETRY:
            return self

        # Create span with HTTP client semantic conventions
        self._span = self._tracer.start_span(
            name=f"{self._method} {self._url}",
            kind=SpanKind.CLIENT,
        )

        # Set initial attributes
        self._span.set_attribute("http.request.method", self._method)
        self._span.set_attribute("url.path", self._url)
        self._span.set_attribute("atlas.request_id", self._request_id)

        if self._request_body_size is not None:
            self._span.set_attribute("http.request.body.size", self._request_body_size)

        # Attach span to context for propagation
        self._token = otel_context.attach(trace.set_span_in_context(self._span))

        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """End the span."""
        if self._span is None:
            return

        if exc_val is not None:
            # Record exception and set error status
            self._span.record_exception(exc_val)
            self._span.set_status(Status(StatusCode.ERROR, str(exc_val)))
        else:
            # Set OK status if not already set by set_response
            if self._span.status.status_code == StatusCode.UNSET:
                self._span.set_status(Status(StatusCode.OK))

        self._span.end()

        # Detach context
        if self._token is not None:
            otel_context.detach(self._token)

    def set_response(self, status_code: int, body_size: int | None = None) -> None:
        """Set response attributes on the span.

        Args:
            status_code: The HTTP response status code.
            body_size: Size of the response body in bytes, or None.
        """
        if self._span is None:
            return

        self._span.set_attribute("http.response.status_code", status_code)

        if body_size is not None:
            self._span.set_attribute("http.response.body.size", body_size)

        # Set appropriate status based on status code
        if status_code >= 400:
            self._span.set_status(Status(StatusCode.ERROR, f"HTTP {status_code}"))
        else:
            self._span.set_status(Status(StatusCode.OK))

    def set_attribute(self, key: str, value: Any) -> None:
        """Set an additional attribute on the span.

        Args:
            key: The attribute key.
            value: The attribute value.
        """
        if self._span is not None:
            self._span.set_attribute(key, value)


def get_atlas_tracer(enable: bool = True) -> Any:
    """Get the OpenTelemetry tracer for Atlas SDK.

    Returns a tracer instance if OpenTelemetry is installed and tracing is
    enabled, otherwise returns None.

    Args:
        enable: Whether tracing should be enabled. If False, returns None.

    Returns:
        An OpenTelemetry Tracer instance, or None if tracing is disabled
        or OpenTelemetry is not installed.

    Example:
        tracer = get_atlas_tracer(enable=True)
        if tracer is not None:
            with tracer.start_as_current_span("my-operation"):
                # traced code
                pass
    """
    if not enable or not _HAS_OPENTELEMETRY:
        return None

    return trace.get_tracer("atlas_sdk")


class InstrumentationConfig:
    """Configuration for SDK instrumentation features.

    Holds configuration for OpenTelemetry tracing and metrics collection.
    Pass an instance to BaseClient to enable instrumentation.

    Attributes:
        enable_tracing: Whether to enable OpenTelemetry tracing.
        metrics_handler: Custom metrics handler for request lifecycle events.

    Example:
        from atlas_sdk.instrumentation import InstrumentationConfig, MetricsHandler

        class MyMetrics(MetricsHandler):
            def on_request_end(self, metrics):
                print(f"Request completed in {metrics.duration_seconds}s")

        config = InstrumentationConfig(
            enable_tracing=True,
            metrics_handler=MyMetrics(),
        )

        async with ControlPlaneClient(
            base_url="http://control-plane:8000",
            instrumentation=config,
        ) as client:
            await client.health()
    """

    def __init__(
        self,
        *,
        enable_tracing: bool = False,
        metrics_handler: MetricsHandler | None = None,
    ) -> None:
        """Initialize instrumentation configuration.

        Args:
            enable_tracing: Whether to enable OpenTelemetry tracing.
                Requires the opentelemetry-api package to be installed.
            metrics_handler: Custom handler for metrics collection.
                If None, a no-op handler is used.
        """
        self.enable_tracing = enable_tracing
        self.metrics_handler: MetricsHandler = metrics_handler or NoOpMetricsHandler()
        self._tracer = get_atlas_tracer(enable_tracing)

    @property
    def tracer(self) -> Any:
        """Get the OpenTelemetry tracer.

        Returns:
            The tracer instance if tracing is enabled and OpenTelemetry is
            installed, otherwise None.
        """
        return self._tracer

    def create_tracing_context(
        self,
        method: str,
        url: str,
        request_id: str,
        request_body_size: int | None = None,
    ) -> TracingContext:
        """Create a tracing context for a request.

        Args:
            method: The HTTP method (GET, POST, etc.).
            url: The request URL path.
            request_id: The X-Request-ID header value.
            request_body_size: Size of the request body in bytes, or None.

        Returns:
            A TracingContext that can be used as a context manager.
        """
        return TracingContext(
            self._tracer,
            method,
            url,
            request_id,
            request_body_size,
        )


class RequestTimer:
    """Simple timer for measuring request duration.

    Example:
        timer = RequestTimer()
        timer.start()
        # ... do work ...
        timer.stop()
        print(f"Duration: {timer.duration_seconds}s")
    """

    def __init__(self) -> None:
        """Initialize the timer."""
        self._start_time: float | None = None
        self._end_time: float | None = None

    def start(self) -> None:
        """Start the timer."""
        self._start_time = time.perf_counter()
        self._end_time = None

    def stop(self) -> None:
        """Stop the timer."""
        self._end_time = time.perf_counter()

    @property
    def duration_seconds(self) -> float:
        """Get the elapsed duration in seconds.

        Returns:
            The duration in seconds. If the timer is still running,
            returns the time elapsed since start. If never started,
            returns 0.0.
        """
        if self._start_time is None:
            return 0.0
        end = self._end_time if self._end_time is not None else time.perf_counter()
        return end - self._start_time


def has_opentelemetry() -> bool:
    """Check if OpenTelemetry is available.

    Returns:
        True if the opentelemetry-api package is installed, False otherwise.
    """
    return _HAS_OPENTELEMETRY
