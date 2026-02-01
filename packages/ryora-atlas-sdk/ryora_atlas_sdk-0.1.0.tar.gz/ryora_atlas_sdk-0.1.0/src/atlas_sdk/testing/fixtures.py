"""Pytest fixtures for testing with the Atlas SDK.

This module provides pytest fixtures that can be imported into your conftest.py
for convenient testing of code that uses the Atlas SDK.

Usage:
    In your conftest.py:
        ```python
        from atlas_sdk.testing.fixtures import (
            mock_http_client,
            fake_control_plane,
            fake_dispatch,
            fake_workflow,
        )
        ```

    In your tests:
        ```python
        @pytest.mark.asyncio
        async def test_my_feature(fake_control_plane):
            async with fake_control_plane as client:
                result = await client.health()
                assert result["status"] == "healthy"
        ```

Note:
    These fixtures are exported from the module level and can be imported
    directly. They are designed to work with pytest-asyncio.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, AsyncGenerator, Generator
from uuid import uuid4

import pytest

from atlas_sdk.testing.factories import reset_factories
from atlas_sdk.testing.fake_clients import (
    FakeControlPlaneClient,
    FakeDispatchClient,
    FakeWorkflowClient,
)
from atlas_sdk.testing.mock_client import MockHTTPClient

if TYPE_CHECKING:
    from uuid import UUID


# =============================================================================
# Mock HTTP Client Fixtures
# =============================================================================


@pytest.fixture
def mock_http_client() -> Generator[MockHTTPClient, None, None]:
    """Provide a MockHTTPClient for testing.

    The mock client allows you to configure responses and verify requests.

    Example:
        ```python
        def test_custom_logic(mock_http_client):
            mock_http_client.add_response("GET", "/api/v1/health", {"status": "ok"})

            # Use with real SDK client
            from atlas_sdk import ControlPlaneClient
            client = ControlPlaneClient(base_url="http://test", http_client=mock_http_client)
            # ...test your code...

            # Verify requests were made
            mock_http_client.assert_request_made("GET", "/api/v1/health")
        ```

    Yields:
        MockHTTPClient instance that is cleared after each test.
    """
    client = MockHTTPClient()
    yield client
    client.clear()


@pytest.fixture
async def async_mock_http_client() -> AsyncGenerator[MockHTTPClient, None]:
    """Provide an async MockHTTPClient for testing.

    Same as mock_http_client but properly enters the async context manager.

    Example:
        ```python
        @pytest.mark.asyncio
        async def test_with_async_mock(async_mock_http_client):
            async_mock_http_client.add_response("GET", "/test", {"ok": True})

            response = await async_mock_http_client._request("GET", "/test")
            assert response.status_code == 200
        ```

    Yields:
        MockHTTPClient instance within async context.
    """
    client = MockHTTPClient()
    async with client:
        yield client


# =============================================================================
# Fake Client Fixtures
# =============================================================================


@pytest.fixture
def fake_control_plane() -> Generator[FakeControlPlaneClient, None, None]:
    """Provide a FakeControlPlaneClient for testing.

    The fake client stores data in memory and implements the full
    ControlPlaneClient interface without making HTTP requests.

    Example:
        ```python
        @pytest.mark.asyncio
        async def test_agent_class_crud(fake_control_plane):
            async with fake_control_plane as client:
                # Create
                agent_class = await client.create_agent_class(
                    AgentClassCreate(name="Test", description="Testing")
                )

                # Read
                fetched = await client.get_agent_class(agent_class.id)
                assert fetched.name == "Test"

                # Delete
                await client.delete_agent_class(agent_class.id)
        ```

    Yields:
        FakeControlPlaneClient instance that is cleared after each test.
    """
    client = FakeControlPlaneClient()
    yield client
    client.clear()


@pytest.fixture
async def async_fake_control_plane() -> AsyncGenerator[FakeControlPlaneClient, None]:
    """Provide an async FakeControlPlaneClient for testing.

    Same as fake_control_plane but properly enters the async context manager.

    Yields:
        FakeControlPlaneClient instance within async context.
    """
    client = FakeControlPlaneClient()
    async with client:
        yield client


@pytest.fixture
def fake_dispatch() -> Generator[FakeDispatchClient, None, None]:
    """Provide a FakeDispatchClient for testing.

    The fake client simulates agent spawning and lifecycle without HTTP.

    Example:
        ```python
        @pytest.mark.asyncio
        async def test_spawn_agent(fake_dispatch):
            async with fake_dispatch as client:
                response = await client.spawn_agent(SpawnRequest(
                    deployment_id=uuid4(),
                    routing_key="test-key",
                ))
                assert response.instance_id is not None
        ```

    Yields:
        FakeDispatchClient instance that is cleared after each test.
    """
    client = FakeDispatchClient()
    yield client
    client.clear()


@pytest.fixture
async def async_fake_dispatch() -> AsyncGenerator[FakeDispatchClient, None]:
    """Provide an async FakeDispatchClient for testing.

    Same as fake_dispatch but properly enters the async context manager.

    Yields:
        FakeDispatchClient instance within async context.
    """
    client = FakeDispatchClient()
    async with client:
        yield client


@pytest.fixture
def fake_workflow() -> Generator[FakeWorkflowClient, None, None]:
    """Provide a FakeWorkflowClient for testing.

    The fake client simulates workflow orchestration without HTTP.

    Example:
        ```python
        @pytest.mark.asyncio
        async def test_create_plan(fake_workflow):
            async with fake_workflow as client:
                plan = await client.create_plan(
                    deployment_id=uuid4(),
                    instance_id=uuid4(),
                    plan=PlanCreate(goal="Test goal"),
                )
                assert plan.goal == "Test goal"
        ```

    Yields:
        FakeWorkflowClient instance that is cleared after each test.
    """
    client = FakeWorkflowClient()
    yield client
    client.clear()


@pytest.fixture
async def async_fake_workflow() -> AsyncGenerator[FakeWorkflowClient, None]:
    """Provide an async FakeWorkflowClient for testing.

    Same as fake_workflow but properly enters the async context manager.

    Yields:
        FakeWorkflowClient instance within async context.
    """
    client = FakeWorkflowClient()
    async with client:
        yield client


# =============================================================================
# Factory Fixtures
# =============================================================================


@pytest.fixture(autouse=False)
def reset_factory_counters() -> Generator[None, None, None]:
    """Reset factory counters for deterministic test data.

    Use this fixture when you need predictable names from factory functions.
    It's not autouse by default, so import it explicitly when needed.

    Example:
        ```python
        def test_with_deterministic_names(reset_factory_counters):
            from atlas_sdk.testing import factory_agent_class

            # First call always generates "TestClass-1"
            agent_class = factory_agent_class()
            assert agent_class.name == "TestClass-1"
        ```

    Yields:
        None (side effect: resets counters before and after test)
    """
    reset_factories()
    yield
    reset_factories()


# =============================================================================
# Common Test Data Fixtures
# =============================================================================


@pytest.fixture
def test_uuid() -> UUID:
    """Provide a random UUID for testing.

    Example:
        ```python
        def test_with_uuid(test_uuid):
            # Use test_uuid in your test
            assert isinstance(test_uuid, UUID)
        ```

    Returns:
        A new random UUID.
    """
    return uuid4()


@pytest.fixture
def test_deployment_id() -> UUID:
    """Provide a random deployment UUID for testing.

    Returns:
        A new random UUID for deployment_id.
    """
    return uuid4()


@pytest.fixture
def test_instance_id() -> UUID:
    """Provide a random instance UUID for testing.

    Returns:
        A new random UUID for instance_id.
    """
    return uuid4()


@pytest.fixture
def test_plan_id() -> UUID:
    """Provide a random plan UUID for testing.

    Returns:
        A new random UUID for plan_id.
    """
    return uuid4()


# =============================================================================
# Fixture Export List
# =============================================================================

__all__ = [
    # Mock client fixtures
    "mock_http_client",
    "async_mock_http_client",
    # Fake client fixtures
    "fake_control_plane",
    "async_fake_control_plane",
    "fake_dispatch",
    "async_fake_dispatch",
    "fake_workflow",
    "async_fake_workflow",
    # Factory fixtures
    "reset_factory_counters",
    # Test data fixtures
    "test_uuid",
    "test_deployment_id",
    "test_instance_id",
    "test_plan_id",
]
