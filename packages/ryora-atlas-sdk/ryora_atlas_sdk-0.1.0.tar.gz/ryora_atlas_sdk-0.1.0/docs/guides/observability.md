# Observability

This guide covers logging, tracing, and metrics in the Atlas SDK.

## Logging

The SDK uses Python's standard `logging` module. All logs are emitted under the `atlas_sdk` logger.

### Enable Debug Logging

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)

# Or just for the SDK
logging.getLogger("atlas_sdk").setLevel(logging.DEBUG)
```

### Log Output

At DEBUG level, the SDK logs:

**Request:**
```
Request: POST /agent-classes request_id=abc-123 body_size=45
```

**Response:**
```
Response: 201 POST /agent-classes request_id=abc-123 duration=0.123s content_type=application/json content_length=256
```

### Structured Logging

For production, use structured logging:

```python
import logging
import json

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        return json.dumps(log_data)

handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logging.getLogger("atlas_sdk").addHandler(handler)
```

### Sensitive Data Masking

The SDK automatically masks sensitive data in logs:

- `api_key`, `apikey`, `api-key`, `x-api-key`
- `authorization`, `bearer`
- `token`, `secret`, `password`, `credential`
- `cookie`, `session`

Masked values appear as `***MASKED***`.

## Request ID Propagation

Every request includes an `X-Request-ID` header for distributed tracing.

### Automatic Generation

By default, a UUID is generated for each request:

```python
# Request ID auto-generated
await client.health()
# Log: Request: GET /health request_id=550e8400-e29b-41d4-a716-446655440000
```

### Custom Request ID

Pass your own request ID for correlation:

```python
# Use custom request ID from upstream
await client.health(request_id="upstream-trace-123")
# Log: Request: GET /health request_id=upstream-trace-123
```

### Correlation Across Services

Pass the same request ID through your service chain:

```python
async def handle_request(upstream_request_id: str):
    async with ControlPlaneClient(base_url="...") as client:
        # Propagate upstream request ID
        agent_class = await client.get_agent_class(
            class_id,
            request_id=upstream_request_id
        )
```

## OpenTelemetry Tracing

The SDK supports optional OpenTelemetry integration for distributed tracing.

### Installation

```bash
pip install ryora-atlas-sdk[otel]
```

### Enable Tracing

```python
from atlas_sdk import ControlPlaneClient

async with ControlPlaneClient(
    base_url="http://control-plane:8000",
    enable_tracing=True,
) as client:
    await client.health()  # Automatically traced
```

### Span Attributes

Each HTTP request creates a span with these attributes:

| Attribute | Description |
|-----------|-------------|
| `http.request.method` | HTTP method (GET, POST, etc.) |
| `url.path` | Request URL path |
| `http.response.status_code` | Response status code |
| `atlas.request_id` | Request ID for correlation |
| `http.request.body.size` | Request body size (if applicable) |
| `http.response.body.size` | Response body size (if available) |

### Configure OpenTelemetry

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

# Set up tracer provider
provider = TracerProvider()
processor = BatchSpanProcessor(OTLPSpanExporter(endpoint="http://otel-collector:4317"))
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

# SDK will now export spans
async with ControlPlaneClient(
    base_url="...",
    enable_tracing=True,
) as client:
    await client.health()
```

### Advanced Configuration

Use `InstrumentationConfig` for full control:

```python
from atlas_sdk.instrumentation import InstrumentationConfig

config = InstrumentationConfig(
    enable_tracing=True,
    metrics_handler=my_metrics_handler,  # Optional
)

async with ControlPlaneClient(
    base_url="...",
    instrumentation=config,
) as client:
    await client.health()
```

## Custom Metrics

Implement `MetricsHandler` to collect custom metrics:

### MetricsHandler Protocol

```python
from atlas_sdk.instrumentation import MetricsHandler, RequestMetrics

class MyMetrics(MetricsHandler):
    def on_request_start(self, method: str, url: str, request_id: str) -> None:
        """Called before each request."""
        pass

    def on_request_end(self, metrics: RequestMetrics) -> None:
        """Called after successful request."""
        pass

    def on_request_error(
        self, method: str, url: str, request_id: str, error: Exception
    ) -> None:
        """Called when request fails."""
        pass
```

### RequestMetrics Fields

| Field | Type | Description |
|-------|------|-------------|
| `method` | str | HTTP method |
| `url` | str | Request URL |
| `request_id` | str | Request ID |
| `status_code` | int | Response status code |
| `duration_seconds` | float | Request duration |
| `request_body_size` | int \| None | Request body size |
| `response_body_size` | int \| None | Response body size |

### Example: Prometheus Metrics

```python
from prometheus_client import Counter, Histogram
from atlas_sdk.instrumentation import MetricsHandler, RequestMetrics

REQUEST_COUNT = Counter(
    "atlas_sdk_requests_total",
    "Total SDK requests",
    ["method", "status_code"]
)
REQUEST_LATENCY = Histogram(
    "atlas_sdk_request_duration_seconds",
    "Request latency",
    ["method"]
)

class PrometheusMetrics(MetricsHandler):
    def on_request_end(self, metrics: RequestMetrics) -> None:
        REQUEST_COUNT.labels(
            method=metrics.method,
            status_code=metrics.status_code
        ).inc()
        REQUEST_LATENCY.labels(method=metrics.method).observe(
            metrics.duration_seconds
        )

    def on_request_error(
        self, method: str, url: str, request_id: str, error: Exception
    ) -> None:
        REQUEST_COUNT.labels(method=method, status_code="error").inc()

# Use with client
async with ControlPlaneClient(
    base_url="...",
    metrics_handler=PrometheusMetrics(),
) as client:
    await client.health()
```

### Example: StatsD Metrics

```python
import statsd
from atlas_sdk.instrumentation import MetricsHandler, RequestMetrics

class StatsdMetrics(MetricsHandler):
    def __init__(self):
        self.client = statsd.StatsClient("localhost", 8125, prefix="atlas_sdk")

    def on_request_end(self, metrics: RequestMetrics) -> None:
        self.client.incr(f"requests.{metrics.method}.{metrics.status_code}")
        self.client.timing(
            f"request_time.{metrics.method}",
            int(metrics.duration_seconds * 1000)
        )

    def on_request_error(
        self, method: str, url: str, request_id: str, error: Exception
    ) -> None:
        self.client.incr(f"requests.{method}.error")
```

## Connection Pool Monitoring

Monitor connection pool health with custom metrics:

```python
from atlas_sdk.instrumentation import MetricsHandler, RequestMetrics

class ConnectionPoolMetrics(MetricsHandler):
    def __init__(self):
        self.active_requests = 0
        self.peak_concurrent = 0

    def on_request_start(self, method: str, url: str, request_id: str) -> None:
        self.active_requests += 1
        self.peak_concurrent = max(self.peak_concurrent, self.active_requests)

    def on_request_end(self, metrics: RequestMetrics) -> None:
        self.active_requests -= 1

    def on_request_error(
        self, method: str, url: str, request_id: str, error: Exception
    ) -> None:
        self.active_requests -= 1
```

## Best Practices

1. **Use request IDs** - Always propagate request IDs for traceability

2. **Enable debug logging in development** - Helps understand SDK behavior

3. **Use structured logging in production** - Easier to query and analyze

4. **Export traces** - Send traces to a collector (Jaeger, Datadog, etc.)

5. **Track key metrics** - Request count, latency, error rate, retry rate

6. **Alert on anomalies** - High error rates, latency spikes, rate limiting

## See Also

- [API Reference: Instrumentation](../api/instrumentation.md) - Full instrumentation API
- [Examples: OpenTelemetry](../examples/index.md#observability) - Tracing examples
