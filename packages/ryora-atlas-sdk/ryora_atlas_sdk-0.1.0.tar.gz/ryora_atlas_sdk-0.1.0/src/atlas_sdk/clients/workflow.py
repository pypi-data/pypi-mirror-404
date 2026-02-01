"""Atlas Workflow client for workflow orchestration operations.

This client provides methods for:
- Creating and managing plans
- Creating and managing tasks
- Monitoring agent definitions, deployments, and instances (read-only)
- Waiting for plan/task completion

Supports both low-level method-based API and high-level resource pattern:
    # Low-level (existing)
    plan = await client.create_plan(deployment_id, PlanCreate(...))

    # High-level (resource pattern)
    plan = await client.plans.create(deployment_id, goal="...")
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any, cast
from uuid import UUID

from atlas_sdk._internal.params import build_list_params
from atlas_sdk._internal.polling import poll_until
from atlas_sdk.clients.base import BaseClient

if TYPE_CHECKING:
    from atlas_sdk.resources.agent_instances import AgentInstancesResource
    from atlas_sdk.resources.deployments import DeploymentsResource
    from atlas_sdk.resources.plans import PlansResource
    from atlas_sdk.resources.tasks import TasksResource
from atlas_sdk.models.agent_definition import (
    AgentDefinitionConfig,
    AgentDefinitionRead,
)
from atlas_sdk.models.agent_instance import AgentInstanceRead
from atlas_sdk.models.deployment import DeploymentRead
from atlas_sdk.models.enums import (
    AgentDefinitionStatus,
    AgentInstanceStatus,
    PlanStatus,
    PlanTaskStatus,
)
from atlas_sdk.models.plan import (
    PlanCreate,
    PlanCreateResponse,
    PlanRead,
    PlanReadWithTasks,
    PlanTaskRead,
    PlanTaskReadEnriched,
    PlanTaskUpdate,
    PlanUpdate,
    TasksAppend,
    TasksAppendResponse,
)

# Progress callback types for waiter methods
PlanProgressCallback = Callable[[PlanReadWithTasks], Awaitable[None] | None]
TaskProgressCallback = Callable[[PlanTaskReadEnriched], Awaitable[None] | None]

# Terminal statuses for plans and tasks
_PLAN_TERMINAL_STATUSES = {
    PlanStatus.COMPLETED,
    PlanStatus.FAILED,
    PlanStatus.CANCELLED,
}
_TASK_TERMINAL_STATUSES = {
    PlanTaskStatus.COMPLETED,
    PlanTaskStatus.FAILED,
    PlanTaskStatus.SKIPPED,
}


class WorkflowClient(BaseClient):
    """Async client for workflow orchestration via the Atlas Control Plane.

    This client provides methods for user-authored workflow code that orchestrates
    agent execution via plans and tasks. It includes read-only access to agent
    definitions, deployments, and instances for monitoring purposes.

    Supports both low-level method-based API and high-level resource pattern:

    Low-level (method-based):
        plan = await client.create_plan(deployment_id, PlanCreate(...))
        task = await client.get_task(task_id)

    High-level (resource pattern):
        plan = await client.plans.create(deployment_id, goal="...")
        task = await client.tasks.get(task_id)

        # Resources support bound methods
        await plan.refresh()
        plan.data.status = PlanStatus.COMPLETED
        await plan.save()

        # Access related resources
        for task in plan.tasks:
            print(task.description)

    Note:
        This client intentionally excludes:
        - Agent instance creation/updates (handled by Dispatch)
        - Admin/governance operations (use ControlPlaneClient)

    Example:
        async with WorkflowClient(base_url="http://control-plane:8000") as client:
            # Check connectivity
            await client.health()

            # Create a plan with tasks (method-based)
            plan_response = await client.create_plan(deployment_id, PlanCreate(
                goal="Process customer data",
                tasks=[
                    PlanTaskCreate(sequence=1, description="Extract data"),
                    PlanTaskCreate(sequence=2, description="Transform data"),
                ]
            ))

            # Or use resource pattern
            plan = await client.plans.create(
                deployment_id,
                goal="Process customer data",
                tasks=[
                    PlanTaskCreate(sequence=1, description="Extract", validation="Done"),
                    PlanTaskCreate(sequence=2, description="Transform", validation="Done"),
                ]
            )

            # Wait for completion using bound method
            await plan.wait_for_completion(poll_interval=2.0, timeout=300.0)
    """

    _deployments_resource: DeploymentsResource | None = None
    _plans_resource: PlansResource | None = None
    _tasks_resource: TasksResource | None = None
    _agent_instances_resource: AgentInstancesResource | None = None

    @property
    def deployments(self) -> DeploymentsResource:
        """Access the deployments resource manager (read-only).

        Provides a high-level API for deployment operations:
            deployment = await client.deployments.get(deployment_id)
            deployments = await client.deployments.list()

        Note:
            WorkflowClient provides read-only access to deployments.
            Use ControlPlaneClient for create/delete operations.

        Returns:
            The DeploymentsResource manager instance.
        """
        if self._deployments_resource is None:
            from atlas_sdk.resources.deployments import DeploymentsResource

            self._deployments_resource = DeploymentsResource(self)
        return self._deployments_resource

    @property
    def plans(self) -> PlansResource:
        """Access the plans resource manager.

        Provides a high-level API for plan operations:
            plan = await client.plans.create(deployment_id, goal="...")
            plan = await client.plans.get(plan_id)
            plans = await client.plans.list(deployment_id)

        Returns:
            The PlansResource manager instance.
        """
        if self._plans_resource is None:
            from atlas_sdk.resources.plans import PlansResource

            self._plans_resource = PlansResource(self)
        return self._plans_resource

    @property
    def tasks(self) -> TasksResource:
        """Access the tasks resource manager.

        Provides a high-level API for task operations:
            task = await client.tasks.get(task_id)
            tasks = await client.tasks.list(plan_id)

        Note:
            Tasks are created through plans, not directly.
            Use plan.append_tasks() or include tasks in plans.create().

        Returns:
            The TasksResource manager instance.
        """
        if self._tasks_resource is None:
            from atlas_sdk.resources.tasks import TasksResource

            self._tasks_resource = TasksResource(self)
        return self._tasks_resource

    @property
    def agent_instances(self) -> AgentInstancesResource:
        """Access the agent instances resource manager (read-only).

        Provides a high-level API for agent instance operations:
            instance = await client.agent_instances.get(instance_id)
            instances = await client.agent_instances.list(deployment_id=...)

        Note:
            Agent instances are created by the Dispatch service.
            This resource provides read-only access for monitoring.

        Returns:
            The AgentInstancesResource manager instance.
        """
        if self._agent_instances_resource is None:
            from atlas_sdk.resources.agent_instances import AgentInstancesResource

            self._agent_instances_resource = AgentInstancesResource(self)
        return self._agent_instances_resource

    # -------------------------------------------------------------------------
    # Plans
    # -------------------------------------------------------------------------

    async def create_plan(
        self,
        deployment_id: UUID,
        plan_create: PlanCreate,
        *,
        idempotency_key: str | None = None,
    ) -> PlanCreateResponse:
        """Create a new plan within a deployment.

        Args:
            deployment_id: The UUID of the deployment.
            plan_create: The plan creation data.
            idempotency_key: Optional idempotency key for safe retries. Use "auto"
                to generate a UUID-based key automatically.

        Returns:
            The created plan with its tasks.

        Raises:
            AtlasAPIError: If the request fails.
        """
        return await self._post_one(
            f"/api/v1/deployments/{deployment_id}/plans",
            plan_create,
            PlanCreateResponse,
            idempotency_key=idempotency_key,
        )

    async def get_plan(self, plan_id: UUID) -> PlanReadWithTasks:
        """Get a plan by ID, including its tasks.

        Args:
            plan_id: The UUID of the plan.

        Returns:
            The plan details with tasks.

        Raises:
            AtlasAPIError: If the request fails.
        """
        return await self._get_one(f"/api/v1/plans/{plan_id}", PlanReadWithTasks)

    async def list_plans(
        self,
        deployment_id: UUID,
        status: PlanStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[PlanRead]:
        """List plans within a deployment.

        Args:
            deployment_id: The UUID of the deployment.
            status: Optional status filter.
            limit: Maximum number of results to return.
            offset: Number of results to skip.

        Returns:
            List of plans.

        Raises:
            AtlasAPIError: If the request fails.
        """
        params = build_list_params(limit, offset, status=status)
        return await self._get_many(
            f"/api/v1/deployments/{deployment_id}/plans", PlanRead, params=params
        )

    async def update_plan(self, plan_id: UUID, update_data: PlanUpdate) -> PlanRead:
        """Update a plan.

        Args:
            plan_id: The UUID of the plan to update.
            update_data: The fields to update.

        Returns:
            The updated plan.

        Raises:
            AtlasAPIError: If the request fails.
        """
        return await self._patch_one(f"/api/v1/plans/{plan_id}", update_data, PlanRead)

    # -------------------------------------------------------------------------
    # Tasks
    # -------------------------------------------------------------------------

    async def append_tasks(
        self,
        plan_id: UUID,
        tasks_append: TasksAppend,
        *,
        idempotency_key: str | None = None,
    ) -> TasksAppendResponse:
        """Append new tasks to a plan.

        Args:
            plan_id: The UUID of the plan.
            tasks_append: The tasks to append.
            idempotency_key: Optional idempotency key for safe retries. Use "auto"
                to generate a UUID-based key automatically.

        Returns:
            The response containing the appended tasks.

        Raises:
            AtlasAPIError: If the request fails.
        """
        return await self._post_one(
            f"/api/v1/plans/{plan_id}/tasks",
            tasks_append,
            TasksAppendResponse,
            idempotency_key=idempotency_key,
        )

    async def get_task(
        self, task_id: UUID, enrich: bool = True
    ) -> PlanTaskReadEnriched:
        """Get a task by ID.

        Args:
            task_id: The UUID of the task.
            enrich: If True, include enriched data like agent instance info.

        Returns:
            The task details.

        Raises:
            AtlasAPIError: If the request fails.
        """
        params: dict[str, Any] = {"enrich": enrich}
        return await self._get_one(
            f"/api/v1/tasks/{task_id}", PlanTaskReadEnriched, params=params
        )

    async def list_tasks(
        self,
        plan_id: UUID,
        status: PlanTaskStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[PlanTaskRead]:
        """List tasks within a plan.

        Args:
            plan_id: The UUID of the plan.
            status: Optional status filter.
            limit: Maximum number of results to return.
            offset: Number of results to skip.

        Returns:
            List of tasks.

        Raises:
            AtlasAPIError: If the request fails.
        """
        params = build_list_params(limit, offset, status=status)
        return await self._get_many(
            f"/api/v1/plans/{plan_id}/tasks", PlanTaskRead, params=params
        )

    async def update_task(
        self, task_id: UUID, update_data: PlanTaskUpdate
    ) -> PlanTaskRead:
        """Update a task.

        Args:
            task_id: The UUID of the task to update.
            update_data: The fields to update.

        Returns:
            The updated task.

        Raises:
            AtlasAPIError: If the request fails.
        """
        return await self._patch_one(
            f"/api/v1/tasks/{task_id}", update_data, PlanTaskRead
        )

    # -------------------------------------------------------------------------
    # Agent Definitions (Read-only)
    # -------------------------------------------------------------------------

    async def get_agent_definition(self, definition_id: UUID) -> AgentDefinitionRead:
        """Get an agent definition by ID.

        Args:
            definition_id: The UUID of the agent definition.

        Returns:
            The agent definition details.

        Raises:
            AtlasAPIError: If the request fails.
        """
        return await self._get_one(
            f"/api/v1/agent-definitions/{definition_id}", AgentDefinitionRead
        )

    async def list_agent_definitions(
        self,
        status: AgentDefinitionStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AgentDefinitionRead]:
        """List all agent definitions, optionally filtered by status.

        Args:
            status: Optional status filter.
            limit: Maximum number of results to return.
            offset: Number of results to skip.

        Returns:
            List of agent definitions.

        Raises:
            AtlasAPIError: If the request fails.
        """
        params = build_list_params(limit, offset, status=status)
        return await self._get_many(
            "/api/v1/agent-definitions", AgentDefinitionRead, params=params
        )

    async def get_agent_definition_config(
        self, definition_id: UUID
    ) -> AgentDefinitionConfig:
        """Get the runtime configuration for an agent definition.

        Args:
            definition_id: The UUID of the agent definition.

        Returns:
            The agent definition runtime configuration.

        Raises:
            AtlasAPIError: If the request fails.
        """
        return await self._get_one(
            f"/api/v1/agent-definitions/{definition_id}/config", AgentDefinitionConfig
        )

    # -------------------------------------------------------------------------
    # Deployments (Read-only)
    # -------------------------------------------------------------------------

    async def get_deployment(self, deployment_id: UUID) -> DeploymentRead:
        """Get a deployment by ID.

        Args:
            deployment_id: The UUID of the deployment.

        Returns:
            The deployment details.

        Raises:
            AtlasAPIError: If the request fails.
        """
        return await self._get_one(
            f"/api/v1/deployments/{deployment_id}", DeploymentRead
        )

    async def list_deployments(
        self,
        environment: str | None = None,
        active_only: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[DeploymentRead]:
        """List all deployments with optional filters.

        Args:
            environment: Optional environment filter.
            active_only: If True, only return active deployments.
            limit: Maximum number of results to return.
            offset: Number of results to skip.

        Returns:
            List of deployments.

        Raises:
            AtlasAPIError: If the request fails.
        """
        params = build_list_params(
            limit, offset, active_only=active_only, environment=environment
        )
        return await self._get_many(
            "/api/v1/deployments", DeploymentRead, params=params
        )

    # -------------------------------------------------------------------------
    # Agent Instances (Read-only)
    # -------------------------------------------------------------------------

    async def get_agent_instance(self, instance_id: UUID) -> AgentInstanceRead:
        """Get an agent instance by ID.

        Args:
            instance_id: The UUID of the agent instance.

        Returns:
            The agent instance details.

        Raises:
            AtlasAPIError: If the request fails.
        """
        return await self._get_one(
            f"/api/v1/instances/{instance_id}", AgentInstanceRead
        )

    async def list_agent_instances(
        self,
        deployment_id: UUID | None = None,
        status: AgentInstanceStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AgentInstanceRead]:
        """List agent instances with optional filters.

        Args:
            deployment_id: Optional deployment filter.
            status: Optional status filter.
            limit: Maximum number of results to return.
            offset: Number of results to skip.

        Returns:
            List of agent instances.

        Raises:
            AtlasAPIError: If the request fails.
        """
        params = build_list_params(
            limit, offset, deployment_id=deployment_id, status=status
        )
        return await self._get_many(
            "/api/v1/instances", AgentInstanceRead, params=params
        )

    # -------------------------------------------------------------------------
    # Health
    # -------------------------------------------------------------------------

    async def health(self) -> dict[str, Any]:
        """Check the health of the Control Plane service.

        Returns:
            Health check response with status and details.

        Raises:
            AtlasAPIError: If the request fails.
        """
        resp = await self._request("GET", "/api/v1/health")
        self._raise_for_status(resp)
        return cast(dict[str, Any], resp.json())

    # -------------------------------------------------------------------------
    # Convenience Methods
    # -------------------------------------------------------------------------

    async def wait_for_plan_completion(
        self,
        plan_id: UUID,
        *,
        poll_interval: float = 2.0,
        timeout: float | None = None,
        on_progress: PlanProgressCallback | None = None,
    ) -> PlanReadWithTasks:
        """Poll until a plan reaches a terminal status.

        Terminal statuses are: COMPLETED, FAILED, CANCELLED.

        Args:
            plan_id: The UUID of the plan to wait for.
            poll_interval: Seconds between polling attempts. Defaults to 2.0.
            timeout: Maximum seconds to wait. None means wait indefinitely.
            on_progress: Optional callback invoked after each poll with the
                current plan state including tasks. Can be sync or async.

        Returns:
            The plan with its tasks once it reaches a terminal status.

        Raises:
            AtlasTimeoutError: If the timeout is exceeded before the plan completes.
                The error includes the last known state via the `last_state`
                attribute, along with `timeout_seconds` and `operation`.
            AtlasAPIError: If any request fails.

        Example:
            # Simple wait
            plan = await client.wait_for_plan_completion(plan_id, timeout=600)

            # With progress callback
            async def on_progress(plan):
                completed = sum(1 for t in plan.tasks if t.status.value == "COMPLETED")
                print(f"Progress: {completed}/{len(plan.tasks)} tasks")

            plan = await client.wait_for_plan_completion(
                plan_id,
                timeout=600,
                on_progress=on_progress
            )
        """
        return await poll_until(
            fetch=lambda: self.get_plan(plan_id),
            is_terminal=lambda p: p.status in _PLAN_TERMINAL_STATUSES,
            poll_interval=poll_interval,
            timeout=timeout,
            on_progress=on_progress,
            timeout_message=lambda p: (
                f"Timeout waiting for plan {plan_id} to complete. "
                f"Current status: {p.status.value}"
            ),
            operation="wait_for_plan_completion",
        )

    async def wait_for_task_completion(
        self,
        task_id: UUID,
        *,
        poll_interval: float = 1.0,
        timeout: float | None = None,
        on_progress: TaskProgressCallback | None = None,
    ) -> PlanTaskReadEnriched:
        """Poll until a task reaches a terminal status.

        Terminal statuses are: COMPLETED, FAILED, SKIPPED.

        Args:
            task_id: The UUID of the task to wait for.
            poll_interval: Seconds between polling attempts. Defaults to 1.0.
            timeout: Maximum seconds to wait. None means wait indefinitely.
            on_progress: Optional callback invoked after each poll with the
                current task state. Can be sync or async.

        Returns:
            The task once it reaches a terminal status.

        Raises:
            AtlasTimeoutError: If the timeout is exceeded before the task completes.
                The error includes the last known state via the `last_state`
                attribute, along with `timeout_seconds` and `operation`.
            AtlasAPIError: If any request fails.

        Example:
            # Simple wait
            task = await client.wait_for_task_completion(task_id, timeout=300)

            # With progress callback
            def on_progress(task):
                print(f"Task status: {task.status.value}")

            task = await client.wait_for_task_completion(
                task_id,
                timeout=300,
                on_progress=on_progress
            )
        """
        return await poll_until(
            fetch=lambda: self.get_task(task_id),
            is_terminal=lambda t: t.status in _TASK_TERMINAL_STATUSES,
            poll_interval=poll_interval,
            timeout=timeout,
            on_progress=on_progress,
            timeout_message=lambda t: (
                f"Timeout waiting for task {task_id} to complete. "
                f"Current status: {t.status.value}"
            ),
            operation="wait_for_task_completion",
        )
