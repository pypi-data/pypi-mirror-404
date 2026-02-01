"""Atlas SDK - Python client library for the Atlas platform.

This SDK provides three purpose-specific clients:
- ControlPlaneClient: Admin/governance operations (agent classes, model providers, etc.)
- DispatchClient: Agent lifecycle management (spawn, stop, A2A communication)
- WorkflowClient: Workflow orchestration (plans, tasks, read-only access to definitions)
"""

try:
    from atlas_sdk._version import __version__
except ImportError:
    __version__ = "0.0.0.dev0"

# Clients
from atlas_sdk.clients import (
    BaseClient,
    ControlPlaneClient,
    DispatchClient,
    WorkflowClient,
)

# Exceptions
from atlas_sdk.exceptions import (
    # Base
    AtlasError,
    # API errors
    AtlasAPIError,
    AtlasAuthenticationError,
    AtlasAuthorizationError,
    AtlasConflictError,
    AtlasNotFoundError,
    AtlasRateLimitError,
    AtlasServerError,
    AtlasValidationError,
    # Domain errors
    AtlasDomainError,
    AgentExecutionError,
    InvalidBlueprintError,
    StateTransitionError,
    # Other errors
    AtlasConnectionError,
    AtlasTimeoutError,
    AtlasInputValidationError,
    # Supporting types
    RequestContext,
    ValidationErrorDetail,
    InputValidationErrorDetail,
    # Note: AtlasHTTPStatusError is provided via __getattr__ with deprecation warning
)

# Validation utilities
from atlas_sdk.validation import (
    validate_model,
    validate_instance,
    validate_uuid,
    validate_enum,
)

# Pagination
from atlas_sdk.pagination import paginate, Paginator, PaginationState

# Deprecation utilities
from atlas_sdk.deprecation import (
    deprecated,
    deprecated_class,
    deprecated_parameter,
    warn_deprecated,
)

# Instrumentation
from atlas_sdk.instrumentation import (
    has_opentelemetry,
    InstrumentationConfig,
    MetricsHandler,
    NoOpMetricsHandler,
    RequestMetrics,
)

# Resources - high-level API
from atlas_sdk.resources import (
    # Base
    HTTPClientProtocol,
    Resource,
    # Deployments
    Deployment,
    DeploymentsResource,
    # Plans
    Plan,
    PlansResource,
    # Tasks
    Task,
    TasksResource,
    # Agent Instances
    AgentInstance,
    AgentInstancesResource,
)

# Models - re-export all models for convenience
from atlas_sdk.models import (
    # Enums
    AgentDefinitionStatus,
    AgentInstanceStatus,
    DeploymentStatus,
    ExecutionMode,
    GraspAnalysisStatus,
    PlanStatus,
    PlanTaskStatus,
    SystemPromptStatus,
    SystemPromptStorageType,
    # Agent Definition
    AgentDefinitionConfig,
    AgentDefinitionCreate,
    AgentDefinitionRead,
    AgentDefinitionUpdate,
    # Agent Instance
    AgentInstanceCreate,
    AgentInstanceRead,
    AgentInstanceUpdate,
    # Deployment
    DeploymentCreate,
    DeploymentRead,
    DeploymentUpdate,
    # Plan
    PlanCreate,
    PlanCreateResponse,
    PlanRead,
    PlanReadWithTasks,
    PlanUpdate,
    # Task
    PlanTaskCreate,
    PlanTaskRead,
    PlanTaskReadEnriched,
    PlanTaskUpdate,
    TasksAppend,
    TasksAppendResponse,
    # Control Plane - Agent Class
    AgentClassCreate,
    AgentClassRead,
    AgentClassUpdate,
    # Control Plane - Model Provider
    ModelProviderCreate,
    ModelProviderRead,
    ModelProviderUpdate,
    # Control Plane - System Prompt
    SystemPromptCreate,
    SystemPromptRead,
    SystemPromptUpdate,
    # Control Plane - Tool
    ToolCreate,
    ToolRead,
    ToolSyncRequest,
    ToolUpdate,
    # Control Plane - GRASP
    GraspAnalysisCreate,
    GraspAnalysisRead,
    GraspAnalysisSummary,
    # Control Plane - Blueprint
    BlueprintCreate,
    BlueprintRead,
    BlueprintUpdate,
    # Dispatch - Spawn
    AgentStatusResponse,
    SpawnRequest,
    SpawnResponse,
    StopResponse,
    WaitResponse,
    # Dispatch - A2A
    A2ACallRequest,
    A2ACallResponse,
    A2ADirectoryResponse,
    AgentDirectoryEntry,
)


# Module-level __getattr__ to provide deprecated aliases with warnings
def __getattr__(name: str) -> type:
    """Provide deprecated module attributes with warnings.

    This function is called when an attribute is not found in the module's
    namespace. It's used to provide backward-compatible aliases that emit
    deprecation warnings when accessed.
    """
    if name == "AtlasHTTPStatusError":
        import warnings

        warnings.warn(
            "'AtlasHTTPStatusError' is deprecated since version 0.2.0 "
            "and will be removed in version 0.4.0. Use 'AtlasAPIError' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return AtlasAPIError
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    # Version
    "__version__",
    # Clients
    "BaseClient",
    "ControlPlaneClient",
    "DispatchClient",
    "WorkflowClient",
    # Exceptions - Base
    "AtlasError",
    # Exceptions - API errors
    "AtlasAPIError",
    "AtlasAuthenticationError",
    "AtlasAuthorizationError",
    "AtlasConflictError",
    "AtlasNotFoundError",
    "AtlasRateLimitError",
    "AtlasServerError",
    "AtlasValidationError",
    # Exceptions - Domain errors
    "AtlasDomainError",
    "AgentExecutionError",
    "InvalidBlueprintError",
    "StateTransitionError",
    # Exceptions - Other
    "AtlasConnectionError",
    "AtlasTimeoutError",
    "AtlasInputValidationError",
    # Exceptions - Supporting types
    "RequestContext",
    "ValidationErrorDetail",
    "InputValidationErrorDetail",
    # Exceptions - Legacy aliases
    "AtlasHTTPStatusError",
    # Validation utilities
    "validate_model",
    "validate_instance",
    "validate_uuid",
    "validate_enum",
    # Pagination
    "paginate",
    "Paginator",
    "PaginationState",
    # Deprecation utilities
    "deprecated",
    "deprecated_class",
    "deprecated_parameter",
    "warn_deprecated",
    # Instrumentation
    "has_opentelemetry",
    "InstrumentationConfig",
    "MetricsHandler",
    "NoOpMetricsHandler",
    "RequestMetrics",
    # Resources - Base
    "HTTPClientProtocol",
    "Resource",
    # Resources - Deployments
    "Deployment",
    "DeploymentsResource",
    # Resources - Plans
    "Plan",
    "PlansResource",
    # Resources - Tasks
    "Task",
    "TasksResource",
    # Resources - Agent Instances
    "AgentInstance",
    "AgentInstancesResource",
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
    # Agent Definition
    "AgentDefinitionConfig",
    "AgentDefinitionCreate",
    "AgentDefinitionRead",
    "AgentDefinitionUpdate",
    # Agent Instance
    "AgentInstanceCreate",
    "AgentInstanceRead",
    "AgentInstanceUpdate",
    # Deployment
    "DeploymentCreate",
    "DeploymentRead",
    "DeploymentUpdate",
    # Plan
    "PlanCreate",
    "PlanCreateResponse",
    "PlanRead",
    "PlanReadWithTasks",
    "PlanUpdate",
    # Task
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
    "ToolSyncRequest",
    "ToolUpdate",
    # Control Plane - GRASP
    "GraspAnalysisCreate",
    "GraspAnalysisRead",
    "GraspAnalysisSummary",
    # Control Plane - Blueprint
    "BlueprintCreate",
    "BlueprintRead",
    "BlueprintUpdate",
    # Dispatch - Spawn
    "AgentStatusResponse",
    "SpawnRequest",
    "SpawnResponse",
    "StopResponse",
    "WaitResponse",
    # Dispatch - A2A
    "A2ACallRequest",
    "A2ACallResponse",
    "A2ADirectoryResponse",
    "AgentDirectoryEntry",
]
