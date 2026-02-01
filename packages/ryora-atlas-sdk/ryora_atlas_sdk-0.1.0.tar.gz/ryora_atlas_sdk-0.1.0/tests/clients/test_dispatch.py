"""Tests for DispatchClient."""

from uuid import UUID, uuid4

import pytest
import respx
from httpx import Response

from atlas_sdk.clients.dispatch import DispatchClient
from atlas_sdk.exceptions import AtlasHTTPStatusError
from atlas_sdk.models.dispatch import (
    A2ACallRequest,
    A2ACallResponse,
    A2ADirectoryResponse,
    AgentDirectoryEntry,
    AgentStatusResponse,
    SpawnRequest,
    SpawnResponse,
    StopResponse,
    WaitResponse,
)


@pytest.fixture
def base_url() -> str:
    return "http://dispatch-service"


@pytest.fixture
def client(base_url: str) -> DispatchClient:
    return DispatchClient(base_url=base_url)


@pytest.fixture
def definition_id() -> UUID:
    return uuid4()


@pytest.fixture
def deployment_id() -> UUID:
    return uuid4()


@pytest.fixture
def instance_id() -> UUID:
    return uuid4()


class TestDispatchClientSpawnAgent:
    """Tests for spawn_agent method."""

    @pytest.mark.asyncio
    async def test_spawn_agent_success(
        self,
        client: DispatchClient,
        base_url: str,
        definition_id: UUID,
        deployment_id: UUID,
        instance_id: UUID,
    ) -> None:
        response_data = {
            "status": "running",
            "port": 8080,
            "pid": 12345,
            "url": "http://localhost:8080",
            "deployment_id": str(deployment_id),
            "instance_id": str(instance_id),
        }

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.post("/agents/spawn").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                request = SpawnRequest(
                    agent_definition_id=definition_id,
                    deployment_id=deployment_id,
                    prompt="Test prompt",
                )
                result = await client.spawn_agent(request)

            assert isinstance(result, SpawnResponse)
            assert result.status == "running"
            assert result.port == 8080
            assert result.pid == 12345
            assert result.instance_id == instance_id

    @pytest.mark.asyncio
    async def test_spawn_agent_error(
        self,
        client: DispatchClient,
        base_url: str,
        definition_id: UUID,
        deployment_id: UUID,
    ) -> None:
        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.post("/agents/spawn").mock(
                return_value=Response(400, json={"detail": "Invalid request"})
            )

            async with client:
                request = SpawnRequest(
                    agent_definition_id=definition_id,
                    deployment_id=deployment_id,
                    prompt="Test prompt",
                )
                with pytest.raises(AtlasHTTPStatusError):
                    await client.spawn_agent(request)


class TestDispatchClientGetAgentStatus:
    """Tests for get_agent_status method."""

    @pytest.mark.asyncio
    async def test_get_agent_status_running(
        self,
        client: DispatchClient,
        base_url: str,
        definition_id: UUID,
        instance_id: UUID,
    ) -> None:
        response_data = {
            "definition_id": str(definition_id),
            "instance_id": str(instance_id),
            "port": 8080,
            "pid": 12345,
            "running": True,
        }

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get(f"/agents/{definition_id}").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.get_agent_status(definition_id)

            assert isinstance(result, AgentStatusResponse)
            assert result.definition_id == definition_id
            assert result.instance_id == instance_id
            assert result.running is True

    @pytest.mark.asyncio
    async def test_get_agent_status_not_running(
        self,
        client: DispatchClient,
        base_url: str,
        definition_id: UUID,
    ) -> None:
        response_data = {
            "definition_id": str(definition_id),
            "instance_id": None,
            "port": None,
            "pid": None,
            "running": False,
        }

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get(f"/agents/{definition_id}").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.get_agent_status(definition_id)

            assert result.running is False
            assert result.instance_id is None

    @pytest.mark.asyncio
    async def test_get_agent_status_not_found(
        self,
        client: DispatchClient,
        base_url: str,
        definition_id: UUID,
    ) -> None:
        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get(f"/agents/{definition_id}").mock(
                return_value=Response(404, json={"detail": "Agent not found"})
            )

            async with client:
                with pytest.raises(AtlasHTTPStatusError):
                    await client.get_agent_status(definition_id)


class TestDispatchClientStopAgent:
    """Tests for stop_agent method."""

    @pytest.mark.asyncio
    async def test_stop_agent_success(
        self,
        client: DispatchClient,
        base_url: str,
        definition_id: UUID,
    ) -> None:
        response_data = {
            "status": "stopped",
            "message": "Agent stopped successfully",
        }

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.delete(f"/agents/{definition_id}").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.stop_agent(definition_id)

            assert isinstance(result, StopResponse)
            assert result.status == "stopped"
            assert result.message == "Agent stopped successfully"

    @pytest.mark.asyncio
    async def test_stop_agent_not_running(
        self,
        client: DispatchClient,
        base_url: str,
        definition_id: UUID,
    ) -> None:
        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.delete(f"/agents/{definition_id}").mock(
                return_value=Response(404, json={"detail": "Agent not running"})
            )

            async with client:
                with pytest.raises(AtlasHTTPStatusError):
                    await client.stop_agent(definition_id)


class TestDispatchClientWaitForAgent:
    """Tests for wait_for_agent method."""

    @pytest.mark.asyncio
    async def test_wait_for_agent_success(
        self,
        client: DispatchClient,
        base_url: str,
        definition_id: UUID,
        instance_id: UUID,
    ) -> None:
        response_data = {
            "status": "completed",
            "instance_id": str(instance_id),
            "output": {"result": "analysis complete"},
            "error": None,
            "exit_code": 0,
        }

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.post(f"/agents/{definition_id}/wait").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.wait_for_agent(definition_id)

            assert isinstance(result, WaitResponse)
            assert result.status == "completed"
            assert result.instance_id == instance_id
            assert result.output == {"result": "analysis complete"}
            assert result.exit_code == 0

    @pytest.mark.asyncio
    async def test_wait_for_agent_with_error(
        self,
        client: DispatchClient,
        base_url: str,
        definition_id: UUID,
        instance_id: UUID,
    ) -> None:
        response_data = {
            "status": "failed",
            "instance_id": str(instance_id),
            "output": None,
            "error": "Agent crashed unexpectedly",
            "exit_code": 1,
        }

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.post(f"/agents/{definition_id}/wait").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.wait_for_agent(definition_id)

            assert result.status == "failed"
            assert result.error == "Agent crashed unexpectedly"
            assert result.exit_code == 1


class TestDispatchClientA2ACall:
    """Tests for a2a_call method."""

    @pytest.mark.asyncio
    async def test_a2a_call_success(
        self,
        client: DispatchClient,
        base_url: str,
        definition_id: UUID,
        instance_id: UUID,
    ) -> None:
        response_data = {
            "content": "Analysis result from called agent",
            "instance_id": str(instance_id),
            "metadata": {"tokens_used": 150},
        }

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.post("/a2a/call").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                request = A2ACallRequest(
                    agent_definition_id=definition_id,
                    prompt="Analyze this data",
                    routing_key="priority",
                )
                result = await client.a2a_call(request)

            assert isinstance(result, A2ACallResponse)
            assert result.content == "Analysis result from called agent"
            assert result.instance_id == instance_id
            assert result.metadata == {"tokens_used": 150}

    @pytest.mark.asyncio
    async def test_a2a_call_without_routing_key(
        self,
        client: DispatchClient,
        base_url: str,
        definition_id: UUID,
        instance_id: UUID,
    ) -> None:
        response_data = {
            "content": "Response without routing",
            "instance_id": str(instance_id),
            "metadata": None,
        }

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.post("/a2a/call").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                request = A2ACallRequest(
                    agent_definition_id=definition_id,
                    prompt="Simple request",
                )
                result = await client.a2a_call(request)

            assert result.content == "Response without routing"
            assert result.metadata is None


class TestDispatchClientGetAgentDirectory:
    """Tests for get_agent_directory method."""

    @pytest.mark.asyncio
    async def test_get_agent_directory_with_agents(
        self,
        client: DispatchClient,
        base_url: str,
        deployment_id: UUID,
    ) -> None:
        agent1_def_id = uuid4()
        agent1_instance_id = uuid4()
        agent1_class_id = uuid4()
        agent2_def_id = uuid4()
        agent2_instance_id = uuid4()
        agent2_class_id = uuid4()

        response_data = {
            "agents": [
                {
                    "agent_definition_id": str(agent1_def_id),
                    "instance_id": str(agent1_instance_id),
                    "url": "http://localhost:8080",
                    "port": 8080,
                    "running": True,
                    "slug": "researcher",
                    "agent_class_id": str(agent1_class_id),
                    "execution_mode": "autonomous",
                    "allow_outbound_a2a": True,
                },
                {
                    "agent_definition_id": str(agent2_def_id),
                    "instance_id": str(agent2_instance_id),
                    "url": "http://localhost:8081",
                    "port": 8081,
                    "running": True,
                    "slug": "analyzer",
                    "agent_class_id": str(agent2_class_id),
                    "execution_mode": "reactive",
                    "allow_outbound_a2a": False,
                },
            ],
            "deployment_id": str(deployment_id),
        }

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get("/a2a/directory").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.get_agent_directory()

            assert isinstance(result, A2ADirectoryResponse)
            assert len(result.agents) == 2
            assert result.deployment_id == deployment_id

            agent1 = result.agents[0]
            assert isinstance(agent1, AgentDirectoryEntry)
            assert agent1.slug == "researcher"
            assert agent1.allow_outbound_a2a is True

            agent2 = result.agents[1]
            assert agent2.slug == "analyzer"
            assert agent2.allow_outbound_a2a is False

    @pytest.mark.asyncio
    async def test_get_agent_directory_empty(
        self,
        client: DispatchClient,
        base_url: str,
        deployment_id: UUID,
    ) -> None:
        response_data = {
            "agents": [],
            "deployment_id": str(deployment_id),
        }

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get("/a2a/directory").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.get_agent_directory()

            assert result.agents == []


class TestDispatchClientHealth:
    """Tests for health method."""

    @pytest.mark.asyncio
    async def test_health_success(
        self,
        client: DispatchClient,
        base_url: str,
    ) -> None:
        response_data = {
            "status": "healthy",
            "version": "1.0.0",
            "uptime": 3600,
        }

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get("/health").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.health()

            assert result["status"] == "healthy"
            assert result["version"] == "1.0.0"
            assert result["uptime"] == 3600

    @pytest.mark.asyncio
    async def test_health_unhealthy(
        self,
        client: DispatchClient,
        base_url: str,
    ) -> None:
        async with respx.mock(base_url=base_url) as respx_mock:
            # Use 500 instead of 503 since 503 is retryable
            respx_mock.get("/health").mock(
                return_value=Response(500, json={"status": "unhealthy"})
            )

            async with client:
                with pytest.raises(AtlasHTTPStatusError):
                    await client.health()
