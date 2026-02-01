"""Tests for the base Resource and ResourceManager classes.

Tests the __getattr__ delegation mechanism that allows Resource subclasses
to automatically expose underlying model fields as read-only attributes.

Also tests the ResourceManager base class that provides common get/list
operations for resource managers.
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import httpx
import pytest

from atlas_sdk.models.deployment import DeploymentRead
from atlas_sdk.models.enums import DeploymentStatus
from atlas_sdk.resources.base import Resource, ResourceManager
from atlas_sdk.resources.deployments import Deployment, DeploymentsResource


class MockHTTPClient:
    """Minimal mock for testing."""

    async def _request(self, method: str, url: str, **kwargs):
        raise NotImplementedError

    def _raise_for_status(self, response):
        pass


@pytest.fixture
def mock_client():
    return MockHTTPClient()


@pytest.fixture
def sample_deployment_data():
    """Create sample deployment data for testing."""
    return {
        "id": str(uuid4()),
        "agent_definition_id": str(uuid4()),
        "blueprint_id": None,
        "name": "test-deployment",
        "description": "A test deployment description",
        "environment": "production",
        "status": "active",
        "config": {"key": "value", "nested": {"inner": 42}},
        "project_context": {"project": "test"},
        "spec_md_path": "/path/to/spec.md",
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:30:00Z",
    }


class TestResourceGetattr:
    """Tests for the __getattr__ delegation mechanism."""

    def test_delegates_model_fields(
        self, sample_deployment_data: dict, mock_client: MockHTTPClient
    ):
        """Test that model fields are accessible as resource attributes."""
        data = DeploymentRead.model_validate(sample_deployment_data)
        deployment = Deployment(data, mock_client)

        # All these should be delegated to _data
        assert deployment.name == "test-deployment"
        assert deployment.description == "A test deployment description"
        assert deployment.environment == "production"
        assert deployment.status == DeploymentStatus.ACTIVE
        assert deployment.config == {"key": "value", "nested": {"inner": 42}}
        assert deployment.project_context == {"project": "test"}
        assert deployment.spec_md_path == "/path/to/spec.md"

    def test_delegates_nested_fields(
        self, sample_deployment_data: dict, mock_client: MockHTTPClient
    ):
        """Test that complex/nested model fields work correctly."""
        data = DeploymentRead.model_validate(sample_deployment_data)
        deployment = Deployment(data, mock_client)

        # Access nested dict values through delegation
        assert deployment.config["nested"]["inner"] == 42

    def test_attribute_error_for_nonexistent_field(
        self, sample_deployment_data: dict, mock_client: MockHTTPClient
    ):
        """Test that AttributeError is raised for nonexistent attributes."""
        data = DeploymentRead.model_validate(sample_deployment_data)
        deployment = Deployment(data, mock_client)

        with pytest.raises(AttributeError) as exc_info:
            _ = deployment.nonexistent_field

        assert "nonexistent_field" in str(exc_info.value)
        assert "Deployment" in str(exc_info.value)

    def test_data_property_still_accessible(
        self, sample_deployment_data: dict, mock_client: MockHTTPClient
    ):
        """Test that the data property is still accessible."""
        data = DeploymentRead.model_validate(sample_deployment_data)
        deployment = Deployment(data, mock_client)

        assert deployment.data is data
        assert isinstance(deployment.data, DeploymentRead)

    def test_id_property_works(
        self, sample_deployment_data: dict, mock_client: MockHTTPClient
    ):
        """Test that the id property from base class works."""
        data = DeploymentRead.model_validate(sample_deployment_data)
        deployment = Deployment(data, mock_client)

        assert deployment.id == data.id

    def test_private_attributes_not_delegated(
        self, sample_deployment_data: dict, mock_client: MockHTTPClient
    ):
        """Test that private attributes work normally and aren't delegated."""
        data = DeploymentRead.model_validate(sample_deployment_data)
        deployment = Deployment(data, mock_client)

        # These private attributes should be accessible directly
        assert deployment._data is data
        assert deployment._client is mock_client

    def test_delegation_with_none_values(
        self, sample_deployment_data: dict, mock_client: MockHTTPClient
    ):
        """Test that None values are correctly delegated."""
        sample_deployment_data["blueprint_id"] = None
        sample_deployment_data["spec_md_path"] = None
        data = DeploymentRead.model_validate(sample_deployment_data)
        deployment = Deployment(data, mock_client)

        assert deployment.blueprint_id is None
        assert deployment.spec_md_path is None

    def test_isinstance_check(
        self, sample_deployment_data: dict, mock_client: MockHTTPClient
    ):
        """Test that isinstance checks work correctly."""
        data = DeploymentRead.model_validate(sample_deployment_data)
        deployment = Deployment(data, mock_client)

        assert isinstance(deployment, Deployment)
        assert isinstance(deployment, Resource)

    def test_hasattr_for_model_fields(
        self, sample_deployment_data: dict, mock_client: MockHTTPClient
    ):
        """Test that hasattr works for delegated model fields."""
        data = DeploymentRead.model_validate(sample_deployment_data)
        deployment = Deployment(data, mock_client)

        # These should return True
        assert hasattr(deployment, "name")
        assert hasattr(deployment, "status")
        assert hasattr(deployment, "config")
        assert hasattr(deployment, "id")
        assert hasattr(deployment, "data")

        # These should return False
        assert not hasattr(deployment, "nonexistent_field")
        assert not hasattr(deployment, "foo_bar_baz")

    def test_dir_includes_model_fields(
        self, sample_deployment_data: dict, mock_client: MockHTTPClient
    ):
        """Test that dir() includes the expected attributes."""
        data = DeploymentRead.model_validate(sample_deployment_data)
        deployment = Deployment(data, mock_client)

        dir_result = dir(deployment)

        # Methods should be in dir
        assert "refresh" in dir_result
        assert "save" in dir_result
        assert "delete" in dir_result

        # Properties should be in dir
        assert "id" in dir_result
        assert "data" in dir_result

    def test_repr_still_works(
        self, sample_deployment_data: dict, mock_client: MockHTTPClient
    ):
        """Test that __repr__ still works correctly with delegation."""
        data = DeploymentRead.model_validate(sample_deployment_data)
        deployment = Deployment(data, mock_client)

        repr_str = repr(deployment)
        assert "Deployment" in repr_str
        assert "test-deployment" in repr_str
        assert "active" in repr_str


class TestResourceManager:
    """Tests for the ResourceManager base class."""

    @pytest.fixture
    def deployment_id(self) -> UUID:
        """Create a sample deployment UUID."""
        return uuid4()

    @pytest.fixture
    def sample_deployment_response(self, deployment_id: UUID) -> dict:
        """Create sample deployment response data."""
        return {
            "id": str(deployment_id),
            "agent_definition_id": str(uuid4()),
            "blueprint_id": None,
            "name": "test-deployment",
            "description": "A test deployment",
            "environment": "production",
            "status": "active",
            "config": {},
            "project_context": {},
            "spec_md_path": None,
            "created_at": "2024-01-15T10:30:00Z",
            "updated_at": "2024-01-15T10:30:00Z",
        }

    def test_resource_manager_class_attributes(self):
        """Test that DeploymentsResource has correct class attributes."""
        assert DeploymentsResource._resource_class is Deployment
        assert DeploymentsResource._model_class is DeploymentRead
        assert DeploymentsResource._base_path == "/api/v1/deployments"

    def test_resource_manager_inherits_from_base(self):
        """Test that DeploymentsResource inherits from ResourceManager."""
        assert issubclass(DeploymentsResource, ResourceManager)

    async def test_resource_manager_get_uses_base_path(
        self, deployment_id: UUID, sample_deployment_response: dict
    ):
        """Test that get() uses the configured _base_path."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.json.return_value = sample_deployment_response

        mock_client = MagicMock()
        mock_client._request = AsyncMock(return_value=mock_response)
        mock_client._raise_for_status = MagicMock()

        resource = DeploymentsResource(mock_client)
        result = await resource.get(deployment_id)

        mock_client._request.assert_called_once_with(
            "GET", f"/api/v1/deployments/{deployment_id}"
        )
        assert isinstance(result, Deployment)
        assert result.id == deployment_id

    async def test_resource_manager_list_helper(self, sample_deployment_response: dict):
        """Test that _list() helper correctly fetches and wraps resources."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.json.return_value = [sample_deployment_response]

        mock_client = MagicMock()
        mock_client._request = AsyncMock(return_value=mock_response)
        mock_client._raise_for_status = MagicMock()

        resource = DeploymentsResource(mock_client)
        result = await resource._list(params={"limit": 10})

        mock_client._request.assert_called_once_with(
            "GET", "/api/v1/deployments", params={"limit": 10}
        )
        assert len(result) == 1
        assert isinstance(result[0], Deployment)

    async def test_resource_manager_list_helper_with_custom_path(
        self, sample_deployment_response: dict
    ):
        """Test that _list() can use a custom path."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.json.return_value = [sample_deployment_response]

        mock_client = MagicMock()
        mock_client._request = AsyncMock(return_value=mock_response)
        mock_client._raise_for_status = MagicMock()

        resource = DeploymentsResource(mock_client)
        result = await resource._list(path="/api/v1/custom/path", params={"limit": 5})

        mock_client._request.assert_called_once_with(
            "GET", "/api/v1/custom/path", params={"limit": 5}
        )
        assert len(result) == 1

    def test_build_list_params_basic(self):
        """Test _build_list_params with basic pagination."""
        params = DeploymentsResource._build_list_params(limit=50, offset=10)

        assert params == {"limit": 50, "offset": 10}

    def test_build_list_params_with_extra(self):
        """Test _build_list_params with extra parameters."""
        params = DeploymentsResource._build_list_params(
            limit=25,
            offset=0,
            status="active",
            environment="production",
        )

        assert params == {
            "limit": 25,
            "offset": 0,
            "status": "active",
            "environment": "production",
        }

    def test_build_list_params_filters_none(self):
        """Test that _build_list_params filters out None values."""
        params = DeploymentsResource._build_list_params(
            limit=100,
            offset=0,
            status=None,
            environment="staging",
            deployment_id=None,
        )

        assert params == {
            "limit": 100,
            "offset": 0,
            "environment": "staging",
        }
        assert "status" not in params
        assert "deployment_id" not in params

    def test_build_list_params_defaults(self):
        """Test _build_list_params uses correct defaults."""
        params = DeploymentsResource._build_list_params()

        assert params == {"limit": 100, "offset": 0}

    async def test_resource_manager_list_empty_response(self):
        """Test that _list() handles empty response correctly."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.json.return_value = []

        mock_client = MagicMock()
        mock_client._request = AsyncMock(return_value=mock_response)
        mock_client._raise_for_status = MagicMock()

        resource = DeploymentsResource(mock_client)
        result = await resource._list(params={})

        assert result == []

    async def test_resource_manager_list_multiple_items(
        self, sample_deployment_response: dict
    ):
        """Test that _list() handles multiple items correctly."""
        response_data = []
        for i in range(3):
            item = sample_deployment_response.copy()
            item["id"] = str(uuid4())
            item["name"] = f"deployment-{i}"
            response_data.append(item)

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.json.return_value = response_data

        mock_client = MagicMock()
        mock_client._request = AsyncMock(return_value=mock_response)
        mock_client._raise_for_status = MagicMock()

        resource = DeploymentsResource(mock_client)
        result = await resource._list(params={})

        assert len(result) == 3
        for i, item in enumerate(result):
            assert isinstance(item, Deployment)
            assert item.name == f"deployment-{i}"
