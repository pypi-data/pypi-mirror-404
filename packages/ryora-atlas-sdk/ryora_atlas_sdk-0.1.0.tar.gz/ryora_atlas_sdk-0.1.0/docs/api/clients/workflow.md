# WorkflowClient

The `WorkflowClient` is used for workflow orchestration through the Control Plane.

## Use Cases

- Creating and managing execution plans
- Monitoring task progress
- Waiting for plan/task completion
- Reading agent instance status

## Quick Example

```python
from atlas_sdk import WorkflowClient
from atlas_sdk.models import PlanCreate, PlanTaskCreate

async with WorkflowClient(base_url="http://control-plane:8000") as client:
    plan = await client.create_plan(deployment_id, PlanCreate(
        goal="Process data pipeline",
        tasks=[
            PlanTaskCreate(sequence=1, description="Extract"),
            PlanTaskCreate(sequence=2, description="Transform"),
            PlanTaskCreate(sequence=3, description="Load"),
        ]
    ))

    # Wait for completion
    completed = await client.wait_for_plan_completion(plan.plan.id)
```

## API Reference

::: atlas_sdk.clients.workflow.WorkflowClient
    options:
      show_root_heading: true
      show_source: false
      members_order: source
      filters: ["!^_"]
