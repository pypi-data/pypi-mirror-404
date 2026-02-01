# Plan: SDK Client Separation

This plan outlines the refactoring of the monolithic `ControlPlaneClient` into three purpose-specific clients to better represent the logical separation of concerns in the Atlas architecture.

## Problem Statement

The current `ControlPlaneClient` is monolithic and conflates three distinct use cases:

1. **Governance/Administration** - Managing definitions, blueprints, model providers, and system configuration
2. **Agent Lifecycle** - Spawning, monitoring, and stopping agent processes via the Dispatch service
3. **Workflow Orchestration** - User-authored workflow code that creates and manages plans/tasks

This leads to:
- Confusion about which methods are appropriate for which context
- Workflows having access to admin operations they shouldn't use
- No client for the Dispatch service (agent lifecycle management)
- Tight coupling between unrelated concerns

## Goal

Split the SDK into three focused clients:
- `ControlPlaneClient` - Admin/governance operations (talks to Control Plane)
- `DispatchClient` - Agent lifecycle management (talks to Dispatch service)
- `WorkflowClient` - Workflow orchestration (talks to Control Plane, scoped access)

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Control Plane Container                      │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    Control Plane API                       │  │
│  │  - Agent Classes, Definitions, Model Providers             │  │
│  │  - System Prompts, Tools, Deployments                      │  │
│  │  - Plans, Tasks, Agent Instances, GRASP Analyses           │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ HTTP
            ┌─────────────────┼─────────────────┐
            │                 │                 │
   ControlPlaneClient    WorkflowClient    (internal)
            │                 │                 │
            ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Dispatch + Workflow Container                  │
│  ┌─────────────────────┐    ┌─────────────────────────────────┐ │
│  │   Dispatch Service   │    │       User Workflows            │ │
│  │  - Agent spawning    │◄───│  - Create/manage plans          │ │
│  │  - A2A communication │    │  - Define task sequences        │ │
│  │  - Process lifecycle │    │  - Monitor execution            │ │
│  └─────────────────────┘    └─────────────────────────────────┘ │
│            ▲                                                     │
│            │ HTTP                                                │
│     DispatchClient                                               │
└─────────────────────────────────────────────────────────────────┘
```

## Client Specifications

### 1. ControlPlaneClient (Admin/Governance)

**Base URL:** Control Plane service
**Purpose:** System administrators and CI/CD pipelines managing Atlas configuration

#### Methods

| Category | Method | HTTP | Endpoint |
|----------|--------|------|----------|
| **Agent Classes** | `create_agent_class()` | POST | `/api/v1/agent-classes` |
| | `get_agent_class()` | GET | `/api/v1/agent-classes/{id}` |
| | `list_agent_classes()` | GET | `/api/v1/agent-classes` |
| | `delete_agent_class()` | DELETE | `/api/v1/agent-classes/{id}` |
| **Agent Definitions** | `create_agent_definition()` | POST | `/api/v1/agent-definitions` |
| | `get_agent_definition()` | GET | `/api/v1/agent-definitions/{id}` |
| | `list_agent_definitions()` | GET | `/api/v1/agent-definitions` |
| | `update_agent_definition()` | PATCH | `/api/v1/agent-definitions/{id}` |
| | `delete_agent_definition()` | DELETE | `/api/v1/agent-definitions/{id}` |
| | `get_agent_definition_config()` | GET | `/api/v1/agent-definitions/{id}/config` |
| | `add_tools_to_definition()` | POST | `/api/v1/agent-definitions/{id}/tools` |
| **Model Providers** | `create_model_provider()` | POST | `/api/v1/model-providers` |
| | `get_model_provider()` | GET | `/api/v1/model-providers/{id}` |
| | `list_model_providers()` | GET | `/api/v1/model-providers` |
| | `update_model_provider()` | PATCH | `/api/v1/model-providers/{id}` |
| | `delete_model_provider()` | DELETE | `/api/v1/model-providers/{id}` |
| | `verify_model_provider()` | POST | `/api/v1/model-providers/{id}/verify` |
| | `list_provider_models()` | GET | `/api/v1/model-providers/{id}/models` |
| **System Prompts** | `create_system_prompt()` | POST | `/api/v1/system-prompts` |
| | `get_system_prompt()` | GET | `/api/v1/system-prompts/{id}` |
| | `list_system_prompts()` | GET | `/api/v1/system-prompts` |
| | `update_system_prompt()` | PATCH | `/api/v1/system-prompts/{id}` |
| | `delete_system_prompt()` | DELETE | `/api/v1/system-prompts/{id}` |
| **Tools** | `list_tools()` | GET | `/api/v1/tools/` |
| | `get_tool()` | GET | `/api/v1/tools/{id}` |
| | `delete_tool()` | DELETE | `/api/v1/tools/{id}` |
| | `sync_tools()` | POST | `/api/v1/tools/sync` |
| | `discover_tools()` | POST | `/api/v1/tools/discover` |
| **Deployments** | `create_deployment()` | POST | `/api/v1/deployments` |
| | `get_deployment()` | GET | `/api/v1/deployments/{id}` |
| | `list_deployments()` | GET | `/api/v1/deployments` |
| | `update_deployment()` | PATCH | `/api/v1/deployments/{id}` |
| | `delete_deployment()` | DELETE | `/api/v1/deployments/{id}` |
| **GRASP Analyses** | `create_grasp_analysis()` | POST | `/api/v1/deployments/{id}/grasp-analyses` |
| | `get_grasp_analysis()` | GET | `/api/v1/grasp-analyses/{id}` |
| | `list_grasp_analyses()` | GET | `/api/v1/deployments/{id}/grasp-analyses` |
| | `query_grasp_analyses()` | GET | `/api/v1/grasp-analyses` |
| **Health** | `health()` | GET | `/api/v1/health` |
| | `metrics()` | GET | `/api/v1/metrics` |
| | `logs()` | GET | `/api/v1/logs` |

---

### 2. DispatchClient (Agent Lifecycle)

**Base URL:** Dispatch service
**Purpose:** Managing agent process lifecycle and inter-agent communication

#### Methods

| Method | HTTP | Endpoint | Description |
|--------|------|----------|-------------|
| `spawn_agent()` | POST | `/agents/spawn` | Spawn a new agent process |
| `get_agent_status()` | GET | `/agents/{definition_id}` | Get status of a running agent |
| `stop_agent()` | DELETE | `/agents/{definition_id}` | Stop a running agent |
| `wait_for_agent()` | POST | `/agents/{definition_id}/wait` | Block until agent completes |
| `a2a_call()` | POST | `/a2a/call` | Execute agent-to-agent call |
| `get_agent_directory()` | GET | `/a2a/directory` | List running agents for discovery |
| `health()` | GET | `/health` | Health check |

#### Request/Response Models (new)

```python
# models/dispatch.py

class SpawnRequest(BaseModel):
    agent_definition_id: UUID
    deployment_id: UUID
    prompt: str

class SpawnResponse(BaseModel):
    status: str
    port: int
    pid: int
    url: str
    deployment_id: UUID
    instance_id: UUID

class AgentStatusResponse(BaseModel):
    definition_id: UUID
    instance_id: Optional[UUID]
    port: Optional[int]
    pid: Optional[int]
    running: bool

class StopResponse(BaseModel):
    status: str
    message: str

class A2ACallRequest(BaseModel):
    agent_definition_id: UUID
    prompt: str
    routing_key: Optional[str] = None

class A2ACallResponse(BaseModel):
    content: str
    instance_id: UUID
    metadata: Optional[dict] = None

class AgentDirectoryEntry(BaseModel):
    agent_definition_id: UUID
    instance_id: UUID
    url: str
    port: int
    running: bool
    slug: str
    agent_class_id: UUID
    execution_mode: str
    allow_outbound_a2a: bool

class A2ADirectoryResponse(BaseModel):
    agents: list[AgentDirectoryEntry]
    deployment_id: UUID
```

---

### 3. WorkflowClient (Workflow Orchestration)

**Base URL:** Control Plane service
**Purpose:** User-authored workflow code that orchestrates agent execution via plans/tasks

#### Methods

| Category | Method | HTTP | Endpoint | Access |
|----------|--------|------|----------|--------|
| **Plans** | `create_plan()` | POST | `/api/v1/deployments/{id}/plans` | Full |
| | `get_plan()` | GET | `/api/v1/plans/{id}` | Full |
| | `list_plans()` | GET | `/api/v1/deployments/{id}/plans` | Full |
| | `update_plan()` | PATCH | `/api/v1/plans/{id}` | Full |
| **Tasks** | `append_tasks()` | POST | `/api/v1/plans/{id}/tasks` | Full |
| | `get_task()` | GET | `/api/v1/tasks/{id}` | Full |
| | `list_tasks()` | GET | `/api/v1/plans/{id}/tasks` | Full |
| | `update_task()` | PATCH | `/api/v1/tasks/{id}` | Full |
| **Agent Definitions** | `get_agent_definition()` | GET | `/api/v1/agent-definitions/{id}` | Read-only |
| | `list_agent_definitions()` | GET | `/api/v1/agent-definitions` | Read-only |
| | `get_agent_definition_config()` | GET | `/api/v1/agent-definitions/{id}/config` | Read-only |
| **Deployments** | `get_deployment()` | GET | `/api/v1/deployments/{id}` | Read-only |
| | `list_deployments()` | GET | `/api/v1/deployments` | Read-only |
| **Agent Instances** | `get_agent_instance()` | GET | `/api/v1/instances/{id}` | Read-only |
| | `list_agent_instances()` | GET | `/api/v1/instances` | Read-only |
| **Health** | `health()` | GET | `/api/v1/health` | Read-only |

#### Convenience Methods

| Method | Description |
|--------|-------------|
| `wait_for_plan_completion()` | Poll until all tasks in a plan reach terminal status (COMPLETED, FAILED, SKIPPED, CANCELLED) |
| `wait_for_task_completion()` | Poll until a specific task reaches terminal status |

**Note:** `WorkflowClient` intentionally excludes:
- Agent instance creation (handled by Dispatch)
- Agent instance updates (handled by Dispatch)
- Any admin/governance operations

---

## Implementation Tasks

### Phase 1: Foundation

- [x] **1.1** Create `BaseClient` class with shared functionality:
  - HTTP client management (httpx.AsyncClient)
  - Context manager support (`__aenter__`, `__aexit__`)
  - Retry logic with tenacity (502, 503, 504, connection errors)
  - Request logging (DEBUG level)
  - Error handling (`_raise_for_status`)
  - Configurable timeout

- [x] **1.2** Create new model submodules:
  - `models/control_plane/` - Agent classes, model providers, system prompts, tools, GRASP
  - `models/dispatch/` - Spawn, A2A, directory models
  - `models/workflow/` - (uses shared models, may not need separate module)
  - Keep `models/` root for shared models (enums, deployment, plan, task, agent_definition, agent_instance)

### Phase 2: Client Implementation

- [x] **2.1** Implement `ControlPlaneClient`:
  - Extend `BaseClient`
  - Add all admin/governance methods from specification
  - Add missing methods not in current client (agent classes, model providers, system prompts, tools, GRASP)

- [x] **2.2** Implement `DispatchClient`:
  - Extend `BaseClient`
  - Implement all dispatch service methods
  - Add dispatch-specific models

- [x] **2.3** Implement `WorkflowClient`:
  - Extend `BaseClient`
  - Migrate plan/task methods from current client
  - Add read-only agent definition, deployment, instance methods
  - Explicitly exclude write operations for instances
  - Add `health()` method for connectivity checks
  - Add convenience methods:
    - `wait_for_plan_completion(plan_id, poll_interval, timeout)` - poll until plan terminal
    - `wait_for_task_completion(task_id, poll_interval, timeout)` - poll until task terminal

### Phase 3: Migration & Cleanup

- [x] **3.1** Update `__init__.py` exports:
  ```python
  from atlas_sdk.clients import ControlPlaneClient, DispatchClient, WorkflowClient
  ```

- [x] **3.2** Remove old monolithic `ControlPlaneClient` (breaking change as agreed)

- [x] **3.3** Update all existing tests to use new clients

- [x] **3.4** Add unit tests for each new client

### Phase 4: Documentation

- [x] **4.1** Update README with new client usage examples
- [x] **4.2** Add docstrings to all public methods
- [x] **4.3** Create migration guide (for internal use)

---

## File Structure (Target)

```
atlas-sdk/src/atlas_sdk/
├── __init__.py                    # Export all three clients
├── _version.py
├── exceptions.py
├── clients/
│   ├── __init__.py                # Export clients
│   ├── base.py                    # BaseClient with shared logic
│   ├── control_plane.py           # ControlPlaneClient
│   ├── dispatch.py                # DispatchClient
│   └── workflow.py                # WorkflowClient
└── models/
    ├── __init__.py                # Re-export all models
    ├── enums.py                   # Shared enums (unchanged)
    ├── agent_definition.py        # Shared (unchanged)
    ├── agent_instance.py          # Shared (unchanged)
    ├── deployment.py              # Shared (unchanged)
    ├── plan.py                    # Shared (unchanged)
    ├── control_plane/
    │   ├── __init__.py
    │   ├── agent_class.py
    │   ├── model_provider.py
    │   ├── system_prompt.py
    │   ├── tool.py
    │   └── grasp.py
    └── dispatch/
        ├── __init__.py
        └── schemas.py             # Spawn, A2A, directory models
```

---

## Usage Examples

### ControlPlaneClient (Admin)

```python
from atlas_sdk import ControlPlaneClient

async with ControlPlaneClient(base_url="http://control-plane:8000") as client:
    # Create a model provider
    provider = await client.create_model_provider(ModelProviderCreate(
        name="openai-prod",
        provider_type="openai",
        api_key="sk-..."
    ))

    # Create an agent definition
    definition = await client.create_agent_definition(AgentDefinitionCreate(
        name="researcher",
        agent_class_id=class_id,
        model_provider_id=provider.id,
        ...
    ))
```

### DispatchClient (Agent Lifecycle)

```python
from atlas_sdk import DispatchClient

async with DispatchClient(base_url="http://dispatch:8000") as client:
    # Spawn an agent
    result = await client.spawn_agent(SpawnRequest(
        agent_definition_id=definition_id,
        deployment_id=deployment_id,
        prompt="Analyze the dataset"
    ))

    # Wait for completion
    completion = await client.wait_for_agent(definition_id)
```

### WorkflowClient (Workflows)

```python
from atlas_sdk import WorkflowClient

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

    # Check available agents (read-only)
    agents = await client.list_agent_definitions(status=AgentDefinitionStatus.PUBLISHED)

    # Wait for plan to complete (convenience method)
    completed_plan = await client.wait_for_plan_completion(
        plan.id,
        poll_interval=2.0,  # seconds between polls
        timeout=300.0       # max wait time in seconds
    )

    # Or wait for a specific task
    task = await client.wait_for_task_completion(task_id, poll_interval=1.0)

    # Monitor instance status (read-only)
    instance = await client.get_agent_instance(instance_id)
```

---

## Acceptance Criteria

1. **Separation of Concerns**: Each client has a clear, focused purpose
2. **No Shared Mutable State**: Clients are independent and can be used in isolation
3. **Backwards Incompatible**: Old `ControlPlaneClient` is removed (clean break)
4. **Full Coverage**: All Control Plane and Dispatch endpoints are accessible via SDK
5. **Type Safety**: All methods have proper type hints and return typed models
6. **Testable**: Each client has unit tests for request formation and response parsing

---

## Resolved Questions

1. **Health endpoints**: ✅ Yes - `WorkflowClient` will include `health()` for connectivity checks.
2. **Convenience methods**: ✅ Yes - Adding `wait_for_plan_completion()` and `wait_for_task_completion()` helpers.
