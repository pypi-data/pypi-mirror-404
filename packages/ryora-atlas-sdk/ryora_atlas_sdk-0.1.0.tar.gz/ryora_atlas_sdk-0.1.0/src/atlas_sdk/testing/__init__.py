"""Testing utilities for the Atlas SDK.

This module provides testing utilities for applications using the Atlas SDK.
It includes mock clients, fake implementations, response factories, and pytest fixtures.

Usage:
    The testing module is designed to make it easy to test code that uses the
    Atlas SDK without making real HTTP requests.

Example - Using MockHTTPClient:
    ```python
    from atlas_sdk.testing import MockHTTPClient
    from atlas_sdk import ControlPlaneClient

    # Create a mock client with predefined responses
    mock = MockHTTPClient()
    mock.add_response("GET", "/api/v1/health", {"status": "healthy"})

    # Inject into the real client
    client = ControlPlaneClient(base_url="http://test", http_client=mock)
    async with client:
        result = await client.health()
    ```

Example - Using FakeControlPlaneClient:
    ```python
    from atlas_sdk.testing import FakeControlPlaneClient
    from atlas_sdk import AgentClassCreate

    # Create a fake client with in-memory storage
    async with FakeControlPlaneClient() as client:
        agent_class = await client.create_agent_class(
            AgentClassCreate(name="TestClass", description="For testing")
        )
        assert agent_class.name == "TestClass"

        # Data persists in memory
        fetched = await client.get_agent_class(agent_class.id)
        assert fetched.id == agent_class.id
    ```

Example - Using factories:
    ```python
    from atlas_sdk.testing import factory_deployment, factory_agent_class

    # Create test data with sensible defaults
    deployment = factory_deployment(name="my-deployment")
    agent_class = factory_agent_class()  # Uses auto-generated values
    ```

Example - Using pytest fixtures:
    ```python
    # In conftest.py
    from atlas_sdk.testing.fixtures import mock_http_client, fake_control_plane

    # In tests
    @pytest.mark.asyncio
    async def test_my_feature(fake_control_plane):
        async with fake_control_plane as client:
            result = await client.health()
            assert result.status == "healthy"
    ```
"""

from atlas_sdk.testing.mock_client import MockHTTPClient, MockRequest, MockResponse
from atlas_sdk.testing.fake_clients import (
    FakeControlPlaneClient,
    FakeDispatchClient,
    FakeWorkflowClient,
    FakeNotFoundError,
)
from atlas_sdk.testing.factories import (
    reset_factories,
    # Agent Class
    factory_agent_class,
    factory_agent_class_create,
    # Agent Definition
    factory_agent_definition,
    factory_agent_definition_create,
    factory_agent_definition_config,
    # Agent Instance
    factory_agent_instance,
    factory_agent_instance_create,
    # Deployment
    factory_deployment,
    factory_deployment_create,
    # Plan
    factory_plan,
    factory_plan_create,
    factory_plan_with_tasks,
    # Task
    factory_task,
    factory_task_create,
    # Model Provider
    factory_model_provider,
    factory_model_provider_create,
    # System Prompt
    factory_system_prompt,
    factory_system_prompt_create,
    # Tool
    factory_tool,
    factory_tool_create,
)

__all__ = [
    # Mock client
    "MockHTTPClient",
    "MockRequest",
    "MockResponse",
    # Fake clients
    "FakeControlPlaneClient",
    "FakeDispatchClient",
    "FakeWorkflowClient",
    "FakeNotFoundError",
    # Factory utilities
    "reset_factories",
    # Agent Class factories
    "factory_agent_class",
    "factory_agent_class_create",
    # Agent Definition factories
    "factory_agent_definition",
    "factory_agent_definition_create",
    "factory_agent_definition_config",
    # Agent Instance factories
    "factory_agent_instance",
    "factory_agent_instance_create",
    # Deployment factories
    "factory_deployment",
    "factory_deployment_create",
    # Plan factories
    "factory_plan",
    "factory_plan_create",
    "factory_plan_with_tasks",
    # Task factories
    "factory_task",
    "factory_task_create",
    # Model Provider factories
    "factory_model_provider",
    "factory_model_provider_create",
    # System Prompt factories
    "factory_system_prompt",
    "factory_system_prompt_create",
    # Tool factories
    "factory_tool",
    "factory_tool_create",
]
