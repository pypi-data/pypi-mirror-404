# Deployment Workflow

This example demonstrates a complete deployment workflow, from creating a deployment to monitoring task execution.

## Use Case: Deploying an Agent for Data Processing

You're deploying an agent to process a large dataset. The workflow involves:

1. Creating a deployment for the agent definition
2. Creating a plan with sequential tasks
3. Monitoring the plan's progress
4. Waiting for completion
5. Handling the final results

## Prerequisites

- Running Control Plane instance
- An existing agent definition (see [Basic CRUD Operations](01_basic_crud.md))

## Complete Example

```python
"""
Example: Complete Deployment Workflow
Use Case: Deploy an agent to process customer data

This example shows how to:
- Create deployments
- Create execution plans with tasks
- Monitor task progress
- Wait for plan completion
- Handle completion and failures
"""

import asyncio
from uuid import UUID

from atlas_sdk import ControlPlaneClient, WorkflowClient
from atlas_sdk.models import (
    DeploymentCreate,
    PlanCreate,
    PlanTaskCreate,
)
from atlas_sdk.exceptions import AtlasTimeoutError


async def deploy_and_execute(
    control_plane_url: str,
    agent_definition_id: UUID,
):
    """Deploy an agent and execute a data processing plan."""

    # Use both clients - ControlPlaneClient for admin ops, WorkflowClient for execution
    async with (
        ControlPlaneClient(base_url=control_plane_url) as admin_client,
        WorkflowClient(base_url=control_plane_url) as workflow_client,
    ):
        # ===== Step 1: Create Deployment =====
        print("Step 1: Creating deployment...")

        deployment = await admin_client.create_deployment(
            DeploymentCreate(
                name="data-processing-job-001",
                agent_definition_id=agent_definition_id,
                config={
                    "environment": "production",
                    "resource_limits": {"max_memory_mb": 2048},
                },
            )
        )
        print(f"  Created deployment: {deployment.name}")
        print(f"  Deployment ID: {deployment.id}")
        print(f"  Status: {deployment.status}")

        # ===== Step 2: Create Execution Plan =====
        print("\nStep 2: Creating execution plan...")

        plan_response = await workflow_client.create_plan(
            deployment_id=deployment.id,
            plan=PlanCreate(
                goal="Process customer data for Q4 analysis",
                tasks=[
                    PlanTaskCreate(
                        sequence=1,
                        description="Extract customer records from source database",
                    ),
                    PlanTaskCreate(
                        sequence=2,
                        description="Validate and clean extracted data",
                    ),
                    PlanTaskCreate(
                        sequence=3,
                        description="Transform data to target schema",
                    ),
                    PlanTaskCreate(
                        sequence=4,
                        description="Load transformed data to warehouse",
                    ),
                    PlanTaskCreate(
                        sequence=5,
                        description="Generate processing summary report",
                    ),
                ],
            ),
        )

        # The response is a wrapper containing both the plan and its tasks.
        # This two-level structure avoids a second API call to fetch tasks.
        plan = plan_response.plan    # PlanRead object with plan metadata
        tasks = plan_response.tasks  # List of PlanTaskRead objects

        print(f"  Created plan: {plan.id}")
        print(f"  Goal: {plan.goal}")
        print(f"  Tasks created: {len(tasks)}")
        for task in tasks:
            print(f"    {task.sequence}. {task.description}")

        # ===== Step 3: Monitor Progress =====
        print("\nStep 3: Monitoring plan execution...")

        # Poll for status updates while waiting
        async def monitor_progress():
            """Background task to show progress updates."""
            last_status = None
            while True:
                current_plan = await workflow_client.get_plan(plan.id)
                if current_plan.status != last_status:
                    print(f"  Plan status: {current_plan.status}")
                    last_status = current_plan.status

                # Check individual task statuses
                current_tasks = await workflow_client.list_tasks(
                    plan_id=plan.id, limit=100
                )
                for task in current_tasks:
                    if task.status == "completed":
                        print(f"    ✓ Task {task.sequence}: {task.description}")

                if current_plan.status in ("completed", "failed", "cancelled"):
                    break

                await asyncio.sleep(2.0)

        # ===== Step 4: Wait for Completion =====
        print("\nStep 4: Waiting for plan completion...")

        try:
            # Wait with timeout (5 minutes)
            completed_plan = await workflow_client.wait_for_plan_completion(
                plan_id=plan.id,
                timeout=300.0,  # 5 minutes
                poll_interval=2.0,  # Check every 2 seconds
            )

            print(f"\n  Plan completed with status: {completed_plan.status}")

            if completed_plan.status == "completed":
                print("\n✓ Data processing completed successfully!")

                # Fetch final task results
                final_tasks = await workflow_client.list_tasks(
                    plan_id=plan.id, limit=100
                )
                print("\nTask Summary:")
                for task in final_tasks:
                    status_icon = "✓" if task.status == "completed" else "✗"
                    print(f"  {status_icon} {task.sequence}. {task.description}")

            elif completed_plan.status == "failed":
                print("\n✗ Plan failed!")
                # Get tasks to find which one failed
                failed_tasks = await workflow_client.list_tasks(
                    plan_id=plan.id, limit=100
                )
                for task in failed_tasks:
                    if task.status == "failed":
                        print(f"  Failed task: {task.description}")
                        if task.error:
                            print(f"  Error: {task.error}")

        except AtlasTimeoutError:
            print("\n⚠ Timeout waiting for plan completion!")
            print("  The plan is still running. Check status later.")

            # Get current status
            current = await workflow_client.get_plan(plan.id)
            print(f"  Current status: {current.status}")

        # ===== Step 5: Cleanup (Optional) =====
        print("\nStep 5: Cleanup...")

        # In production, you might want to keep the deployment
        # For this example, we'll clean up
        # await admin_client.delete_deployment(deployment.id)
        # print("  Deployment deleted.")

        print("\nWorkflow complete!")

        return deployment, plan


async def main():
    """Main entry point."""
    # Replace with your actual values
    CONTROL_PLANE_URL = "http://localhost:8000"
    AGENT_DEFINITION_ID = UUID("00000000-0000-0000-0000-000000000001")

    await deploy_and_execute(CONTROL_PLANE_URL, AGENT_DEFINITION_ID)


if __name__ == "__main__":
    asyncio.run(main())
```

## Key Points

### Two Clients, Different Purposes

- **ControlPlaneClient**: Administrative operations (create/manage deployments)
- **WorkflowClient**: Workflow execution (plans, tasks, monitoring)

```python
async with (
    ControlPlaneClient(base_url=url) as admin_client,
    WorkflowClient(base_url=url) as workflow_client,
):
    ...
```

### Plan and Tasks

A **Plan** represents a high-level goal with ordered **Tasks**:

```python
plan_response = await workflow_client.create_plan(
    deployment_id=deployment.id,
    plan=PlanCreate(
        goal="High-level objective",
        tasks=[
            PlanTaskCreate(sequence=1, description="First step"),
            PlanTaskCreate(sequence=2, description="Second step"),
        ],
    ),
)
```

### Response Wrapper Pattern

The `create_plan()` method returns a `PlanCreateResponse` wrapper object, not a plain `Plan`:

```python
plan_response = await workflow_client.create_plan(...)

# Access the plan via the .plan attribute
plan = plan_response.plan          # PlanRead object
plan_id = plan_response.plan.id    # UUID of the created plan

# Access the created tasks via the .tasks attribute
tasks = plan_response.tasks        # List[PlanTaskRead]
```

This pattern serves two purposes:
1. **Efficiency**: Returns the plan and its tasks in a single response, avoiding extra API calls
2. **Atomicity**: Guarantees you see the tasks exactly as they were created with the plan

Other SDK methods return the resource directly (e.g., `get_plan()` returns `PlanRead`).

### Wait for Completion

Use `wait_for_plan_completion()` to block until a plan finishes:

```python
completed = await workflow_client.wait_for_plan_completion(
    plan_id=plan.id,
    timeout=300.0,      # Maximum wait time
    poll_interval=2.0,  # How often to check
)
```

For individual tasks:

```python
task = await workflow_client.wait_for_task_completion(
    task_id=task.id,
    timeout=60.0,
    poll_interval=1.0,
)
```

### Handling Timeout

When `wait_for_plan_completion()` exceeds its timeout, it raises `AtlasTimeoutError`:

```python
try:
    completed = await workflow_client.wait_for_plan_completion(plan_id, timeout=60.0)
except AtlasTimeoutError:
    # Plan is still running - decide how to handle
    current = await workflow_client.get_plan(plan_id)
    print(f"Status after timeout: {current.status}")
```

## Next Steps

- [Robust Error Recovery](03_error_recovery.md) - Handle failures gracefully
- [Waiting for Plan Completion](07_waiters.md) - Advanced waiter patterns
