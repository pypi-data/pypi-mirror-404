# Custom Metrics Collection

This example demonstrates how to collect custom metrics from SDK operations.

## Use Case: Application Performance Monitoring

You need to:

- Track request counts by endpoint and status
- Monitor latency distributions
- Alert on error rate spikes
- Integrate with your metrics backend (Prometheus, StatsD, Datadog)

## Prerequisites

- Atlas SDK installed
- Metrics backend (examples show Prometheus and StatsD)

## Complete Example

```python
"""
Example: Custom Metrics Collection
Use Case: Monitor SDK performance in production

This example shows how to:
- Implement the MetricsHandler protocol
- Collect latency, error rate, and throughput metrics
- Integrate with Prometheus and StatsD
- Build composite metrics handlers
"""

import asyncio
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field

from atlas_sdk import ControlPlaneClient
from atlas_sdk.instrumentation import MetricsHandler, RequestMetrics


# =============================================================================
# Basic Logging Metrics
# =============================================================================


class LoggingMetricsHandler(MetricsHandler):
    """Simple metrics handler that logs all requests."""

    def on_request_start(self, method: str, url: str, request_id: str) -> None:
        print(f"[START] {method} {url} (id={request_id})")

    def on_request_end(self, metrics: RequestMetrics) -> None:
        print(
            f"[END] {metrics.method} {metrics.url} "
            f"status={metrics.status_code} "
            f"duration={metrics.duration_seconds:.3f}s"
        )

    def on_request_error(
        self, method: str, url: str, request_id: str, error: Exception
    ) -> None:
        print(f"[ERROR] {method} {url} error={error}")


# =============================================================================
# In-Memory Stats
# =============================================================================


@dataclass
class InMemoryStats(MetricsHandler):
    """
    Collect metrics in memory for testing or small deployments.
    """

    request_count: int = 0
    error_count: int = 0
    total_duration: float = 0.0
    status_counts: dict = field(default_factory=lambda: defaultdict(int))
    endpoint_stats: dict = field(default_factory=lambda: defaultdict(list))

    def on_request_start(self, method: str, url: str, request_id: str) -> None:
        pass  # Nothing to do on start

    def on_request_end(self, metrics: RequestMetrics) -> None:
        self.request_count += 1
        self.total_duration += metrics.duration_seconds
        self.status_counts[metrics.status_code] += 1
        self.endpoint_stats[metrics.url].append(metrics.duration_seconds)

    def on_request_error(
        self, method: str, url: str, request_id: str, error: Exception
    ) -> None:
        self.error_count += 1

    @property
    def avg_latency(self) -> float:
        if self.request_count == 0:
            return 0.0
        return self.total_duration / self.request_count

    @property
    def error_rate(self) -> float:
        total = self.request_count + self.error_count
        if total == 0:
            return 0.0
        return self.error_count / total

    def get_endpoint_p99(self, endpoint: str) -> float:
        """Get p99 latency for an endpoint."""
        durations = sorted(self.endpoint_stats.get(endpoint, []))
        if not durations:
            return 0.0
        idx = int(len(durations) * 0.99)
        return durations[min(idx, len(durations) - 1)]

    def print_summary(self) -> None:
        print("\n=== Metrics Summary ===")
        print(f"Total requests: {self.request_count}")
        print(f"Errors: {self.error_count}")
        print(f"Error rate: {self.error_rate:.2%}")
        print(f"Avg latency: {self.avg_latency:.3f}s")
        print("\nStatus codes:")
        for status, count in sorted(self.status_counts.items()):
            print(f"  {status}: {count}")
        print("\nEndpoint latencies (p99):")
        for endpoint, durations in self.endpoint_stats.items():
            p99 = self.get_endpoint_p99(endpoint)
            print(f"  {endpoint}: {p99:.3f}s")


# =============================================================================
# Prometheus Metrics
# =============================================================================


class PrometheusMetrics(MetricsHandler):
    """
    Export metrics to Prometheus.

    Requires: pip install prometheus-client
    """

    def __init__(self):
        try:
            from prometheus_client import Counter, Histogram, Gauge
        except ImportError:
            raise ImportError("Install prometheus-client: pip install prometheus-client")

        self.request_counter = Counter(
            "atlas_sdk_requests_total",
            "Total SDK requests",
            ["method", "endpoint", "status_code"],
        )

        self.request_latency = Histogram(
            "atlas_sdk_request_duration_seconds",
            "Request duration in seconds",
            ["method", "endpoint"],
            buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
        )

        self.error_counter = Counter(
            "atlas_sdk_errors_total",
            "Total SDK errors",
            ["method", "endpoint", "error_type"],
        )

        self.in_flight = Gauge(
            "atlas_sdk_requests_in_flight",
            "Number of requests currently in flight",
        )

    def on_request_start(self, method: str, url: str, request_id: str) -> None:
        self.in_flight.inc()

    def on_request_end(self, metrics: RequestMetrics) -> None:
        self.in_flight.dec()

        # Extract endpoint from URL
        endpoint = metrics.url.split("?")[0]

        self.request_counter.labels(
            method=metrics.method,
            endpoint=endpoint,
            status_code=str(metrics.status_code),
        ).inc()

        self.request_latency.labels(
            method=metrics.method,
            endpoint=endpoint,
        ).observe(metrics.duration_seconds)

    def on_request_error(
        self, method: str, url: str, request_id: str, error: Exception
    ) -> None:
        self.in_flight.dec()

        endpoint = url.split("?")[0]
        error_type = type(error).__name__

        self.error_counter.labels(
            method=method,
            endpoint=endpoint,
            error_type=error_type,
        ).inc()


# =============================================================================
# StatsD Metrics
# =============================================================================


class StatsdMetrics(MetricsHandler):
    """
    Export metrics to StatsD.

    Requires: pip install statsd
    """

    def __init__(self, host: str = "localhost", port: int = 8125, prefix: str = "atlas_sdk"):
        try:
            import statsd
        except ImportError:
            raise ImportError("Install statsd: pip install statsd")

        self.client = statsd.StatsClient(host, port, prefix=prefix)

    def on_request_start(self, method: str, url: str, request_id: str) -> None:
        self.client.incr("requests.started")

    def on_request_end(self, metrics: RequestMetrics) -> None:
        endpoint = metrics.url.replace("/", ".").strip(".")

        # Count
        self.client.incr(f"requests.{metrics.method}.{metrics.status_code}")
        self.client.incr(f"endpoints.{endpoint}.count")

        # Timing (in milliseconds)
        self.client.timing(
            f"requests.{metrics.method}.latency",
            int(metrics.duration_seconds * 1000),
        )
        self.client.timing(
            f"endpoints.{endpoint}.latency",
            int(metrics.duration_seconds * 1000),
        )

    def on_request_error(
        self, method: str, url: str, request_id: str, error: Exception
    ) -> None:
        error_type = type(error).__name__
        self.client.incr(f"errors.{error_type}")


# =============================================================================
# Composite Handler
# =============================================================================


class CompositeMetricsHandler(MetricsHandler):
    """
    Combine multiple metrics handlers.
    """

    def __init__(self, handlers: list[MetricsHandler]):
        self.handlers = handlers

    def on_request_start(self, method: str, url: str, request_id: str) -> None:
        for handler in self.handlers:
            handler.on_request_start(method, url, request_id)

    def on_request_end(self, metrics: RequestMetrics) -> None:
        for handler in self.handlers:
            handler.on_request_end(metrics)

    def on_request_error(
        self, method: str, url: str, request_id: str, error: Exception
    ) -> None:
        for handler in self.handlers:
            handler.on_request_error(method, url, request_id, error)


# =============================================================================
# Alerting Handler
# =============================================================================


@dataclass
class AlertingMetrics(MetricsHandler):
    """
    Metrics handler that triggers alerts on thresholds.
    """

    error_threshold: int = 10
    latency_threshold: float = 5.0
    on_alert: callable = None

    _error_count: int = field(default=0, init=False)
    _slow_requests: int = field(default=0, init=False)

    def on_request_start(self, method: str, url: str, request_id: str) -> None:
        pass

    def on_request_end(self, metrics: RequestMetrics) -> None:
        if metrics.duration_seconds > self.latency_threshold:
            self._slow_requests += 1
            if self.on_alert:
                self.on_alert(
                    "slow_request",
                    f"{metrics.method} {metrics.url} took {metrics.duration_seconds:.2f}s",
                )

    def on_request_error(
        self, method: str, url: str, request_id: str, error: Exception
    ) -> None:
        self._error_count += 1
        if self._error_count >= self.error_threshold:
            if self.on_alert:
                self.on_alert(
                    "error_threshold",
                    f"Error count reached {self._error_count}",
                )
            self._error_count = 0  # Reset after alert


# =============================================================================
# Main
# =============================================================================


async def main():
    """Demonstrate metrics collection patterns."""

    # Example 1: In-memory stats
    print("=== In-Memory Stats ===\n")
    stats = InMemoryStats()

    async with ControlPlaneClient(
        base_url="http://localhost:8000",
        metrics_handler=stats,
    ) as client:
        # Make some requests
        for _ in range(10):
            await client.health()
        await client.list_agent_classes(limit=10)
        await client.list_model_providers(limit=10)

    stats.print_summary()

    # Example 2: Logging handler
    print("\n=== Logging Handler ===\n")
    async with ControlPlaneClient(
        base_url="http://localhost:8000",
        metrics_handler=LoggingMetricsHandler(),
    ) as client:
        await client.health()
        await client.list_agent_classes(limit=5)

    # Example 3: Composite handler
    print("\n=== Composite Handler ===\n")
    stats2 = InMemoryStats()
    composite = CompositeMetricsHandler([
        LoggingMetricsHandler(),
        stats2,
    ])

    async with ControlPlaneClient(
        base_url="http://localhost:8000",
        metrics_handler=composite,
    ) as client:
        await client.health()

    print(f"\nComposite captured {stats2.request_count} requests")

    # Example 4: Alerting handler
    print("\n=== Alerting Handler ===\n")

    def handle_alert(alert_type: str, message: str):
        print(f"ALERT [{alert_type}]: {message}")

    alerting = AlertingMetrics(
        error_threshold=3,
        latency_threshold=0.001,  # Very low for demo
        on_alert=handle_alert,
    )

    async with ControlPlaneClient(
        base_url="http://localhost:8000",
        metrics_handler=alerting,
    ) as client:
        # These will trigger slow request alerts
        await client.health()
        await client.list_agent_classes(limit=10)


if __name__ == "__main__":
    asyncio.run(main())
```

## Key Points

### MetricsHandler Protocol

Implement these three methods:

```python
class MyMetrics(MetricsHandler):
    def on_request_start(self, method: str, url: str, request_id: str) -> None:
        # Called before request

    def on_request_end(self, metrics: RequestMetrics) -> None:
        # Called after successful request

    def on_request_error(self, method: str, url: str, request_id: str, error: Exception) -> None:
        # Called when request fails
```

### RequestMetrics Fields

| Field | Type | Description |
|-------|------|-------------|
| `method` | str | HTTP method |
| `url` | str | Request URL |
| `request_id` | str | Request correlation ID |
| `status_code` | int | Response status code |
| `duration_seconds` | float | Request duration |
| `request_body_size` | int \| None | Request body size |
| `response_body_size` | int \| None | Response body size |

### Best Practices

1. **Keep handlers fast** - Don't block on metrics export
2. **Use async export** - Queue metrics for background export
3. **Aggregate locally** - Reduce cardinality before export
4. **Use standard naming** - Follow conventions (e.g., Prometheus)
5. **Include dimensions** - Method, endpoint, status for filtering

## Next Steps

- [OpenTelemetry Integration](10_opentelemetry.md) - Add tracing alongside metrics
- [Testing with Mocked Clients](12_testing.md) - Test your metrics handlers
