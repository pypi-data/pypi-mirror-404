# OpenTelemetry Integration

This example demonstrates distributed tracing with OpenTelemetry.

## Use Case: Production Observability

You're running the Atlas SDK in a production microservices environment and need:

- Distributed tracing across services
- Correlation with upstream requests
- Visibility into SDK performance
- Integration with your observability platform (Datadog, Jaeger, etc.)

## Prerequisites

- Atlas SDK installed with OpenTelemetry extra: `pip install ryora-atlas-sdk[otel]`
- OpenTelemetry packages configured
- A trace collector (Jaeger, Datadog, etc.)

## Complete Example

```python
"""
Example: OpenTelemetry Integration
Use Case: Production observability with distributed tracing

This example shows how to:
- Enable tracing in the SDK
- Configure OpenTelemetry exporters
- Correlate traces across services
- Add custom attributes to spans
"""

import asyncio
from uuid import UUID

# OpenTelemetry imports
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
)
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes

# For OTLP export (production)
# from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

from atlas_sdk import ControlPlaneClient, WorkflowClient
from atlas_sdk.instrumentation import InstrumentationConfig


# =============================================================================
# OpenTelemetry Setup
# =============================================================================


def setup_tracing(service_name: str = "atlas-sdk-example") -> trace.Tracer:
    """
    Configure OpenTelemetry tracing.

    In production, you'd configure an OTLP exporter to send traces
    to your observability platform (Datadog, Jaeger, etc.).
    """
    # Create a resource identifying your service
    resource = Resource.create({
        ResourceAttributes.SERVICE_NAME: service_name,
        ResourceAttributes.SERVICE_VERSION: "1.0.0",
    })

    # Create tracer provider
    provider = TracerProvider(resource=resource)

    # Add console exporter for demo (use OTLP in production)
    processor = BatchSpanProcessor(ConsoleSpanExporter())
    provider.add_span_processor(processor)

    # For production with OTLP:
    # otlp_exporter = OTLPSpanExporter(endpoint="http://otel-collector:4317")
    # provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

    # Set as global provider
    trace.set_tracer_provider(provider)

    return trace.get_tracer(__name__)


# =============================================================================
# Basic Tracing
# =============================================================================


async def basic_tracing_example():
    """
    Enable tracing with the simple enable_tracing flag.
    """
    print("=== Basic Tracing ===\n")

    async with ControlPlaneClient(
        base_url="http://localhost:8000",
        enable_tracing=True,  # Simply enable tracing
    ) as client:
        # All requests are automatically traced
        await client.health()
        await client.list_agent_classes(limit=10)

    print("\nSpans were automatically created for each request.\n")


# =============================================================================
# Custom Request IDs for Correlation
# =============================================================================


async def correlation_example():
    """
    Use custom request IDs to correlate traces across services.
    """
    print("=== Trace Correlation ===\n")

    async with ControlPlaneClient(
        base_url="http://localhost:8000",
        enable_tracing=True,
    ) as client:
        # Use a request ID from an upstream service
        upstream_request_id = "upstream-service-abc-123"

        result = await client.health(request_id=upstream_request_id)
        print(f"Request traced with ID: {upstream_request_id}")

        # All related operations use the same request ID
        await client.list_agent_classes(limit=10, request_id=upstream_request_id)
        await client.list_model_providers(limit=10, request_id=upstream_request_id)

    print("\nAll spans share the same request_id for correlation.\n")


# =============================================================================
# Parent Span Integration
# =============================================================================


async def parent_span_example(tracer: trace.Tracer):
    """
    Integrate SDK tracing with your application's spans.
    """
    print("=== Parent Span Integration ===\n")

    # Create a parent span for your operation
    with tracer.start_as_current_span("process_workflow") as parent_span:
        parent_span.set_attribute("workflow.type", "data_processing")

        async with ControlPlaneClient(
            base_url="http://localhost:8000",
            enable_tracing=True,
        ) as client:
            # SDK spans are automatically children of the current span
            with tracer.start_as_current_span("fetch_resources"):
                classes = await client.list_agent_classes(limit=10)
                parent_span.set_attribute("workflow.class_count", len(classes))

            with tracer.start_as_current_span("create_deployment"):
                # Your deployment logic here
                await client.health()
                parent_span.set_attribute("workflow.status", "completed")

    print("SDK spans are nested under your application spans.\n")


# =============================================================================
# Instrumentation Config
# =============================================================================


async def full_config_example():
    """
    Use InstrumentationConfig for full control over instrumentation.
    """
    print("=== Full Instrumentation Config ===\n")

    from atlas_sdk.instrumentation import MetricsHandler, RequestMetrics

    class LoggingMetrics(MetricsHandler):
        """Metrics handler that logs request details."""

        def on_request_start(self, method: str, url: str, request_id: str) -> None:
            print(f"  → {method} {url} ({request_id})")

        def on_request_end(self, metrics: RequestMetrics) -> None:
            print(
                f"  ← {metrics.status_code} in {metrics.duration_seconds:.3f}s"
            )

        def on_request_error(
            self, method: str, url: str, request_id: str, error: Exception
        ) -> None:
            print(f"  ✗ Error: {error}")

    # Combine tracing and custom metrics
    config = InstrumentationConfig(
        enable_tracing=True,
        metrics_handler=LoggingMetrics(),
    )

    async with ControlPlaneClient(
        base_url="http://localhost:8000",
        instrumentation=config,
    ) as client:
        await client.health()
        await client.list_agent_classes(limit=5)

    print()


# =============================================================================
# Multi-Service Tracing
# =============================================================================


async def multi_service_example(tracer: trace.Tracer):
    """
    Demonstrate tracing across multiple Atlas services.
    """
    print("=== Multi-Service Tracing ===\n")

    with tracer.start_as_current_span("multi_service_operation") as span:
        span.set_attribute("operation.type", "full_workflow")

        # Use both clients with tracing
        async with (
            ControlPlaneClient(
                base_url="http://localhost:8000",
                enable_tracing=True,
            ) as control_plane,
            WorkflowClient(
                base_url="http://localhost:8000",
                enable_tracing=True,
            ) as workflow,
        ):
            # Control Plane operations
            with tracer.start_as_current_span("admin_operations"):
                classes = await control_plane.list_agent_classes(limit=10)
                span.set_attribute("admin.classes_found", len(classes))

            # Workflow operations
            with tracer.start_as_current_span("workflow_operations"):
                await workflow.health()
                span.set_attribute("workflow.health_checked", True)

    print("Traces show the full flow across both services.\n")


# =============================================================================
# Error Tracing
# =============================================================================


async def error_tracing_example(tracer: trace.Tracer):
    """
    Demonstrate how errors appear in traces.
    """
    print("=== Error Tracing ===\n")

    with tracer.start_as_current_span("operation_with_error") as span:
        async with ControlPlaneClient(
            base_url="http://localhost:8000",
            enable_tracing=True,
        ) as client:
            try:
                # This will fail with 404
                await client.get_agent_class(
                    UUID("00000000-0000-0000-0000-000000000000")
                )
            except Exception as e:
                # Span automatically records the error
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                print(f"Error captured in trace: {type(e).__name__}")

    print("Error details are visible in the trace span.\n")


# =============================================================================
# Production Configuration
# =============================================================================


def production_setup():
    """
    Example production configuration for OTLP export.
    """
    # Uncomment and configure for production:

    # from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    # from opentelemetry.sdk.trace.export import BatchSpanProcessor

    # resource = Resource.create({
    #     ResourceAttributes.SERVICE_NAME: "my-service",
    #     ResourceAttributes.SERVICE_VERSION: os.getenv("VERSION", "unknown"),
    #     ResourceAttributes.DEPLOYMENT_ENVIRONMENT: os.getenv("ENV", "development"),
    # })

    # provider = TracerProvider(resource=resource)

    # # OTLP exporter to collector
    # otlp_exporter = OTLPSpanExporter(
    #     endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4317"),
    # )
    # provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

    # trace.set_tracer_provider(provider)

    print("See code comments for production configuration.\n")


# =============================================================================
# Main
# =============================================================================


async def main():
    """Run all OpenTelemetry examples."""
    # Setup tracing first
    tracer = setup_tracing("atlas-sdk-examples")

    print("OpenTelemetry configured. Traces will be exported to console.\n")
    print("=" * 60)

    # Run examples
    await basic_tracing_example()
    await correlation_example()
    await parent_span_example(tracer)
    await full_config_example()
    await multi_service_example(tracer)
    await error_tracing_example(tracer)

    print("=" * 60)
    print("\nAll examples complete. Check trace output above.")


if __name__ == "__main__":
    asyncio.run(main())
```

## Key Points

### Enabling Tracing

Simple flag:

```python
async with ControlPlaneClient(
    base_url="...",
    enable_tracing=True,
) as client:
    await client.health()  # Automatically traced
```

### Span Attributes

SDK spans include these attributes:

| Attribute | Description |
|-----------|-------------|
| `http.request.method` | GET, POST, etc. |
| `url.path` | Request path |
| `http.response.status_code` | Response status |
| `atlas.request_id` | Request correlation ID |
| `http.request.body.size` | Request size (if applicable) |
| `http.response.body.size` | Response size (if available) |

### Correlation

Use custom request IDs to correlate:

```python
# Pass ID from upstream service
await client.health(request_id="upstream-trace-123")
```

### Parent Spans

SDK spans are children of the current span:

```python
with tracer.start_as_current_span("my_operation"):
    await client.health()  # SDK span is a child
```

### Production Export

```python
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

exporter = OTLPSpanExporter(endpoint="http://otel-collector:4317")
provider.add_span_processor(BatchSpanProcessor(exporter))
```

## Best Practices

1. **Use request IDs** - Correlate traces across service boundaries
2. **Set resource attributes** - Identify service name, version, environment
3. **Use batch processing** - Export spans in batches for efficiency
4. **Handle errors** - Record exceptions in spans for debugging
5. **Sample appropriately** - Use sampling in high-traffic production

## Next Steps

- [Custom Metrics Collection](11_custom_metrics.md) - Add metrics alongside traces
- [High-Throughput Configuration](08_connection_pool.md) - Scale with observability
