"""Integration tests for ControlPlaneClient.

These tests require a running Control Plane instance and are skipped by default.
Run with: ATLAS_INTEGRATION_TEST=1 pytest tests/integration/
"""

from uuid import UUID

import pytest

from atlas_sdk.clients.control_plane import ControlPlaneClient
from atlas_sdk.models.control_plane.agent_class import (
    AgentClassCreate,
    AgentClassUpdate,
)
from atlas_sdk.models.control_plane.model_provider import (
    ModelProviderCreate,
    ModelProviderUpdate,
)
from atlas_sdk.models.control_plane.system_prompt import SystemPromptCreate
from atlas_sdk.models.control_plane.tool import ToolCreate, ToolSyncRequest
from atlas_sdk.models.enums import SystemPromptStatus, SystemPromptStorageType


@pytest.mark.integration
class TestAgentClassIntegration:
    """Integration tests for agent class operations."""

    async def test_create_and_get_agent_class(
        self,
        control_plane_client: ControlPlaneClient,
        unique_name: str,
    ) -> None:
        """Should create an agent class and retrieve it."""
        created = await control_plane_client.create_agent_class(
            AgentClassCreate(
                name=unique_name,
                description="Test description",
            )
        )

        assert created.name == unique_name
        assert created.description == "Test description"
        assert isinstance(created.id, UUID)

        # Retrieve and verify
        retrieved = await control_plane_client.get_agent_class(created.id)
        assert retrieved.name == unique_name
        assert retrieved.id == created.id

        # Cleanup
        await control_plane_client.delete_agent_class(created.id)

    async def test_update_agent_class(
        self,
        control_plane_client: ControlPlaneClient,
        unique_name: str,
    ) -> None:
        """Should update an agent class."""
        created = await control_plane_client.create_agent_class(
            AgentClassCreate(name=unique_name)
        )

        updated = await control_plane_client.update_agent_class(
            created.id,
            AgentClassUpdate(
                name=f"{unique_name}-updated",
                description="Updated description",
            ),
        )

        assert updated.name == f"{unique_name}-updated"
        assert updated.description == "Updated description"

        # Cleanup
        await control_plane_client.delete_agent_class(created.id)

    async def test_list_agent_classes(
        self,
        control_plane_client: ControlPlaneClient,
        test_agent_class: dict,
    ) -> None:
        """Should list agent classes with pagination."""
        classes = await control_plane_client.list_agent_classes(limit=10)

        assert len(classes) >= 1
        assert any(c.id == UUID(test_agent_class["id"]) for c in classes)

    async def test_delete_agent_class(
        self,
        control_plane_client: ControlPlaneClient,
        unique_name: str,
    ) -> None:
        """Should delete an agent class."""
        created = await control_plane_client.create_agent_class(
            AgentClassCreate(name=unique_name)
        )

        await control_plane_client.delete_agent_class(created.id)

        # Verify deletion raises 404
        from atlas_sdk.exceptions import AtlasHTTPStatusError

        with pytest.raises(AtlasHTTPStatusError) as exc_info:
            await control_plane_client.get_agent_class(created.id)

        assert exc_info.value.response.status_code == 404


@pytest.mark.integration
class TestModelProviderIntegration:
    """Integration tests for model provider operations."""

    async def test_create_and_get_model_provider(
        self,
        control_plane_client: ControlPlaneClient,
        unique_name: str,
    ) -> None:
        """Should create a model provider and retrieve it."""
        created = await control_plane_client.create_model_provider(
            ModelProviderCreate(
                name=unique_name,
                api_base_url="http://localhost:11434",
                description="Test provider",
                config={"timeout": 30},
            )
        )

        assert created.name == unique_name
        assert created.api_base_url == "http://localhost:11434"

        # Retrieve and verify
        retrieved = await control_plane_client.get_model_provider(created.id)
        assert retrieved.name == unique_name

        # Cleanup
        await control_plane_client.delete_model_provider(created.id)

    async def test_update_model_provider(
        self,
        control_plane_client: ControlPlaneClient,
        unique_name: str,
    ) -> None:
        """Should update a model provider."""
        created = await control_plane_client.create_model_provider(
            ModelProviderCreate(name=unique_name)
        )

        updated = await control_plane_client.update_model_provider(
            created.id,
            ModelProviderUpdate(
                api_base_url="http://new-url:8080",
            ),
        )

        assert updated.api_base_url == "http://new-url:8080"

        # Cleanup
        await control_plane_client.delete_model_provider(created.id)

    async def test_list_model_providers(
        self,
        control_plane_client: ControlPlaneClient,
        test_model_provider: dict,
    ) -> None:
        """Should list model providers."""
        providers = await control_plane_client.list_model_providers(limit=10)

        assert len(providers) >= 1


@pytest.mark.integration
class TestSystemPromptIntegration:
    """Integration tests for system prompt operations."""

    async def test_create_system_prompt(
        self,
        control_plane_client: ControlPlaneClient,
        test_agent_class: dict,
        unique_name: str,
    ) -> None:
        """Should create a system prompt."""
        created = await control_plane_client.create_system_prompt(
            SystemPromptCreate(
                name=unique_name,
                content="You are a helpful assistant.",
                status=SystemPromptStatus.DRAFT,
                content_storage_type=SystemPromptStorageType.INLINE,
                agent_class_id=UUID(test_agent_class["id"]),
            )
        )

        assert created.name == unique_name
        assert created.content == "You are a helpful assistant."

        # Cleanup
        await control_plane_client.delete_system_prompt(created.id)


@pytest.mark.integration
class TestToolIntegration:
    """Integration tests for tool operations."""

    async def test_create_and_get_tool(
        self,
        control_plane_client: ControlPlaneClient,
        unique_name: str,
    ) -> None:
        """Should create a tool and retrieve it."""
        created = await control_plane_client.create_tool(
            ToolCreate(
                name=unique_name,
                description="A test tool",
                json_schema={
                    "type": "object",
                    "properties": {"input": {"type": "string"}},
                },
                risk_level="low",
            )
        )

        assert created.name == unique_name

        # Retrieve and verify
        retrieved = await control_plane_client.get_tool(created.id)
        assert retrieved.name == unique_name

        # Cleanup
        await control_plane_client.delete_tool(created.id)

    async def test_sync_tools(
        self,
        control_plane_client: ControlPlaneClient,
    ) -> None:
        """Should sync multiple tools."""
        tools = [
            ToolCreate(
                name=f"sync-tool-{i}",
                json_schema={"type": "object"},
            )
            for i in range(3)
        ]

        result = await control_plane_client.sync_tools(ToolSyncRequest(tools=tools))

        # Note: sync_tools may return created/updated counts
        # depending on implementation
        assert result is not None


@pytest.mark.integration
class TestPaginationIntegration:
    """Integration tests for pagination behavior."""

    async def test_list_with_limit_and_offset(
        self,
        control_plane_client: ControlPlaneClient,
    ) -> None:
        """Should respect limit and offset parameters."""
        # Get first page
        page1 = await control_plane_client.list_agent_classes(limit=2, offset=0)

        # Get second page
        page2 = await control_plane_client.list_agent_classes(limit=2, offset=2)

        # Pages should not overlap (if there are enough records)
        if len(page1) == 2 and len(page2) > 0:
            page1_ids = {c.id for c in page1}
            page2_ids = {c.id for c in page2}
            assert page1_ids.isdisjoint(page2_ids)


@pytest.mark.integration
class TestErrorHandlingIntegration:
    """Integration tests for error handling."""

    async def test_not_found_error(
        self,
        control_plane_client: ControlPlaneClient,
    ) -> None:
        """Should raise appropriate error for non-existent resource."""
        from uuid import uuid4

        from atlas_sdk.exceptions import AtlasHTTPStatusError

        with pytest.raises(AtlasHTTPStatusError) as exc_info:
            await control_plane_client.get_agent_class(uuid4())

        assert exc_info.value.response.status_code == 404
