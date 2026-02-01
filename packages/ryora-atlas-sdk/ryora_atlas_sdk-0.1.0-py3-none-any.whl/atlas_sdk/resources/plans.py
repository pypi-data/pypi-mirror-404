"""Plan resource and resource manager.

Provides a high-level API for managing plans:
- PlansResource: Collection operations (create, get, list)
- Plan: Individual resource with bound methods (refresh, save, wait_for_completion) and tasks access
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any
from uuid import UUID

from atlas_sdk._internal.polling import poll_until
from atlas_sdk.models.enums import PlanStatus
from atlas_sdk.models.plan import (
    PlanCreate,
    PlanCreateResponse,
    PlanRead,
    PlanReadWithTasks,
    PlanTaskCreate,
    PlanTaskReadEnriched,
    PlanUpdate,
    TasksAppend,
    TasksAppendResponse,
)
from atlas_sdk.resources.base import Resource, ResourceManager
from atlas_sdk.resources.tasks import Task

if TYPE_CHECKING:
    pass


# Terminal statuses for plans
_PLAN_TERMINAL_STATUSES = {
    PlanStatus.COMPLETED,
    PlanStatus.FAILED,
    PlanStatus.CANCELLED,
}

# Progress callback type for waiter methods
ProgressCallback = Callable[[PlanReadWithTasks], Awaitable[None] | None]


class Plan(Resource[PlanReadWithTasks]):
    """A plan resource with bound methods and task access.

    Wraps a PlanReadWithTasks model and provides methods to refresh, save,
    and access related tasks.

    All model fields are accessible as read-only attributes via delegation
    to the underlying PlanReadWithTasks model:
        id: The plan UUID.
        deployment_id: The parent deployment UUID.
        created_by_instance_id: The UUID of the agent instance that created this plan.
        goal: The plan goal.
        constraints: Plan constraints dict.
        state: Plan state dict.
        status: The plan status.
        spec_reference: Optional spec reference.
        created_at: When the plan was created.
        updated_at: When the plan was last updated.

    The `tasks` property provides Task resource wrappers (not raw model data).

    Example:
        plan = await client.plans.get(plan_id)

        # Access fields (delegated to underlying model)
        print(f"Plan: {plan.goal} ({plan.status})")

        # Access tasks through relationship
        for task in plan.tasks:
            print(f"  Task {task.sequence}: {task.description}")

        # Update and save
        plan.data.status = PlanStatus.COMPLETED
        await plan.save()

        # Refresh from server
        await plan.refresh()

        # Append new tasks
        task_ids = await plan.append_tasks([
            PlanTaskCreate(sequence=10, description="New task", validation="Done")
        ])
    """

    @property
    def tasks(self) -> list[Task]:
        """Get the tasks for this plan as Task resources.

        Returns a list of Task resources wrapping the plan's tasks. Note that
        these tasks are not enriched - call task.refresh() to get enriched data.

        Returns:
            List of Task resources.
        """
        result = []
        for task_data in self._data.tasks:
            # Convert PlanTaskRead to PlanTaskReadEnriched
            enriched = PlanTaskReadEnriched(
                **task_data.model_dump(),
                assignee_agent_slug=None,
                assignee_agent_name=None,
            )
            result.append(Task(enriched, self._client))
        return result

    async def refresh(self) -> None:
        """Re-fetch this plan from the server.

        Updates the internal data with the latest state from the server,
        including the tasks list.

        Raises:
            AtlasNotFoundError: If the plan no longer exists.
            AtlasAPIError: If the request fails.
        """
        resp = await self._client._request("GET", f"/api/v1/plans/{self.id}")
        self._client._raise_for_status(resp)
        self._data = PlanReadWithTasks.model_validate(resp.json())

    async def save(self) -> None:
        """Persist local changes to the server.

        Sends the current state of mutable fields (goal, constraints, state,
        status, spec_reference) to the server.

        Note:
            This does not save changes to tasks. Use task.save() for that.

        Raises:
            AtlasValidationError: If the update data is invalid.
            AtlasNotFoundError: If the plan no longer exists.
            AtlasAPIError: If the request fails.
        """
        update = PlanUpdate(
            goal=self._data.goal,
            constraints=self._data.constraints,
            state=self._data.state,
            status=self._data.status,
            spec_reference=self._data.spec_reference,
        )
        resp = await self._client._request(
            "PATCH",
            f"/api/v1/plans/{self.id}",
            json=update.model_dump(exclude_unset=True, mode="json"),
        )
        self._client._raise_for_status(resp)
        # PATCH returns PlanRead without tasks, so refresh to get full data
        await self.refresh()

    async def delete(self) -> None:
        """Delete is not supported for plans through the resource API.

        Plans are typically managed through deployment lifecycle.

        Raises:
            NotImplementedError: Always, as plan deletion is not exposed.
        """
        raise NotImplementedError(
            "Plan deletion is not supported through the resource API. "
            "Plans are managed through deployment lifecycle."
        )

    async def append_tasks(self, tasks: list[PlanTaskCreate]) -> list[UUID]:
        """Append new tasks to this plan.

        Args:
            tasks: List of tasks to append.

        Returns:
            List of UUIDs for the created tasks.

        Raises:
            AtlasValidationError: If the task data is invalid.
            AtlasAPIError: If the request fails.
        """
        append_data = TasksAppend(tasks=tasks)
        resp = await self._client._request(
            "POST",
            f"/api/v1/plans/{self.id}/tasks",
            json=append_data.model_dump(exclude_unset=True, mode="json"),
        )
        self._client._raise_for_status(resp)
        response = TasksAppendResponse.model_validate(resp.json())
        # Refresh to update internal tasks list
        await self.refresh()
        return response.task_ids

    async def wait_for_completion(
        self,
        *,
        poll_interval: float = 2.0,
        timeout: float | None = None,
        on_progress: ProgressCallback | None = None,
    ) -> None:
        """Wait for this plan to reach a terminal status.

        Terminal statuses are: COMPLETED, FAILED, CANCELLED.

        Args:
            poll_interval: Seconds between polling attempts. Defaults to 2.0.
            timeout: Maximum seconds to wait. None means wait indefinitely.
            on_progress: Optional callback invoked after each poll with the
                current plan state including tasks. Can be sync or async.

        Raises:
            AtlasTimeoutError: If the timeout is exceeded before completion.
                The error includes the last known state via the `last_state`
                attribute, along with `timeout_seconds` and `operation`.
            AtlasAPIError: If any request fails.

        Example:
            plan = await client.plans.get(plan_id)

            # Simple wait
            await plan.wait_for_completion(timeout=600)

            # With progress callback
            async def on_progress(state):
                completed = sum(1 for t in state.tasks if t.status == "COMPLETED")
                print(f"Progress: {completed}/{len(state.tasks)} tasks")

            await plan.wait_for_completion(
                timeout=600,
                on_progress=on_progress
            )
        """

        async def fetch_state() -> PlanReadWithTasks:
            await self.refresh()
            return self._data

        await poll_until(
            fetch=fetch_state,
            is_terminal=lambda p: p.status in _PLAN_TERMINAL_STATUSES,
            poll_interval=poll_interval,
            timeout=timeout,
            on_progress=on_progress,
            timeout_message=lambda p: (
                f"Timeout waiting for plan {self.id} to complete. "
                f"Current status: {p.status.value}"
            ),
            operation="wait_for_completion",
        )

    def __repr__(self) -> str:
        """Return a string representation of the plan."""
        return f"<Plan id={self.id} status={self.status.value} tasks={len(self._data.tasks)}>"


class PlansResource(ResourceManager["Plan", PlanReadWithTasks]):
    """Resource manager for plan collection operations.

    Provides methods for creating, retrieving, and listing plans
    using a fluent API pattern.

    Args:
        client: The HTTP client protocol for making requests.

    Example:
        # Create a plan with tasks
        plan = await client.plans.create(
            deployment_id=deployment_id,
            goal="Process customer data",
            tasks=[
                PlanTaskCreate(sequence=1, description="Extract", validation="Done"),
                PlanTaskCreate(sequence=2, description="Transform", validation="Done"),
            ]
        )

        # Get a plan by ID
        plan = await client.plans.get(plan_id)

        # List plans for a deployment
        plans = await client.plans.list(deployment_id, status=PlanStatus.ACTIVE)
    """

    _resource_class = Plan
    _model_class = PlanReadWithTasks
    _base_path = "/api/v1/plans"

    async def create(
        self,
        deployment_id: UUID,
        goal: str,
        *,
        constraints: dict[str, Any] | None = None,
        state: dict[str, Any] | None = None,
        spec_reference: str | None = None,
        tasks: list[PlanTaskCreate] | None = None,
        idempotency_key: str | None = None,
    ) -> Plan:
        """Create a new plan within a deployment.

        Args:
            deployment_id: The UUID of the deployment.
            goal: The plan goal.
            constraints: Optional constraints dict.
            state: Optional state dict.
            spec_reference: Optional spec reference.
            tasks: Optional list of initial tasks.
            idempotency_key: Optional idempotency key for safe retries. Use "auto"
                to generate a UUID-based key automatically.

        Returns:
            The created Plan resource.

        Raises:
            AtlasValidationError: If the creation data is invalid.
            AtlasAPIError: If the request fails.
        """
        create_data = PlanCreate(
            goal=goal,
            constraints=constraints or {},
            state=state or {},
            spec_reference=spec_reference,
            tasks=tasks or [],
        )
        resp = await self._client._request(
            "POST",
            f"/api/v1/deployments/{deployment_id}/plans",
            idempotency_key=idempotency_key,
            json=create_data.model_dump(exclude_unset=True, mode="json"),
        )
        self._client._raise_for_status(resp)

        # The create endpoint returns PlanCreateResponse with task_ids
        # We need to fetch the full plan with tasks
        create_response = PlanCreateResponse.model_validate(resp.json())
        return await self.get(create_response.id)

    async def list(
        self,
        deployment_id: UUID,
        *,
        status: PlanStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Plan]:
        """List plans within a deployment.

        Note:
            The list endpoint returns PlanRead without tasks. Each plan
            is converted to a Plan resource that can be refreshed to get
            the full plan with tasks (or call plan.refresh()).

        Args:
            deployment_id: The UUID of the deployment containing the plans.
            status: Optional status filter.
            limit: Maximum number of results to return. Defaults to 100.
            offset: Number of results to skip. Defaults to 0.

        Returns:
            List of Plan resources.

        Raises:
            AtlasAPIError: If the request fails.
        """
        params = self._build_list_params(
            limit=limit,
            offset=offset,
            status=status.value if status else None,
        )

        resp = await self._client._request(
            "GET", f"/api/v1/deployments/{deployment_id}/plans", params=params
        )
        self._client._raise_for_status(resp)

        # Convert PlanRead to PlanReadWithTasks (tasks will be empty)
        plans = []
        for p in resp.json():
            plan_read = PlanRead.model_validate(p)
            # Create version with empty tasks
            plan_with_tasks = PlanReadWithTasks(**plan_read.model_dump(), tasks=[])
            plans.append(Plan(plan_with_tasks, self._client))

        return plans
