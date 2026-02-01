# Atlas SDK

Official Python SDK for the Atlas Platform.

## Overview

The Atlas SDK provides a type-safe, async-first Python client for interacting with Atlas platform services. It offers three purpose-specific clients:

| Client | Purpose | Service |
|--------|---------|---------|
| [`ControlPlaneClient`](api/clients/control-plane.md) | Admin/governance operations | Control Plane |
| [`DispatchClient`](api/clients/dispatch.md) | Agent lifecycle management | Dispatch |
| [`WorkflowClient`](api/clients/workflow.md) | Workflow orchestration | Control Plane |

## Features

- **Async/await support** - Built on httpx for modern async Python
- **Automatic retries** - Resilient HTTP client with configurable retry policies
- **Rate limiting** - Automatic backoff respecting Retry-After headers
- **Type annotations** - Full type hints for IDE support and type checking
- **Pydantic models** - Request/response validation with Pydantic v2
- **OpenTelemetry integration** - Optional distributed tracing support
- **Pagination utilities** - Stateful, resumable pagination for large datasets
- **Separation of concerns** - Three focused clients for distinct use cases

## Quick Example

```python
from atlas_sdk import ControlPlaneClient
from atlas_sdk.models import AgentClassCreate

async with ControlPlaneClient(base_url="http://control-plane:8000") as client:
    # Create an agent class
    agent_class = await client.create_agent_class(AgentClassCreate(
        name="BugHunter",
        description="Security vulnerability detection"
    ))
    print(f"Created: {agent_class.name}")
```

## Next Steps

- [Installation](getting-started/installation.md) - Install the SDK
- [Quick Start](getting-started/quickstart.md) - Get up and running in minutes
- [Examples](examples/index.md) - Real-world usage patterns
- [API Reference](api/clients/control-plane.md) - Full API documentation
