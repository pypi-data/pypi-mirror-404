# Examples

Real-world usage patterns for the Atlas SDK. Each example is a complete use case narrative showing how to accomplish a specific goal.

## Available Examples

### Getting Started

| Example | Description | Topics |
|---------|-------------|--------|
| [Basic CRUD Operations](01_basic_crud.md) | Create, read, update, and delete agent classes and definitions | ControlPlaneClient, models |
| [Deployment Workflow](02_deployment_workflow.md) | Complete deployment pipeline with validation | WorkflowClient, plans, tasks |

### Error Handling & Resilience

| Example | Description | Topics |
|---------|-------------|--------|
| [Robust Error Recovery](03_error_recovery.md) | Handle errors gracefully with recovery strategies | Exceptions, retry |
| [Custom Retry Configuration](04_custom_retry.md) | Customize retry behavior for specific needs | tenacity, backoff |

### Pagination

| Example | Description | Topics |
|---------|-------------|--------|
| [Efficient Pagination](05_pagination.md) | Process large datasets efficiently | paginate, Paginator |
| [Resumable Processing](06_resumable_processing.md) | Pause and resume long-running operations | PaginationState |

### Waiters & Async Operations

| Example | Description | Topics |
|---------|-------------|--------|
| [Waiting for Plan Completion](07_waiters.md) | Monitor and wait for async operations | wait_for_plan_completion |

### Performance & Scalability

| Example | Description | Topics |
|---------|-------------|--------|
| [High-Throughput Configuration](08_connection_pool.md) | Tune connection pools for high concurrency | max_connections |
| [Concurrent Operations](09_concurrent_operations.md) | Run multiple operations in parallel | asyncio.gather |

### Observability

| Example | Description | Topics |
|---------|-------------|--------|
| [OpenTelemetry Integration](10_opentelemetry.md) | Distributed tracing with OpenTelemetry | enable_tracing |
| [Custom Metrics Collection](11_custom_metrics.md) | Collect metrics with custom handlers | MetricsHandler |

### Testing

| Example | Description | Topics |
|---------|-------------|--------|
| [Testing with Mocked Clients](12_testing.md) | Unit test your code using mocked SDK responses | respx, pytest |

## Running the Examples

Most examples can be run directly after installing the SDK:

```bash
# Install the SDK
pip install ryora-atlas-sdk

# Run an example
python examples/01_basic_crud.py
```

Some examples require additional setup (e.g., running Control Plane service). See individual example files for prerequisites.

## Prerequisites

- Python 3.13+
- Atlas SDK installed
- For most examples: Access to a Control Plane instance
- For observability examples: OpenTelemetry packages
