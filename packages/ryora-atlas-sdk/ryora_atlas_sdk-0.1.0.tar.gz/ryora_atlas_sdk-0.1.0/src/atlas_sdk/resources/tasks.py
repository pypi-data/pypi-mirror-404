"""Task resource and resource manager.

Provides a high-level API for managing plan tasks:
- TasksResource: Collection operations (get, list)
- Task: Individual resource with bound methods (refresh, save)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from atlas_sdk.models.enums import PlanTaskStatus
from atlas_sdk.models.plan import PlanTaskRead, PlanTaskReadEnriched, PlanTaskUpdate
from atlas_sdk.resources.base import Resource, ResourceManager

if TYPE_CHECKING:
    pass


class Task(Resource[PlanTaskReadEnriched]):
    """A task resource with bound methods.

    Wraps a PlanTaskReadEnriched model and provides methods to refresh
    and save the task.

    Note:
        Tasks cannot be deleted individually - they are deleted when their
        parent plan is deleted. The delete() method raises NotImplementedError.

    All model fields are accessible as read-only attributes via delegation
    to the underlying PlanTaskReadEnriched model:
        id: The task UUID.
        plan_id: The parent plan UUID.
        sequence: The task sequence number.
        description: The task description.
        validation: The validation criteria.
        assignee_agent_definition_id: Optional assignee agent definition UUID.
        assignee_agent_slug: Optional assignee agent slug (enriched).
        assignee_agent_name: Optional assignee agent name (enriched).
        status: The task status.
        result: Optional task result.
        meta: Task metadata dict.
        created_at: When the task was created.
        updated_at: When the task was last updated.

    Example:
        task = await client.tasks.get(task_id)

        # Access fields (delegated to underlying model)
        print(f"Task: {task.description} ({task.status})")

        # Update and save
        task.data.status = PlanTaskStatus.COMPLETED
        task.data.result = "Task completed successfully"
        await task.save()

        # Refresh from server
        await task.refresh()
    """

    async def refresh(self) -> None:
        """Re-fetch this task from the server.

        Updates the internal data with the latest state from the server.

        Raises:
            AtlasNotFoundError: If the task no longer exists.
            AtlasAPIError: If the request fails.
        """
        params: dict[str, Any] = {"enrich": True}
        resp = await self._client._request(
            "GET", f"/api/v1/tasks/{self.id}", params=params
        )
        self._client._raise_for_status(resp)
        self._data = PlanTaskReadEnriched.model_validate(resp.json())

    async def save(self) -> None:
        """Persist local changes to the server.

        Sends the current state of mutable fields (sequence, description,
        validation, assignee_agent_definition_id, status, result, meta)
        to the server.

        Raises:
            AtlasValidationError: If the update data is invalid.
            AtlasNotFoundError: If the task no longer exists.
            AtlasAPIError: If the request fails.
        """
        update = PlanTaskUpdate(
            sequence=self._data.sequence,
            description=self._data.description,
            validation=self._data.validation,
            assignee_agent_definition_id=self._data.assignee_agent_definition_id,
            status=self._data.status,
            result=self._data.result,
            meta=self._data.meta,
        )
        resp = await self._client._request(
            "PATCH",
            f"/api/v1/tasks/{self.id}",
            json=update.model_dump(exclude_unset=True, mode="json"),
        )
        self._client._raise_for_status(resp)
        # The PATCH endpoint returns PlanTaskRead, but we want enriched data
        # Re-fetch with enrichment to maintain consistency
        await self.refresh()

    async def delete(self) -> None:
        """Delete is not supported for tasks.

        Tasks are deleted when their parent plan is deleted.

        Raises:
            NotImplementedError: Always, as tasks cannot be deleted individually.
        """
        raise NotImplementedError(
            "Tasks cannot be deleted individually. Delete the parent plan instead."
        )

    def __repr__(self) -> str:
        """Return a string representation of the task."""
        return (
            f"<Task id={self.id} sequence={self.sequence} status={self.status.value}>"
        )


class TasksResource(ResourceManager["Task", PlanTaskReadEnriched]):
    """Resource manager for task collection operations.

    Provides methods for retrieving and listing tasks using a fluent
    API pattern.

    Note:
        Tasks are created through the PlansResource.append_tasks() method
        or by including tasks in the PlanCreate data.

    Args:
        client: The HTTP client protocol for making requests.

    Example:
        # Get a task by ID
        task = await client.tasks.get(task_id)

        # List tasks for a plan
        tasks = await client.tasks.list(plan_id, status=PlanTaskStatus.PENDING)
    """

    _resource_class = Task
    _model_class = PlanTaskReadEnriched
    _base_path = "/api/v1/tasks"

    async def get(self, task_id: UUID, *, enrich: bool = True) -> Task:
        """Get a task by ID.

        Args:
            task_id: The UUID of the task to retrieve.
            enrich: If True, include enriched data like agent instance info.
                Defaults to True.

        Returns:
            The Task resource.

        Raises:
            AtlasNotFoundError: If the task does not exist.
            AtlasAPIError: If the request fails.
        """
        params: dict[str, Any] = {"enrich": enrich}
        resp = await self._client._request(
            "GET", f"{self._base_path}/{task_id}", params=params
        )
        self._client._raise_for_status(resp)
        data = PlanTaskReadEnriched.model_validate(resp.json())
        return Task(data, self._client)

    async def list(
        self,
        plan_id: UUID,
        *,
        status: PlanTaskStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Task]:
        """List tasks within a plan.

        Note:
            The list endpoint returns PlanTaskRead (not enriched). Each task
            is wrapped in a Task resource that can be refreshed to get
            enriched data.

        Args:
            plan_id: The UUID of the plan containing the tasks.
            status: Optional status filter.
            limit: Maximum number of results to return. Defaults to 100.
            offset: Number of results to skip. Defaults to 0.

        Returns:
            List of Task resources.

        Raises:
            AtlasAPIError: If the request fails.
        """
        params = self._build_list_params(
            limit=limit,
            offset=offset,
            status=status.value if status else None,
        )

        resp = await self._client._request(
            "GET", f"/api/v1/plans/{plan_id}/tasks", params=params
        )
        self._client._raise_for_status(resp)

        # Convert PlanTaskRead to PlanTaskReadEnriched (enriched fields will be None)
        tasks = []
        for t in resp.json():
            task_read = PlanTaskRead.model_validate(t)
            # Create enriched version with None for enriched fields
            enriched = PlanTaskReadEnriched(
                **task_read.model_dump(),
                assignee_agent_slug=None,
                assignee_agent_name=None,
            )
            tasks.append(Task(enriched, self._client))

        return tasks
