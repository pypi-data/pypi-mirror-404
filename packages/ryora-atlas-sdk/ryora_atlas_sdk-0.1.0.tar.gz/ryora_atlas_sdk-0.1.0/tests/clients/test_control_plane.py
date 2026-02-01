"""Tests for ControlPlaneClient admin/governance operations."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
import respx
from httpx import Response

from atlas_sdk.clients.control_plane import ControlPlaneClient
from atlas_sdk.exceptions import AtlasHTTPStatusError
from atlas_sdk.models.agent_definition import (
    AgentDefinitionCreate,
    AgentDefinitionUpdate,
)
from atlas_sdk.models.control_plane import (
    AgentClassCreate,
    AgentClassUpdate,
    GraspAnalysisCreate,
    ModelProviderCreate,
    ModelProviderUpdate,
    SystemPromptCreate,
    SystemPromptUpdate,
    ToolCreate,
    ToolSyncRequest,
    ToolUpdate,
)
from atlas_sdk.models.deployment import DeploymentCreate, DeploymentUpdate
from atlas_sdk.models.enums import (
    AgentDefinitionStatus,
    DeploymentStatus,
    GraspAnalysisStatus,
    SystemPromptStatus,
)


# =============================================================================
# Parametrized Test Data for Repetitive Patterns
# =============================================================================

# Pagination test cases: (endpoint, method_name, limit, offset, trailing_slash)
PAGINATION_TEST_CASES = [
    pytest.param(
        "/api/v1/agent-classes",
        "list_agent_classes",
        50,
        10,
        False,
        id="agent_classes",
    ),
    pytest.param(
        "/api/v1/agent-definitions",
        "list_agent_definitions",
        25,
        50,
        False,
        id="agent_definitions",
    ),
    pytest.param(
        "/api/v1/model-providers",
        "list_model_providers",
        20,
        5,
        False,
        id="model_providers",
    ),
    pytest.param(
        "/api/v1/system-prompts",
        "list_system_prompts",
        30,
        15,
        False,
        id="system_prompts",
    ),
    pytest.param(
        "/api/v1/tools/",
        "list_tools",
        40,
        20,
        True,
        id="tools",
    ),
]


@pytest.fixture
def base_url() -> str:
    return "http://control-plane"


@pytest.fixture
def client(base_url: str) -> ControlPlaneClient:
    return ControlPlaneClient(base_url=base_url)


@pytest.fixture
def agent_class_id() -> UUID:
    return uuid4()


@pytest.fixture
def definition_id() -> UUID:
    return uuid4()


@pytest.fixture
def provider_id() -> UUID:
    return uuid4()


@pytest.fixture
def prompt_id() -> UUID:
    return uuid4()


@pytest.fixture
def tool_id() -> UUID:
    return uuid4()


@pytest.fixture
def deployment_id() -> UUID:
    return uuid4()


@pytest.fixture
def analysis_id() -> UUID:
    return uuid4()


@pytest.fixture
def now_iso() -> str:
    """Provides a consistent ISO timestamp for mock responses."""
    return datetime.now(timezone.utc).isoformat()


@pytest.fixture
def make_agent_class_response(now_iso: str):
    """Factory fixture for creating agent class response data."""

    def _make(
        id: UUID,
        name: str = "BugHunter",
        description: str | None = "Test class",
    ) -> dict:
        return {
            "id": str(id),
            "name": name,
            "description": description,
            "created_at": now_iso,
            "updated_at": now_iso,
        }

    return _make


@pytest.fixture
def make_agent_definition_response(now_iso: str):
    """Factory fixture for creating agent definition response data."""

    def _make(
        id: UUID,
        agent_class_id: UUID | None = None,
        name: str = "researcher-v1",
        status: str = "draft",
        **kwargs,
    ) -> dict:
        base = {
            "id": str(id),
            "agent_class_id": str(agent_class_id) if agent_class_id else None,
            "name": name,
            "slug": name,
            "description": None,
            "status": status,
            "execution_mode": "ephemeral",
            "model_provider_id": None,
            "model_name": None,
            "config": {},
            "allow_outbound_a2a": False,
            "system_prompt_id": None,
            "structured_output_id": None,
            "created_at": now_iso,
            "updated_at": now_iso,
        }
        base.update(kwargs)
        return base

    return _make


@pytest.fixture
def make_model_provider_response(now_iso: str):
    """Factory fixture for creating model provider response data."""

    def _make(
        id: UUID,
        name: str = "openai-prod",
        api_base_url: str = "https://api.openai.com/v1",
        **kwargs,
    ) -> dict:
        base = {
            "id": str(id),
            "name": name,
            "api_base_url": api_base_url,
            "description": None,
            "config": {},
            "created_at": now_iso,
            "updated_at": now_iso,
        }
        base.update(kwargs)
        return base

    return _make


@pytest.fixture
def make_system_prompt_response(now_iso: str):
    """Factory fixture for creating system prompt response data."""

    def _make(
        id: UUID,
        name: str = "test-prompt",
        status: str = "draft",
        content: str = "Test content",
        **kwargs,
    ) -> dict:
        base = {
            "id": str(id),
            "agent_class_id": None,
            "name": name,
            "description": None,
            "status": status,
            "content": content,
            "content_storage_type": "inline",
            "meta": None,
            "created_at": now_iso,
            "updated_at": now_iso,
        }
        base.update(kwargs)
        return base

    return _make


@pytest.fixture
def make_tool_response():
    """Factory fixture for creating tool response data."""

    def _make(
        id: UUID,
        name: str = "search",
        description: str = "Search tool",
        **kwargs,
    ) -> dict:
        base = {
            "id": str(id),
            "name": name,
            "description": description,
            "json_schema": {"type": "object"},
            "safety_policy": None,
            "risk_level": "low",
        }
        base.update(kwargs)
        return base

    return _make


@pytest.fixture
def make_deployment_response(now_iso: str):
    """Factory fixture for creating deployment response data."""

    def _make(
        id: UUID,
        definition_id: UUID,
        name: str = "test-deployment",
        status: str = "active",
        **kwargs,
    ) -> dict:
        base = {
            "id": str(id),
            "agent_definition_id": str(definition_id),
            "blueprint_id": None,
            "name": name,
            "description": None,
            "environment": "staging",
            "status": status,
            "config": {},
            "project_context": {},
            "spec_md_path": None,
            "created_at": now_iso,
            "updated_at": now_iso,
        }
        base.update(kwargs)
        return base

    return _make


# =============================================================================
# Parametrized Tests - Consolidated Repetitive Patterns
# =============================================================================


class TestPaginationParameters:
    """Parametrized tests for pagination across all list endpoints.

    This class consolidates the repetitive test_list_*_with_pagination tests
    that previously appeared in each entity's test class. All tests follow
    the same pattern: verify that limit and offset parameters are correctly
    passed as query parameters to the API endpoint.
    """

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "endpoint,method_name,limit,offset,trailing_slash",
        PAGINATION_TEST_CASES,
    )
    async def test_list_with_pagination(
        self,
        client: ControlPlaneClient,
        base_url: str,
        endpoint: str,
        method_name: str,
        limit: int,
        offset: int,
        trailing_slash: bool,  # noqa: ARG002 - kept for documentation
    ) -> None:
        """Verify pagination parameters are correctly passed to all list endpoints.

        Args:
            client: The ControlPlaneClient instance.
            base_url: The base URL for the mock server.
            endpoint: The API endpoint path.
            method_name: The client method name to call.
            limit: The limit parameter value to test.
            offset: The offset parameter value to test.
            trailing_slash: Whether the endpoint has a trailing slash (unused in test).
        """
        async with respx.mock(base_url=base_url) as respx_mock:
            route = respx_mock.get(endpoint).mock(return_value=Response(200, json=[]))

            async with client:
                method = getattr(client, method_name)
                await method(limit=limit, offset=offset)

            assert route.called
            params = route.calls[0].request.url.params
            assert params.get("limit") == str(limit)
            assert params.get("offset") == str(offset)


class TestControlPlaneClientAgentClasses:
    """Tests for agent class methods."""

    @pytest.mark.asyncio
    async def test_create_agent_class_success(
        self, client: ControlPlaneClient, base_url: str, agent_class_id: UUID
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        response_data = {
            "id": str(agent_class_id),
            "name": "BugHunter",
            "description": "Security vulnerability detection",
            "created_at": now,
            "updated_at": now,
        }

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.post("/api/v1/agent-classes").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.create_agent_class(
                    AgentClassCreate(
                        name="BugHunter", description="Security vulnerability detection"
                    )
                )

            assert result.id == agent_class_id
            assert result.name == "BugHunter"
            assert result.description == "Security vulnerability detection"

    @pytest.mark.asyncio
    async def test_create_agent_class_with_idempotency_key(
        self, client: ControlPlaneClient, base_url: str, agent_class_id: UUID
    ) -> None:
        """Create agent class should pass idempotency key to header."""
        import httpx as _httpx

        now = datetime.now(timezone.utc).isoformat()
        response_data = {
            "id": str(agent_class_id),
            "name": "BugHunter",
            "description": "Test",
            "created_at": now,
            "updated_at": now,
        }
        captured_request: _httpx.Request | None = None

        async def capture_request(request: _httpx.Request) -> Response:
            nonlocal captured_request
            captured_request = request
            return Response(200, json=response_data)

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.post("/api/v1/agent-classes").mock(side_effect=capture_request)

            async with client:
                await client.create_agent_class(
                    AgentClassCreate(name="BugHunter", description="Test"),
                    idempotency_key="my-idem-key-123",
                )

        assert captured_request is not None
        assert "Idempotency-Key" in captured_request.headers
        assert captured_request.headers["Idempotency-Key"] == "my-idem-key-123"

    @pytest.mark.asyncio
    async def test_get_agent_class_success(
        self, client: ControlPlaneClient, base_url: str, agent_class_id: UUID
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        response_data = {
            "id": str(agent_class_id),
            "name": "BugHunter",
            "description": "Test class",
            "created_at": now,
            "updated_at": now,
        }

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get(f"/api/v1/agent-classes/{agent_class_id}").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.get_agent_class(agent_class_id)

            assert result.id == agent_class_id
            assert result.name == "BugHunter"

    @pytest.mark.asyncio
    async def test_get_agent_class_not_found(
        self, client: ControlPlaneClient, base_url: str, agent_class_id: UUID
    ) -> None:
        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get(f"/api/v1/agent-classes/{agent_class_id}").mock(
                return_value=Response(404, json={"detail": "Agent class not found"})
            )

            async with client:
                with pytest.raises(AtlasHTTPStatusError) as exc_info:
                    await client.get_agent_class(agent_class_id)

                assert "404" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_list_agent_classes_success(
        self, client: ControlPlaneClient, base_url: str, agent_class_id: UUID
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        response_data = [
            {
                "id": str(agent_class_id),
                "name": "BugHunter",
                "description": "Test class",
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": str(uuid4()),
                "name": "CodeReviewer",
                "description": None,
                "created_at": now,
                "updated_at": now,
            },
        ]

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get("/api/v1/agent-classes").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.list_agent_classes()

            assert len(result) == 2
            assert result[0].name == "BugHunter"
            assert result[1].name == "CodeReviewer"

    # NOTE: test_list_agent_classes_with_pagination moved to TestPaginationParameters

    @pytest.mark.asyncio
    async def test_update_agent_class_success(
        self, client: ControlPlaneClient, base_url: str, agent_class_id: UUID
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        response_data = {
            "id": str(agent_class_id),
            "name": "UpdatedBugHunter",
            "description": "Updated description",
            "created_at": now,
            "updated_at": now,
        }

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.patch(f"/api/v1/agent-classes/{agent_class_id}").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.update_agent_class(
                    agent_class_id,
                    AgentClassUpdate(
                        name="UpdatedBugHunter", description="Updated description"
                    ),
                )

            assert result.name == "UpdatedBugHunter"
            assert result.description == "Updated description"

    @pytest.mark.asyncio
    async def test_delete_agent_class_success(
        self, client: ControlPlaneClient, base_url: str, agent_class_id: UUID
    ) -> None:
        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.delete(f"/api/v1/agent-classes/{agent_class_id}").mock(
                return_value=Response(204)
            )

            async with client:
                await client.delete_agent_class(agent_class_id)


class TestControlPlaneClientAgentDefinitions:
    """Tests for agent definition methods."""

    @pytest.mark.asyncio
    async def test_create_agent_definition_success(
        self,
        client: ControlPlaneClient,
        base_url: str,
        agent_class_id: UUID,
        definition_id: UUID,
        provider_id: UUID,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        response_data = {
            "id": str(definition_id),
            "agent_class_id": str(agent_class_id),
            "name": "researcher-v1",
            "slug": "researcher-v1",
            "description": "Research agent",
            "status": "draft",
            "execution_mode": "ephemeral",
            "model_provider_id": str(provider_id),
            "model_name": "gpt-4",
            "config": {"temperature": 0.7},
            "allow_outbound_a2a": False,
            "system_prompt_id": None,
            "structured_output_id": None,
            "created_at": now,
            "updated_at": now,
        }

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.post("/api/v1/agent-definitions").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.create_agent_definition(
                    AgentDefinitionCreate(
                        agent_class_id=agent_class_id,
                        name="researcher-v1",
                        description="Research agent",
                        model_provider_id=provider_id,
                        model_name="gpt-4",
                        config={"temperature": 0.7},
                    )
                )

            assert result.id == definition_id
            assert result.name == "researcher-v1"
            assert result.status == AgentDefinitionStatus.DRAFT

    @pytest.mark.asyncio
    async def test_get_agent_definition_success(
        self,
        client: ControlPlaneClient,
        base_url: str,
        agent_class_id: UUID,
        definition_id: UUID,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        response_data = {
            "id": str(definition_id),
            "agent_class_id": str(agent_class_id),
            "name": "researcher-v1",
            "slug": "researcher-v1",
            "description": None,
            "status": "published",
            "execution_mode": "ephemeral",
            "model_provider_id": None,
            "model_name": None,
            "config": {},
            "allow_outbound_a2a": False,
            "system_prompt_id": None,
            "structured_output_id": None,
            "created_at": now,
            "updated_at": now,
        }

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get(f"/api/v1/agent-definitions/{definition_id}").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.get_agent_definition(definition_id)

            assert result.id == definition_id
            assert result.status == AgentDefinitionStatus.PUBLISHED

    @pytest.mark.asyncio
    async def test_get_agent_definition_config_success(
        self, client: ControlPlaneClient, base_url: str, definition_id: UUID
    ) -> None:
        response_data = {
            "id": str(definition_id),
            "name": "researcher-v1",
            "slug": "researcher-v1",
            "description": "Research agent",
            "status": "published",
            "execution_mode": "ephemeral",
            "model_name": "gpt-4",
            "config": {"temperature": 0.7},
            "system_prompt": "You are a research assistant.",
            "structured_output_schema": None,
            "tools": [{"name": "search", "schema": {}}],
        }

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get(f"/api/v1/agent-definitions/{definition_id}/config").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.get_agent_definition_config(definition_id)

            assert result.id == definition_id
            assert result.system_prompt == "You are a research assistant."
            assert len(result.tools) == 1

    @pytest.mark.asyncio
    async def test_list_agent_definitions_success(
        self,
        client: ControlPlaneClient,
        base_url: str,
        agent_class_id: UUID,
        definition_id: UUID,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        response_data = [
            {
                "id": str(definition_id),
                "agent_class_id": str(agent_class_id),
                "name": "researcher-v1",
                "slug": "researcher-v1",
                "description": None,
                "status": "draft",
                "execution_mode": "ephemeral",
                "model_provider_id": None,
                "model_name": None,
                "config": {},
                "allow_outbound_a2a": False,
                "system_prompt_id": None,
                "structured_output_id": None,
                "created_at": now,
                "updated_at": now,
            }
        ]

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get("/api/v1/agent-definitions").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.list_agent_definitions()

            assert len(result) == 1
            assert result[0].name == "researcher-v1"

    @pytest.mark.asyncio
    async def test_list_agent_definitions_with_status_filter(
        self, client: ControlPlaneClient, base_url: str
    ) -> None:
        async with respx.mock(base_url=base_url) as respx_mock:
            route = respx_mock.get("/api/v1/agent-definitions").mock(
                return_value=Response(200, json=[])
            )

            async with client:
                await client.list_agent_definitions(
                    status=AgentDefinitionStatus.PUBLISHED
                )

            assert route.called
            assert route.calls[0].request.url.params.get("status") == "published"

    # NOTE: test_list_agent_definitions_with_pagination moved to TestPaginationParameters

    @pytest.mark.asyncio
    async def test_update_agent_definition_success(
        self,
        client: ControlPlaneClient,
        base_url: str,
        agent_class_id: UUID,
        definition_id: UUID,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        response_data = {
            "id": str(definition_id),
            "agent_class_id": str(agent_class_id),
            "name": "researcher-v2",
            "slug": "researcher-v1",
            "description": "Updated",
            "status": "published",
            "execution_mode": "ephemeral",
            "model_provider_id": None,
            "model_name": None,
            "config": {},
            "allow_outbound_a2a": False,
            "system_prompt_id": None,
            "structured_output_id": None,
            "created_at": now,
            "updated_at": now,
        }

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.patch(f"/api/v1/agent-definitions/{definition_id}").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.update_agent_definition(
                    definition_id,
                    AgentDefinitionUpdate(
                        name="researcher-v2",
                        status=AgentDefinitionStatus.PUBLISHED,
                    ),
                )

            assert result.name == "researcher-v2"
            assert result.status == AgentDefinitionStatus.PUBLISHED

    @pytest.mark.asyncio
    async def test_delete_agent_definition_success(
        self, client: ControlPlaneClient, base_url: str, definition_id: UUID
    ) -> None:
        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.delete(f"/api/v1/agent-definitions/{definition_id}").mock(
                return_value=Response(204)
            )

            async with client:
                await client.delete_agent_definition(definition_id)

    @pytest.mark.asyncio
    async def test_add_tools_to_definition_success(
        self,
        client: ControlPlaneClient,
        base_url: str,
        agent_class_id: UUID,
        definition_id: UUID,
        tool_id: UUID,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        response_data = {
            "id": str(definition_id),
            "agent_class_id": str(agent_class_id),
            "name": "researcher-v1",
            "slug": "researcher-v1",
            "description": None,
            "status": "draft",
            "execution_mode": "ephemeral",
            "model_provider_id": None,
            "model_name": None,
            "config": {},
            "allow_outbound_a2a": False,
            "system_prompt_id": None,
            "structured_output_id": None,
            "created_at": now,
            "updated_at": now,
        }

        async with respx.mock(base_url=base_url) as respx_mock:
            route = respx_mock.post(
                f"/api/v1/agent-definitions/{definition_id}/tools"
            ).mock(return_value=Response(200, json=response_data))

            async with client:
                result = await client.add_tools_to_definition(definition_id, [tool_id])

            assert result.id == definition_id
            assert route.called


class TestControlPlaneClientModelProviders:
    """Tests for model provider methods."""

    @pytest.mark.asyncio
    async def test_create_model_provider_success(
        self, client: ControlPlaneClient, base_url: str, provider_id: UUID
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        response_data = {
            "id": str(provider_id),
            "name": "openai-prod",
            "api_base_url": "https://api.openai.com/v1",
            "description": "Production OpenAI",
            "config": {"model": "gpt-4"},
            "created_at": now,
            "updated_at": now,
        }

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.post("/api/v1/model-providers").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.create_model_provider(
                    ModelProviderCreate(
                        name="openai-prod",
                        api_base_url="https://api.openai.com/v1",
                        description="Production OpenAI",
                        config={"model": "gpt-4"},
                    )
                )

            assert result.id == provider_id
            assert result.name == "openai-prod"

    @pytest.mark.asyncio
    async def test_get_model_provider_success(
        self, client: ControlPlaneClient, base_url: str, provider_id: UUID
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        response_data = {
            "id": str(provider_id),
            "name": "openai-prod",
            "api_base_url": "https://api.openai.com/v1",
            "description": None,
            "config": {},
            "created_at": now,
            "updated_at": now,
        }

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get(f"/api/v1/model-providers/{provider_id}").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.get_model_provider(provider_id)

            assert result.id == provider_id

    @pytest.mark.asyncio
    async def test_list_model_providers_success(
        self, client: ControlPlaneClient, base_url: str, provider_id: UUID
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        response_data = [
            {
                "id": str(provider_id),
                "name": "openai-prod",
                "api_base_url": "https://api.openai.com/v1",
                "description": None,
                "config": {},
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": str(uuid4()),
                "name": "anthropic-prod",
                "api_base_url": "https://api.anthropic.com/v1",
                "description": None,
                "config": {},
                "created_at": now,
                "updated_at": now,
            },
        ]

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get("/api/v1/model-providers").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.list_model_providers()

            assert len(result) == 2
            assert result[0].name == "openai-prod"
            assert result[1].name == "anthropic-prod"

    # NOTE: test_list_model_providers_with_pagination moved to TestPaginationParameters

    @pytest.mark.asyncio
    async def test_update_model_provider_success(
        self, client: ControlPlaneClient, base_url: str, provider_id: UUID
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        response_data = {
            "id": str(provider_id),
            "name": "openai-updated",
            "api_base_url": "https://api.openai.com/v2",
            "description": "Updated provider",
            "config": {},
            "created_at": now,
            "updated_at": now,
        }

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.patch(f"/api/v1/model-providers/{provider_id}").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.update_model_provider(
                    provider_id,
                    ModelProviderUpdate(
                        name="openai-updated",
                        api_base_url="https://api.openai.com/v2",
                    ),
                )

            assert result.name == "openai-updated"

    @pytest.mark.asyncio
    async def test_delete_model_provider_success(
        self, client: ControlPlaneClient, base_url: str, provider_id: UUID
    ) -> None:
        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.delete(f"/api/v1/model-providers/{provider_id}").mock(
                return_value=Response(204)
            )

            async with client:
                await client.delete_model_provider(provider_id)

    @pytest.mark.asyncio
    async def test_verify_model_provider_success(
        self, client: ControlPlaneClient, base_url: str, provider_id: UUID
    ) -> None:
        response_data = {"status": "ok", "message": "Provider verified successfully"}

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.post(f"/api/v1/model-providers/{provider_id}/verify").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.verify_model_provider(provider_id)

            assert result["status"] == "ok"

    @pytest.mark.asyncio
    async def test_list_provider_models_success(
        self, client: ControlPlaneClient, base_url: str, provider_id: UUID
    ) -> None:
        response_data = [
            {"id": "gpt-4", "name": "GPT-4"},
            {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo"},
        ]

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get(f"/api/v1/model-providers/{provider_id}/models").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.list_provider_models(provider_id)

            assert len(result) == 2
            assert result[0]["id"] == "gpt-4"


class TestControlPlaneClientSystemPrompts:
    """Tests for system prompt methods."""

    @pytest.mark.asyncio
    async def test_create_system_prompt_success(
        self,
        client: ControlPlaneClient,
        base_url: str,
        prompt_id: UUID,
        agent_class_id: UUID,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        response_data = {
            "id": str(prompt_id),
            "agent_class_id": str(agent_class_id),
            "name": "bug-hunter-prompt",
            "description": "System prompt for bug hunting",
            "status": "draft",
            "content": "You are a security researcher.",
            "content_storage_type": "inline",
            "meta": None,
            "created_at": now,
            "updated_at": now,
        }

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.post("/api/v1/system-prompts").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.create_system_prompt(
                    SystemPromptCreate(
                        name="bug-hunter-prompt",
                        description="System prompt for bug hunting",
                        content="You are a security researcher.",
                        agent_class_id=agent_class_id,
                    )
                )

            assert result.id == prompt_id
            assert result.name == "bug-hunter-prompt"
            assert result.status == SystemPromptStatus.DRAFT

    @pytest.mark.asyncio
    async def test_get_system_prompt_success(
        self, client: ControlPlaneClient, base_url: str, prompt_id: UUID
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        response_data = {
            "id": str(prompt_id),
            "agent_class_id": None,
            "name": "test-prompt",
            "description": None,
            "status": "published",
            "content": "Test content",
            "content_storage_type": "inline",
            "meta": None,
            "created_at": now,
            "updated_at": now,
        }

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get(f"/api/v1/system-prompts/{prompt_id}").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.get_system_prompt(prompt_id)

            assert result.id == prompt_id
            assert result.status == SystemPromptStatus.PUBLISHED

    @pytest.mark.asyncio
    async def test_list_system_prompts_success(
        self, client: ControlPlaneClient, base_url: str, prompt_id: UUID
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        response_data = [
            {
                "id": str(prompt_id),
                "agent_class_id": None,
                "name": "prompt-1",
                "description": None,
                "status": "draft",
                "content": "Content 1",
                "content_storage_type": "inline",
                "meta": None,
                "created_at": now,
                "updated_at": now,
            }
        ]

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get("/api/v1/system-prompts").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.list_system_prompts()

            assert len(result) == 1
            assert result[0].name == "prompt-1"

    @pytest.mark.asyncio
    async def test_list_system_prompts_with_filters(
        self, client: ControlPlaneClient, base_url: str, agent_class_id: UUID
    ) -> None:
        async with respx.mock(base_url=base_url) as respx_mock:
            route = respx_mock.get("/api/v1/system-prompts").mock(
                return_value=Response(200, json=[])
            )

            async with client:
                await client.list_system_prompts(
                    agent_class_id=agent_class_id, status=SystemPromptStatus.PUBLISHED
                )

            assert route.called
            params = route.calls[0].request.url.params
            assert params.get("agent_class_id") == str(agent_class_id)
            assert params.get("status") == "published"

    # NOTE: test_list_system_prompts_with_pagination moved to TestPaginationParameters

    @pytest.mark.asyncio
    async def test_update_system_prompt_success(
        self, client: ControlPlaneClient, base_url: str, prompt_id: UUID
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        response_data = {
            "id": str(prompt_id),
            "agent_class_id": None,
            "name": "updated-prompt",
            "description": "Updated description",
            "status": "published",
            "content": "Updated content",
            "content_storage_type": "inline",
            "meta": None,
            "created_at": now,
            "updated_at": now,
        }

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.patch(f"/api/v1/system-prompts/{prompt_id}").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.update_system_prompt(
                    prompt_id,
                    SystemPromptUpdate(
                        name="updated-prompt",
                        status=SystemPromptStatus.PUBLISHED,
                        content="Updated content",
                    ),
                )

            assert result.name == "updated-prompt"
            assert result.status == SystemPromptStatus.PUBLISHED

    @pytest.mark.asyncio
    async def test_delete_system_prompt_success(
        self, client: ControlPlaneClient, base_url: str, prompt_id: UUID
    ) -> None:
        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.delete(f"/api/v1/system-prompts/{prompt_id}").mock(
                return_value=Response(204)
            )

            async with client:
                await client.delete_system_prompt(prompt_id)


class TestControlPlaneClientTools:
    """Tests for tool methods."""

    @pytest.mark.asyncio
    async def test_create_tool_success(
        self, client: ControlPlaneClient, base_url: str, tool_id: UUID
    ) -> None:
        response_data = {
            "id": str(tool_id),
            "name": "search",
            "description": "Search tool",
            "json_schema": {"type": "object"},
            "safety_policy": None,
            "risk_level": "low",
        }

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.post("/api/v1/tools").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.create_tool(
                    ToolCreate(
                        name="search",
                        description="Search tool",
                        json_schema={"type": "object"},
                    )
                )

            assert result.id == tool_id
            assert result.name == "search"

    @pytest.mark.asyncio
    async def test_update_tool_success(
        self, client: ControlPlaneClient, base_url: str, tool_id: UUID
    ) -> None:
        response_data = {
            "id": str(tool_id),
            "name": "search",
            "description": "Updated description",
            "json_schema": {"type": "object"},
            "safety_policy": None,
            "risk_level": "low",
        }

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.patch(f"/api/v1/tools/{tool_id}").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.update_tool(
                    tool_id,
                    ToolUpdate(
                        description="Updated description",
                    ),
                )

            assert result.description == "Updated description"

    @pytest.mark.asyncio
    async def test_list_tools_success(
        self, client: ControlPlaneClient, base_url: str, tool_id: UUID
    ) -> None:
        response_data = [
            {
                "id": str(tool_id),
                "name": "search",
                "description": "Search tool",
                "json_schema": {"type": "object"},
                "safety_policy": None,
                "risk_level": "low",
            }
        ]

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get("/api/v1/tools/").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.list_tools()

            assert len(result) == 1
            assert result[0].name == "search"

    # NOTE: test_list_tools_with_pagination moved to TestPaginationParameters

    @pytest.mark.asyncio
    async def test_get_tool_success(
        self, client: ControlPlaneClient, base_url: str, tool_id: UUID
    ) -> None:
        response_data = {
            "id": str(tool_id),
            "name": "search",
            "description": "Search tool",
            "json_schema": {"type": "object", "properties": {}},
            "safety_policy": "No dangerous queries",
            "risk_level": "medium",
        }

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get(f"/api/v1/tools/{tool_id}").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.get_tool(tool_id)

            assert result.id == tool_id
            assert result.risk_level == "medium"

    @pytest.mark.asyncio
    async def test_delete_tool_success(
        self, client: ControlPlaneClient, base_url: str, tool_id: UUID
    ) -> None:
        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.delete(f"/api/v1/tools/{tool_id}").mock(
                return_value=Response(204)
            )

            async with client:
                await client.delete_tool(tool_id)

    @pytest.mark.asyncio
    async def test_sync_tools_success(
        self, client: ControlPlaneClient, base_url: str, tool_id: UUID
    ) -> None:
        response_data = [
            {
                "id": str(tool_id),
                "name": "new_tool",
                "description": "New tool",
                "json_schema": {"type": "object"},
                "safety_policy": None,
                "risk_level": "low",
            }
        ]

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.post("/api/v1/tools/sync").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.sync_tools(
                    ToolSyncRequest(
                        tools=[
                            ToolCreate(
                                name="new_tool",
                                description="New tool",
                                json_schema={"type": "object"},
                            )
                        ]
                    )
                )

            assert len(result) == 1
            assert result[0].name == "new_tool"

    @pytest.mark.asyncio
    async def test_discover_tools_success(
        self, client: ControlPlaneClient, base_url: str, tool_id: UUID
    ) -> None:
        response_data = [
            {
                "id": str(tool_id),
                "name": "discovered_tool",
                "description": "Discovered tool",
                "json_schema": {"type": "object"},
                "safety_policy": None,
                "risk_level": "low",
            }
        ]

        async with respx.mock(base_url=base_url) as respx_mock:
            route = respx_mock.post("/api/v1/tools/discover").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.discover_tools("my_module.tools")

            assert len(result) == 1
            assert result[0].name == "discovered_tool"
            assert route.called


class TestControlPlaneClientDeployments:
    """Tests for deployment methods."""

    @pytest.mark.asyncio
    async def test_create_deployment_success(
        self,
        client: ControlPlaneClient,
        base_url: str,
        deployment_id: UUID,
        definition_id: UUID,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        response_data = {
            "id": str(deployment_id),
            "agent_definition_id": str(definition_id),
            "blueprint_id": None,
            "name": "prod-deployment",
            "description": "Production deployment",
            "environment": "production",
            "status": "spawning",
            "config": {},
            "project_context": {},
            "spec_md_path": None,
            "created_at": now,
            "updated_at": now,
        }

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.post("/api/v1/deployments").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.create_deployment(
                    DeploymentCreate(
                        agent_definition_id=definition_id,
                        name="prod-deployment",
                        description="Production deployment",
                        environment="production",
                    )
                )

            assert result.id == deployment_id
            assert result.name == "prod-deployment"
            assert result.status == DeploymentStatus.SPAWNING

    @pytest.mark.asyncio
    async def test_get_deployment_success(
        self,
        client: ControlPlaneClient,
        base_url: str,
        deployment_id: UUID,
        definition_id: UUID,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        response_data = {
            "id": str(deployment_id),
            "agent_definition_id": str(definition_id),
            "blueprint_id": None,
            "name": "test-deployment",
            "description": None,
            "environment": "staging",
            "status": "active",
            "config": {},
            "project_context": {},
            "spec_md_path": None,
            "created_at": now,
            "updated_at": now,
        }

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get(f"/api/v1/deployments/{deployment_id}").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.get_deployment(deployment_id)

            assert result.id == deployment_id
            assert result.environment == "staging"

    @pytest.mark.asyncio
    async def test_update_deployment_success(
        self,
        client: ControlPlaneClient,
        base_url: str,
        deployment_id: UUID,
        definition_id: UUID,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        response_data = {
            "id": str(deployment_id),
            "agent_definition_id": str(definition_id),
            "blueprint_id": None,
            "name": "updated-deployment",
            "description": "Updated description",
            "environment": "production",
            "status": "active",
            "config": {"key": "value"},
            "project_context": {},
            "spec_md_path": None,
            "created_at": now,
            "updated_at": now,
        }

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.patch(f"/api/v1/deployments/{deployment_id}").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.update_deployment(
                    deployment_id,
                    DeploymentUpdate(
                        name="updated-deployment", config={"key": "value"}
                    ),
                )

            assert result.name == "updated-deployment"
            assert result.config == {"key": "value"}

    @pytest.mark.asyncio
    async def test_list_deployments_success(
        self,
        client: ControlPlaneClient,
        base_url: str,
        deployment_id: UUID,
        definition_id: UUID,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        response_data = [
            {
                "id": str(deployment_id),
                "agent_definition_id": str(definition_id),
                "blueprint_id": None,
                "name": "deployment-1",
                "description": None,
                "environment": "production",
                "status": "active",
                "config": {},
                "project_context": {},
                "spec_md_path": None,
                "created_at": now,
                "updated_at": now,
            }
        ]

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get("/api/v1/deployments").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.list_deployments()

            assert len(result) == 1
            assert result[0].name == "deployment-1"

    @pytest.mark.asyncio
    async def test_list_deployments_with_filters(
        self, client: ControlPlaneClient, base_url: str
    ) -> None:
        async with respx.mock(base_url=base_url) as respx_mock:
            route = respx_mock.get("/api/v1/deployments").mock(
                return_value=Response(200, json=[])
            )

            async with client:
                await client.list_deployments(
                    environment="staging", active_only=True, limit=50, offset=10
                )

            assert route.called
            params = route.calls[0].request.url.params
            assert params.get("environment") == "staging"
            assert params.get("active_only") == "true"
            assert params.get("limit") == "50"
            assert params.get("offset") == "10"

    @pytest.mark.asyncio
    async def test_delete_deployment_success(
        self, client: ControlPlaneClient, base_url: str, deployment_id: UUID
    ) -> None:
        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.delete(f"/api/v1/deployments/{deployment_id}").mock(
                return_value=Response(204)
            )

            async with client:
                await client.delete_deployment(deployment_id)


class TestControlPlaneClientGraspAnalyses:
    """Tests for GRASP analysis methods."""

    @pytest.mark.asyncio
    async def test_create_grasp_analysis_success(
        self,
        client: ControlPlaneClient,
        base_url: str,
        deployment_id: UUID,
        analysis_id: UUID,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        response_data = {
            "id": str(analysis_id),
            "deployment_id": str(deployment_id),
            "blueprint_id": None,
            "agent_definition_id": None,
            "status": "pending",
            "governance_value": None,
            "governance_summary": None,
            "governance_evidence": {},
            "reach_value": None,
            "reach_summary": None,
            "reach_evidence": {},
            "agency_value": None,
            "agency_summary": None,
            "agency_evidence": {},
            "safeguards_value": None,
            "safeguards_summary": None,
            "safeguards_evidence": {},
            "potential_damage_value": None,
            "potential_damage_summary": None,
            "potential_damage_evidence": {},
            "analysis_context": {"test": "context"},
            "error_message": None,
            "created_at": now,
            "completed_at": None,
        }

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.post(f"/api/v1/deployments/{deployment_id}/grasp-analyses").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.create_grasp_analysis(
                    deployment_id,
                    GraspAnalysisCreate(analysis_context={"test": "context"}),
                )

            assert result.id == analysis_id
            assert result.status == GraspAnalysisStatus.PENDING

    @pytest.mark.asyncio
    async def test_get_grasp_analysis_success(
        self,
        client: ControlPlaneClient,
        base_url: str,
        analysis_id: UUID,
        deployment_id: UUID,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        response_data = {
            "id": str(analysis_id),
            "deployment_id": str(deployment_id),
            "blueprint_id": None,
            "agent_definition_id": None,
            "status": "completed",
            "governance_value": 85,
            "governance_summary": "Good governance",
            "governance_evidence": {"key": "value"},
            "reach_value": 60,
            "reach_summary": "Moderate reach",
            "reach_evidence": {},
            "agency_value": 70,
            "agency_summary": "Some autonomy",
            "agency_evidence": {},
            "safeguards_value": 90,
            "safeguards_summary": "Strong safeguards",
            "safeguards_evidence": {},
            "potential_damage_value": 40,
            "potential_damage_summary": "Limited damage potential",
            "potential_damage_evidence": {},
            "analysis_context": {},
            "error_message": None,
            "created_at": now,
            "completed_at": now,
        }

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get(f"/api/v1/grasp-analyses/{analysis_id}").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.get_grasp_analysis(analysis_id)

            assert result.id == analysis_id
            assert result.status == GraspAnalysisStatus.COMPLETED
            assert result.governance_value == 85

    @pytest.mark.asyncio
    async def test_list_grasp_analyses_success(
        self,
        client: ControlPlaneClient,
        base_url: str,
        deployment_id: UUID,
        analysis_id: UUID,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        response_data = [
            {
                "id": str(analysis_id),
                "deployment_id": str(deployment_id),
                "blueprint_id": None,
                "agent_definition_id": None,
                "status": "completed",
                "governance_value": 85,
                "reach_value": 60,
                "agency_value": 70,
                "safeguards_value": 90,
                "potential_damage_value": 40,
                "created_at": now,
                "completed_at": now,
            }
        ]

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get(f"/api/v1/deployments/{deployment_id}/grasp-analyses").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.list_grasp_analyses(deployment_id)

            assert len(result) == 1
            assert result[0].governance_value == 85

    @pytest.mark.asyncio
    async def test_list_grasp_analyses_with_status_filter(
        self, client: ControlPlaneClient, base_url: str, deployment_id: UUID
    ) -> None:
        async with respx.mock(base_url=base_url) as respx_mock:
            route = respx_mock.get(
                f"/api/v1/deployments/{deployment_id}/grasp-analyses"
            ).mock(return_value=Response(200, json=[]))

            async with client:
                await client.list_grasp_analyses(
                    deployment_id, status=GraspAnalysisStatus.COMPLETED
                )

            assert route.called
            assert route.calls[0].request.url.params.get("status") == "completed"

    @pytest.mark.asyncio
    async def test_query_grasp_analyses_success(
        self,
        client: ControlPlaneClient,
        base_url: str,
        deployment_id: UUID,
        analysis_id: UUID,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        response_data = [
            {
                "id": str(analysis_id),
                "deployment_id": str(deployment_id),
                "blueprint_id": None,
                "agent_definition_id": None,
                "status": "completed",
                "governance_value": 85,
                "reach_value": 60,
                "agency_value": 70,
                "safeguards_value": 90,
                "potential_damage_value": 40,
                "created_at": now,
                "completed_at": now,
            }
        ]

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get("/api/v1/grasp-analyses").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.query_grasp_analyses()

            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_query_grasp_analyses_with_filters(
        self, client: ControlPlaneClient, base_url: str, deployment_id: UUID
    ) -> None:
        async with respx.mock(base_url=base_url) as respx_mock:
            route = respx_mock.get("/api/v1/grasp-analyses").mock(
                return_value=Response(200, json=[])
            )

            async with client:
                await client.query_grasp_analyses(
                    deployment_id=deployment_id,
                    status=GraspAnalysisStatus.PENDING,
                    limit=25,
                    offset=5,
                )

            assert route.called
            params = route.calls[0].request.url.params
            assert params.get("deployment_id") == str(deployment_id)
            assert params.get("status") == "pending"
            assert params.get("limit") == "25"
            assert params.get("offset") == "5"


class TestControlPlaneClientHealth:
    """Tests for health and observability methods."""

    @pytest.mark.asyncio
    async def test_health_success(
        self, client: ControlPlaneClient, base_url: str
    ) -> None:
        response_data = {"status": "healthy", "version": "1.0.0"}

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get("/api/v1/health").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.health()

            assert result["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_health_error(
        self, client: ControlPlaneClient, base_url: str
    ) -> None:
        async with respx.mock(base_url=base_url) as respx_mock:
            # Use 500 instead of 503 since 503 is retryable
            respx_mock.get("/api/v1/health").mock(
                return_value=Response(500, json={"status": "unhealthy"})
            )

            async with client:
                with pytest.raises(AtlasHTTPStatusError) as exc_info:
                    await client.health()

                assert "500" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_metrics_success(
        self, client: ControlPlaneClient, base_url: str
    ) -> None:
        response_data = {
            "requests_total": 1000,
            "errors_total": 5,
            "latency_p99": 150.0,
        }

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get("/api/v1/metrics").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.metrics()

            assert result["requests_total"] == 1000

    @pytest.mark.asyncio
    async def test_logs_success(
        self, client: ControlPlaneClient, base_url: str
    ) -> None:
        response_data = [
            {
                "timestamp": "2024-01-01T00:00:00Z",
                "level": "INFO",
                "message": "Test log",
            }
        ]

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get("/api/v1/logs").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.logs()

            assert len(result) == 1
            assert result[0]["level"] == "INFO"

    @pytest.mark.asyncio
    async def test_logs_with_filters(
        self, client: ControlPlaneClient, base_url: str, deployment_id: UUID
    ) -> None:
        async with respx.mock(base_url=base_url) as respx_mock:
            route = respx_mock.get("/api/v1/logs").mock(
                return_value=Response(200, json=[])
            )

            async with client:
                await client.logs(deployment_id=deployment_id, level="ERROR", limit=50)

            assert route.called
            params = route.calls[0].request.url.params
            assert params.get("deployment_id") == str(deployment_id)
            assert params.get("level") == "ERROR"
            assert params.get("limit") == "50"
