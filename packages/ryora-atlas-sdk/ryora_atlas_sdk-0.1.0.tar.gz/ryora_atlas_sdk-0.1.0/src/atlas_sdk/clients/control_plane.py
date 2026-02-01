"""Atlas Control Plane API client for admin/governance operations.

This client provides methods for managing:
- Agent Classes
- Agent Definitions
- Model Providers
- System Prompts
- Tools
- Deployments
- GRASP Analyses

Supports both low-level method-based API and high-level resource pattern:
    # Low-level (existing)
    deployment = await client.create_deployment(DeploymentCreate(...))

    # High-level (resource pattern)
    deployment = await client.deployments.create(...)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast
from uuid import UUID

from atlas_sdk._internal.params import build_list_params
from atlas_sdk.clients.base import BaseClient

if TYPE_CHECKING:
    from atlas_sdk.resources.deployments import DeploymentsResource
from atlas_sdk.models.agent_definition import (
    AgentDefinitionConfig,
    AgentDefinitionCreate,
    AgentDefinitionRead,
    AgentDefinitionUpdate,
)
from atlas_sdk.models.control_plane import (
    AgentClassCreate,
    AgentClassRead,
    AgentClassUpdate,
    GraspAnalysisCreate,
    GraspAnalysisRead,
    GraspAnalysisSummary,
    ModelProviderCreate,
    ModelProviderRead,
    ModelProviderUpdate,
    SystemPromptCreate,
    SystemPromptRead,
    SystemPromptUpdate,
    ToolCreate,
    ToolRead,
    ToolSyncRequest,
    ToolUpdate,
)
from atlas_sdk.models.deployment import (
    DeploymentCreate,
    DeploymentRead,
    DeploymentUpdate,
)
from atlas_sdk.models.enums import (
    AgentDefinitionStatus,
    GraspAnalysisStatus,
    SystemPromptStatus,
)


class ControlPlaneClient(BaseClient):
    """Async client for admin/governance operations on the Atlas Control Plane.

    This client provides methods for system administrators and CI/CD pipelines
    to manage Atlas configuration including agent classes, definitions, model
    providers, system prompts, tools, deployments, and GRASP analyses.

    Supports both low-level method-based API and high-level resource pattern:

    Low-level (method-based):
        deployment = await client.create_deployment(DeploymentCreate(...))
        deployment = await client.get_deployment(deployment_id)

    High-level (resource pattern):
        deployment = await client.deployments.create(
            agent_definition_id=uuid,
            name="my-deployment"
        )
        deployment = await client.deployments.get(deployment_id)

        # Resources support bound methods
        await deployment.refresh()
        deployment.data.description = "Updated"
        await deployment.save()
        await deployment.delete()

    Example:
        async with ControlPlaneClient(base_url="http://control-plane:8000") as client:
            # Create a model provider
            provider = await client.create_model_provider(ModelProviderCreate(
                name="openai-prod",
                api_base_url="https://api.openai.com/v1"
            ))

            # Create an agent class
            agent_class = await client.create_agent_class(AgentClassCreate(
                name="BugHunter",
                description="Security vulnerability detection"
            ))

            # Use resource pattern for deployments
            deployment = await client.deployments.create(
                agent_definition_id=definition_id,
                name="bug-hunter-prod",
                environment="production"
            )
    """

    _deployments_resource: DeploymentsResource | None = None

    @property
    def deployments(self) -> DeploymentsResource:
        """Access the deployments resource manager.

        Provides a high-level API for deployment operations:
            deployment = await client.deployments.create(...)
            deployment = await client.deployments.get(deployment_id)
            deployments = await client.deployments.list()

        Returns:
            The DeploymentsResource manager instance.
        """
        if self._deployments_resource is None:
            from atlas_sdk.resources.deployments import DeploymentsResource

            self._deployments_resource = DeploymentsResource(self)
        return self._deployments_resource

    # -------------------------------------------------------------------------
    # Agent Classes
    # -------------------------------------------------------------------------

    async def create_agent_class(
        self,
        agent_class: AgentClassCreate,
        *,
        idempotency_key: str | None = None,
    ) -> AgentClassRead:
        """Create a new agent class.

        Args:
            agent_class: The agent class creation data.
            idempotency_key: Optional idempotency key for safe retries. Use "auto"
                to generate a UUID-based key automatically.

        Returns:
            The created agent class.

        Raises:
            AtlasAPIError: If the request fails.
        """
        return await self._post_one(
            "/api/v1/agent-classes",
            agent_class,
            AgentClassRead,
            idempotency_key=idempotency_key,
        )

    async def get_agent_class(self, agent_class_id: UUID) -> AgentClassRead:
        """Get an agent class by ID.

        Args:
            agent_class_id: The UUID of the agent class.

        Returns:
            The agent class details.

        Raises:
            AtlasAPIError: If the request fails.
        """
        return await self._get_one(
            f"/api/v1/agent-classes/{agent_class_id}", AgentClassRead
        )

    async def list_agent_classes(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AgentClassRead]:
        """List all agent classes.

        Args:
            limit: Maximum number of results to return.
            offset: Number of results to skip.

        Returns:
            List of agent classes.

        Raises:
            AtlasAPIError: If the request fails.
        """
        params = build_list_params(limit, offset)
        return await self._get_many(
            "/api/v1/agent-classes", AgentClassRead, params=params
        )

    async def update_agent_class(
        self, agent_class_id: UUID, update_data: AgentClassUpdate
    ) -> AgentClassRead:
        """Update an agent class.

        Args:
            agent_class_id: The UUID of the agent class to update.
            update_data: The fields to update.

        Returns:
            The updated agent class.

        Raises:
            AtlasAPIError: If the request fails.
        """
        return await self._patch_one(
            f"/api/v1/agent-classes/{agent_class_id}", update_data, AgentClassRead
        )

    async def delete_agent_class(self, agent_class_id: UUID) -> None:
        """Delete an agent class.

        Args:
            agent_class_id: The UUID of the agent class to delete.

        Raises:
            AtlasAPIError: If the request fails.
        """
        await self._delete(f"/api/v1/agent-classes/{agent_class_id}")

    # -------------------------------------------------------------------------
    # Agent Definitions
    # -------------------------------------------------------------------------

    async def create_agent_definition(
        self,
        agent_definition: AgentDefinitionCreate,
        *,
        idempotency_key: str | None = None,
    ) -> AgentDefinitionRead:
        """Create a new agent definition.

        Args:
            agent_definition: The agent definition creation data.
            idempotency_key: Optional idempotency key for safe retries. Use "auto"
                to generate a UUID-based key automatically.

        Returns:
            The created agent definition.

        Raises:
            AtlasAPIError: If the request fails.
        """
        return await self._post_one(
            "/api/v1/agent-definitions",
            agent_definition,
            AgentDefinitionRead,
            idempotency_key=idempotency_key,
        )

    async def get_agent_definition(self, definition_id: UUID) -> AgentDefinitionRead:
        """Get an agent definition by ID.

        Args:
            definition_id: The UUID of the agent definition.

        Returns:
            The agent definition details.

        Raises:
            AtlasAPIError: If the request fails.
        """
        return await self._get_one(
            f"/api/v1/agent-definitions/{definition_id}", AgentDefinitionRead
        )

    async def get_agent_definition_config(
        self, definition_id: UUID
    ) -> AgentDefinitionConfig:
        """Get the runtime configuration for an agent definition.

        Args:
            definition_id: The UUID of the agent definition.

        Returns:
            The agent definition runtime configuration.

        Raises:
            AtlasAPIError: If the request fails.
        """
        return await self._get_one(
            f"/api/v1/agent-definitions/{definition_id}/config", AgentDefinitionConfig
        )

    async def list_agent_definitions(
        self,
        status: AgentDefinitionStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AgentDefinitionRead]:
        """List all agent definitions, optionally filtered by status.

        Args:
            status: Optional status filter.
            limit: Maximum number of results to return.
            offset: Number of results to skip.

        Returns:
            List of agent definitions.

        Raises:
            AtlasAPIError: If the request fails.
        """
        params = build_list_params(limit, offset, status=status)
        return await self._get_many(
            "/api/v1/agent-definitions", AgentDefinitionRead, params=params
        )

    async def update_agent_definition(
        self, definition_id: UUID, update_data: AgentDefinitionUpdate
    ) -> AgentDefinitionRead:
        """Update an agent definition.

        Args:
            definition_id: The UUID of the agent definition to update.
            update_data: The fields to update.

        Returns:
            The updated agent definition.

        Raises:
            AtlasAPIError: If the request fails.
        """
        return await self._patch_one(
            f"/api/v1/agent-definitions/{definition_id}",
            update_data,
            AgentDefinitionRead,
        )

    async def delete_agent_definition(self, definition_id: UUID) -> None:
        """Delete an agent definition.

        Args:
            definition_id: The UUID of the agent definition to delete.

        Raises:
            AtlasAPIError: If the request fails.
        """
        await self._delete(f"/api/v1/agent-definitions/{definition_id}")

    async def add_tools_to_definition(
        self, definition_id: UUID, tool_ids: list[UUID]
    ) -> AgentDefinitionRead:
        """Add tools to an agent definition.

        Args:
            definition_id: The UUID of the agent definition.
            tool_ids: List of tool UUIDs to add.

        Returns:
            The updated agent definition.

        Raises:
            AtlasAPIError: If the request fails.
        """
        resp = await self._request(
            "POST",
            f"/api/v1/agent-definitions/{definition_id}/tools",
            json={"tool_ids": [str(tid) for tid in tool_ids]},
        )
        self._raise_for_status(resp)
        return AgentDefinitionRead.model_validate(resp.json())

    # -------------------------------------------------------------------------
    # Model Providers
    # -------------------------------------------------------------------------

    async def create_model_provider(
        self,
        model_provider: ModelProviderCreate,
        *,
        idempotency_key: str | None = None,
    ) -> ModelProviderRead:
        """Create a new model provider.

        Args:
            model_provider: The model provider creation data.
            idempotency_key: Optional idempotency key for safe retries. Use "auto"
                to generate a UUID-based key automatically.

        Returns:
            The created model provider.

        Raises:
            AtlasAPIError: If the request fails.
        """
        return await self._post_one(
            "/api/v1/model-providers",
            model_provider,
            ModelProviderRead,
            idempotency_key=idempotency_key,
        )

    async def get_model_provider(self, provider_id: UUID) -> ModelProviderRead:
        """Get a model provider by ID.

        Args:
            provider_id: The UUID of the model provider.

        Returns:
            The model provider details.

        Raises:
            AtlasAPIError: If the request fails.
        """
        return await self._get_one(
            f"/api/v1/model-providers/{provider_id}", ModelProviderRead
        )

    async def list_model_providers(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ModelProviderRead]:
        """List all model providers.

        Args:
            limit: Maximum number of results to return.
            offset: Number of results to skip.

        Returns:
            List of model providers.

        Raises:
            AtlasAPIError: If the request fails.
        """
        params = build_list_params(limit, offset)
        return await self._get_many(
            "/api/v1/model-providers", ModelProviderRead, params=params
        )

    async def update_model_provider(
        self, provider_id: UUID, update_data: ModelProviderUpdate
    ) -> ModelProviderRead:
        """Update a model provider.

        Args:
            provider_id: The UUID of the model provider to update.
            update_data: The fields to update.

        Returns:
            The updated model provider.

        Raises:
            AtlasAPIError: If the request fails.
        """
        return await self._patch_one(
            f"/api/v1/model-providers/{provider_id}", update_data, ModelProviderRead
        )

    async def delete_model_provider(self, provider_id: UUID) -> None:
        """Delete a model provider.

        Args:
            provider_id: The UUID of the model provider to delete.

        Raises:
            AtlasAPIError: If the request fails.
        """
        await self._delete(f"/api/v1/model-providers/{provider_id}")

    async def verify_model_provider(self, provider_id: UUID) -> dict[str, Any]:
        """Verify a model provider's connectivity and credentials.

        Args:
            provider_id: The UUID of the model provider to verify.

        Returns:
            Verification result with status and details.

        Raises:
            AtlasAPIError: If the request fails.
        """
        resp = await self._request(
            "POST", f"/api/v1/model-providers/{provider_id}/verify"
        )
        self._raise_for_status(resp)
        return cast(dict[str, Any], resp.json())

    async def list_provider_models(self, provider_id: UUID) -> list[dict[str, Any]]:
        """List models available from a model provider.

        Args:
            provider_id: The UUID of the model provider.

        Returns:
            List of available models with their details.

        Raises:
            AtlasAPIError: If the request fails.
        """
        resp = await self._request(
            "GET", f"/api/v1/model-providers/{provider_id}/models"
        )
        self._raise_for_status(resp)
        return cast(list[dict[str, Any]], resp.json())

    # -------------------------------------------------------------------------
    # System Prompts
    # -------------------------------------------------------------------------

    async def create_system_prompt(
        self,
        system_prompt: SystemPromptCreate,
        *,
        idempotency_key: str | None = None,
    ) -> SystemPromptRead:
        """Create a new system prompt.

        Args:
            system_prompt: The system prompt creation data.
            idempotency_key: Optional idempotency key for safe retries. Use "auto"
                to generate a UUID-based key automatically.

        Returns:
            The created system prompt.

        Raises:
            AtlasAPIError: If the request fails.
        """
        return await self._post_one(
            "/api/v1/system-prompts",
            system_prompt,
            SystemPromptRead,
            idempotency_key=idempotency_key,
        )

    async def get_system_prompt(self, prompt_id: UUID) -> SystemPromptRead:
        """Get a system prompt by ID.

        Args:
            prompt_id: The UUID of the system prompt.

        Returns:
            The system prompt details.

        Raises:
            AtlasAPIError: If the request fails.
        """
        return await self._get_one(
            f"/api/v1/system-prompts/{prompt_id}", SystemPromptRead
        )

    async def list_system_prompts(
        self,
        agent_class_id: UUID | None = None,
        status: SystemPromptStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[SystemPromptRead]:
        """List system prompts with optional filters.

        Args:
            agent_class_id: Optional agent class filter.
            status: Optional status filter.
            limit: Maximum number of results to return.
            offset: Number of results to skip.

        Returns:
            List of system prompts.

        Raises:
            AtlasAPIError: If the request fails.
        """
        params = build_list_params(
            limit, offset, agent_class_id=agent_class_id, status=status
        )
        return await self._get_many(
            "/api/v1/system-prompts", SystemPromptRead, params=params
        )

    async def update_system_prompt(
        self, prompt_id: UUID, update_data: SystemPromptUpdate
    ) -> SystemPromptRead:
        """Update a system prompt.

        Args:
            prompt_id: The UUID of the system prompt to update.
            update_data: The fields to update.

        Returns:
            The updated system prompt.

        Raises:
            AtlasAPIError: If the request fails.
        """
        return await self._patch_one(
            f"/api/v1/system-prompts/{prompt_id}", update_data, SystemPromptRead
        )

    async def delete_system_prompt(self, prompt_id: UUID) -> None:
        """Delete a system prompt.

        Args:
            prompt_id: The UUID of the system prompt to delete.

        Raises:
            AtlasAPIError: If the request fails.
        """
        await self._delete(f"/api/v1/system-prompts/{prompt_id}")

    # -------------------------------------------------------------------------
    # Tools
    # -------------------------------------------------------------------------

    async def create_tool(
        self,
        tool: ToolCreate,
        *,
        idempotency_key: str | None = None,
    ) -> ToolRead:
        """Create a new tool.

        Args:
            tool: The tool creation data.
            idempotency_key: Optional idempotency key for safe retries. Use "auto"
                to generate a UUID-based key automatically.

        Returns:
            The created tool.

        Raises:
            AtlasAPIError: If the request fails.
        """
        return await self._post_one(
            "/api/v1/tools", tool, ToolRead, idempotency_key=idempotency_key
        )

    async def update_tool(self, tool_id: UUID, update_data: ToolUpdate) -> ToolRead:
        """Update a tool.

        Args:
            tool_id: The UUID of the tool to update.
            update_data: The fields to update.

        Returns:
            The updated tool.

        Raises:
            AtlasAPIError: If the request fails.
        """
        return await self._patch_one(f"/api/v1/tools/{tool_id}", update_data, ToolRead)

    async def list_tools(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ToolRead]:
        """List all tools.

        Args:
            limit: Maximum number of results to return.
            offset: Number of results to skip.

        Returns:
            List of tools.

        Raises:
            AtlasAPIError: If the request fails.
        """
        params = build_list_params(limit, offset)
        return await self._get_many("/api/v1/tools/", ToolRead, params=params)

    async def get_tool(self, tool_id: UUID) -> ToolRead:
        """Get a tool by ID.

        Args:
            tool_id: The UUID of the tool.

        Returns:
            The tool details.

        Raises:
            AtlasAPIError: If the request fails.
        """
        return await self._get_one(f"/api/v1/tools/{tool_id}", ToolRead)

    async def delete_tool(self, tool_id: UUID) -> None:
        """Delete a tool.

        Args:
            tool_id: The UUID of the tool to delete.

        Raises:
            AtlasAPIError: If the request fails.
        """
        await self._delete(f"/api/v1/tools/{tool_id}")

    async def sync_tools(self, tools: ToolSyncRequest) -> list[ToolRead]:
        """Sync tools from a tool registry.

        Creates or updates tools based on the provided definitions.

        Args:
            tools: The tools to sync.

        Returns:
            List of synced tools.

        Raises:
            AtlasAPIError: If the request fails.
        """
        resp = await self._request(
            "POST",
            "/api/v1/tools/sync",
            json=tools.model_dump(exclude_unset=True, mode="json"),
        )
        self._raise_for_status(resp)
        return [ToolRead.model_validate(t) for t in resp.json()]

    async def discover_tools(self, source: str) -> list[ToolRead]:
        """Discover tools from a source.

        Args:
            source: The source to discover tools from (e.g., module path).

        Returns:
            List of discovered tools.

        Raises:
            AtlasAPIError: If the request fails.
        """
        resp = await self._request(
            "POST",
            "/api/v1/tools/discover",
            json={"source": source},
        )
        self._raise_for_status(resp)
        return [ToolRead.model_validate(t) for t in resp.json()]

    # -------------------------------------------------------------------------
    # Deployments
    # -------------------------------------------------------------------------

    async def create_deployment(
        self,
        deployment: DeploymentCreate,
        *,
        idempotency_key: str | None = None,
    ) -> DeploymentRead:
        """Create a new deployment.

        Args:
            deployment: The deployment creation data.
            idempotency_key: Optional idempotency key for safe retries. Use "auto"
                to generate a UUID-based key automatically.

        Returns:
            The created deployment.

        Raises:
            AtlasAPIError: If the request fails.
        """
        return await self._post_one(
            "/api/v1/deployments",
            deployment,
            DeploymentRead,
            idempotency_key=idempotency_key,
        )

    async def get_deployment(self, deployment_id: UUID) -> DeploymentRead:
        """Get a deployment by ID.

        Args:
            deployment_id: The UUID of the deployment.

        Returns:
            The deployment details.

        Raises:
            AtlasAPIError: If the request fails.
        """
        return await self._get_one(
            f"/api/v1/deployments/{deployment_id}", DeploymentRead
        )

    async def update_deployment(
        self, deployment_id: UUID, update_data: DeploymentUpdate
    ) -> DeploymentRead:
        """Update a deployment.

        Args:
            deployment_id: The UUID of the deployment to update.
            update_data: The fields to update.

        Returns:
            The updated deployment.

        Raises:
            AtlasAPIError: If the request fails.
        """
        return await self._patch_one(
            f"/api/v1/deployments/{deployment_id}", update_data, DeploymentRead
        )

    async def list_deployments(
        self,
        environment: str | None = None,
        active_only: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[DeploymentRead]:
        """List all deployments with optional filters.

        Args:
            environment: Optional environment filter.
            active_only: If True, only return active deployments.
            limit: Maximum number of results to return.
            offset: Number of results to skip.

        Returns:
            List of deployments.

        Raises:
            AtlasAPIError: If the request fails.
        """
        params = build_list_params(
            limit, offset, active_only=active_only, environment=environment
        )
        return await self._get_many(
            "/api/v1/deployments", DeploymentRead, params=params
        )

    async def delete_deployment(self, deployment_id: UUID) -> None:
        """Delete a deployment.

        Args:
            deployment_id: The UUID of the deployment to delete.

        Raises:
            AtlasAPIError: If the request fails.
        """
        await self._delete(f"/api/v1/deployments/{deployment_id}")

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
        """Create a new GRASP analysis for a deployment.

        Args:
            deployment_id: The UUID of the deployment.
            analysis: The GRASP analysis creation data.
            idempotency_key: Optional idempotency key for safe retries. Use "auto"
                to generate a UUID-based key automatically.

        Returns:
            The created GRASP analysis.

        Raises:
            AtlasAPIError: If the request fails.
        """
        return await self._post_one(
            f"/api/v1/deployments/{deployment_id}/grasp-analyses",
            analysis,
            GraspAnalysisRead,
            idempotency_key=idempotency_key,
        )

    async def get_grasp_analysis(self, analysis_id: UUID) -> GraspAnalysisRead:
        """Get a GRASP analysis by ID.

        Args:
            analysis_id: The UUID of the GRASP analysis.

        Returns:
            The GRASP analysis details.

        Raises:
            AtlasAPIError: If the request fails.
        """
        return await self._get_one(
            f"/api/v1/grasp-analyses/{analysis_id}", GraspAnalysisRead
        )

    async def list_grasp_analyses(
        self, deployment_id: UUID, status: GraspAnalysisStatus | None = None
    ) -> list[GraspAnalysisSummary]:
        """List GRASP analyses for a deployment.

        Args:
            deployment_id: The UUID of the deployment.
            status: Optional status filter.

        Returns:
            List of GRASP analysis summaries.

        Raises:
            AtlasAPIError: If the request fails.
        """
        params: dict[str, Any] = {}
        if status:
            params["status"] = status.value
        return await self._get_many(
            f"/api/v1/deployments/{deployment_id}/grasp-analyses",
            GraspAnalysisSummary,
            params=params,
        )

    async def query_grasp_analyses(
        self,
        deployment_id: UUID | None = None,
        status: GraspAnalysisStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[GraspAnalysisSummary]:
        """Query GRASP analyses across all deployments.

        Args:
            deployment_id: Optional deployment filter.
            status: Optional status filter.
            limit: Maximum number of results to return.
            offset: Number of results to skip.

        Returns:
            List of GRASP analysis summaries.

        Raises:
            AtlasAPIError: If the request fails.
        """
        params = build_list_params(
            limit, offset, deployment_id=deployment_id, status=status
        )
        return await self._get_many(
            "/api/v1/grasp-analyses", GraspAnalysisSummary, params=params
        )

    # -------------------------------------------------------------------------
    # Health
    # -------------------------------------------------------------------------

    async def health(self) -> dict[str, Any]:
        """Check the health of the Control Plane service.

        Returns:
            Health check response with status and details.

        Raises:
            AtlasAPIError: If the request fails.
        """
        resp = await self._request("GET", "/api/v1/health")
        self._raise_for_status(resp)
        return cast(dict[str, Any], resp.json())

    async def metrics(self) -> dict[str, Any]:
        """Get metrics from the Control Plane service.

        Returns:
            Metrics data.

        Raises:
            AtlasAPIError: If the request fails.
        """
        resp = await self._request("GET", "/api/v1/metrics")
        self._raise_for_status(resp)
        return cast(dict[str, Any], resp.json())

    async def logs(
        self,
        deployment_id: UUID | None = None,
        level: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get logs from the Control Plane service.

        Args:
            deployment_id: Optional deployment filter.
            level: Optional log level filter.
            limit: Maximum number of log entries to return.

        Returns:
            List of log entries.

        Raises:
            AtlasAPIError: If the request fails.
        """
        params: dict[str, Any] = {"limit": limit}
        if deployment_id:
            params["deployment_id"] = str(deployment_id)
        if level:
            params["level"] = level
        resp = await self._request("GET", "/api/v1/logs", params=params)
        self._raise_for_status(resp)
        return cast(list[dict[str, Any]], resp.json())
