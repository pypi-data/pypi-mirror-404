"""Agent instance resource and resource manager.

Provides a high-level API for managing agent instances:
- AgentInstancesResource: Collection operations (get, list, wait_until_active, wait_for_completion)
- AgentInstance: Individual resource with bound methods (refresh, wait_until_active, wait_for_completion)

Note:
    Agent instances are created by the Dispatch service, not directly
    through this API. This resource provides read-only access for
    monitoring purposes.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING
from uuid import UUID

from atlas_sdk._internal.polling import poll_until
from atlas_sdk.models.agent_instance import AgentInstanceRead
from atlas_sdk.models.enums import AgentInstanceStatus
from atlas_sdk.resources.base import Resource, ResourceManager

if TYPE_CHECKING:
    pass

# Terminal statuses for agent instances - once in these states, status will not change
_INSTANCE_TERMINAL_STATUSES = {
    AgentInstanceStatus.COMPLETED,
    AgentInstanceStatus.FAILED,
    AgentInstanceStatus.CANCELLED,
}

# Progress callback type for waiter methods
ProgressCallback = Callable[[AgentInstanceRead], Awaitable[None] | None]


class AgentInstance(Resource[AgentInstanceRead]):
    """An agent instance resource with bound methods.

    Wraps an AgentInstanceRead model and provides methods to refresh
    the instance data.

    Note:
        Agent instances are created and managed by the Dispatch service.
        This resource provides read-only access for monitoring. The save()
        and delete() methods raise NotImplementedError.

    All model fields are accessible as read-only attributes via delegation
    to the underlying AgentInstanceRead model:
        id: The agent instance UUID.
        deployment_id: The parent deployment UUID.
        agent_definition_id: The agent definition UUID.
        routing_key: The routing key.
        status: The instance status.
        input: The input data dict.
        output: Optional output data dict.
        error: Optional error message.
        exit_code: Optional exit code.
        metrics: Metrics dict.
        created_at: When the instance was created.
        started_at: Optional start timestamp.
        completed_at: Optional completion timestamp.

    Example:
        instance = await client.agent_instances.get(instance_id)

        # Access fields (delegated to underlying model)
        print(f"Instance: {instance.routing_key} ({instance.status})")

        # Check output
        if instance.output:
            print(f"Output: {instance.output}")

        # Refresh from server
        await instance.refresh()
    """

    async def refresh(self) -> None:
        """Re-fetch this agent instance from the server.

        Updates the internal data with the latest state from the server.

        Raises:
            AtlasNotFoundError: If the instance no longer exists.
            AtlasAPIError: If the request fails.
        """
        resp = await self._client._request("GET", f"/api/v1/instances/{self.id}")
        self._client._raise_for_status(resp)
        self._data = AgentInstanceRead.model_validate(resp.json())

    async def save(self) -> None:
        """Save is not supported for agent instances.

        Agent instances are managed by the Dispatch service.

        Raises:
            NotImplementedError: Always, as agent instances are read-only.
        """
        raise NotImplementedError(
            "Agent instances are managed by the Dispatch service and cannot "
            "be modified through this API."
        )

    async def delete(self) -> None:
        """Delete is not supported for agent instances.

        Agent instances are managed by the Dispatch service.

        Raises:
            NotImplementedError: Always, as agent instances are read-only.
        """
        raise NotImplementedError(
            "Agent instances are managed by the Dispatch service and cannot "
            "be deleted through this API."
        )

    async def wait_until_active(
        self,
        *,
        poll_interval: float = 1.0,
        timeout: float | None = 300.0,
        on_progress: ProgressCallback | None = None,
    ) -> None:
        """Wait for this agent instance to become active.

        Polls the server until the instance reaches ACTIVE status or a
        terminal status (COMPLETED, FAILED, CANCELLED).

        Args:
            poll_interval: Seconds between polling attempts. Defaults to 1.0.
            timeout: Maximum seconds to wait. Defaults to 300.0 (5 minutes).
                Set to None to wait indefinitely.
            on_progress: Optional callback invoked after each poll with the
                current instance state. Can be sync or async.

        Raises:
            AtlasTimeoutError: If the timeout is exceeded. The error includes
                the last known state via the `last_state` attribute.
            AtlasAPIError: If any request fails.

        Example:
            instance = await client.agent_instances.get(instance_id)

            # Simple wait
            await instance.wait_until_active()

            # With progress callback
            def on_progress(state):
                print(f"Status: {state.status.value}")

            await instance.wait_until_active(
                timeout=60,
                on_progress=on_progress
            )
        """

        async def fetch_state() -> AgentInstanceRead:
            await self.refresh()
            return self._data

        def is_terminal(data: AgentInstanceRead) -> bool:
            return (
                data.status == AgentInstanceStatus.ACTIVE
                or data.status in _INSTANCE_TERMINAL_STATUSES
            )

        await poll_until(
            fetch=fetch_state,
            is_terminal=is_terminal,
            poll_interval=poll_interval,
            timeout=timeout,
            on_progress=on_progress,
            timeout_message=lambda d: (
                f"Timeout waiting for agent instance {self.id} to become active. "
                f"Current status: {d.status.value}"
            ),
            operation="wait_until_active",
        )

    async def wait_for_completion(
        self,
        *,
        poll_interval: float = 1.0,
        timeout: float | None = None,
        on_progress: ProgressCallback | None = None,
    ) -> None:
        """Wait for this agent instance to reach a terminal status.

        Polls the server until the instance reaches COMPLETED, FAILED, or
        CANCELLED status.

        Args:
            poll_interval: Seconds between polling attempts. Defaults to 1.0.
            timeout: Maximum seconds to wait. None means wait indefinitely.
            on_progress: Optional callback invoked after each poll with the
                current instance state. Can be sync or async.

        Raises:
            AtlasTimeoutError: If the timeout is exceeded. The error includes
                the last known state via the `last_state` attribute.
            AtlasAPIError: If any request fails.

        Example:
            instance = await client.agent_instances.get(instance_id)

            # Wait for completion
            await instance.wait_for_completion(timeout=3600)

            if instance.status == AgentInstanceStatus.COMPLETED:
                print(f"Output: {instance.output}")
            elif instance.status == AgentInstanceStatus.FAILED:
                print(f"Error: {instance.error}")
        """

        async def fetch_state() -> AgentInstanceRead:
            await self.refresh()
            return self._data

        await poll_until(
            fetch=fetch_state,
            is_terminal=lambda d: d.status in _INSTANCE_TERMINAL_STATUSES,
            poll_interval=poll_interval,
            timeout=timeout,
            on_progress=on_progress,
            timeout_message=lambda d: (
                f"Timeout waiting for agent instance {self.id} to complete. "
                f"Current status: {d.status.value}"
            ),
            operation="wait_for_completion",
        )

    def __repr__(self) -> str:
        """Return a string representation of the agent instance."""
        return (
            f"<AgentInstance id={self.id} "
            f"routing_key={self.routing_key!r} "
            f"status={self.status.value}>"
        )


class AgentInstancesResource(ResourceManager["AgentInstance", AgentInstanceRead]):
    """Resource manager for agent instance collection operations.

    Provides methods for retrieving and listing agent instances using
    a fluent API pattern.

    Note:
        Agent instances are created by the Dispatch service, not directly
        through this API. This resource provides read-only access.

    Args:
        client: The HTTP client protocol for making requests.

    Example:
        # Get an agent instance by ID
        instance = await client.agent_instances.get(instance_id)

        # List instances for a deployment
        instances = await client.agent_instances.list(
            deployment_id=deployment_id,
            status=AgentInstanceStatus.ACTIVE
        )
    """

    _resource_class = AgentInstance
    _model_class = AgentInstanceRead
    _base_path = "/api/v1/instances"

    async def list(
        self,
        *,
        deployment_id: UUID | None = None,
        status: AgentInstanceStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AgentInstance]:
        """List agent instances with optional filters.

        Args:
            deployment_id: Optional deployment filter.
            status: Optional status filter.
            limit: Maximum number of results to return. Defaults to 100.
            offset: Number of results to skip. Defaults to 0.

        Returns:
            List of AgentInstance resources.

        Raises:
            AtlasAPIError: If the request fails.
        """
        params = self._build_list_params(
            limit=limit,
            offset=offset,
            deployment_id=str(deployment_id) if deployment_id else None,
            status=status.value if status else None,
        )
        return await self._list(params=params)

    async def wait_until_active(
        self,
        instance_id: UUID,
        *,
        poll_interval: float = 1.0,
        timeout: float | None = 300.0,
        on_progress: ProgressCallback | None = None,
    ) -> AgentInstance:
        """Wait for an agent instance to become active by ID.

        Polls the server until the instance reaches ACTIVE status or a
        terminal status (COMPLETED, FAILED, CANCELLED).

        Args:
            instance_id: The UUID of the agent instance to wait for.
            poll_interval: Seconds between polling attempts. Defaults to 1.0.
            timeout: Maximum seconds to wait. Defaults to 300.0 (5 minutes).
                Set to None to wait indefinitely.
            on_progress: Optional callback invoked after each poll with the
                current instance state. Can be sync or async.

        Returns:
            The AgentInstance resource once it reaches ACTIVE or a terminal status.

        Raises:
            AtlasTimeoutError: If the timeout is exceeded. The error includes
                the last known state via the `last_state` attribute.
            AtlasNotFoundError: If the instance does not exist.
            AtlasAPIError: If any request fails.

        Example:
            instance = await client.agent_instances.wait_until_active(
                instance_id,
                timeout=60,
            )
            print(f"Instance is {instance.status}")
        """
        instance = await self.get(instance_id)
        await instance.wait_until_active(
            poll_interval=poll_interval,
            timeout=timeout,
            on_progress=on_progress,
        )
        return instance

    async def wait_for_completion(
        self,
        instance_id: UUID,
        *,
        poll_interval: float = 1.0,
        timeout: float | None = None,
        on_progress: ProgressCallback | None = None,
    ) -> AgentInstance:
        """Wait for an agent instance to complete by ID.

        Polls the server until the instance reaches a terminal status
        (COMPLETED, FAILED, CANCELLED).

        Args:
            instance_id: The UUID of the agent instance to wait for.
            poll_interval: Seconds between polling attempts. Defaults to 1.0.
            timeout: Maximum seconds to wait. None means wait indefinitely.
            on_progress: Optional callback invoked after each poll with the
                current instance state. Can be sync or async.

        Returns:
            The AgentInstance resource once it reaches a terminal status.

        Raises:
            AtlasTimeoutError: If the timeout is exceeded. The error includes
                the last known state via the `last_state` attribute.
            AtlasNotFoundError: If the instance does not exist.
            AtlasAPIError: If any request fails.

        Example:
            instance = await client.agent_instances.wait_for_completion(
                instance_id,
                timeout=3600,
            )
            if instance.status == AgentInstanceStatus.COMPLETED:
                print(f"Output: {instance.output}")
        """
        instance = await self.get(instance_id)
        await instance.wait_for_completion(
            poll_interval=poll_interval,
            timeout=timeout,
            on_progress=on_progress,
        )
        return instance
