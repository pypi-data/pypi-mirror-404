# ControlPlaneClient

The `ControlPlaneClient` is used for administrative and governance operations on the Atlas Control Plane.

## Use Cases

- CI/CD pipelines managing Atlas configuration
- Administrative scripts for bulk operations
- System administration dashboards
- Configuration management tools

## Quick Example

```python
from atlas_sdk import ControlPlaneClient
from atlas_sdk.models import AgentClassCreate

async with ControlPlaneClient(base_url="http://control-plane:8000") as client:
    agent_class = await client.create_agent_class(AgentClassCreate(
        name="BugHunter",
        description="Security vulnerability detection"
    ))
```

## API Reference

::: atlas_sdk.clients.control_plane.ControlPlaneClient
    options:
      show_root_heading: true
      show_source: false
      members_order: source
      filters: ["!^_"]
