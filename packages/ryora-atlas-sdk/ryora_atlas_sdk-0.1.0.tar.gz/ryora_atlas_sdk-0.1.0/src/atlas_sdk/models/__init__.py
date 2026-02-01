"""Atlas SDK models for API communication.

This module provides Pydantic models for all Atlas SDK API operations.

Model Categories:
    - **InputModel**: Base class for request models (Create/Update) with validation.
    - **ResponseModel**: Base class for response models (Read) with ORM support.

Type Coercion:
    Input models (Create/Update) use standard Pydantic coercion for backward
    compatibility. For strict type enforcement, use ``validate_model()`` from
    ``atlas_sdk.validation``.
"""

from atlas_sdk.models.base import InputModel, ResponseModel, StrictModel
from atlas_sdk.models.agent_definition import (
    AgentDefinitionConfig,
    AgentDefinitionCreate,
    AgentDefinitionRead,
    AgentDefinitionUpdate,
)
from atlas_sdk.models.agent_instance import (
    AgentInstanceCreate,
    AgentInstanceRead,
    AgentInstanceUpdate,
)
from atlas_sdk.models.deployment import (
    DeploymentCreate,
    DeploymentRead,
    DeploymentUpdate,
)
from atlas_sdk.models.enums import (
    AgentDefinitionStatus,
    AgentInstanceStatus,
    DeploymentStatus,
    ExecutionMode,
    GraspAnalysisStatus,
    PlanStatus,
    PlanTaskStatus,
    SystemPromptStatus,
    SystemPromptStorageType,
)
from atlas_sdk.models.plan import (
    PlanCreate,
    PlanCreateResponse,
    PlanRead,
    PlanReadWithTasks,
    PlanTaskCreate,
    PlanTaskRead,
    PlanTaskReadEnriched,
    PlanTaskUpdate,
    PlanUpdate,
    TasksAppend,
    TasksAppendResponse,
)

# Control Plane models (admin/governance)
from atlas_sdk.models.control_plane import (
    AgentClassCreate,
    AgentClassRead,
    AgentClassUpdate,
    BlueprintCreate,
    BlueprintRead,
    BlueprintUpdate,
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

# Dispatch models (agent lifecycle)
from atlas_sdk.models.dispatch import (
    A2ACallRequest,
    A2ACallResponse,
    A2ADirectoryResponse,
    AgentDirectoryEntry,
    AgentStatusResponse,
    SpawnRequest,
    SpawnResponse,
    StopResponse,
    WaitResponse,
)

__all__ = [
    # Base classes
    "InputModel",
    "ResponseModel",
    "StrictModel",
    # Enums
    "AgentDefinitionStatus",
    "AgentInstanceStatus",
    "DeploymentStatus",
    "ExecutionMode",
    "GraspAnalysisStatus",
    "PlanStatus",
    "PlanTaskStatus",
    "SystemPromptStatus",
    "SystemPromptStorageType",
    # Agent Definition (shared)
    "AgentDefinitionCreate",
    "AgentDefinitionRead",
    "AgentDefinitionUpdate",
    "AgentDefinitionConfig",
    # Agent Instance (shared)
    "AgentInstanceCreate",
    "AgentInstanceRead",
    "AgentInstanceUpdate",
    # Deployment (shared)
    "DeploymentCreate",
    "DeploymentRead",
    "DeploymentUpdate",
    # Plan (shared)
    "PlanCreate",
    "PlanCreateResponse",
    "PlanRead",
    "PlanReadWithTasks",
    "PlanUpdate",
    # Task (shared)
    "PlanTaskCreate",
    "PlanTaskRead",
    "PlanTaskReadEnriched",
    "PlanTaskUpdate",
    "TasksAppend",
    "TasksAppendResponse",
    # Control Plane - Agent Class
    "AgentClassCreate",
    "AgentClassRead",
    "AgentClassUpdate",
    # Control Plane - Model Provider
    "ModelProviderCreate",
    "ModelProviderRead",
    "ModelProviderUpdate",
    # Control Plane - System Prompt
    "SystemPromptCreate",
    "SystemPromptRead",
    "SystemPromptUpdate",
    # Control Plane - Tool
    "ToolCreate",
    "ToolRead",
    "ToolUpdate",
    "ToolSyncRequest",
    # Control Plane - GRASP
    "GraspAnalysisCreate",
    "GraspAnalysisRead",
    "GraspAnalysisSummary",
    # Control Plane - Blueprint
    "BlueprintCreate",
    "BlueprintRead",
    "BlueprintUpdate",
    # Dispatch - Spawn
    "SpawnRequest",
    "SpawnResponse",
    "AgentStatusResponse",
    "StopResponse",
    "WaitResponse",
    # Dispatch - A2A
    "A2ACallRequest",
    "A2ACallResponse",
    "AgentDirectoryEntry",
    "A2ADirectoryResponse",
]
