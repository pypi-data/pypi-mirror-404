# Waiting for Plan Completion

This example demonstrates patterns for waiting on asynchronous operations.

## Use Case: Synchronous API Wrapper

You're building an API that wraps Atlas operations but provides a synchronous interface to consumers. The API should:

- Submit a plan for execution
- Wait for completion
- Return the final result or error

## Prerequisites

- Running Control Plane instance
- Atlas SDK installed

## Complete Example

```python
"""
Example: Waiting for Async Operations
Use Case: Build a synchronous wrapper around async Atlas operations

This example shows how to:
- Use wait_for_plan_completion() and wait_for_task_completion()
- Implement custom waiting with progress reporting
- Handle timeouts gracefully
- Build synchronous wrappers
"""

import asyncio
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from atlas_sdk import WorkflowClient
from atlas_sdk.exceptions import AtlasTimeoutError
from atlas_sdk.models import PlanCreate, PlanTaskCreate


@dataclass
class ExecutionResult:
    """Result of a plan execution."""

    success: bool
    plan_id: UUID
    status: str
    duration_seconds: float
    task_results: list[dict]
    error: str | None = None


# =============================================================================
# Basic Waiting
# =============================================================================


async def execute_and_wait(
    client: WorkflowClient,
    deployment_id: UUID,
    goal: str,
    tasks: list[str],
    timeout: float = 300.0,
) -> ExecutionResult:
    """
    Execute a plan and wait for completion.

    Args:
        client: WorkflowClient instance
        deployment_id: Target deployment
        goal: Plan goal description
        tasks: List of task descriptions
        timeout: Maximum wait time in seconds

    Returns:
        ExecutionResult with final status and results
    """
    import time

    start_time = time.time()

    # Create the plan
    plan_response = await client.create_plan(
        deployment_id=deployment_id,
        plan=PlanCreate(
            goal=goal,
            tasks=[
                PlanTaskCreate(sequence=i + 1, description=desc)
                for i, desc in enumerate(tasks)
            ],
        ),
    )
    plan = plan_response.plan

    # Wait for completion
    try:
        completed = await client.wait_for_plan_completion(
            plan_id=plan.id,
            timeout=timeout,
            poll_interval=2.0,
        )

        duration = time.time() - start_time

        # Fetch final task states
        final_tasks = await client.list_tasks(plan_id=plan.id, limit=100)
        task_results = [
            {
                "sequence": t.sequence,
                "description": t.description,
                "status": t.status,
            }
            for t in final_tasks
        ]

        return ExecutionResult(
            success=completed.status == "completed",
            plan_id=plan.id,
            status=completed.status,
            duration_seconds=duration,
            task_results=task_results,
            error=None if completed.status == "completed" else "Plan did not complete successfully",
        )

    except AtlasTimeoutError:
        duration = time.time() - start_time
        current = await client.get_plan(plan.id)

        return ExecutionResult(
            success=False,
            plan_id=plan.id,
            status=current.status,
            duration_seconds=duration,
            task_results=[],
            error=f"Timeout after {timeout} seconds",
        )


# =============================================================================
# Waiting with Progress
# =============================================================================


async def execute_with_progress(
    client: WorkflowClient,
    deployment_id: UUID,
    goal: str,
    tasks: list[str],
    timeout: float = 300.0,
    on_progress: callable = None,
) -> ExecutionResult:
    """
    Execute a plan with progress callbacks.

    Args:
        client: WorkflowClient instance
        deployment_id: Target deployment
        goal: Plan goal description
        tasks: List of task descriptions
        timeout: Maximum wait time
        on_progress: Callback(completed_tasks, total_tasks, current_task_desc)
    """
    import time

    start_time = time.time()
    total_tasks = len(tasks)

    # Create plan
    plan_response = await client.create_plan(
        deployment_id=deployment_id,
        plan=PlanCreate(
            goal=goal,
            tasks=[
                PlanTaskCreate(sequence=i + 1, description=desc)
                for i, desc in enumerate(tasks)
            ],
        ),
    )
    plan = plan_response.plan

    # Custom polling loop with progress
    deadline = time.time() + timeout
    last_completed = -1

    while time.time() < deadline:
        # Check plan status
        current_plan = await client.get_plan(plan.id)

        if current_plan.status in ("completed", "failed", "cancelled"):
            break

        # Check task progress
        current_tasks = await client.list_tasks(plan_id=plan.id, limit=100)
        completed_count = sum(1 for t in current_tasks if t.status == "completed")

        # Report progress if changed
        if completed_count != last_completed and on_progress:
            current_task = next(
                (t for t in current_tasks if t.status == "in_progress"),
                None,
            )
            on_progress(
                completed_count,
                total_tasks,
                current_task.description if current_task else None,
            )
            last_completed = completed_count

        await asyncio.sleep(2.0)

    else:
        # Timeout
        return ExecutionResult(
            success=False,
            plan_id=plan.id,
            status="timeout",
            duration_seconds=time.time() - start_time,
            task_results=[],
            error=f"Timeout after {timeout} seconds",
        )

    # Final result
    final_tasks = await client.list_tasks(plan_id=plan.id, limit=100)

    return ExecutionResult(
        success=current_plan.status == "completed",
        plan_id=plan.id,
        status=current_plan.status,
        duration_seconds=time.time() - start_time,
        task_results=[
            {"sequence": t.sequence, "description": t.description, "status": t.status}
            for t in final_tasks
        ],
    )


# =============================================================================
# Wait for Individual Task
# =============================================================================


async def wait_for_specific_task(
    client: WorkflowClient,
    plan_id: UUID,
    task_sequence: int,
    timeout: float = 60.0,
) -> dict:
    """
    Wait for a specific task in a plan to complete.

    Useful when you want to proceed after a particular milestone.
    """
    # Find the task
    tasks = await client.list_tasks(plan_id=plan_id, limit=100)
    target_task = next((t for t in tasks if t.sequence == task_sequence), None)

    if not target_task:
        raise ValueError(f"Task with sequence {task_sequence} not found")

    # Wait for it
    try:
        completed_task = await client.wait_for_task_completion(
            task_id=target_task.id,
            timeout=timeout,
            poll_interval=1.0,
        )
        return {
            "status": completed_task.status,
            "description": completed_task.description,
            "completed": completed_task.status == "completed",
        }
    except AtlasTimeoutError:
        current = await client.get_task(target_task.id)
        return {
            "status": current.status,
            "description": current.description,
            "completed": False,
            "error": "Timeout",
        }


# =============================================================================
# Parallel Plan Execution
# =============================================================================


async def execute_plans_parallel(
    client: WorkflowClient,
    plans: list[tuple[UUID, str, list[str]]],  # (deployment_id, goal, tasks)
    timeout: float = 300.0,
) -> list[ExecutionResult]:
    """
    Execute multiple plans in parallel and wait for all.
    """

    async def execute_one(deployment_id: UUID, goal: str, tasks: list[str]):
        return await execute_and_wait(client, deployment_id, goal, tasks, timeout)

    results = await asyncio.gather(
        *[execute_one(d, g, t) for d, g, t in plans],
        return_exceptions=True,
    )

    # Convert exceptions to error results
    final_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            final_results.append(
                ExecutionResult(
                    success=False,
                    plan_id=UUID(int=0),  # Unknown
                    status="error",
                    duration_seconds=0,
                    task_results=[],
                    error=str(result),
                )
            )
        else:
            final_results.append(result)

    return final_results


# =============================================================================
# Cancellation Support
# =============================================================================


async def execute_with_cancellation(
    client: WorkflowClient,
    deployment_id: UUID,
    goal: str,
    tasks: list[str],
    cancel_event: asyncio.Event,
    timeout: float = 300.0,
) -> ExecutionResult:
    """
    Execute a plan that can be cancelled via an event.
    """
    import time

    start_time = time.time()

    # Create plan
    plan_response = await client.create_plan(
        deployment_id=deployment_id,
        plan=PlanCreate(
            goal=goal,
            tasks=[
                PlanTaskCreate(sequence=i + 1, description=desc)
                for i, desc in enumerate(tasks)
            ],
        ),
    )
    plan = plan_response.plan

    # Wait with cancellation check
    deadline = time.time() + timeout

    while time.time() < deadline:
        # Check for cancellation
        if cancel_event.is_set():
            # Could cancel the plan here if API supports it
            return ExecutionResult(
                success=False,
                plan_id=plan.id,
                status="cancelled",
                duration_seconds=time.time() - start_time,
                task_results=[],
                error="Cancelled by user",
            )

        # Check plan status
        current = await client.get_plan(plan.id)
        if current.status in ("completed", "failed", "cancelled"):
            final_tasks = await client.list_tasks(plan_id=plan.id, limit=100)
            return ExecutionResult(
                success=current.status == "completed",
                plan_id=plan.id,
                status=current.status,
                duration_seconds=time.time() - start_time,
                task_results=[
                    {"sequence": t.sequence, "description": t.description, "status": t.status}
                    for t in final_tasks
                ],
            )

        await asyncio.sleep(2.0)

    return ExecutionResult(
        success=False,
        plan_id=plan.id,
        status="timeout",
        duration_seconds=timeout,
        task_results=[],
        error=f"Timeout after {timeout} seconds",
    )


# =============================================================================
# Main
# =============================================================================


async def main():
    """Demonstrate waiter patterns."""
    deployment_id = UUID("00000000-0000-0000-0000-000000000001")

    async with WorkflowClient(base_url="http://localhost:8000") as client:
        # Basic wait
        print("=== Basic Wait ===")
        result = await execute_and_wait(
            client,
            deployment_id,
            goal="Process data",
            tasks=["Extract", "Transform", "Load"],
            timeout=60.0,
        )
        print(f"Result: {result.status} in {result.duration_seconds:.1f}s")

        # With progress
        print("\n=== With Progress ===")

        def show_progress(completed: int, total: int, current: str | None):
            pct = (completed / total) * 100
            print(f"  Progress: {completed}/{total} ({pct:.0f}%) - {current or 'waiting'}")

        result = await execute_with_progress(
            client,
            deployment_id,
            goal="Process data",
            tasks=["Step 1", "Step 2", "Step 3"],
            timeout=60.0,
            on_progress=show_progress,
        )
        print(f"Final: {result.status}")


if __name__ == "__main__":
    asyncio.run(main())
```

## Key Points

### wait_for_plan_completion

The SDK provides a built-in waiter:

```python
completed = await client.wait_for_plan_completion(
    plan_id=plan.id,
    timeout=300.0,      # Max wait time
    poll_interval=2.0,  # Check frequency
)
```

### wait_for_task_completion

Wait for individual tasks:

```python
task = await client.wait_for_task_completion(
    task_id=task.id,
    timeout=60.0,
    poll_interval=1.0,
)
```

### Timeout Handling

Always handle `AtlasTimeoutError`:

```python
try:
    result = await client.wait_for_plan_completion(plan_id, timeout=60.0)
except AtlasTimeoutError:
    # Plan is still running
    current = await client.get_plan(plan_id)
    print(f"Still running: {current.status}")
```

### Progress Tracking

For UI feedback, poll manually with status checks:

```python
while not done:
    plan = await client.get_plan(plan_id)
    tasks = await client.list_tasks(plan_id=plan_id)
    completed = sum(1 for t in tasks if t.status == "completed")
    report_progress(completed, len(tasks))
    await asyncio.sleep(2.0)
```

## Next Steps

- [Deployment Workflow](02_deployment_workflow.md) - Complete deployment example
- [Concurrent Operations](09_concurrent_operations.md) - Run multiple plans in parallel
