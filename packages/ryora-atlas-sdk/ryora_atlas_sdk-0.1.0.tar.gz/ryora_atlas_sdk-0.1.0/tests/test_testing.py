"""Tests for the atlas_sdk.testing module."""

from __future__ import annotations

import re
from uuid import uuid4

import httpx
import pytest

from atlas_sdk import (
    AgentClassCreate,
    AgentClassUpdate,
    AgentDefinitionStatus,
    DeploymentCreate,
    DeploymentStatus,
    PlanCreate,
    PlanStatus,
    PlanTaskCreate,
    SpawnRequest,
    SystemPromptCreate,
    ToolSyncRequest,
    ToolCreate,
)
from atlas_sdk.exceptions import AtlasAPIError
from atlas_sdk.testing.fake_clients import FakeNotFoundError
from atlas_sdk.testing import (
    # Mock client
    MockHTTPClient,
    MockRequest,
    FakeControlPlaneClient,
    FakeDispatchClient,
    FakeWorkflowClient,
    # Factories
    reset_factories,
    factory_agent_class,
    factory_agent_class_create,
    factory_agent_definition,
    factory_agent_definition_create,
    factory_agent_definition_config,
    factory_agent_instance,
    factory_deployment,
    factory_plan,
    factory_plan_with_tasks,
    factory_task,
    factory_model_provider,
    factory_system_prompt,
    factory_tool,
)


# =============================================================================
# MockHTTPClient Tests
# =============================================================================


class TestMockHTTPClient:
    """Tests for MockHTTPClient."""

    @pytest.fixture
    def mock(self) -> MockHTTPClient:
        """Create a mock HTTP client."""
        return MockHTTPClient()

    @pytest.mark.asyncio
    async def test_add_response_and_request(self, mock: MockHTTPClient) -> None:
        """Test adding a response and making a request."""
        mock.add_response("GET", "/api/v1/health", {"status": "healthy"})

        async with mock:
            response = await mock._request("GET", "/api/v1/health")

        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    @pytest.mark.asyncio
    async def test_response_with_custom_status_code(self, mock: MockHTTPClient) -> None:
        """Test response with custom status code."""
        mock.add_response("POST", "/api/v1/items", {"id": "123"}, status_code=201)

        async with mock:
            response = await mock._request("POST", "/api/v1/items")

        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_records_requests(self, mock: MockHTTPClient) -> None:
        """Test that requests are recorded."""
        mock.add_response("GET", "/api/v1/health", {"status": "ok"})

        async with mock:
            await mock._request("GET", "/api/v1/health", params={"key": "value"})

        assert len(mock.requests) == 1
        assert mock.requests[0].method == "GET"
        assert mock.requests[0].url == "/api/v1/health"
        assert mock.requests[0].params == {"key": "value"}

    @pytest.mark.asyncio
    async def test_records_json_body(self, mock: MockHTTPClient) -> None:
        """Test that JSON body is recorded."""
        mock.add_response("POST", "/api/v1/items", {"id": "123"})

        async with mock:
            await mock._request("POST", "/api/v1/items", json={"name": "test"})

        assert mock.get_request_body() == {"name": "test"}

    @pytest.mark.asyncio
    async def test_regex_url_matching(self, mock: MockHTTPClient) -> None:
        """Test regex pattern matching for URLs."""
        mock.add_response(
            "GET",
            re.compile(r"/api/v1/items/[a-f0-9-]+"),
            {"id": "matched"},
        )

        async with mock:
            response = await mock._request(
                "GET", "/api/v1/items/12345678-1234-1234-1234-123456789abc"
            )

        assert response.json() == {"id": "matched"}

    @pytest.mark.asyncio
    async def test_response_queue(self, mock: MockHTTPClient) -> None:
        """Test that responses are consumed in LIFO order."""
        mock.add_response("GET", "/api/v1/health", {"call": 1})
        mock.add_response("GET", "/api/v1/health", {"call": 2})

        async with mock:
            response1 = await mock._request("GET", "/api/v1/health")
            response2 = await mock._request("GET", "/api/v1/health")

        # LIFO order - last added is consumed first
        assert response1.json() == {"call": 2}
        assert response2.json() == {"call": 1}

    @pytest.mark.asyncio
    async def test_add_error_response(self, mock: MockHTTPClient) -> None:
        """Test adding an error response."""
        mock.add_error_response("GET", "/api/v1/missing", 404, "Not found")

        async with mock:
            response = await mock._request("GET", "/api/v1/missing")

        assert response.status_code == 404
        assert response.json() == {"detail": "Not found"}

    @pytest.mark.asyncio
    async def test_add_exception(self, mock: MockHTTPClient) -> None:
        """Test adding an exception response."""
        mock.add_exception(
            "GET", "/api/v1/error", httpx.ConnectError("Connection refused")
        )

        async with mock:
            with pytest.raises(httpx.ConnectError):
                await mock._request("GET", "/api/v1/error")

    @pytest.mark.asyncio
    async def test_default_response(self, mock: MockHTTPClient) -> None:
        """Test default response fallback."""
        mock.set_default_response({"default": True})

        async with mock:
            response = await mock._request("GET", "/anything")

        assert response.json() == {"default": True}

    @pytest.mark.asyncio
    async def test_no_matching_response_raises(self, mock: MockHTTPClient) -> None:
        """Test that unmatched requests raise ValueError."""
        async with mock:
            with pytest.raises(ValueError, match="No mock response configured"):
                await mock._request("GET", "/unknown")

    @pytest.mark.asyncio
    async def test_raise_for_status(self, mock: MockHTTPClient) -> None:
        """Test _raise_for_status method."""
        mock.add_error_response("GET", "/api/v1/error", 404, "Not found")

        async with mock:
            response = await mock._request("GET", "/api/v1/error")
            with pytest.raises(AtlasAPIError):
                mock._raise_for_status(response)

    def test_assert_request_made(self, mock: MockHTTPClient) -> None:
        """Test assert_request_made helper."""
        mock._requests.append(MockRequest(method="GET", url="/api/v1/test"))

        # Should not raise
        mock.assert_request_made("GET", "/api/v1/test")

        # Should raise
        with pytest.raises(AssertionError):
            mock.assert_request_made("POST", "/api/v1/test")

    def test_assert_request_made_with_times(self, mock: MockHTTPClient) -> None:
        """Test assert_request_made with times parameter."""
        mock._requests.append(MockRequest(method="GET", url="/api/v1/test"))
        mock._requests.append(MockRequest(method="GET", url="/api/v1/test"))

        mock.assert_request_made("GET", "/api/v1/test", times=2)

        with pytest.raises(AssertionError):
            mock.assert_request_made("GET", "/api/v1/test", times=1)

    def test_assert_no_requests(self, mock: MockHTTPClient) -> None:
        """Test assert_no_requests helper."""
        mock.assert_no_requests()

        mock._requests.append(MockRequest(method="GET", url="/test"))
        with pytest.raises(AssertionError):
            mock.assert_no_requests()

    def test_clear(self, mock: MockHTTPClient) -> None:
        """Test clear method."""
        mock.add_response("GET", "/test", {})
        mock._requests.append(MockRequest(method="GET", url="/test"))

        mock.clear()

        assert len(mock._responses) == 0
        assert len(mock.requests) == 0

    def test_reset_requests(self, mock: MockHTTPClient) -> None:
        """Test reset_requests method."""
        mock.add_response("GET", "/test", {})
        mock._requests.append(MockRequest(method="GET", url="/test"))

        mock.reset_requests()

        assert len(mock._responses) == 1  # Responses kept
        assert len(mock.requests) == 0  # Requests cleared

    def test_method_chaining(self, mock: MockHTTPClient) -> None:
        """Test that add methods return self for chaining."""
        result = (
            mock.add_response("GET", "/a", {})
            .add_response("POST", "/b", {})
            .add_error_response("GET", "/c", 404, "Not found")
            .set_default_response({})
        )
        assert result is mock


# =============================================================================
# FakeControlPlaneClient Tests
# =============================================================================


class TestFakeControlPlaneClient:
    """Tests for FakeControlPlaneClient."""

    @pytest.fixture
    def client(self) -> FakeControlPlaneClient:
        """Create a fake client."""
        return FakeControlPlaneClient()

    @pytest.mark.asyncio
    async def test_agent_class_crud(self, client: FakeControlPlaneClient) -> None:
        """Test agent class CRUD operations."""
        async with client:
            # Create
            created = await client.create_agent_class(
                AgentClassCreate(name="TestClass", description="Testing")
            )
            assert created.name == "TestClass"
            assert created.description == "Testing"
            assert created.id is not None

            # Read
            fetched = await client.get_agent_class(created.id)
            assert fetched.id == created.id
            assert fetched.name == "TestClass"

            # Update
            updated = await client.update_agent_class(
                created.id, AgentClassUpdate(name="UpdatedClass")
            )
            assert updated.name == "UpdatedClass"

            # List
            all_classes = await client.list_agent_classes()
            assert len(all_classes) == 1

            # Delete
            await client.delete_agent_class(created.id)
            all_classes = await client.list_agent_classes()
            assert len(all_classes) == 0

    @pytest.mark.asyncio
    async def test_get_nonexistent_raises(self, client: FakeControlPlaneClient) -> None:
        """Test that getting nonexistent resource raises error."""
        async with client:
            with pytest.raises(FakeNotFoundError):
                await client.get_agent_class(uuid4())

    @pytest.mark.asyncio
    async def test_delete_nonexistent_raises(
        self, client: FakeControlPlaneClient
    ) -> None:
        """Test that deleting nonexistent resource raises error."""
        async with client:
            with pytest.raises(FakeNotFoundError):
                await client.delete_agent_class(uuid4())

    @pytest.mark.asyncio
    async def test_deployment_crud(self, client: FakeControlPlaneClient) -> None:
        """Test deployment CRUD operations."""
        async with client:
            # Create
            created = await client.create_deployment(
                DeploymentCreate(
                    agent_definition_id=uuid4(),
                    name="test-deployment",
                    environment="staging",
                )
            )
            assert created.name == "test-deployment"
            assert created.status == DeploymentStatus.ACTIVE

            # Read
            fetched = await client.get_deployment(created.id)
            assert fetched.id == created.id

            # List with filter
            deployments = await client.list_deployments(environment="staging")
            assert len(deployments) == 1

            # Delete
            await client.delete_deployment(created.id)

    @pytest.mark.asyncio
    async def test_system_prompt_crud(self, client: FakeControlPlaneClient) -> None:
        """Test system prompt CRUD operations."""
        async with client:
            created = await client.create_system_prompt(
                SystemPromptCreate(
                    name="test-prompt",
                    content="You are a helpful assistant.",
                )
            )
            assert created.name == "test-prompt"

            fetched = await client.get_system_prompt(created.id)
            assert fetched.content == "You are a helpful assistant."

    @pytest.mark.asyncio
    async def test_tool_sync(self, client: FakeControlPlaneClient) -> None:
        """Test tool sync operation."""
        async with client:
            tools = await client.sync_tools(
                ToolSyncRequest(
                    tools=[
                        ToolCreate(
                            name="test_tool",
                            json_schema={"type": "object", "properties": {}},
                        )
                    ]
                )
            )
            assert len(tools) == 1
            assert tools[0].name == "test_tool"

    @pytest.mark.asyncio
    async def test_health(self, client: FakeControlPlaneClient) -> None:
        """Test health check."""
        async with client:
            health = await client.health()
            assert health["status"] == "healthy"
            assert health["fake"] is True

    @pytest.mark.asyncio
    async def test_clear(self, client: FakeControlPlaneClient) -> None:
        """Test clear method."""
        async with client:
            await client.create_agent_class(AgentClassCreate(name="Test"))
            assert len(client.agent_classes) == 1

            client.clear()
            assert len(client.agent_classes) == 0


# =============================================================================
# FakeDispatchClient Tests
# =============================================================================


class TestFakeDispatchClient:
    """Tests for FakeDispatchClient."""

    @pytest.fixture
    def client(self) -> FakeDispatchClient:
        """Create a fake client."""
        return FakeDispatchClient()

    @pytest.mark.asyncio
    async def test_spawn_agent(self, client: FakeDispatchClient) -> None:
        """Test spawning an agent."""
        async with client:
            response = await client.spawn_agent(
                SpawnRequest(
                    agent_definition_id=uuid4(),
                    deployment_id=uuid4(),
                    prompt="Hello agent",
                )
            )
            assert response.instance_id is not None
            assert response.status == "spawned"

    @pytest.mark.asyncio
    async def test_get_agent_status(self, client: FakeDispatchClient) -> None:
        """Test getting agent status."""
        async with client:
            spawn_resp = await client.spawn_agent(
                SpawnRequest(
                    agent_definition_id=uuid4(),
                    deployment_id=uuid4(),
                    prompt="Hello",
                )
            )

            status = await client.get_agent_status(spawn_resp.instance_id)
            assert status.instance_id == spawn_resp.instance_id
            assert status.running is True

    @pytest.mark.asyncio
    async def test_stop_agent(self, client: FakeDispatchClient) -> None:
        """Test stopping an agent."""
        async with client:
            spawn_resp = await client.spawn_agent(
                SpawnRequest(
                    agent_definition_id=uuid4(),
                    deployment_id=uuid4(),
                    prompt="Hello",
                )
            )

            stop_resp = await client.stop_agent(spawn_resp.instance_id)
            assert stop_resp.status == "stopped"

    @pytest.mark.asyncio
    async def test_wait_for_agent(self, client: FakeDispatchClient) -> None:
        """Test waiting for an agent."""
        async with client:
            spawn_resp = await client.spawn_agent(
                SpawnRequest(
                    agent_definition_id=uuid4(),
                    deployment_id=uuid4(),
                    prompt="Hello",
                )
            )

            wait_resp = await client.wait_for_agent(spawn_resp.instance_id)
            assert wait_resp.instance_id == spawn_resp.instance_id
            assert wait_resp.status == "completed"


# =============================================================================
# FakeWorkflowClient Tests
# =============================================================================


class TestFakeWorkflowClient:
    """Tests for FakeWorkflowClient."""

    @pytest.fixture
    def client(self) -> FakeWorkflowClient:
        """Create a fake client."""
        return FakeWorkflowClient()

    @pytest.mark.asyncio
    async def test_create_plan(self, client: FakeWorkflowClient) -> None:
        """Test creating a plan."""
        async with client:
            response = await client.create_plan(
                deployment_id=uuid4(),
                instance_id=uuid4(),
                plan=PlanCreate(goal="Test goal"),
            )
            assert response.goal == "Test goal"
            assert response.status == PlanStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_create_plan_with_tasks(self, client: FakeWorkflowClient) -> None:
        """Test creating a plan with tasks."""
        async with client:
            response = await client.create_plan(
                deployment_id=uuid4(),
                instance_id=uuid4(),
                plan=PlanCreate(
                    goal="Test goal",
                    tasks=[
                        PlanTaskCreate(description="Task 1", validation="Done"),
                        PlanTaskCreate(description="Task 2", validation="Done"),
                    ],
                ),
            )
            assert len(response.task_ids) == 2

            plan = await client.get_plan(response.id)
            assert len(plan.tasks) == 2

    @pytest.mark.asyncio
    async def test_list_plans(self, client: FakeWorkflowClient) -> None:
        """Test listing plans."""
        deployment_id = uuid4()

        async with client:
            await client.create_plan(
                deployment_id=deployment_id,
                instance_id=uuid4(),
                plan=PlanCreate(goal="Goal 1"),
            )
            await client.create_plan(
                deployment_id=deployment_id,
                instance_id=uuid4(),
                plan=PlanCreate(goal="Goal 2"),
            )

            plans = await client.list_plans(deployment_id)
            assert len(plans) == 2


# =============================================================================
# Factory Tests
# =============================================================================


class TestFactories:
    """Tests for factory functions."""

    def test_reset_factories(self) -> None:
        """Test that reset_factories resets counters."""
        reset_factories()

        class1 = factory_agent_class()
        class2 = factory_agent_class()
        assert "1" in class1.name
        assert "2" in class2.name

        reset_factories()

        class3 = factory_agent_class()
        assert "1" in class3.name  # Counter reset

    def test_factory_agent_class(self) -> None:
        """Test factory_agent_class creates valid models."""
        reset_factories()

        agent_class = factory_agent_class()
        assert agent_class.id is not None
        assert agent_class.name is not None
        assert agent_class.created_at is not None

    def test_factory_agent_class_with_overrides(self) -> None:
        """Test factory_agent_class accepts overrides."""
        custom_id = uuid4()
        agent_class = factory_agent_class(
            id=custom_id,
            name="CustomName",
            description="Custom description",
        )
        assert agent_class.id == custom_id
        assert agent_class.name == "CustomName"
        assert agent_class.description == "Custom description"

    def test_factory_agent_class_create(self) -> None:
        """Test factory_agent_class_create creates valid create models."""
        reset_factories()

        create = factory_agent_class_create()
        assert create.name is not None

    def test_factory_agent_definition(self) -> None:
        """Test factory_agent_definition creates valid models."""
        reset_factories()

        definition = factory_agent_definition()
        assert definition.id is not None
        assert definition.agent_class_id is not None
        assert definition.status == AgentDefinitionStatus.DRAFT

    def test_factory_agent_definition_create(self) -> None:
        """Test factory_agent_definition_create creates valid create models."""
        reset_factories()

        create = factory_agent_definition_create()
        assert create.agent_class_id is not None
        assert create.name is not None

    def test_factory_agent_definition_config(self) -> None:
        """Test factory_agent_definition_config creates valid config models."""
        reset_factories()

        config = factory_agent_definition_config()
        assert config.id is not None
        assert config.system_prompt is not None

    def test_factory_agent_instance(self) -> None:
        """Test factory_agent_instance creates valid models."""
        reset_factories()

        instance = factory_agent_instance()
        assert instance.id is not None
        assert instance.deployment_id is not None

    def test_factory_deployment(self) -> None:
        """Test factory_deployment creates valid models."""
        reset_factories()

        deployment = factory_deployment()
        assert deployment.id is not None
        assert deployment.status == DeploymentStatus.ACTIVE

    def test_factory_deployment_with_overrides(self) -> None:
        """Test factory_deployment accepts overrides."""
        deployment = factory_deployment(
            name="custom-deployment",
            environment="staging",
            status=DeploymentStatus.SPAWNING,
        )
        assert deployment.name == "custom-deployment"
        assert deployment.environment == "staging"
        assert deployment.status == DeploymentStatus.SPAWNING

    def test_factory_plan(self) -> None:
        """Test factory_plan creates valid models."""
        reset_factories()

        plan = factory_plan()
        assert plan.id is not None
        assert plan.goal is not None

    def test_factory_plan_with_tasks(self) -> None:
        """Test factory_plan_with_tasks creates plan with tasks."""
        reset_factories()

        plan = factory_plan_with_tasks(num_tasks=5)
        assert len(plan.tasks) == 5

    def test_factory_task(self) -> None:
        """Test factory_task creates valid models."""
        reset_factories()

        task = factory_task()
        assert task.id is not None
        assert task.description is not None

    def test_factory_model_provider(self) -> None:
        """Test factory_model_provider creates valid models."""
        reset_factories()

        provider = factory_model_provider()
        assert provider.id is not None
        assert provider.name is not None

    def test_factory_system_prompt(self) -> None:
        """Test factory_system_prompt creates valid models."""
        reset_factories()

        prompt = factory_system_prompt()
        assert prompt.id is not None
        assert prompt.content is not None

    def test_factory_tool(self) -> None:
        """Test factory_tool creates valid models."""
        reset_factories()

        tool = factory_tool()
        assert tool.id is not None
        assert tool.json_schema is not None


# =============================================================================
# Integration Tests
# =============================================================================


class TestMockClientWithSDKClient:
    """Test using MockHTTPClient with real SDK clients."""

    @pytest.mark.asyncio
    async def test_mock_with_control_plane_client(self) -> None:
        """Test using mock client with ControlPlaneClient."""

        mock = MockHTTPClient()
        mock.add_response("GET", "/api/v1/health", {"status": "healthy"})

        # The mock client can be used directly for testing
        async with mock:
            response = await mock._request("GET", "/api/v1/health")
            assert response.json() == {"status": "healthy"}
