# Instrumentation

OpenTelemetry tracing and metrics hooks for observability.

## Overview

The instrumentation module provides:

- **OpenTelemetry integration**: Automatic span creation for HTTP requests
- **Metrics hooks**: Custom handlers for request metrics collection

## Quick Example

### Enable Tracing

```python
from atlas_sdk import ControlPlaneClient

# Simple: enable tracing
async with ControlPlaneClient(
    base_url="http://control-plane:8000",
    enable_tracing=True,
) as client:
    await client.health()  # Automatically traced
```

### Custom Metrics

```python
from atlas_sdk import ControlPlaneClient
from atlas_sdk.instrumentation import MetricsHandler, RequestMetrics

class MyMetrics(MetricsHandler):
    def on_request_start(self, method: str, url: str, request_id: str) -> None:
        print(f"Starting {method} {url}")

    def on_request_end(self, metrics: RequestMetrics) -> None:
        print(f"Completed in {metrics.duration_seconds:.3f}s")

    def on_request_error(
        self, method: str, url: str, request_id: str, error: Exception
    ) -> None:
        print(f"Error: {error}")

async with ControlPlaneClient(
    base_url="http://control-plane:8000",
    metrics_handler=MyMetrics(),
) as client:
    await client.health()
```

## API Reference

::: atlas_sdk.instrumentation
    options:
      show_root_heading: false
      members_order: source
      filters: ["!^_", "!^NoOp"]
