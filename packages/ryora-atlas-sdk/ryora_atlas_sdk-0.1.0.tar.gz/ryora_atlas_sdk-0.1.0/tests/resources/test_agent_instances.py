"""Tests for the agent_instances resource module."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
import respx
from httpx import Response

from atlas_sdk.clients.workflow import WorkflowClient
from atlas_sdk.exceptions import AtlasTimeoutError
from atlas_sdk.models.agent_instance import AgentInstanceRead
from atlas_sdk.models.enums import AgentInstanceStatus
from atlas_sdk.resources.agent_instances import AgentInstance, AgentInstancesResource


@pytest.fixture
def base_url() -> str:
    return "http://control-plane"


@pytest.fixture
def workflow_client(base_url: str) -> WorkflowClient:
    return WorkflowClient(base_url=base_url)


@pytest.fixture
def instance_id() -> UUID:
    return uuid4()


@pytest.fixture
def deployment_id() -> UUID:
    return uuid4()


@pytest.fixture
def agent_definition_id() -> UUID:
    return uuid4()


@pytest.fixture
def sample_instance_data(
    instance_id: UUID, deployment_id: UUID, agent_definition_id: UUID
) -> dict:
    """Return sample agent instance data."""
    now = datetime.now(timezone.utc).isoformat()
    return {
        "id": str(instance_id),
        "deployment_id": str(deployment_id),
        "agent_definition_id": str(agent_definition_id),
        "routing_key": "test-key",
        "status": "active",
        "input": {"prompt": "Hello"},
        "output": None,
        "error": None,
        "exit_code": None,
        "metrics": {"latency": 100},
        "created_at": now,
        "started_at": now,
        "completed_at": None,
    }


class TestAgentInstance:
    """Tests for the AgentInstance resource class."""

    def test_id_property(
        self,
        sample_instance_data: dict,
        instance_id: UUID,
        workflow_client: WorkflowClient,
    ):
        """Test that id property returns the correct UUID."""
        data = AgentInstanceRead.model_validate(sample_instance_data)
        instance = AgentInstance(data, workflow_client)
        assert instance.id == instance_id

    def test_routing_key_property(
        self, sample_instance_data: dict, workflow_client: WorkflowClient
    ):
        """Test that routing_key property returns the correct value."""
        data = AgentInstanceRead.model_validate(sample_instance_data)
        instance = AgentInstance(data, workflow_client)
        assert instance.routing_key == "test-key"

    def test_status_property(
        self, sample_instance_data: dict, workflow_client: WorkflowClient
    ):
        """Test that status property returns the correct enum."""
        data = AgentInstanceRead.model_validate(sample_instance_data)
        instance = AgentInstance(data, workflow_client)
        assert instance.status == AgentInstanceStatus.ACTIVE

    def test_input_property(
        self, sample_instance_data: dict, workflow_client: WorkflowClient
    ):
        """Test that input property returns the correct dict."""
        data = AgentInstanceRead.model_validate(sample_instance_data)
        instance = AgentInstance(data, workflow_client)
        assert instance.input == {"prompt": "Hello"}

    def test_metrics_property(
        self, sample_instance_data: dict, workflow_client: WorkflowClient
    ):
        """Test that metrics property returns the correct dict."""
        data = AgentInstanceRead.model_validate(sample_instance_data)
        instance = AgentInstance(data, workflow_client)
        assert instance.metrics == {"latency": 100}

    def test_repr(
        self,
        sample_instance_data: dict,
        instance_id: UUID,
        workflow_client: WorkflowClient,
    ):
        """Test string representation."""
        data = AgentInstanceRead.model_validate(sample_instance_data)
        instance = AgentInstance(data, workflow_client)
        repr_str = repr(instance)
        assert "AgentInstance" in repr_str
        assert str(instance_id) in repr_str
        assert "test-key" in repr_str
        assert "active" in repr_str

    @pytest.mark.asyncio
    async def test_refresh(
        self,
        base_url: str,
        sample_instance_data: dict,
        instance_id: UUID,
        workflow_client: WorkflowClient,
    ):
        """Test that refresh updates the internal data."""
        data = AgentInstanceRead.model_validate(sample_instance_data)
        instance = AgentInstance(data, workflow_client)

        updated_data = sample_instance_data.copy()
        updated_data["status"] = "completed"
        updated_data["output"] = {"result": "Done!"}
        updated_data["exit_code"] = 0

        async with respx.mock(base_url=base_url) as respx_mock:
            route = respx_mock.get(f"/api/v1/instances/{instance_id}").mock(
                return_value=Response(200, json=updated_data)
            )
            async with workflow_client:
                await instance.refresh()

        assert route.called
        assert instance.status == AgentInstanceStatus.COMPLETED
        assert instance.output == {"result": "Done!"}
        assert instance.exit_code == 0

    @pytest.mark.asyncio
    async def test_save_raises_not_implemented(
        self, sample_instance_data: dict, workflow_client: WorkflowClient
    ):
        """Test that save raises NotImplementedError."""
        data = AgentInstanceRead.model_validate(sample_instance_data)
        instance = AgentInstance(data, workflow_client)
        async with workflow_client:
            with pytest.raises(NotImplementedError):
                await instance.save()

    @pytest.mark.asyncio
    async def test_delete_raises_not_implemented(
        self, sample_instance_data: dict, workflow_client: WorkflowClient
    ):
        """Test that delete raises NotImplementedError."""
        data = AgentInstanceRead.model_validate(sample_instance_data)
        instance = AgentInstance(data, workflow_client)
        async with workflow_client:
            with pytest.raises(NotImplementedError):
                await instance.delete()


class TestAgentInstancesResource:
    """Tests for the AgentInstancesResource manager class."""

    @pytest.mark.asyncio
    async def test_get(
        self,
        base_url: str,
        sample_instance_data: dict,
        instance_id: UUID,
        workflow_client: WorkflowClient,
    ):
        """Test getting an agent instance by ID."""
        async with respx.mock(base_url=base_url) as respx_mock:
            route = respx_mock.get(f"/api/v1/instances/{instance_id}").mock(
                return_value=Response(200, json=sample_instance_data)
            )
            async with workflow_client:
                resource = AgentInstancesResource(workflow_client)
                instance = await resource.get(instance_id)

        assert route.called
        assert isinstance(instance, AgentInstance)
        assert instance.id == instance_id

    @pytest.mark.asyncio
    async def test_list(
        self,
        base_url: str,
        sample_instance_data: dict,
        workflow_client: WorkflowClient,
    ):
        """Test listing agent instances."""
        async with respx.mock(base_url=base_url) as respx_mock:
            route = respx_mock.get("/api/v1/instances").mock(
                return_value=Response(200, json=[sample_instance_data])
            )
            async with workflow_client:
                resource = AgentInstancesResource(workflow_client)
                instances = await resource.list()

        assert route.called
        assert len(instances) == 1
        assert isinstance(instances[0], AgentInstance)

    @pytest.mark.asyncio
    async def test_list_with_filters(
        self,
        base_url: str,
        sample_instance_data: dict,
        deployment_id: UUID,
        workflow_client: WorkflowClient,
    ):
        """Test listing agent instances with filters."""
        async with respx.mock(base_url=base_url) as respx_mock:
            route = respx_mock.get("/api/v1/instances").mock(
                return_value=Response(200, json=[sample_instance_data])
            )
            async with workflow_client:
                resource = AgentInstancesResource(workflow_client)
                await resource.list(
                    deployment_id=deployment_id,
                    status=AgentInstanceStatus.ACTIVE,
                    limit=50,
                    offset=10,
                )

        assert route.called
        request = route.calls[0].request
        assert f"deployment_id={deployment_id}" in str(request.url)
        assert "status=active" in str(request.url)
        assert "limit=50" in str(request.url)
        assert "offset=10" in str(request.url)


class TestClientAgentInstancesProperty:
    """Test that workflow_client.agent_instances returns the correct manager."""

    @pytest.mark.asyncio
    async def test_workflow_client_agent_instances(
        self, workflow_client: WorkflowClient
    ):
        """Test that WorkflowClient has agent_instances property."""
        async with workflow_client as client:
            assert hasattr(client, "agent_instances")
            assert isinstance(client.agent_instances, AgentInstancesResource)

    @pytest.mark.asyncio
    async def test_agent_instances_cached(self, workflow_client: WorkflowClient):
        """Test that agent_instances property returns the same instance."""
        async with workflow_client as client:
            instances1 = client.agent_instances
            instances2 = client.agent_instances
            assert instances1 is instances2


class TestAgentInstanceWaiters:
    """Tests for agent instance waiter methods."""

    @pytest.mark.asyncio
    async def test_wait_until_active_already_active(
        self,
        base_url: str,
        sample_instance_data: dict,
        instance_id: UUID,
        workflow_client: WorkflowClient,
    ):
        """Test wait_until_active when instance is already active."""
        data = AgentInstanceRead.model_validate(sample_instance_data)
        instance = AgentInstance(data, workflow_client)

        async with respx.mock(base_url=base_url) as respx_mock:
            route = respx_mock.get(f"/api/v1/instances/{instance_id}").mock(
                return_value=Response(200, json=sample_instance_data)
            )
            async with workflow_client:
                await instance.wait_until_active(poll_interval=0.01)

        assert route.called
        assert instance.status == AgentInstanceStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_wait_until_active_transitions_to_active(
        self,
        base_url: str,
        sample_instance_data: dict,
        instance_id: UUID,
        workflow_client: WorkflowClient,
    ):
        """Test wait_until_active waits for instance to become active."""
        spawning_data = sample_instance_data.copy()
        spawning_data["status"] = "spawning"

        active_data = sample_instance_data.copy()
        active_data["status"] = "active"

        data = AgentInstanceRead.model_validate(spawning_data)
        instance = AgentInstance(data, workflow_client)

        call_count = 0

        async with respx.mock(base_url=base_url) as respx_mock:

            def response_callback(request):
                nonlocal call_count
                call_count += 1
                if call_count < 3:
                    return Response(200, json=spawning_data)
                return Response(200, json=active_data)

            route = respx_mock.get(f"/api/v1/instances/{instance_id}").mock(
                side_effect=response_callback
            )
            async with workflow_client:
                await instance.wait_until_active(poll_interval=0.01, timeout=5.0)

        assert route.call_count == 3
        assert instance.status == AgentInstanceStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_wait_until_active_stops_on_failed(
        self,
        base_url: str,
        sample_instance_data: dict,
        instance_id: UUID,
        workflow_client: WorkflowClient,
    ):
        """Test wait_until_active returns when instance fails."""
        failed_data = sample_instance_data.copy()
        failed_data["status"] = "failed"
        failed_data["error"] = "Something went wrong"

        data = AgentInstanceRead.model_validate(sample_instance_data)
        instance = AgentInstance(data, workflow_client)

        async with respx.mock(base_url=base_url) as respx_mock:
            route = respx_mock.get(f"/api/v1/instances/{instance_id}").mock(
                return_value=Response(200, json=failed_data)
            )
            async with workflow_client:
                await instance.wait_until_active(poll_interval=0.01)

        assert route.called
        assert instance.status == AgentInstanceStatus.FAILED

    @pytest.mark.asyncio
    async def test_wait_until_active_timeout(
        self,
        base_url: str,
        sample_instance_data: dict,
        instance_id: UUID,
        workflow_client: WorkflowClient,
    ):
        """Test wait_until_active raises AtlasTimeoutError on timeout."""
        spawning_data = sample_instance_data.copy()
        spawning_data["status"] = "spawning"

        data = AgentInstanceRead.model_validate(spawning_data)
        instance = AgentInstance(data, workflow_client)

        async with respx.mock(base_url=base_url) as respx_mock:
            route = respx_mock.get(f"/api/v1/instances/{instance_id}").mock(
                return_value=Response(200, json=spawning_data)
            )
            async with workflow_client:
                with pytest.raises(AtlasTimeoutError) as exc_info:
                    await instance.wait_until_active(poll_interval=0.01, timeout=0.03)

        assert route.called
        assert exc_info.value.operation == "wait_until_active"
        assert exc_info.value.timeout_seconds == 0.03
        assert exc_info.value.last_state is not None
        assert exc_info.value.last_state.status == AgentInstanceStatus.SPAWNING

    @pytest.mark.asyncio
    async def test_wait_for_completion_completed(
        self,
        base_url: str,
        sample_instance_data: dict,
        instance_id: UUID,
        workflow_client: WorkflowClient,
    ):
        """Test wait_for_completion when instance completes."""
        completed_data = sample_instance_data.copy()
        completed_data["status"] = "completed"
        completed_data["output"] = {"result": "done"}
        completed_data["exit_code"] = 0

        data = AgentInstanceRead.model_validate(sample_instance_data)
        instance = AgentInstance(data, workflow_client)

        async with respx.mock(base_url=base_url) as respx_mock:
            route = respx_mock.get(f"/api/v1/instances/{instance_id}").mock(
                return_value=Response(200, json=completed_data)
            )
            async with workflow_client:
                await instance.wait_for_completion(poll_interval=0.01)

        assert route.called
        assert instance.status == AgentInstanceStatus.COMPLETED
        assert instance.output == {"result": "done"}

    @pytest.mark.asyncio
    async def test_wait_for_completion_failed(
        self,
        base_url: str,
        sample_instance_data: dict,
        instance_id: UUID,
        workflow_client: WorkflowClient,
    ):
        """Test wait_for_completion when instance fails."""
        failed_data = sample_instance_data.copy()
        failed_data["status"] = "failed"
        failed_data["error"] = "Execution error"

        data = AgentInstanceRead.model_validate(sample_instance_data)
        instance = AgentInstance(data, workflow_client)

        async with respx.mock(base_url=base_url) as respx_mock:
            route = respx_mock.get(f"/api/v1/instances/{instance_id}").mock(
                return_value=Response(200, json=failed_data)
            )
            async with workflow_client:
                await instance.wait_for_completion(poll_interval=0.01)

        assert route.called
        assert instance.status == AgentInstanceStatus.FAILED
        assert instance.error == "Execution error"

    @pytest.mark.asyncio
    async def test_wait_for_completion_cancelled(
        self,
        base_url: str,
        sample_instance_data: dict,
        instance_id: UUID,
        workflow_client: WorkflowClient,
    ):
        """Test wait_for_completion when instance is cancelled."""
        cancelled_data = sample_instance_data.copy()
        cancelled_data["status"] = "cancelled"

        data = AgentInstanceRead.model_validate(sample_instance_data)
        instance = AgentInstance(data, workflow_client)

        async with respx.mock(base_url=base_url) as respx_mock:
            route = respx_mock.get(f"/api/v1/instances/{instance_id}").mock(
                return_value=Response(200, json=cancelled_data)
            )
            async with workflow_client:
                await instance.wait_for_completion(poll_interval=0.01)

        assert route.called
        assert instance.status == AgentInstanceStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_wait_for_completion_timeout(
        self,
        base_url: str,
        sample_instance_data: dict,
        instance_id: UUID,
        workflow_client: WorkflowClient,
    ):
        """Test wait_for_completion raises AtlasTimeoutError on timeout."""
        # Instance stays active, never completes
        data = AgentInstanceRead.model_validate(sample_instance_data)
        instance = AgentInstance(data, workflow_client)

        async with respx.mock(base_url=base_url) as respx_mock:
            route = respx_mock.get(f"/api/v1/instances/{instance_id}").mock(
                return_value=Response(200, json=sample_instance_data)
            )
            async with workflow_client:
                with pytest.raises(AtlasTimeoutError) as exc_info:
                    await instance.wait_for_completion(poll_interval=0.01, timeout=0.03)

        assert route.called
        assert exc_info.value.operation == "wait_for_completion"
        assert exc_info.value.timeout_seconds == 0.03
        assert exc_info.value.last_state is not None
        assert exc_info.value.last_state.status == AgentInstanceStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_wait_until_active_with_progress_callback(
        self,
        base_url: str,
        sample_instance_data: dict,
        instance_id: UUID,
        workflow_client: WorkflowClient,
    ):
        """Test wait_until_active calls progress callback."""
        data = AgentInstanceRead.model_validate(sample_instance_data)
        instance = AgentInstance(data, workflow_client)

        callback_states: list[AgentInstanceRead] = []

        def on_progress(state: AgentInstanceRead) -> None:
            callback_states.append(state)

        async with respx.mock(base_url=base_url) as respx_mock:
            route = respx_mock.get(f"/api/v1/instances/{instance_id}").mock(
                return_value=Response(200, json=sample_instance_data)
            )
            async with workflow_client:
                await instance.wait_until_active(
                    poll_interval=0.01, on_progress=on_progress
                )

        assert route.called
        assert len(callback_states) == 1
        assert callback_states[0].status == AgentInstanceStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_wait_for_completion_with_async_progress_callback(
        self,
        base_url: str,
        sample_instance_data: dict,
        instance_id: UUID,
        workflow_client: WorkflowClient,
    ):
        """Test wait_for_completion calls async progress callback."""
        completed_data = sample_instance_data.copy()
        completed_data["status"] = "completed"

        data = AgentInstanceRead.model_validate(sample_instance_data)
        instance = AgentInstance(data, workflow_client)

        callback_states: list[AgentInstanceRead] = []

        async def on_progress(state: AgentInstanceRead) -> None:
            callback_states.append(state)

        async with respx.mock(base_url=base_url) as respx_mock:
            route = respx_mock.get(f"/api/v1/instances/{instance_id}").mock(
                return_value=Response(200, json=completed_data)
            )
            async with workflow_client:
                await instance.wait_for_completion(
                    poll_interval=0.01, on_progress=on_progress
                )

        assert route.called
        assert len(callback_states) == 1

    @pytest.mark.asyncio
    async def test_resource_wait_until_active(
        self,
        base_url: str,
        sample_instance_data: dict,
        instance_id: UUID,
        workflow_client: WorkflowClient,
    ):
        """Test AgentInstancesResource.wait_until_active returns the instance."""
        async with respx.mock(base_url=base_url) as respx_mock:
            route = respx_mock.get(f"/api/v1/instances/{instance_id}").mock(
                return_value=Response(200, json=sample_instance_data)
            )
            async with workflow_client:
                resource = AgentInstancesResource(workflow_client)
                instance = await resource.wait_until_active(
                    instance_id, poll_interval=0.01
                )

        # Called twice: once in get(), once in wait_until_active()
        assert route.call_count == 2
        assert isinstance(instance, AgentInstance)
        assert instance.status == AgentInstanceStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_resource_wait_for_completion(
        self,
        base_url: str,
        sample_instance_data: dict,
        instance_id: UUID,
        workflow_client: WorkflowClient,
    ):
        """Test AgentInstancesResource.wait_for_completion returns the instance."""
        completed_data = sample_instance_data.copy()
        completed_data["status"] = "completed"

        async with respx.mock(base_url=base_url) as respx_mock:
            route = respx_mock.get(f"/api/v1/instances/{instance_id}").mock(
                return_value=Response(200, json=completed_data)
            )
            async with workflow_client:
                resource = AgentInstancesResource(workflow_client)
                instance = await resource.wait_for_completion(
                    instance_id, poll_interval=0.01
                )

        # Called twice: once in get(), once in wait_for_completion()
        assert route.call_count == 2
        assert isinstance(instance, AgentInstance)
        assert instance.status == AgentInstanceStatus.COMPLETED
