# Atlas SDK

Official Python SDK for the Atlas Platform.

## Installation

```bash
pip install ryora-atlas-sdk
```

## Clients

The SDK provides three purpose-specific clients:

| Client | Purpose | Service |
|--------|---------|---------|
| `ControlPlaneClient` | Admin/governance operations | Control Plane |
| `DispatchClient` | Agent lifecycle management | Dispatch |
| `WorkflowClient` | Workflow orchestration | Control Plane |

## Quick Start

### ControlPlaneClient (Admin/Governance)

Use this client for system administration and CI/CD pipelines managing Atlas configuration.

```python
from atlas_sdk import ControlPlaneClient
from atlas_sdk.models import AgentClassCreate, ModelProviderCreate

async with ControlPlaneClient(base_url="http://control-plane:8000") as client:
    # Create a model provider
    provider = await client.create_model_provider(ModelProviderCreate(
        name="openai-prod",
        api_base_url="https://api.openai.com/v1"
    ))

    # Create an agent class
    agent_class = await client.create_agent_class(AgentClassCreate(
        name="BugHunter",
        description="Security vulnerability detection"
    ))

    # List all agent definitions
    definitions = await client.list_agent_definitions()
```

### DispatchClient (Agent Lifecycle)

Use this client for managing agent processes and inter-agent communication.

```python
from atlas_sdk import DispatchClient
from atlas_sdk.models import SpawnRequest

async with DispatchClient(base_url="http://dispatch:8000") as client:
    # Spawn an agent
    result = await client.spawn_agent(SpawnRequest(
        agent_definition_id=definition_id,
        deployment_id=deployment_id,
        prompt="Analyze the dataset"
    ))

    # Check agent status
    status = await client.get_agent_status(definition_id)

    # Wait for agent completion
    completion = await client.wait_for_agent(definition_id)

    # List running agents
    directory = await client.get_agent_directory()
```

### WorkflowClient (Workflow Orchestration)

Use this client for user-authored workflow code that orchestrates agent execution.

```python
from atlas_sdk import WorkflowClient
from atlas_sdk.models import PlanCreate, PlanTaskCreate

async with WorkflowClient(base_url="http://control-plane:8000") as client:
    # Check connectivity
    await client.health()

    # Create a plan with tasks
    plan = await client.create_plan(deployment_id, PlanCreate(
        goal="Process customer data",
        tasks=[
            PlanTaskCreate(sequence=1, description="Extract data"),
            PlanTaskCreate(sequence=2, description="Transform data"),
            PlanTaskCreate(sequence=3, description="Load to warehouse"),
        ]
    ))

    # Wait for plan to complete (convenience method)
    completed_plan = await client.wait_for_plan_completion(
        plan.plan.id,
        poll_interval=2.0,
        timeout=300.0
    )

    # Or wait for a specific task
    task = await client.wait_for_task_completion(task_id, poll_interval=1.0)

    # Monitor instance status (read-only)
    instance = await client.get_agent_instance(instance_id)
```

## Features

- **Async/await support** - Built on httpx for modern async Python
- **Automatic retries** - Resilient HTTP client with configurable retry policies
- **Type annotations** - Full type hints for IDE support and type checking
- **Pydantic models** - Request/response validation with Pydantic v2
- **Separation of concerns** - Three focused clients for distinct use cases

## Development

```bash
# Install dependencies
uv sync --extra dev --extra test

# Run tests
uv run pytest

# Run linting
uv run ruff check src/ tests/
uv run mypy src/atlas_sdk --strict

# Run security checks
uv run bandit -r src/atlas_sdk -c pyproject.toml
```

## License

MIT
