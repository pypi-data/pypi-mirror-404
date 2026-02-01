"""Fake client implementations for testing.

This module provides in-memory implementations of the SDK clients for testing.
These fake clients store data in dictionaries and don't make any HTTP requests,
making them ideal for unit testing business logic.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Self
from uuid import UUID, uuid4

from atlas_sdk.exceptions import AtlasError
from atlas_sdk.models import (
    # Enums
    AgentDefinitionStatus,
    DeploymentStatus,
    GraspAnalysisStatus,
    PlanStatus,
    PlanTaskStatus,
    SystemPromptStatus,
    # Agent Class
    AgentClassCreate,
    AgentClassRead,
    AgentClassUpdate,
    # Agent Definition
    AgentDefinitionConfig,
    AgentDefinitionCreate,
    AgentDefinitionRead,
    AgentDefinitionUpdate,
    # Agent Instance
    AgentInstanceRead,
    # Deployment
    DeploymentCreate,
    DeploymentRead,
    DeploymentUpdate,
    # Plan
    PlanCreate,
    PlanCreateResponse,
    PlanRead,
    PlanReadWithTasks,
    PlanTaskRead,
    PlanTaskUpdate,
    PlanUpdate,
    TasksAppend,
    TasksAppendResponse,
    # Model Provider
    ModelProviderCreate,
    ModelProviderRead,
    ModelProviderUpdate,
    # System Prompt
    SystemPromptCreate,
    SystemPromptRead,
    SystemPromptUpdate,
    # Tool
    ToolRead,
    ToolSyncRequest,
)
from atlas_sdk.models.control_plane import (
    GraspAnalysisCreate,
    GraspAnalysisRead,
    GraspAnalysisSummary,
)
from atlas_sdk.models.dispatch import (
    AgentStatusResponse,
    SpawnRequest,
    SpawnResponse,
    StopResponse,
    WaitResponse,
)


def _now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


def _make_slug(name: str) -> str:
    """Generate a URL-safe slug from a name."""
    return name.lower().replace(" ", "-").replace("_", "-")


class FakeNotFoundError(AtlasError):
    """A simplified NotFoundError for fake clients that doesn't require httpx objects.

    This exception is raised by fake clients when a resource is not found.
    It inherits from AtlasError so it can be caught with the same exception
    hierarchy, but doesn't require the httpx Request/Response objects that
    AtlasNotFoundError needs.
    """

    pass


class FakeControlPlaneClient:
    """In-memory fake implementation of ControlPlaneClient for testing.

    This fake client stores all data in memory and provides the same interface
    as the real ControlPlaneClient. It's useful for unit testing business logic
    without HTTP mocking overhead.

    All CRUD operations work as expected:
    - Create: Adds to in-memory storage with auto-generated IDs
    - Read: Returns from storage or raises FakeNotFoundError
    - Update: Modifies in storage
    - Delete: Removes from storage

    Example:
        ```python
        from atlas_sdk.testing import FakeControlPlaneClient
        from atlas_sdk import AgentClassCreate

        async with FakeControlPlaneClient() as client:
            # Create an agent class
            agent_class = await client.create_agent_class(
                AgentClassCreate(name="TestClass", description="Testing")
            )
            assert agent_class.name == "TestClass"

            # Data persists in memory
            fetched = await client.get_agent_class(agent_class.id)
            assert fetched.id == agent_class.id

            # List operations work
            classes = await client.list_agent_classes()
            assert len(classes) == 1

            # Cleanup
            await client.delete_agent_class(agent_class.id)
            classes = await client.list_agent_classes()
            assert len(classes) == 0
        ```

    Attributes:
        agent_classes: In-memory storage for agent classes
        agent_definitions: In-memory storage for agent definitions
        model_providers: In-memory storage for model providers
        system_prompts: In-memory storage for system prompts
        tools: In-memory storage for tools
        deployments: In-memory storage for deployments
        grasp_analyses: In-memory storage for GRASP analyses
    """

    def __init__(self, base_url: str = "http://fake-control-plane") -> None:
        """Initialize the fake client.

        Args:
            base_url: Base URL (for compatibility, not used)
        """
        self.base_url = base_url
        self._closed = False

        # In-memory storage
        self.agent_classes: dict[UUID, AgentClassRead] = {}
        self.agent_definitions: dict[UUID, AgentDefinitionRead] = {}
        self.model_providers: dict[UUID, ModelProviderRead] = {}
        self.system_prompts: dict[UUID, SystemPromptRead] = {}
        self.tools: dict[UUID, ToolRead] = {}
        self.deployments: dict[UUID, DeploymentRead] = {}
        self.grasp_analyses: dict[UUID, GraspAnalysisRead] = {}

    async def __aenter__(self) -> Self:
        """Enter async context manager."""
        self._closed = False
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Exit async context manager."""
        self._closed = True

    async def close(self) -> None:
        """Close the fake client."""
        self._closed = True

    def clear(self) -> None:
        """Clear all stored data."""
        self.agent_classes.clear()
        self.agent_definitions.clear()
        self.model_providers.clear()
        self.system_prompts.clear()
        self.tools.clear()
        self.deployments.clear()
        self.grasp_analyses.clear()

    # -------------------------------------------------------------------------
    # Agent Classes
    # -------------------------------------------------------------------------

    async def create_agent_class(
        self,
        agent_class: AgentClassCreate,
        *,
        idempotency_key: str | None = None,
    ) -> AgentClassRead:
        """Create an agent class in memory."""
        now = _now()
        read_model = AgentClassRead(
            id=uuid4(),
            name=agent_class.name,
            description=agent_class.description,
            created_at=now,
            updated_at=now,
        )
        self.agent_classes[read_model.id] = read_model
        return read_model

    async def get_agent_class(self, agent_class_id: UUID) -> AgentClassRead:
        """Get an agent class from memory."""
        if agent_class_id not in self.agent_classes:
            raise FakeNotFoundError(f"Agent class {agent_class_id} not found")
        return self.agent_classes[agent_class_id]

    async def list_agent_classes(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AgentClassRead]:
        """List agent classes from memory."""
        items = list(self.agent_classes.values())
        return items[offset : offset + limit]

    async def update_agent_class(
        self, agent_class_id: UUID, update_data: AgentClassUpdate
    ) -> AgentClassRead:
        """Update an agent class in memory."""
        if agent_class_id not in self.agent_classes:
            raise FakeNotFoundError(f"Agent class {agent_class_id} not found")

        existing = self.agent_classes[agent_class_id]
        update_dict = update_data.model_dump(exclude_unset=True)

        updated = AgentClassRead(
            id=existing.id,
            name=update_dict.get("name", existing.name),
            description=update_dict.get("description", existing.description),
            created_at=existing.created_at,
            updated_at=_now(),
        )
        self.agent_classes[agent_class_id] = updated
        return updated

    async def delete_agent_class(self, agent_class_id: UUID) -> None:
        """Delete an agent class from memory."""
        if agent_class_id not in self.agent_classes:
            raise FakeNotFoundError(f"Agent class {agent_class_id} not found")
        del self.agent_classes[agent_class_id]

    # -------------------------------------------------------------------------
    # Agent Definitions
    # -------------------------------------------------------------------------

    async def create_agent_definition(
        self,
        agent_definition: AgentDefinitionCreate,
        *,
        idempotency_key: str | None = None,
    ) -> AgentDefinitionRead:
        """Create an agent definition in memory."""
        now = _now()
        read_model = AgentDefinitionRead(
            id=uuid4(),
            agent_class_id=agent_definition.agent_class_id,
            system_prompt_id=agent_definition.system_prompt_id,
            structured_output_id=agent_definition.structured_output_id,
            model_provider_id=agent_definition.model_provider_id,
            name=agent_definition.name,
            slug=_make_slug(agent_definition.name),
            description=agent_definition.description,
            status=AgentDefinitionStatus.DRAFT,
            execution_mode=agent_definition.execution_mode,
            model_name=agent_definition.model_name,
            config=agent_definition.config,
            allow_outbound_a2a=agent_definition.allow_outbound_a2a,
            created_at=now,
            updated_at=now,
        )
        self.agent_definitions[read_model.id] = read_model
        return read_model

    async def get_agent_definition(self, definition_id: UUID) -> AgentDefinitionRead:
        """Get an agent definition from memory."""
        if definition_id not in self.agent_definitions:
            raise FakeNotFoundError(f"Agent definition {definition_id} not found")
        return self.agent_definitions[definition_id]

    async def get_agent_definition_config(
        self, definition_id: UUID
    ) -> AgentDefinitionConfig:
        """Get agent definition config from memory."""
        if definition_id not in self.agent_definitions:
            raise FakeNotFoundError(f"Agent definition {definition_id} not found")

        defn = self.agent_definitions[definition_id]

        # Resolve system prompt content if present
        system_prompt_content: str | None = None
        if defn.system_prompt_id and defn.system_prompt_id in self.system_prompts:
            system_prompt_content = self.system_prompts[defn.system_prompt_id].content

        return AgentDefinitionConfig(
            id=defn.id,
            name=defn.name,
            slug=defn.slug,
            description=defn.description,
            status=defn.status,
            execution_mode=defn.execution_mode,
            model_name=defn.model_name,
            config=defn.config,
            system_prompt=system_prompt_content,
            structured_output_schema=None,
            tools=[],
        )

    async def list_agent_definitions(
        self,
        status: AgentDefinitionStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AgentDefinitionRead]:
        """List agent definitions from memory."""
        items = list(self.agent_definitions.values())
        if status:
            items = [d for d in items if d.status == status]
        return items[offset : offset + limit]

    async def update_agent_definition(
        self, definition_id: UUID, update_data: AgentDefinitionUpdate
    ) -> AgentDefinitionRead:
        """Update an agent definition in memory."""
        if definition_id not in self.agent_definitions:
            raise FakeNotFoundError(f"Agent definition {definition_id} not found")

        existing = self.agent_definitions[definition_id]
        update_dict = update_data.model_dump(exclude_unset=True)

        updated = AgentDefinitionRead(
            id=existing.id,
            agent_class_id=existing.agent_class_id,
            system_prompt_id=update_dict.get(
                "system_prompt_id", existing.system_prompt_id
            ),
            structured_output_id=update_dict.get(
                "structured_output_id", existing.structured_output_id
            ),
            model_provider_id=update_dict.get(
                "model_provider_id", existing.model_provider_id
            ),
            name=update_dict.get("name", existing.name),
            slug=existing.slug,
            description=update_dict.get("description", existing.description),
            status=update_dict.get("status", existing.status),
            execution_mode=update_dict.get("execution_mode", existing.execution_mode),
            model_name=update_dict.get("model_name", existing.model_name),
            config=update_dict.get("config", existing.config),
            allow_outbound_a2a=update_dict.get(
                "allow_outbound_a2a", existing.allow_outbound_a2a
            ),
            created_at=existing.created_at,
            updated_at=_now(),
        )
        self.agent_definitions[definition_id] = updated
        return updated

    async def delete_agent_definition(self, definition_id: UUID) -> None:
        """Delete an agent definition from memory."""
        if definition_id not in self.agent_definitions:
            raise FakeNotFoundError(f"Agent definition {definition_id} not found")
        del self.agent_definitions[definition_id]

    async def add_tools_to_definition(
        self, definition_id: UUID, tool_ids: list[UUID]
    ) -> AgentDefinitionRead:
        """Add tools to definition (no-op in fake)."""
        if definition_id not in self.agent_definitions:
            raise FakeNotFoundError(f"Agent definition {definition_id} not found")
        return self.agent_definitions[definition_id]

    # -------------------------------------------------------------------------
    # Model Providers
    # -------------------------------------------------------------------------

    async def create_model_provider(
        self,
        model_provider: ModelProviderCreate,
        *,
        idempotency_key: str | None = None,
    ) -> ModelProviderRead:
        """Create a model provider in memory."""
        now = _now()
        read_model = ModelProviderRead(
            id=uuid4(),
            name=model_provider.name,
            api_base_url=model_provider.api_base_url,
            description=model_provider.description,
            config=model_provider.config,
            created_at=now,
            updated_at=now,
        )
        self.model_providers[read_model.id] = read_model
        return read_model

    async def get_model_provider(self, provider_id: UUID) -> ModelProviderRead:
        """Get a model provider from memory."""
        if provider_id not in self.model_providers:
            raise FakeNotFoundError(f"Model provider {provider_id} not found")
        return self.model_providers[provider_id]

    async def list_model_providers(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ModelProviderRead]:
        """List model providers from memory."""
        items = list(self.model_providers.values())
        return items[offset : offset + limit]

    async def update_model_provider(
        self, provider_id: UUID, update_data: ModelProviderUpdate
    ) -> ModelProviderRead:
        """Update a model provider in memory."""
        if provider_id not in self.model_providers:
            raise FakeNotFoundError(f"Model provider {provider_id} not found")

        existing = self.model_providers[provider_id]
        update_dict = update_data.model_dump(exclude_unset=True)

        updated = ModelProviderRead(
            id=existing.id,
            name=update_dict.get("name", existing.name),
            api_base_url=update_dict.get("api_base_url", existing.api_base_url),
            description=update_dict.get("description", existing.description),
            config=update_dict.get("config", existing.config),
            created_at=existing.created_at,
            updated_at=_now(),
        )
        self.model_providers[provider_id] = updated
        return updated

    async def delete_model_provider(self, provider_id: UUID) -> None:
        """Delete a model provider from memory."""
        if provider_id not in self.model_providers:
            raise FakeNotFoundError(f"Model provider {provider_id} not found")
        del self.model_providers[provider_id]

    async def verify_model_provider(self, provider_id: UUID) -> dict[str, Any]:
        """Verify model provider (returns success in fake)."""
        if provider_id not in self.model_providers:
            raise FakeNotFoundError(f"Model provider {provider_id} not found")
        return {"status": "ok", "provider_id": str(provider_id)}

    async def list_provider_models(self, provider_id: UUID) -> list[dict[str, Any]]:
        """List provider models (returns empty in fake)."""
        if provider_id not in self.model_providers:
            raise FakeNotFoundError(f"Model provider {provider_id} not found")
        return []

    # -------------------------------------------------------------------------
    # System Prompts
    # -------------------------------------------------------------------------

    async def create_system_prompt(
        self,
        system_prompt: SystemPromptCreate,
        *,
        idempotency_key: str | None = None,
    ) -> SystemPromptRead:
        """Create a system prompt in memory."""
        now = _now()
        read_model = SystemPromptRead(
            id=uuid4(),
            agent_class_id=system_prompt.agent_class_id,
            name=system_prompt.name,
            description=system_prompt.description,
            status=system_prompt.status,
            content=system_prompt.content,
            content_storage_type=system_prompt.content_storage_type,
            meta=system_prompt.meta,
            created_at=now,
            updated_at=now,
        )
        self.system_prompts[read_model.id] = read_model
        return read_model

    async def get_system_prompt(self, prompt_id: UUID) -> SystemPromptRead:
        """Get a system prompt from memory."""
        if prompt_id not in self.system_prompts:
            raise FakeNotFoundError(f"System prompt {prompt_id} not found")
        return self.system_prompts[prompt_id]

    async def list_system_prompts(
        self,
        agent_class_id: UUID | None = None,
        status: SystemPromptStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[SystemPromptRead]:
        """List system prompts from memory."""
        items = list(self.system_prompts.values())
        if agent_class_id:
            items = [p for p in items if p.agent_class_id == agent_class_id]
        if status:
            items = [p for p in items if p.status == status]
        return items[offset : offset + limit]

    async def update_system_prompt(
        self, prompt_id: UUID, update_data: SystemPromptUpdate
    ) -> SystemPromptRead:
        """Update a system prompt in memory."""
        if prompt_id not in self.system_prompts:
            raise FakeNotFoundError(f"System prompt {prompt_id} not found")

        existing = self.system_prompts[prompt_id]
        update_dict = update_data.model_dump(exclude_unset=True)

        updated = SystemPromptRead(
            id=existing.id,
            agent_class_id=existing.agent_class_id,
            name=update_dict.get("name", existing.name),
            description=update_dict.get("description", existing.description),
            status=update_dict.get("status", existing.status),
            content=update_dict.get("content", existing.content),
            content_storage_type=update_dict.get(
                "content_storage_type", existing.content_storage_type
            ),
            meta=update_dict.get("meta", existing.meta),
            created_at=existing.created_at,
            updated_at=_now(),
        )
        self.system_prompts[prompt_id] = updated
        return updated

    async def delete_system_prompt(self, prompt_id: UUID) -> None:
        """Delete a system prompt from memory."""
        if prompt_id not in self.system_prompts:
            raise FakeNotFoundError(f"System prompt {prompt_id} not found")
        del self.system_prompts[prompt_id]

    # -------------------------------------------------------------------------
    # Tools
    # -------------------------------------------------------------------------

    async def list_tools(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ToolRead]:
        """List tools from memory."""
        items = list(self.tools.values())
        return items[offset : offset + limit]

    async def get_tool(self, tool_id: UUID) -> ToolRead:
        """Get a tool from memory."""
        if tool_id not in self.tools:
            raise FakeNotFoundError(f"Tool {tool_id} not found")
        return self.tools[tool_id]

    async def delete_tool(self, tool_id: UUID) -> None:
        """Delete a tool from memory."""
        if tool_id not in self.tools:
            raise FakeNotFoundError(f"Tool {tool_id} not found")
        del self.tools[tool_id]

    async def sync_tools(self, tools: ToolSyncRequest) -> list[ToolRead]:
        """Sync tools to memory."""
        result = []
        for tool_create in tools.tools:
            tool_read = ToolRead(
                id=uuid4(),
                name=tool_create.name,
                description=tool_create.description,
                json_schema=tool_create.json_schema,
                safety_policy=tool_create.safety_policy,
                risk_level=tool_create.risk_level,
            )
            self.tools[tool_read.id] = tool_read
            result.append(tool_read)
        return result

    async def discover_tools(self, source: str) -> list[ToolRead]:
        """Discover tools (returns empty in fake)."""
        return []

    # -------------------------------------------------------------------------
    # Deployments
    # -------------------------------------------------------------------------

    async def create_deployment(
        self,
        deployment: DeploymentCreate,
        *,
        idempotency_key: str | None = None,
    ) -> DeploymentRead:
        """Create a deployment in memory."""
        now = _now()
        read_model = DeploymentRead(
            id=uuid4(),
            agent_definition_id=deployment.agent_definition_id,
            blueprint_id=deployment.blueprint_id,
            name=deployment.name,
            description=deployment.description,
            environment=deployment.environment,
            status=DeploymentStatus.ACTIVE,
            config=deployment.config,
            project_context=deployment.project_context,
            spec_md_path=deployment.spec_md_path,
            created_at=now,
            updated_at=now,
        )
        self.deployments[read_model.id] = read_model
        return read_model

    async def get_deployment(self, deployment_id: UUID) -> DeploymentRead:
        """Get a deployment from memory."""
        if deployment_id not in self.deployments:
            raise FakeNotFoundError(f"Deployment {deployment_id} not found")
        return self.deployments[deployment_id]

    async def update_deployment(
        self, deployment_id: UUID, update_data: DeploymentUpdate
    ) -> DeploymentRead:
        """Update a deployment in memory."""
        if deployment_id not in self.deployments:
            raise FakeNotFoundError(f"Deployment {deployment_id} not found")

        existing = self.deployments[deployment_id]
        update_dict = update_data.model_dump(exclude_unset=True)

        updated = DeploymentRead(
            id=existing.id,
            agent_definition_id=existing.agent_definition_id,
            blueprint_id=existing.blueprint_id,
            name=update_dict.get("name", existing.name),
            description=update_dict.get("description", existing.description),
            environment=update_dict.get("environment", existing.environment),
            status=update_dict.get("status", existing.status),
            config=update_dict.get("config", existing.config),
            project_context=update_dict.get(
                "project_context", existing.project_context
            ),
            spec_md_path=update_dict.get("spec_md_path", existing.spec_md_path),
            created_at=existing.created_at,
            updated_at=_now(),
        )
        self.deployments[deployment_id] = updated
        return updated

    async def list_deployments(
        self,
        environment: str | None = None,
        active_only: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[DeploymentRead]:
        """List deployments from memory."""
        items = list(self.deployments.values())
        if environment:
            items = [d for d in items if d.environment == environment]
        if active_only:
            items = [d for d in items if d.status == DeploymentStatus.ACTIVE]
        return items[offset : offset + limit]

    async def delete_deployment(self, deployment_id: UUID) -> None:
        """Delete a deployment from memory."""
        if deployment_id not in self.deployments:
            raise FakeNotFoundError(f"Deployment {deployment_id} not found")
        del self.deployments[deployment_id]

    # -------------------------------------------------------------------------
    # GRASP Analyses
    # -------------------------------------------------------------------------

    async def create_grasp_analysis(
        self,
        deployment_id: UUID,
        analysis: GraspAnalysisCreate,
        *,
        idempotency_key: str | None = None,
    ) -> GraspAnalysisRead:
        """Create a GRASP analysis in memory."""
        if deployment_id not in self.deployments:
            raise FakeNotFoundError(f"Deployment {deployment_id} not found")

        now = _now()
        read_model = GraspAnalysisRead(
            id=uuid4(),
            deployment_id=deployment_id,
            status=GraspAnalysisStatus.PENDING,
            analysis_context=analysis.analysis_context,
            error_message=None,
            created_at=now,
        )
        self.grasp_analyses[read_model.id] = read_model
        return read_model

    async def get_grasp_analysis(self, analysis_id: UUID) -> GraspAnalysisRead:
        """Get a GRASP analysis from memory."""
        if analysis_id not in self.grasp_analyses:
            raise FakeNotFoundError(f"GRASP analysis {analysis_id} not found")
        return self.grasp_analyses[analysis_id]

    async def list_grasp_analyses(
        self, deployment_id: UUID, status: GraspAnalysisStatus | None = None
    ) -> list[GraspAnalysisSummary]:
        """List GRASP analyses for a deployment."""
        items = [
            a for a in self.grasp_analyses.values() if a.deployment_id == deployment_id
        ]
        if status:
            items = [a for a in items if a.status == status]
        return [
            GraspAnalysisSummary(
                id=a.id,
                deployment_id=a.deployment_id,
                status=a.status,
                created_at=a.created_at,
                completed_at=a.completed_at,
            )
            for a in items
        ]

    async def query_grasp_analyses(
        self,
        deployment_id: UUID | None = None,
        status: GraspAnalysisStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[GraspAnalysisSummary]:
        """Query GRASP analyses across deployments."""
        items = list(self.grasp_analyses.values())
        if deployment_id:
            items = [a for a in items if a.deployment_id == deployment_id]
        if status:
            items = [a for a in items if a.status == status]
        items = items[offset : offset + limit]
        return [
            GraspAnalysisSummary(
                id=a.id,
                deployment_id=a.deployment_id,
                status=a.status,
                created_at=a.created_at,
                completed_at=a.completed_at,
            )
            for a in items
        ]

    # -------------------------------------------------------------------------
    # Health
    # -------------------------------------------------------------------------

    async def health(self) -> dict[str, Any]:
        """Return fake health status."""
        return {"status": "healthy", "fake": True}

    async def metrics(self) -> dict[str, Any]:
        """Return fake metrics."""
        return {
            "agent_classes_count": len(self.agent_classes),
            "agent_definitions_count": len(self.agent_definitions),
            "deployments_count": len(self.deployments),
        }

    async def logs(
        self,
        deployment_id: UUID | None = None,
        level: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Return fake logs."""
        return []


class FakeDispatchClient:
    """In-memory fake implementation of DispatchClient for testing.

    This fake client simulates agent spawning and lifecycle management
    without making any HTTP requests.

    Example:
        ```python
        from atlas_sdk.testing import FakeDispatchClient
        from atlas_sdk import SpawnRequest

        async with FakeDispatchClient() as client:
            response = await client.spawn_agent(SpawnRequest(
                agent_definition_id=uuid4(),
                deployment_id=uuid4(),
                prompt="Hello agent",
            ))
            assert response.instance_id is not None

            status = await client.get_agent_status(response.instance_id)
            assert status.running is True
        ```
    """

    def __init__(self, base_url: str = "http://fake-dispatch") -> None:
        """Initialize the fake client."""
        self.base_url = base_url
        self._closed = False
        self.agents: dict[UUID, AgentStatusResponse] = {}
        self._next_port = 8000
        self._next_pid = 1000

    async def __aenter__(self) -> Self:
        """Enter async context manager."""
        self._closed = False
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Exit async context manager."""
        self._closed = True

    async def close(self) -> None:
        """Close the fake client."""
        self._closed = True

    def clear(self) -> None:
        """Clear all stored data."""
        self.agents.clear()

    async def spawn_agent(
        self,
        spawn_request: SpawnRequest,
        *,
        idempotency_key: str | None = None,
    ) -> SpawnResponse:
        """Spawn a fake agent."""
        instance_id = uuid4()
        port = self._next_port
        pid = self._next_pid
        self._next_port += 1
        self._next_pid += 1

        status = AgentStatusResponse(
            definition_id=spawn_request.agent_definition_id,
            instance_id=instance_id,
            port=port,
            pid=pid,
            running=True,
        )
        self.agents[instance_id] = status
        return SpawnResponse(
            status="spawned",
            port=port,
            pid=pid,
            url=f"http://localhost:{port}",
            deployment_id=spawn_request.deployment_id,
            instance_id=instance_id,
        )

    async def get_agent_status(self, instance_id: UUID) -> AgentStatusResponse:
        """Get fake agent status."""
        if instance_id not in self.agents:
            raise FakeNotFoundError(f"Agent instance {instance_id} not found")
        return self.agents[instance_id]

    async def stop_agent(self, instance_id: UUID) -> StopResponse:
        """Stop a fake agent."""
        if instance_id not in self.agents:
            raise FakeNotFoundError(f"Agent instance {instance_id} not found")

        agent = self.agents[instance_id]
        # Update status to stopped
        self.agents[instance_id] = AgentStatusResponse(
            definition_id=agent.definition_id,
            instance_id=agent.instance_id,
            port=agent.port,
            pid=agent.pid,
            running=False,
        )
        return StopResponse(status="stopped", message="Agent stopped successfully")

    async def wait_for_agent(
        self,
        instance_id: UUID,
        timeout: float | None = None,
    ) -> WaitResponse:
        """Wait for fake agent (returns immediately)."""
        if instance_id not in self.agents:
            raise FakeNotFoundError(f"Agent instance {instance_id} not found")

        return WaitResponse(
            status="completed",
            instance_id=instance_id,
            output=None,
            error=None,
            exit_code=0,
        )

    async def health(self) -> dict[str, Any]:
        """Return fake health status."""
        return {"status": "healthy", "fake": True}


class FakeWorkflowClient:
    """In-memory fake implementation of WorkflowClient for testing.

    This fake client simulates workflow orchestration without making
    any HTTP requests.

    Example:
        ```python
        from atlas_sdk.testing import FakeWorkflowClient
        from atlas_sdk import PlanCreate

        async with FakeWorkflowClient() as client:
            plan = await client.create_plan(
                deployment_id=uuid4(),
                instance_id=uuid4(),
                plan=PlanCreate(goal="Test goal"),
            )
            assert plan.goal == "Test goal"
        ```
    """

    def __init__(self, base_url: str = "http://fake-workflow") -> None:
        """Initialize the fake client."""
        self.base_url = base_url
        self._closed = False
        self.plans: dict[UUID, PlanRead] = {}
        self.tasks: dict[UUID, PlanTaskRead] = {}
        self.plan_tasks: dict[UUID, list[UUID]] = {}  # plan_id -> task_ids
        self.agent_instances: dict[UUID, AgentInstanceRead] = {}
        self.deployments: dict[UUID, DeploymentRead] = {}

    async def __aenter__(self) -> Self:
        """Enter async context manager."""
        self._closed = False
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Exit async context manager."""
        self._closed = True

    async def close(self) -> None:
        """Close the fake client."""
        self._closed = True

    def clear(self) -> None:
        """Clear all stored data."""
        self.plans.clear()
        self.tasks.clear()
        self.plan_tasks.clear()
        self.agent_instances.clear()
        self.deployments.clear()

    # -------------------------------------------------------------------------
    # Plans
    # -------------------------------------------------------------------------

    async def create_plan(
        self,
        deployment_id: UUID,
        instance_id: UUID,
        plan: PlanCreate,
        *,
        idempotency_key: str | None = None,
    ) -> PlanCreateResponse:
        """Create a plan in memory."""
        now = _now()
        plan_id = uuid4()

        # Create tasks
        task_ids: list[UUID] = []
        for i, task_create in enumerate(plan.tasks):
            task_id = uuid4()
            task_read = PlanTaskRead(
                id=task_id,
                plan_id=plan_id,
                sequence=task_create.sequence or i,
                description=task_create.description,
                validation=task_create.validation,
                assignee_agent_definition_id=task_create.assignee_agent_definition_id,
                status=PlanTaskStatus.PENDING,
                result=None,
                meta=task_create.meta,
                created_at=now,
                updated_at=now,
            )
            self.tasks[task_id] = task_read
            task_ids.append(task_id)

        self.plan_tasks[plan_id] = task_ids

        plan_read = PlanRead(
            id=plan_id,
            deployment_id=deployment_id,
            created_by_instance_id=instance_id,
            goal=plan.goal,
            constraints=plan.constraints,
            state=plan.state,
            status=PlanStatus.ACTIVE,
            spec_reference=plan.spec_reference,
            created_at=now,
            updated_at=now,
        )
        self.plans[plan_id] = plan_read

        return PlanCreateResponse(
            id=plan_id,
            deployment_id=deployment_id,
            created_by_instance_id=instance_id,
            goal=plan.goal,
            constraints=plan.constraints,
            state=plan.state,
            status=PlanStatus.ACTIVE,
            spec_reference=plan.spec_reference,
            created_at=now,
            updated_at=now,
            task_ids=task_ids,
        )

    async def get_plan(self, plan_id: UUID) -> PlanReadWithTasks:
        """Get a plan from memory."""
        if plan_id not in self.plans:
            raise FakeNotFoundError(f"Plan {plan_id} not found")

        plan = self.plans[plan_id]
        task_ids = self.plan_tasks.get(plan_id, [])
        tasks = [self.tasks[tid] for tid in task_ids if tid in self.tasks]

        return PlanReadWithTasks(
            id=plan.id,
            deployment_id=plan.deployment_id,
            created_by_instance_id=plan.created_by_instance_id,
            goal=plan.goal,
            constraints=plan.constraints,
            state=plan.state,
            status=plan.status,
            spec_reference=plan.spec_reference,
            created_at=plan.created_at,
            updated_at=plan.updated_at,
            tasks=tasks,
        )

    async def list_plans(
        self,
        deployment_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[PlanRead]:
        """List plans from memory."""
        items = [p for p in self.plans.values() if p.deployment_id == deployment_id]
        return items[offset : offset + limit]

    async def update_plan(self, plan_id: UUID, update_data: PlanUpdate) -> PlanRead:
        """Update a plan in memory."""
        if plan_id not in self.plans:
            raise FakeNotFoundError(f"Plan {plan_id} not found")

        existing = self.plans[plan_id]
        update_dict = update_data.model_dump(exclude_unset=True)

        updated = PlanRead(
            id=existing.id,
            deployment_id=existing.deployment_id,
            created_by_instance_id=existing.created_by_instance_id,
            goal=update_dict.get("goal", existing.goal),
            constraints=update_dict.get("constraints", existing.constraints),
            state=update_dict.get("state", existing.state),
            status=update_dict.get("status", existing.status),
            spec_reference=update_dict.get("spec_reference", existing.spec_reference),
            created_at=existing.created_at,
            updated_at=_now(),
        )
        self.plans[plan_id] = updated
        return updated

    # -------------------------------------------------------------------------
    # Tasks
    # -------------------------------------------------------------------------

    async def append_tasks(
        self,
        plan_id: UUID,
        tasks: TasksAppend,
        *,
        idempotency_key: str | None = None,
    ) -> TasksAppendResponse:
        """Append tasks to a plan."""
        if plan_id not in self.plans:
            raise FakeNotFoundError(f"Plan {plan_id} not found")

        now = _now()
        task_ids: list[UUID] = []

        for task_create in tasks.tasks:
            task_id = uuid4()
            task_read = PlanTaskRead(
                id=task_id,
                plan_id=plan_id,
                sequence=task_create.sequence,
                description=task_create.description,
                validation=task_create.validation,
                assignee_agent_definition_id=task_create.assignee_agent_definition_id,
                status=PlanTaskStatus.PENDING,
                result=None,
                meta=task_create.meta,
                created_at=now,
                updated_at=now,
            )
            self.tasks[task_id] = task_read
            task_ids.append(task_id)

        if plan_id not in self.plan_tasks:
            self.plan_tasks[plan_id] = []
        self.plan_tasks[plan_id].extend(task_ids)

        return TasksAppendResponse(task_ids=task_ids)

    async def get_task(self, task_id: UUID) -> PlanTaskRead:
        """Get a task from memory."""
        if task_id not in self.tasks:
            raise FakeNotFoundError(f"Task {task_id} not found")
        return self.tasks[task_id]

    async def list_tasks(
        self,
        plan_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[PlanTaskRead]:
        """List tasks for a plan."""
        task_ids = self.plan_tasks.get(plan_id, [])
        tasks = [self.tasks[tid] for tid in task_ids if tid in self.tasks]
        return tasks[offset : offset + limit]

    async def update_task(
        self, task_id: UUID, update_data: PlanTaskUpdate
    ) -> PlanTaskRead:
        """Update a task in memory."""
        if task_id not in self.tasks:
            raise FakeNotFoundError(f"Task {task_id} not found")

        existing = self.tasks[task_id]
        update_dict = update_data.model_dump(exclude_unset=True)

        updated = PlanTaskRead(
            id=existing.id,
            plan_id=existing.plan_id,
            sequence=update_dict.get("sequence", existing.sequence),
            description=update_dict.get("description", existing.description),
            validation=update_dict.get("validation", existing.validation),
            assignee_agent_definition_id=update_dict.get(
                "assignee_agent_definition_id", existing.assignee_agent_definition_id
            ),
            status=update_dict.get("status", existing.status),
            result=update_dict.get("result", existing.result),
            meta=update_dict.get("meta", existing.meta),
            created_at=existing.created_at,
            updated_at=_now(),
        )
        self.tasks[task_id] = updated
        return updated

    # -------------------------------------------------------------------------
    # Wait methods
    # -------------------------------------------------------------------------

    async def wait_for_plan_completion(
        self,
        plan_id: UUID,
        timeout: float | None = None,
        poll_interval: float = 2.0,
        on_progress: Any = None,
    ) -> PlanRead:
        """Wait for plan completion (returns immediately in fake)."""
        if plan_id not in self.plans:
            raise FakeNotFoundError(f"Plan {plan_id} not found")
        return self.plans[plan_id]

    async def wait_for_task_completion(
        self,
        task_id: UUID,
        timeout: float | None = None,
        poll_interval: float = 1.0,
        on_progress: Any = None,
    ) -> PlanTaskRead:
        """Wait for task completion (returns immediately in fake)."""
        if task_id not in self.tasks:
            raise FakeNotFoundError(f"Task {task_id} not found")
        return self.tasks[task_id]
