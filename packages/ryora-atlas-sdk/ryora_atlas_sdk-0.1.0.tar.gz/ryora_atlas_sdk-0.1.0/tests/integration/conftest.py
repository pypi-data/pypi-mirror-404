"""Pytest configuration for integration tests.

Integration tests require a running Control Plane instance. They are skipped
by default unless the ATLAS_INTEGRATION_TEST environment variable is set.

Environment Variables:
    ATLAS_INTEGRATION_TEST: Set to "1" or "true" to enable integration tests
    ATLAS_BASE_URL: Base URL of the Control Plane (default: http://localhost:8000)
    ATLAS_DISPATCH_URL: Base URL of the Dispatch service (default: http://localhost:8001)
"""

import os
from collections.abc import AsyncGenerator
from uuid import uuid4

import pytest

from atlas_sdk.clients.control_plane import ControlPlaneClient
from atlas_sdk.clients.dispatch import DispatchClient
from atlas_sdk.clients.workflow import WorkflowClient


def _is_integration_enabled() -> bool:
    """Check if integration tests should run."""
    value = os.environ.get("ATLAS_INTEGRATION_TEST", "").lower()
    return value in ("1", "true", "yes")


# Custom pytest marker for integration tests
def pytest_configure(config: pytest.Config) -> None:
    """Register the integration marker."""
    config.addinivalue_line(
        "markers",
        "integration: mark test as requiring a real Control Plane instance",
    )


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Skip integration tests unless explicitly enabled."""
    if _is_integration_enabled():
        return

    skip_integration = pytest.mark.skip(
        reason="Integration tests disabled. Set ATLAS_INTEGRATION_TEST=1 to enable."
    )
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)


@pytest.fixture
def control_plane_base_url() -> str:
    """Get the Control Plane base URL from environment."""
    return os.environ.get("ATLAS_BASE_URL", "http://localhost:8000")


@pytest.fixture
def dispatch_base_url() -> str:
    """Get the Dispatch service base URL from environment."""
    return os.environ.get("ATLAS_DISPATCH_URL", "http://localhost:8001")


@pytest.fixture
async def control_plane_client(
    control_plane_base_url: str,
) -> AsyncGenerator[ControlPlaneClient, None]:
    """Create a ControlPlaneClient for integration tests."""
    client = ControlPlaneClient(base_url=control_plane_base_url)
    async with client:
        yield client


@pytest.fixture
async def dispatch_client(
    dispatch_base_url: str,
) -> AsyncGenerator[DispatchClient, None]:
    """Create a DispatchClient for integration tests."""
    client = DispatchClient(base_url=dispatch_base_url)
    async with client:
        yield client


@pytest.fixture
async def workflow_client(
    control_plane_base_url: str,
) -> AsyncGenerator[WorkflowClient, None]:
    """Create a WorkflowClient for integration tests."""
    client = WorkflowClient(base_url=control_plane_base_url)
    async with client:
        yield client


@pytest.fixture
def unique_name() -> str:
    """Generate a unique name for test resources."""
    return f"test-{uuid4().hex[:8]}"


@pytest.fixture
async def test_agent_class(
    control_plane_client: ControlPlaneClient,
    unique_name: str,
) -> AsyncGenerator[dict, None]:
    """Create and cleanup a test agent class.

    Yields the created agent class dict and cleans it up after the test.
    """
    from atlas_sdk.models.control_plane.agent_class import AgentClassCreate

    agent_class = await control_plane_client.create_agent_class(
        AgentClassCreate(
            name=unique_name,
            description="Integration test agent class",
        )
    )

    yield agent_class.model_dump()

    # Cleanup
    try:
        await control_plane_client.delete_agent_class(agent_class.id)
    except Exception:
        pass  # Ignore cleanup errors


@pytest.fixture
async def test_model_provider(
    control_plane_client: ControlPlaneClient,
    unique_name: str,
) -> AsyncGenerator[dict, None]:
    """Create and cleanup a test model provider.

    Yields the created model provider dict and cleans it up after the test.
    """
    from atlas_sdk.models.control_plane.model_provider import ModelProviderCreate

    provider = await control_plane_client.create_model_provider(
        ModelProviderCreate(
            name=unique_name,
            api_base_url="http://localhost:11434",
            description="Integration test provider",
        )
    )

    yield provider.model_dump()

    # Cleanup
    try:
        await control_plane_client.delete_model_provider(provider.id)
    except Exception:
        pass  # Ignore cleanup errors
