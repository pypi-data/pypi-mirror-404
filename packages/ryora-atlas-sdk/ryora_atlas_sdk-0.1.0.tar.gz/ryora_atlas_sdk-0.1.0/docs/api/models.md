# Models

Pydantic models for request/response validation.

## Overview

The SDK uses Pydantic v2 models for all API interactions. Models are organized by domain:

- **Control Plane models**: Agent classes, definitions, providers, prompts, tools
- **Dispatch models**: Spawn requests, agent status
- **Workflow models**: Plans, tasks, agent instances, deployments

## Model Categories

### Create Models

Used when creating new resources:

- `AgentClassCreate`
- `AgentDefinitionCreate`
- `ModelProviderCreate`
- `SystemPromptCreate`
- `ToolCreate`
- `DeploymentCreate`
- `PlanCreate`
- `PlanTaskCreate`

### Update Models

Used when updating existing resources:

- `AgentClassUpdate`
- `AgentDefinitionUpdate`
- `ModelProviderUpdate`
- `SystemPromptUpdate`
- `ToolUpdate`
- `DeploymentUpdate`

### Response Models

Returned from API operations:

- `AgentClass`
- `AgentDefinition`
- `ModelProvider`
- `SystemPrompt`
- `Tool`
- `Deployment`
- `Plan`
- `PlanTask`
- `AgentInstance`

## Quick Example

```python
from atlas_sdk.models import (
    AgentClassCreate,
    AgentDefinitionCreate,
    ModelProviderCreate,
)

# Create models with validation
provider = ModelProviderCreate(
    name="openai-prod",
    api_base_url="https://api.openai.com/v1"
)

agent_class = AgentClassCreate(
    name="BugHunter",
    description="Security vulnerability detection"
)
```

## API Reference

### Control Plane Models

::: atlas_sdk.models.control_plane
    options:
      show_root_heading: false
      members_order: alphabetical

### Dispatch Models

::: atlas_sdk.models.dispatch
    options:
      show_root_heading: false
      members_order: alphabetical

### Workflow Models

::: atlas_sdk.models.plan
    options:
      show_root_heading: false
      members_order: alphabetical

::: atlas_sdk.models.deployment
    options:
      show_root_heading: false
      members_order: alphabetical

::: atlas_sdk.models.agent_instance
    options:
      show_root_heading: false
      members_order: alphabetical
