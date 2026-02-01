# Quick Start

This guide will get you up and running with the Atlas SDK in minutes.

## Choose Your Client

The SDK provides three purpose-specific clients:

- **ControlPlaneClient**: For system administration and CI/CD pipelines
- **DispatchClient**: For agent lifecycle management
- **WorkflowClient**: For workflow orchestration code

## Basic Usage

### ControlPlaneClient

Use this client for administrative operations: managing agent classes, definitions, model providers, and deployments.

```python
import asyncio
from atlas_sdk import ControlPlaneClient
from atlas_sdk.models import AgentClassCreate, ModelProviderCreate

async def main():
    async with ControlPlaneClient(base_url="http://control-plane:8000") as client:
        # Check connectivity
        health = await client.health()
        print(f"Control Plane status: {health}")

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

        # List all agent definitions with pagination
        definitions = await client.list_agent_definitions(limit=100, offset=0)
        for defn in definitions:
            print(f"  - {defn.name}")

asyncio.run(main())
```

### DispatchClient

Use this client for managing agent processes and inter-agent communication.

```python
import asyncio
from atlas_sdk import DispatchClient
from atlas_sdk.models import SpawnRequest

async def main():
    async with DispatchClient(base_url="http://dispatch:8000") as client:
        # Spawn an agent
        result = await client.spawn_agent(SpawnRequest(
            agent_definition_id=definition_id,
            deployment_id=deployment_id,
            prompt="Analyze the security of this codebase"
        ))

        # Check agent status
        status = await client.get_agent_status(definition_id)

        # Wait for agent completion
        completion = await client.wait_for_agent(definition_id)
        print(f"Agent completed: {completion}")

asyncio.run(main())
```

### WorkflowClient

Use this client for orchestrating workflows and monitoring task execution.

```python
import asyncio
from atlas_sdk import WorkflowClient
from atlas_sdk.models import PlanCreate, PlanTaskCreate

async def main():
    async with WorkflowClient(base_url="http://control-plane:8000") as client:
        # Create a plan with tasks
        plan = await client.create_plan(deployment_id, PlanCreate(
            goal="Process customer data",
            tasks=[
                PlanTaskCreate(sequence=1, description="Extract data"),
                PlanTaskCreate(sequence=2, description="Transform data"),
                PlanTaskCreate(sequence=3, description="Load to warehouse"),
            ]
        ))

        # Wait for plan to complete
        completed_plan = await client.wait_for_plan_completion(
            plan.plan.id,
            poll_interval=2.0,
            timeout=300.0
        )
        print(f"Plan completed with status: {completed_plan.status}")

asyncio.run(main())
```

## Context Manager Usage

All clients support async context managers for proper resource cleanup:

```python
# Recommended: Use as context manager
async with ControlPlaneClient(base_url="...") as client:
    await client.health()
# Client is automatically closed

# Alternative: Manual lifecycle management
client = ControlPlaneClient(base_url="...")
try:
    await client.health()
finally:
    await client.close()
```

## Next Steps

- [Error Handling](../guides/error-handling.md) - Handle errors gracefully
- [Retry Behavior](../guides/retry-behavior.md) - Understand automatic retries
- [Pagination](../guides/pagination.md) - Work with large datasets
- [Examples](../examples/index.md) - Real-world usage patterns
