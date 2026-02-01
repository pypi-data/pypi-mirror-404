# DispatchClient

The `DispatchClient` is used for agent lifecycle management through the Dispatch service.

## Use Cases

- Spawning agent processes
- Monitoring agent execution status
- Inter-agent communication
- Agent directory management

## Quick Example

```python
from atlas_sdk import DispatchClient
from atlas_sdk.models import SpawnRequest

async with DispatchClient(base_url="http://dispatch:8000") as client:
    result = await client.spawn_agent(SpawnRequest(
        agent_definition_id=definition_id,
        deployment_id=deployment_id,
        prompt="Analyze the security of this codebase"
    ))
```

## API Reference

::: atlas_sdk.clients.dispatch.DispatchClient
    options:
      show_root_heading: true
      show_source: false
      members_order: source
      filters: ["!^_"]
