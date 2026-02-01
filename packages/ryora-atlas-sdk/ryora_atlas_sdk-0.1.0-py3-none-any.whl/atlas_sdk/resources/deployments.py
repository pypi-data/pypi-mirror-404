"""Deployment resource and resource manager.

Provides a high-level API for managing deployments:
- DeploymentsResource: Collection operations (create, get, list, wait_until_active)
- Deployment: Individual resource with bound methods (refresh, save, delete, wait_until_active)
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any
from uuid import UUID

from atlas_sdk._internal.polling import poll_until
from atlas_sdk.models.deployment import (
    DeploymentCreate,
    DeploymentRead,
    DeploymentUpdate,
)
from atlas_sdk.models.enums import DeploymentStatus
from atlas_sdk.resources.base import Resource, ResourceManager

if TYPE_CHECKING:
    pass

# Terminal statuses for deployments - once in these states, status will not change
_DEPLOYMENT_TERMINAL_STATUSES = {
    DeploymentStatus.COMPLETED,
    DeploymentStatus.FAILED,
}

# Progress callback type for waiter methods
ProgressCallback = Callable[[DeploymentRead], Awaitable[None] | None]


class Deployment(Resource[DeploymentRead]):
    """A deployment resource with bound methods.

    Wraps a DeploymentRead model and provides methods to refresh, save,
    and delete the deployment.

    All model fields are accessible as read-only attributes via delegation
    to the underlying DeploymentRead model:
        id: The deployment UUID.
        agent_definition_id: The agent definition UUID.
        blueprint_id: Optional blueprint UUID.
        name: The deployment name.
        description: Optional description.
        environment: The deployment environment (e.g., "production").
        status: The deployment status.
        config: Deployment configuration dict.
        project_context: Project context dict.
        spec_md_path: Optional spec markdown path.
        created_at: When the deployment was created.
        updated_at: When the deployment was last updated.

    Example:
        deployment = await client.deployments.get(deployment_id)

        # Access fields (delegated to underlying model)
        print(f"Deployment: {deployment.name} ({deployment.status})")

        # Update and save
        deployment.data.description = "Updated description"
        await deployment.save()

        # Refresh from server
        await deployment.refresh()

        # Delete
        await deployment.delete()
    """

    async def refresh(self) -> None:
        """Re-fetch this deployment from the server.

        Updates the internal data with the latest state from the server.

        Raises:
            AtlasNotFoundError: If the deployment no longer exists.
            AtlasAPIError: If the request fails.
        """
        resp = await self._client._request("GET", f"/api/v1/deployments/{self.id}")
        self._client._raise_for_status(resp)
        self._data = DeploymentRead.model_validate(resp.json())

    async def save(self) -> None:
        """Persist local changes to the server.

        Sends the current state of mutable fields (name, description, environment,
        status, config, project_context, spec_md_path) to the server.

        Raises:
            AtlasValidationError: If the update data is invalid.
            AtlasNotFoundError: If the deployment no longer exists.
            AtlasAPIError: If the request fails.
        """
        update = DeploymentUpdate(
            name=self._data.name,
            description=self._data.description,
            environment=self._data.environment,
            status=self._data.status,
            config=self._data.config,
            project_context=self._data.project_context,
            spec_md_path=self._data.spec_md_path,
        )
        resp = await self._client._request(
            "PATCH",
            f"/api/v1/deployments/{self.id}",
            json=update.model_dump(exclude_unset=True, mode="json"),
        )
        self._client._raise_for_status(resp)
        self._data = DeploymentRead.model_validate(resp.json())

    async def delete(self) -> None:
        """Delete this deployment from the server.

        After deletion, this resource should not be used further.

        Raises:
            AtlasNotFoundError: If the deployment does not exist.
            AtlasAPIError: If the request fails.
        """
        resp = await self._client._request("DELETE", f"/api/v1/deployments/{self.id}")
        self._client._raise_for_status(resp)

    async def wait_until_active(
        self,
        *,
        poll_interval: float = 2.0,
        timeout: float | None = 300.0,
        on_progress: ProgressCallback | None = None,
    ) -> None:
        """Wait for this deployment to become active.

        Polls the server until the deployment reaches ACTIVE status or a
        terminal status (COMPLETED, FAILED).

        Args:
            poll_interval: Seconds between polling attempts. Defaults to 2.0.
            timeout: Maximum seconds to wait. Defaults to 300.0 (5 minutes).
                Set to None to wait indefinitely.
            on_progress: Optional callback invoked after each poll with the
                current deployment state. Can be sync or async.

        Raises:
            AtlasTimeoutError: If the timeout is exceeded. The error includes
                the last known state via the `last_state` attribute.
            AtlasAPIError: If any request fails.

        Example:
            deployment = await client.deployments.create(...)

            # Simple wait
            await deployment.wait_until_active()

            # With progress callback
            async def on_progress(state):
                print(f"Status: {state.status.value}")

            await deployment.wait_until_active(
                timeout=600,
                on_progress=on_progress
            )
        """

        async def fetch_state() -> DeploymentRead:
            await self.refresh()
            return self._data

        def is_terminal(data: DeploymentRead) -> bool:
            return (
                data.status == DeploymentStatus.ACTIVE
                or data.status in _DEPLOYMENT_TERMINAL_STATUSES
            )

        await poll_until(
            fetch=fetch_state,
            is_terminal=is_terminal,
            poll_interval=poll_interval,
            timeout=timeout,
            on_progress=on_progress,
            timeout_message=lambda d: (
                f"Timeout waiting for deployment {self.id} to become active. "
                f"Current status: {d.status.value}"
            ),
            operation="wait_until_active",
        )

    def __repr__(self) -> str:
        """Return a string representation of the deployment."""
        return (
            f"<Deployment id={self.id} name={self.name!r} status={self.status.value}>"
        )


class DeploymentsResource(ResourceManager["Deployment", DeploymentRead]):
    """Resource manager for deployment collection operations.

    Provides methods for creating, retrieving, and listing deployments
    using a fluent API pattern.

    This class is designed for dependency injection - it accepts an
    HTTPClientProtocol implementation, making it easy to test.

    Args:
        client: The HTTP client protocol for making requests.

    Example:
        # Create a deployment
        deployment = await client.deployments.create(
            agent_definition_id=uuid,
            name="my-deployment",
            environment="production",
        )

        # Get a deployment by ID
        deployment = await client.deployments.get(deployment_id)

        # List deployments
        deployments = await client.deployments.list(environment="production")
    """

    _resource_class = Deployment
    _model_class = DeploymentRead
    _base_path = "/api/v1/deployments"

    async def create(
        self,
        agent_definition_id: UUID,
        name: str,
        *,
        blueprint_id: UUID | None = None,
        description: str | None = None,
        environment: str = "production",
        config: dict[str, Any] | None = None,
        project_context: dict[str, Any] | None = None,
        spec_md_path: str | None = None,
        idempotency_key: str | None = None,
    ) -> Deployment:
        """Create a new deployment.

        Args:
            agent_definition_id: The UUID of the agent definition to deploy.
            name: The name for the deployment.
            blueprint_id: Optional UUID of the blueprint to use.
            description: Optional description.
            environment: The deployment environment. Defaults to "production".
            config: Optional configuration dict.
            project_context: Optional project context dict.
            spec_md_path: Optional spec markdown path.
            idempotency_key: Optional idempotency key for safe retries. Use "auto"
                to generate a UUID-based key automatically.

        Returns:
            The created Deployment resource.

        Raises:
            AtlasValidationError: If the creation data is invalid.
            AtlasAPIError: If the request fails.
        """
        create_data = DeploymentCreate(
            agent_definition_id=agent_definition_id,
            blueprint_id=blueprint_id,
            name=name,
            description=description,
            environment=environment,
            config=config or {},
            project_context=project_context or {},
            spec_md_path=spec_md_path,
        )
        resp = await self._client._request(
            "POST",
            "/api/v1/deployments",
            idempotency_key=idempotency_key,
            json=create_data.model_dump(exclude_unset=True, mode="json"),
        )
        self._client._raise_for_status(resp)
        data = DeploymentRead.model_validate(resp.json())
        return Deployment(data, self._client)

    async def list(
        self,
        *,
        environment: str | None = None,
        active_only: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Deployment]:
        """List deployments with optional filters.

        Args:
            environment: Optional environment filter.
            active_only: If True, only return active deployments.
            limit: Maximum number of results to return. Defaults to 100.
            offset: Number of results to skip. Defaults to 0.

        Returns:
            List of Deployment resources.

        Raises:
            AtlasAPIError: If the request fails.
        """
        params = self._build_list_params(
            limit=limit,
            offset=offset,
            active_only=active_only,
            environment=environment,
        )
        return await self._list(params=params)

    async def wait_until_active(
        self,
        deployment_id: UUID,
        *,
        poll_interval: float = 2.0,
        timeout: float | None = 300.0,
        on_progress: ProgressCallback | None = None,
    ) -> Deployment:
        """Wait for a deployment to become active by ID.

        Polls the server until the deployment reaches ACTIVE status or a
        terminal status (COMPLETED, FAILED).

        Args:
            deployment_id: The UUID of the deployment to wait for.
            poll_interval: Seconds between polling attempts. Defaults to 2.0.
            timeout: Maximum seconds to wait. Defaults to 300.0 (5 minutes).
                Set to None to wait indefinitely.
            on_progress: Optional callback invoked after each poll with the
                current deployment state. Can be sync or async.

        Returns:
            The Deployment resource once it reaches ACTIVE or a terminal status.

        Raises:
            AtlasTimeoutError: If the timeout is exceeded. The error includes
                the last known state via the `last_state` attribute.
            AtlasNotFoundError: If the deployment does not exist.
            AtlasAPIError: If any request fails.

        Example:
            # Wait for a deployment to be ready
            deployment = await client.deployments.wait_until_active(
                deployment_id,
                timeout=600,
            )
            print(f"Deployment is {deployment.status}")
        """
        deployment = await self.get(deployment_id)
        await deployment.wait_until_active(
            poll_interval=poll_interval,
            timeout=timeout,
            on_progress=on_progress,
        )
        return deployment
