"""Tests for the deployments resource module."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
import respx
from httpx import Response

from atlas_sdk.clients.control_plane import ControlPlaneClient
from atlas_sdk.clients.workflow import WorkflowClient
from atlas_sdk.exceptions import AtlasTimeoutError
from atlas_sdk.models.deployment import DeploymentRead
from atlas_sdk.models.enums import DeploymentStatus
from atlas_sdk.resources.deployments import Deployment, DeploymentsResource


@pytest.fixture
def base_url() -> str:
    return "http://control-plane"


@pytest.fixture
def control_plane_client(base_url: str) -> ControlPlaneClient:
    return ControlPlaneClient(base_url=base_url)


@pytest.fixture
def workflow_client(base_url: str) -> WorkflowClient:
    return WorkflowClient(base_url=base_url)


@pytest.fixture
def agent_definition_id() -> UUID:
    return uuid4()


@pytest.fixture
def deployment_id() -> UUID:
    return uuid4()


@pytest.fixture
def sample_deployment_data(deployment_id: UUID, agent_definition_id: UUID) -> dict:
    """Return sample deployment data for testing."""
    now = datetime.now(timezone.utc).isoformat()
    return {
        "id": str(deployment_id),
        "agent_definition_id": str(agent_definition_id),
        "blueprint_id": None,
        "name": "test-deployment",
        "description": "A test deployment",
        "environment": "production",
        "status": "active",
        "config": {"key": "value"},
        "project_context": {"project": "test"},
        "spec_md_path": None,
        "created_at": now,
        "updated_at": now,
    }


class TestDeployment:
    """Tests for the Deployment resource class."""

    def test_id_property(
        self,
        sample_deployment_data: dict,
        deployment_id: UUID,
        control_plane_client: ControlPlaneClient,
    ):
        """Test that id property returns the correct UUID."""
        data = DeploymentRead.model_validate(sample_deployment_data)
        deployment = Deployment(data, control_plane_client)
        assert deployment.id == deployment_id

    def test_name_property(
        self, sample_deployment_data: dict, control_plane_client: ControlPlaneClient
    ):
        """Test that name property returns the correct value."""
        data = DeploymentRead.model_validate(sample_deployment_data)
        deployment = Deployment(data, control_plane_client)
        assert deployment.name == "test-deployment"

    def test_status_property(
        self, sample_deployment_data: dict, control_plane_client: ControlPlaneClient
    ):
        """Test that status property returns the correct enum."""
        data = DeploymentRead.model_validate(sample_deployment_data)
        deployment = Deployment(data, control_plane_client)
        assert deployment.status == DeploymentStatus.ACTIVE

    def test_environment_property(
        self, sample_deployment_data: dict, control_plane_client: ControlPlaneClient
    ):
        """Test that environment property returns the correct value."""
        data = DeploymentRead.model_validate(sample_deployment_data)
        deployment = Deployment(data, control_plane_client)
        assert deployment.environment == "production"

    def test_config_property(
        self, sample_deployment_data: dict, control_plane_client: ControlPlaneClient
    ):
        """Test that config property returns the correct dict."""
        data = DeploymentRead.model_validate(sample_deployment_data)
        deployment = Deployment(data, control_plane_client)
        assert deployment.config == {"key": "value"}

    def test_repr(
        self,
        sample_deployment_data: dict,
        deployment_id: UUID,
        control_plane_client: ControlPlaneClient,
    ):
        """Test string representation."""
        data = DeploymentRead.model_validate(sample_deployment_data)
        deployment = Deployment(data, control_plane_client)
        repr_str = repr(deployment)
        assert "Deployment" in repr_str
        assert str(deployment_id) in repr_str
        assert "test-deployment" in repr_str
        assert "active" in repr_str

    @pytest.mark.asyncio
    async def test_refresh(
        self,
        base_url: str,
        sample_deployment_data: dict,
        deployment_id: UUID,
        control_plane_client: ControlPlaneClient,
    ):
        """Test that refresh updates the internal data."""
        data = DeploymentRead.model_validate(sample_deployment_data)
        deployment = Deployment(data, control_plane_client)

        updated_data = sample_deployment_data.copy()
        updated_data["name"] = "updated-deployment"
        updated_data["status"] = "completed"

        async with respx.mock(base_url=base_url) as respx_mock:
            route = respx_mock.get(f"/api/v1/deployments/{deployment_id}").mock(
                return_value=Response(200, json=updated_data)
            )
            async with control_plane_client:
                await deployment.refresh()

        assert route.called
        assert deployment.name == "updated-deployment"
        assert deployment.status == DeploymentStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_save(
        self,
        base_url: str,
        sample_deployment_data: dict,
        deployment_id: UUID,
        control_plane_client: ControlPlaneClient,
    ):
        """Test that save sends the correct data to the server."""
        data = DeploymentRead.model_validate(sample_deployment_data)
        deployment = Deployment(data, control_plane_client)

        # Modify the deployment
        deployment.data.description = "Updated description"

        updated_data = sample_deployment_data.copy()
        updated_data["description"] = "Updated description"

        async with respx.mock(base_url=base_url) as respx_mock:
            route = respx_mock.patch(f"/api/v1/deployments/{deployment_id}").mock(
                return_value=Response(200, json=updated_data)
            )
            async with control_plane_client:
                await deployment.save()

        assert route.called
        assert deployment.description == "Updated description"

    @pytest.mark.asyncio
    async def test_delete(
        self,
        base_url: str,
        sample_deployment_data: dict,
        deployment_id: UUID,
        control_plane_client: ControlPlaneClient,
    ):
        """Test that delete sends the correct request."""
        data = DeploymentRead.model_validate(sample_deployment_data)
        deployment = Deployment(data, control_plane_client)

        async with respx.mock(base_url=base_url) as respx_mock:
            route = respx_mock.delete(f"/api/v1/deployments/{deployment_id}").mock(
                return_value=Response(204)
            )
            async with control_plane_client:
                await deployment.delete()

        assert route.called


class TestDeploymentsResource:
    """Tests for the DeploymentsResource manager class."""

    @pytest.mark.asyncio
    async def test_create(
        self,
        base_url: str,
        sample_deployment_data: dict,
        agent_definition_id: UUID,
        control_plane_client: ControlPlaneClient,
    ):
        """Test creating a deployment through the resource manager."""
        async with respx.mock(base_url=base_url) as respx_mock:
            route = respx_mock.post("/api/v1/deployments").mock(
                return_value=Response(200, json=sample_deployment_data)
            )
            async with control_plane_client:
                resource = DeploymentsResource(control_plane_client)
                deployment = await resource.create(
                    agent_definition_id=agent_definition_id,
                    name="test-deployment",
                    environment="production",
                    description="A test deployment",
                    config={"key": "value"},
                )

        assert route.called
        assert isinstance(deployment, Deployment)
        assert deployment.name == "test-deployment"
        assert deployment.environment == "production"

    @pytest.mark.asyncio
    async def test_get(
        self,
        base_url: str,
        sample_deployment_data: dict,
        deployment_id: UUID,
        control_plane_client: ControlPlaneClient,
    ):
        """Test getting a deployment by ID."""
        async with respx.mock(base_url=base_url) as respx_mock:
            route = respx_mock.get(f"/api/v1/deployments/{deployment_id}").mock(
                return_value=Response(200, json=sample_deployment_data)
            )
            async with control_plane_client:
                resource = DeploymentsResource(control_plane_client)
                deployment = await resource.get(deployment_id)

        assert route.called
        assert isinstance(deployment, Deployment)
        assert deployment.id == deployment_id

    @pytest.mark.asyncio
    async def test_list(
        self,
        base_url: str,
        sample_deployment_data: dict,
        control_plane_client: ControlPlaneClient,
    ):
        """Test listing deployments."""
        async with respx.mock(base_url=base_url) as respx_mock:
            route = respx_mock.get("/api/v1/deployments").mock(
                return_value=Response(200, json=[sample_deployment_data])
            )
            async with control_plane_client:
                resource = DeploymentsResource(control_plane_client)
                deployments = await resource.list()

        assert route.called
        assert len(deployments) == 1
        assert isinstance(deployments[0], Deployment)

    @pytest.mark.asyncio
    async def test_list_with_filters(
        self,
        base_url: str,
        sample_deployment_data: dict,
        control_plane_client: ControlPlaneClient,
    ):
        """Test listing deployments with filters."""
        async with respx.mock(base_url=base_url) as respx_mock:
            route = respx_mock.get("/api/v1/deployments").mock(
                return_value=Response(200, json=[sample_deployment_data])
            )
            async with control_plane_client:
                resource = DeploymentsResource(control_plane_client)
                deployments = await resource.list(
                    environment="production",
                    active_only=True,
                    limit=50,
                    offset=10,
                )

        assert route.called
        # Check query params
        request = route.calls[0].request
        assert "environment=production" in str(request.url)
        assert "active_only=true" in str(request.url)
        assert "limit=50" in str(request.url)
        assert "offset=10" in str(request.url)
        assert len(deployments) == 1


class TestClientDeploymentsProperty:
    """Test that client.deployments returns the correct resource manager."""

    @pytest.mark.asyncio
    async def test_control_plane_client_deployments(
        self, control_plane_client: ControlPlaneClient
    ):
        """Test that ControlPlaneClient has deployments property."""
        async with control_plane_client as client:
            assert hasattr(client, "deployments")
            assert isinstance(client.deployments, DeploymentsResource)

    @pytest.mark.asyncio
    async def test_workflow_client_deployments(self, workflow_client: WorkflowClient):
        """Test that WorkflowClient has deployments property."""
        async with workflow_client as client:
            assert hasattr(client, "deployments")
            assert isinstance(client.deployments, DeploymentsResource)

    @pytest.mark.asyncio
    async def test_deployments_cached(self, control_plane_client: ControlPlaneClient):
        """Test that deployments property returns the same instance."""
        async with control_plane_client as client:
            deployments1 = client.deployments
            deployments2 = client.deployments
            assert deployments1 is deployments2


class TestDeploymentWaiters:
    """Tests for deployment waiter methods."""

    @pytest.mark.asyncio
    async def test_wait_until_active_already_active(
        self,
        base_url: str,
        sample_deployment_data: dict,
        deployment_id: UUID,
        control_plane_client: ControlPlaneClient,
    ):
        """Test wait_until_active when deployment is already active."""
        # Deployment is already active in sample_deployment_data
        data = DeploymentRead.model_validate(sample_deployment_data)
        deployment = Deployment(data, control_plane_client)

        async with respx.mock(base_url=base_url) as respx_mock:
            route = respx_mock.get(f"/api/v1/deployments/{deployment_id}").mock(
                return_value=Response(200, json=sample_deployment_data)
            )
            async with control_plane_client:
                await deployment.wait_until_active(poll_interval=0.01)

        assert route.called
        assert deployment.status == DeploymentStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_wait_until_active_transitions_to_active(
        self,
        base_url: str,
        sample_deployment_data: dict,
        deployment_id: UUID,
        control_plane_client: ControlPlaneClient,
    ):
        """Test wait_until_active waits for deployment to become active."""
        spawning_data = sample_deployment_data.copy()
        spawning_data["status"] = "spawning"

        active_data = sample_deployment_data.copy()
        active_data["status"] = "active"

        data = DeploymentRead.model_validate(spawning_data)
        deployment = Deployment(data, control_plane_client)

        call_count = 0

        async with respx.mock(base_url=base_url) as respx_mock:

            def response_callback(request):
                nonlocal call_count
                call_count += 1
                if call_count < 3:
                    return Response(200, json=spawning_data)
                return Response(200, json=active_data)

            route = respx_mock.get(f"/api/v1/deployments/{deployment_id}").mock(
                side_effect=response_callback
            )
            async with control_plane_client:
                await deployment.wait_until_active(poll_interval=0.01, timeout=5.0)

        assert route.call_count == 3
        assert deployment.status == DeploymentStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_wait_until_active_stops_on_failed(
        self,
        base_url: str,
        sample_deployment_data: dict,
        deployment_id: UUID,
        control_plane_client: ControlPlaneClient,
    ):
        """Test wait_until_active returns when deployment fails."""
        failed_data = sample_deployment_data.copy()
        failed_data["status"] = "failed"

        data = DeploymentRead.model_validate(sample_deployment_data)
        deployment = Deployment(data, control_plane_client)

        async with respx.mock(base_url=base_url) as respx_mock:
            route = respx_mock.get(f"/api/v1/deployments/{deployment_id}").mock(
                return_value=Response(200, json=failed_data)
            )
            async with control_plane_client:
                await deployment.wait_until_active(poll_interval=0.01)

        assert route.called
        assert deployment.status == DeploymentStatus.FAILED

    @pytest.mark.asyncio
    async def test_wait_until_active_timeout(
        self,
        base_url: str,
        sample_deployment_data: dict,
        deployment_id: UUID,
        control_plane_client: ControlPlaneClient,
    ):
        """Test wait_until_active raises AtlasTimeoutError on timeout."""
        spawning_data = sample_deployment_data.copy()
        spawning_data["status"] = "spawning"

        data = DeploymentRead.model_validate(spawning_data)
        deployment = Deployment(data, control_plane_client)

        async with respx.mock(base_url=base_url) as respx_mock:
            route = respx_mock.get(f"/api/v1/deployments/{deployment_id}").mock(
                return_value=Response(200, json=spawning_data)
            )
            async with control_plane_client:
                with pytest.raises(AtlasTimeoutError) as exc_info:
                    await deployment.wait_until_active(poll_interval=0.01, timeout=0.03)

        assert route.called
        assert exc_info.value.operation == "wait_until_active"
        assert exc_info.value.timeout_seconds == 0.03
        assert exc_info.value.last_state is not None
        assert exc_info.value.last_state.status == DeploymentStatus.SPAWNING

    @pytest.mark.asyncio
    async def test_wait_until_active_with_progress_callback(
        self,
        base_url: str,
        sample_deployment_data: dict,
        deployment_id: UUID,
        control_plane_client: ControlPlaneClient,
    ):
        """Test wait_until_active calls progress callback."""
        data = DeploymentRead.model_validate(sample_deployment_data)
        deployment = Deployment(data, control_plane_client)

        callback_states: list[DeploymentRead] = []

        def on_progress(state: DeploymentRead) -> None:
            callback_states.append(state)

        async with respx.mock(base_url=base_url) as respx_mock:
            route = respx_mock.get(f"/api/v1/deployments/{deployment_id}").mock(
                return_value=Response(200, json=sample_deployment_data)
            )
            async with control_plane_client:
                await deployment.wait_until_active(
                    poll_interval=0.01, on_progress=on_progress
                )

        assert route.called
        assert len(callback_states) == 1
        assert callback_states[0].status == DeploymentStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_wait_until_active_with_async_progress_callback(
        self,
        base_url: str,
        sample_deployment_data: dict,
        deployment_id: UUID,
        control_plane_client: ControlPlaneClient,
    ):
        """Test wait_until_active calls async progress callback."""
        data = DeploymentRead.model_validate(sample_deployment_data)
        deployment = Deployment(data, control_plane_client)

        callback_states: list[DeploymentRead] = []

        async def on_progress(state: DeploymentRead) -> None:
            callback_states.append(state)

        async with respx.mock(base_url=base_url) as respx_mock:
            route = respx_mock.get(f"/api/v1/deployments/{deployment_id}").mock(
                return_value=Response(200, json=sample_deployment_data)
            )
            async with control_plane_client:
                await deployment.wait_until_active(
                    poll_interval=0.01, on_progress=on_progress
                )

        assert route.called
        assert len(callback_states) == 1

    @pytest.mark.asyncio
    async def test_resource_wait_until_active(
        self,
        base_url: str,
        sample_deployment_data: dict,
        deployment_id: UUID,
        control_plane_client: ControlPlaneClient,
    ):
        """Test DeploymentsResource.wait_until_active returns the deployment."""
        async with respx.mock(base_url=base_url) as respx_mock:
            route = respx_mock.get(f"/api/v1/deployments/{deployment_id}").mock(
                return_value=Response(200, json=sample_deployment_data)
            )
            async with control_plane_client:
                resource = DeploymentsResource(control_plane_client)
                deployment = await resource.wait_until_active(
                    deployment_id, poll_interval=0.01
                )

        # Called twice: once in get(), once in wait_until_active()
        assert route.call_count == 2
        assert isinstance(deployment, Deployment)
        assert deployment.status == DeploymentStatus.ACTIVE
