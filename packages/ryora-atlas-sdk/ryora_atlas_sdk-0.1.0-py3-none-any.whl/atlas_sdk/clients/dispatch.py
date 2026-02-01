"""Atlas Dispatch service client for agent lifecycle management.

This client provides methods for:
- Spawning and stopping agent processes
- Monitoring agent status
- Agent-to-agent (A2A) communication
- Agent directory discovery
"""

from typing import Any, cast
from uuid import UUID

from atlas_sdk.clients.base import BaseClient
from atlas_sdk.models.dispatch import (
    A2ACallRequest,
    A2ACallResponse,
    A2ADirectoryResponse,
    AgentStatusResponse,
    SpawnRequest,
    SpawnResponse,
    StopResponse,
    WaitResponse,
)


class DispatchClient(BaseClient):
    """Async client for agent lifecycle management via the Atlas Dispatch service.

    This client provides methods for managing agent processes, including spawning,
    stopping, monitoring, and inter-agent communication.

    Example:
        async with DispatchClient(base_url="http://dispatch:8000") as client:
            # Spawn an agent
            result = await client.spawn_agent(SpawnRequest(
                agent_definition_id=definition_id,
                deployment_id=deployment_id,
                prompt="Analyze the dataset"
            ))

            # Wait for completion
            completion = await client.wait_for_agent(definition_id)
    """

    # -------------------------------------------------------------------------
    # Agent Lifecycle
    # -------------------------------------------------------------------------

    async def spawn_agent(
        self,
        request: SpawnRequest,
        *,
        idempotency_key: str | None = None,
    ) -> SpawnResponse:
        """Spawn a new agent process.

        Args:
            request: The spawn request containing agent definition, deployment,
                and initial prompt.
            idempotency_key: Optional idempotency key for safe retries. Use "auto"
                to generate a UUID-based key automatically.

        Returns:
            The spawn response with process details (port, pid, url, instance_id).

        Raises:
            AtlasAPIError: If the request fails.
        """
        return await self._post_one(
            "/agents/spawn", request, SpawnResponse, idempotency_key=idempotency_key
        )

    async def get_agent_status(self, definition_id: UUID) -> AgentStatusResponse:
        """Get the status of a running agent.

        Args:
            definition_id: The UUID of the agent definition.

        Returns:
            The agent status including running state, port, pid, and instance_id.

        Raises:
            AtlasAPIError: If the request fails.
        """
        return await self._get_one(f"/agents/{definition_id}", AgentStatusResponse)

    async def stop_agent(self, definition_id: UUID) -> StopResponse:
        """Stop a running agent.

        Args:
            definition_id: The UUID of the agent definition to stop.

        Returns:
            The stop response with status and message.

        Raises:
            AtlasAPIError: If the request fails.
        """
        resp = await self._request("DELETE", f"/agents/{definition_id}")
        self._raise_for_status(resp)
        return StopResponse.model_validate(resp.json())

    async def wait_for_agent(self, definition_id: UUID) -> WaitResponse:
        """Block until an agent completes.

        Args:
            definition_id: The UUID of the agent definition to wait for.

        Returns:
            The wait response with completion status, output, and any errors.

        Raises:
            AtlasAPIError: If the request fails.
        """
        resp = await self._request("POST", f"/agents/{definition_id}/wait")
        self._raise_for_status(resp)
        return WaitResponse.model_validate(resp.json())

    # -------------------------------------------------------------------------
    # Agent-to-Agent Communication
    # -------------------------------------------------------------------------

    async def a2a_call(self, request: A2ACallRequest) -> A2ACallResponse:
        """Execute an agent-to-agent call.

        Args:
            request: The A2A call request containing target agent, prompt,
                and optional routing key.

        Returns:
            The A2A response with content from the called agent.

        Raises:
            AtlasAPIError: If the request fails.
        """
        return await self._post_one("/a2a/call", request, A2ACallResponse)

    async def get_agent_directory(self) -> A2ADirectoryResponse:
        """List running agents for discovery.

        Returns:
            The directory response containing a list of running agents
            with their connection details.

        Raises:
            AtlasAPIError: If the request fails.
        """
        return await self._get_one("/a2a/directory", A2ADirectoryResponse)

    # -------------------------------------------------------------------------
    # Health
    # -------------------------------------------------------------------------

    async def health(self) -> dict[str, Any]:
        """Check the health of the Dispatch service.

        Returns:
            Health check response with status and details.

        Raises:
            AtlasAPIError: If the request fails.
        """
        resp = await self._request("GET", "/health")
        self._raise_for_status(resp)
        return cast(dict[str, Any], resp.json())
