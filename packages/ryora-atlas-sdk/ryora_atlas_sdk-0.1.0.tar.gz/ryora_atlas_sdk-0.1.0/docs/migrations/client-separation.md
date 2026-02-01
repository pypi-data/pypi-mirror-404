# Migration Guide: SDK Client Separation

This guide explains how to migrate from the old monolithic `ControlPlaneClient` to the new purpose-specific clients.

## Overview

The SDK has been refactored from a single `ControlPlaneClient` into three focused clients:

| Client | Purpose | Base URL |
|--------|---------|----------|
| `ControlPlaneClient` | Admin/governance operations | Control Plane service |
| `DispatchClient` | Agent lifecycle management | Dispatch service |
| `WorkflowClient` | Workflow orchestration | Control Plane service |

## Breaking Changes

This is a **breaking change**. The old monolithic client has been removed and replaced with three new clients.

### Import Changes

**Before:**
```python
from atlas_sdk import ControlPlaneClient

async with ControlPlaneClient(base_url="http://control-plane:8000") as client:
    # All operations on one client
    pass
```

**After:**
```python
from atlas_sdk import ControlPlaneClient, DispatchClient, WorkflowClient

# Use the appropriate client for your use case
async with ControlPlaneClient(base_url="http://control-plane:8000") as admin_client:
    # Admin/governance operations
    pass

async with DispatchClient(base_url="http://dispatch:8000") as dispatch_client:
    # Agent lifecycle operations
    pass

async with WorkflowClient(base_url="http://control-plane:8000") as workflow_client:
    # Workflow orchestration operations
    pass
```

## Method Migration Reference

### Methods moved to ControlPlaneClient

These methods are for **system administrators and CI/CD pipelines**:

| Category | Methods |
|----------|---------|
| Agent Classes | `create_agent_class`, `get_agent_class`, `list_agent_classes`, `update_agent_class`, `delete_agent_class` |
| Agent Definitions | `create_agent_definition`, `get_agent_definition`, `list_agent_definitions`, `update_agent_definition`, `delete_agent_definition`, `get_agent_definition_config`, `add_tools_to_definition` |
| Model Providers | `create_model_provider`, `get_model_provider`, `list_model_providers`, `update_model_provider`, `delete_model_provider`, `verify_model_provider`, `list_provider_models` |
| System Prompts | `create_system_prompt`, `get_system_prompt`, `list_system_prompts`, `update_system_prompt`, `delete_system_prompt` |
| Tools | `list_tools`, `get_tool`, `delete_tool`, `sync_tools`, `discover_tools` |
| Deployments | `create_deployment`, `get_deployment`, `list_deployments`, `update_deployment`, `delete_deployment` |
| GRASP Analyses | `create_grasp_analysis`, `get_grasp_analysis`, `list_grasp_analyses`, `query_grasp_analyses` |
| Health | `health`, `metrics`, `logs` |

### Methods moved to DispatchClient

These methods are for **agent lifecycle management** (talks to Dispatch service):

| Category | Methods |
|----------|---------|
| Agent Lifecycle | `spawn_agent`, `get_agent_status`, `stop_agent`, `wait_for_agent` |
| A2A Communication | `a2a_call`, `get_agent_directory` |
| Health | `health` |

### Methods moved to WorkflowClient

These methods are for **user-authored workflow code**:

| Category | Methods | Access |
|----------|---------|--------|
| Plans | `create_plan`, `get_plan`, `list_plans`, `update_plan` | Full |
| Tasks | `append_tasks`, `get_task`, `list_tasks`, `update_task` | Full |
| Agent Definitions | `get_agent_definition`, `list_agent_definitions`, `get_agent_definition_config` | Read-only |
| Deployments | `get_deployment`, `list_deployments` | Read-only |
| Agent Instances | `get_agent_instance`, `list_agent_instances` | Read-only |
| Health | `health` | Read-only |
| Convenience | `wait_for_plan_completion`, `wait_for_task_completion` | - |

## Common Migration Patterns

### Admin/CI scripts

**Before:**
```python
from atlas_sdk import ControlPlaneClient

async with ControlPlaneClient(base_url=url) as client:
    provider = await client.create_model_provider(...)
    definition = await client.create_agent_definition(...)
```

**After:**
```python
from atlas_sdk import ControlPlaneClient

async with ControlPlaneClient(base_url=url) as client:
    provider = await client.create_model_provider(...)
    definition = await client.create_agent_definition(...)
```

No change needed - these operations remain on `ControlPlaneClient`.

### Agent spawning code

**Before:**
```python
from atlas_sdk import ControlPlaneClient

async with ControlPlaneClient(base_url=url) as client:
    # This method didn't exist in the old client
    pass
```

**After:**
```python
from atlas_sdk import DispatchClient
from atlas_sdk.models.dispatch import SpawnRequest

async with DispatchClient(base_url="http://dispatch:8000") as client:
    result = await client.spawn_agent(SpawnRequest(
        agent_definition_id=definition_id,
        deployment_id=deployment_id,
        prompt="Analyze the data"
    ))
    await client.wait_for_agent(definition_id)
```

### Workflow orchestration

**Before:**
```python
from atlas_sdk import ControlPlaneClient

async with ControlPlaneClient(base_url=url) as client:
    plan = await client.create_plan(deployment_id, plan_data)
    # Manual polling for completion
    while True:
        plan = await client.get_plan(plan.id)
        if plan.status in terminal_statuses:
            break
        await asyncio.sleep(2)
```

**After:**
```python
from atlas_sdk import WorkflowClient

async with WorkflowClient(base_url=url) as client:
    response = await client.create_plan(deployment_id, plan_data)

    # Use the convenience method
    completed_plan = await client.wait_for_plan_completion(
        response.plan.id,
        poll_interval=2.0,
        timeout=300.0
    )
```

## New Features

### Convenience Methods (WorkflowClient)

The `WorkflowClient` includes new convenience methods for common patterns:

```python
# Wait for a plan to reach terminal status (COMPLETED, FAILED, CANCELLED)
plan = await client.wait_for_plan_completion(
    plan_id,
    poll_interval=2.0,  # seconds between polls
    timeout=300.0       # max wait time in seconds
)

# Wait for a specific task to complete (COMPLETED, FAILED, SKIPPED)
task = await client.wait_for_task_completion(
    task_id,
    poll_interval=1.0,
    timeout=60.0
)
```

### New Dispatch Models

New Pydantic models for Dispatch service operations:

```python
from atlas_sdk.models.dispatch import (
    SpawnRequest,
    SpawnResponse,
    AgentStatusResponse,
    StopResponse,
    WaitResponse,
    A2ACallRequest,
    A2ACallResponse,
    A2ADirectoryResponse,
    AgentDirectoryEntry,
)
```

## Choosing the Right Client

| Use Case | Client |
|----------|--------|
| Setting up agent definitions, prompts, tools | `ControlPlaneClient` |
| CI/CD deployment automation | `ControlPlaneClient` |
| Spawning/stopping agent processes | `DispatchClient` |
| Agent-to-agent communication | `DispatchClient` |
| Writing workflow orchestration code | `WorkflowClient` |
| Creating and managing plans/tasks | `WorkflowClient` |
| Monitoring agent instances from workflows | `WorkflowClient` |
