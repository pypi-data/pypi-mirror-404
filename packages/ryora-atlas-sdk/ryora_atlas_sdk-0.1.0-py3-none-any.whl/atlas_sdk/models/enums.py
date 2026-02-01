"""Enums for Atlas SDK models.

This module defines all enumeration types used throughout the Atlas SDK.
Each enum represents a specific state or configuration option for Atlas resources.
"""

from enum import Enum


class AgentDefinitionStatus(str, Enum):
    """Status of an agent definition in its lifecycle.

    Agent definitions progress through states as they move from development
    to production use and eventual retirement.

    Values:
        DRAFT: Definition is under development and can be modified freely.
            Not yet ready for deployment. Use this state while iterating
            on the agent's configuration.
        PUBLISHED: Definition is finalized and immutable. Ready for deployment
            to production environments. Changes require creating a new definition.
        DEPRECATED: Definition is retired and should no longer be used for new
            deployments. Existing deployments may continue running.
    """

    DRAFT = "draft"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"


class ExecutionMode(str, Enum):
    """Defines how agent instances are managed at runtime.

    The execution mode determines the lifecycle and resource management
    strategy for agent instances.

    Values:
        STATEFUL: Agent instance persists across multiple interactions.
            Maintains conversation history, learned context, and session state.
            Use for multi-turn conversations or agents that need memory.
        EPHEMERAL: Agent instance is created fresh for each request and
            destroyed afterward. No state is preserved between calls.
            Use for stateless, single-shot operations.
    """

    STATEFUL = "stateful"
    EPHEMERAL = "ephemeral"


class DeploymentStatus(str, Enum):
    """Status of a deployment.

    Deployments progress through states as the agent is provisioned
    and executes its tasks.

    Values:
        SPAWNING: Deployment is being initialized. Resources are being
            allocated and the agent instance is starting up.
        ACTIVE: Deployment is running and ready to accept work. The agent
            is fully operational and processing tasks.
        COMPLETED: Deployment finished successfully. All tasks completed
            and the deployment has been cleanly shut down.
        FAILED: Deployment encountered an error and could not continue.
            Check logs for failure details.
    """

    SPAWNING = "spawning"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentInstanceStatus(str, Enum):
    """Status of an agent instance.

    Tracks the lifecycle of an individual agent instance within a deployment.

    Values:
        SPAWNING: Instance is starting up. The agent process is initializing
            and loading its configuration.
        ACTIVE: Instance is running and processing work. Ready to receive
            and execute tasks.
        COMPLETED: Instance finished all assigned work successfully and
            has been shut down.
        FAILED: Instance encountered an unrecoverable error. Check error
            details for the cause.
        CANCELLED: Instance was manually terminated before completing.
            Work may be incomplete.
    """

    SPAWNING = "spawning"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PlanStatus(str, Enum):
    """Status of a plan.

    Plans progress through states as they are created, executed, and completed.

    Values:
        DRAFT: Plan has been created but not yet started. Tasks can still
            be added or modified.
        ACTIVE: Plan is currently being executed. Tasks are being processed
            in sequence.
        COMPLETED: All tasks in the plan finished successfully.
        FAILED: One or more tasks in the plan failed. Check task statuses
            for details on which tasks failed.
        CANCELLED: Plan was manually cancelled before completion. Remaining
            tasks were not executed.
    """

    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class PlanTaskStatus(str, Enum):
    """Status of a plan task.

    Individual tasks within a plan progress through these states.

    Values:
        PENDING: Task is waiting to be executed. Queued but not yet started.
        IN_PROGRESS: Task is currently being executed by the agent.
        COMPLETED: Task finished successfully with expected results.
        FAILED: Task encountered an error and could not complete.
            Check the task's error field for details.
        SKIPPED: Task was not executed, typically because a preceding task
            failed or the plan was cancelled.
    """

    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class SystemPromptStatus(str, Enum):
    """Status of a system prompt.

    System prompts follow the same lifecycle pattern as agent definitions.

    Values:
        DRAFT: Prompt is under development and can be modified. Use while
            iterating on prompt engineering.
        PUBLISHED: Prompt is finalized and immutable. Ready to be used
            in agent definitions.
        DEPRECATED: Prompt is retired and should not be used in new
            definitions. Existing references may continue working.
    """

    DRAFT = "draft"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"


class SystemPromptStorageType(str, Enum):
    """Storage type for system prompt content.

    Determines where the prompt text is stored.

    Values:
        INLINE: Prompt content is stored directly in the database.
            Best for shorter prompts (under ~64KB).
        S3: Prompt content is stored in S3 with a reference in the database.
            Use for very large prompts or when versioning is needed.
    """

    INLINE = "inline"
    S3 = "s3"


class GraspAnalysisStatus(str, Enum):
    """Status of a GRASP analysis.

    Tracks the progress of GRASP (Goal, Role, Audience, Situation, Product)
    analysis operations.

    Values:
        PENDING: Analysis has been requested but not yet started.
        IN_PROGRESS: Analysis is currently running.
        COMPLETED: Analysis finished successfully. Results are available.
        FAILED: Analysis encountered an error. Check error details.
    """

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
