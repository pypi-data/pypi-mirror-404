"""Factory functions for creating test data.

This module provides factory functions that generate valid Pydantic model
instances with sensible defaults. These make it easy to create test data
without having to specify every required field.

All factory functions accept keyword arguments to override any default values.

Example:
    ```python
    from atlas_sdk.testing import factory_deployment, factory_agent_class

    # Create with all defaults
    deployment = factory_deployment()

    # Override specific fields
    deployment = factory_deployment(
        name="my-deployment",
        environment="staging",
    )

    # Use in tests
    assert deployment.status == DeploymentStatus.ACTIVE
    ```
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from atlas_sdk.models import (
    # Enums
    AgentDefinitionStatus,
    AgentInstanceStatus,
    DeploymentStatus,
    ExecutionMode,
    PlanStatus,
    PlanTaskStatus,
    SystemPromptStatus,
    SystemPromptStorageType,
    # Agent Class
    AgentClassCreate,
    AgentClassRead,
    # Agent Definition
    AgentDefinitionConfig,
    AgentDefinitionCreate,
    AgentDefinitionRead,
    # Agent Instance
    AgentInstanceCreate,
    AgentInstanceRead,
    # Deployment
    DeploymentCreate,
    DeploymentRead,
    # Plan
    PlanCreate,
    PlanRead,
    PlanReadWithTasks,
    PlanTaskCreate,
    PlanTaskRead,
    # Model Provider
    ModelProviderCreate,
    ModelProviderRead,
    # System Prompt
    SystemPromptCreate,
    SystemPromptRead,
    # Tool
    ToolCreate,
    ToolRead,
)


def _now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


_counter_value: int = 0


def _counter() -> int:
    """Generate incrementing counter for unique names."""
    global _counter_value
    _counter_value += 1
    return _counter_value


def reset_factories() -> None:
    """Reset factory counters for deterministic test behavior.

    Call this in test setup to ensure consistent naming across test runs.
    """
    global _counter_value
    _counter_value = 0


# =============================================================================
# Agent Class Factories
# =============================================================================


def factory_agent_class_create(
    *,
    name: str | None = None,
    description: str | None = None,
) -> AgentClassCreate:
    """Create an AgentClassCreate instance with defaults.

    Args:
        name: Agent class name (default: "TestClass-{n}")
        description: Description (default: None)

    Returns:
        AgentClassCreate instance
    """
    return AgentClassCreate(
        name=name or f"TestClass-{_counter()}",
        description=description,
    )


def factory_agent_class(
    *,
    id: UUID | None = None,
    name: str | None = None,
    description: str | None = None,
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
) -> AgentClassRead:
    """Create an AgentClassRead instance with defaults.

    Args:
        id: Agent class UUID (default: random UUID)
        name: Agent class name (default: "TestClass-{n}")
        description: Description (default: None)
        created_at: Creation timestamp (default: now)
        updated_at: Update timestamp (default: now)

    Returns:
        AgentClassRead instance
    """
    now = _now()
    return AgentClassRead(
        id=id or uuid4(),
        name=name or f"TestClass-{_counter()}",
        description=description,
        created_at=created_at or now,
        updated_at=updated_at or now,
    )


# =============================================================================
# Agent Definition Factories
# =============================================================================


def factory_agent_definition_create(
    *,
    agent_class_id: UUID | None = None,
    name: str | None = None,
    description: str | None = None,
    system_prompt_id: UUID | None = None,
    structured_output_id: UUID | None = None,
    model_provider_id: UUID | None = None,
    model_name: str | None = None,
    execution_mode: ExecutionMode = ExecutionMode.EPHEMERAL,
    config: dict[str, Any] | None = None,
    allow_outbound_a2a: bool = False,
    tool_ids: list[UUID] | None = None,
) -> AgentDefinitionCreate:
    """Create an AgentDefinitionCreate instance with defaults.

    Args:
        agent_class_id: Parent agent class UUID (default: random UUID)
        name: Definition name (default: "TestDefinition-{n}")
        description: Description (default: None)
        system_prompt_id: System prompt UUID (default: None)
        structured_output_id: Structured output UUID (default: None)
        model_provider_id: Model provider UUID (default: None)
        model_name: Model name (default: None)
        execution_mode: Execution mode (default: EPHEMERAL)
        config: Configuration dict (default: {})
        allow_outbound_a2a: Allow outbound A2A (default: False)
        tool_ids: Tool UUIDs (default: [])

    Returns:
        AgentDefinitionCreate instance
    """
    return AgentDefinitionCreate(
        agent_class_id=agent_class_id or uuid4(),
        name=name or f"TestDefinition-{_counter()}",
        description=description,
        system_prompt_id=system_prompt_id,
        structured_output_id=structured_output_id,
        model_provider_id=model_provider_id,
        model_name=model_name,
        execution_mode=execution_mode,
        config=config or {},
        allow_outbound_a2a=allow_outbound_a2a,
        tool_ids=tool_ids or [],
    )


def factory_agent_definition(
    *,
    id: UUID | None = None,
    agent_class_id: UUID | None = None,
    system_prompt_id: UUID | None = None,
    structured_output_id: UUID | None = None,
    model_provider_id: UUID | None = None,
    name: str | None = None,
    slug: str | None = None,
    description: str | None = None,
    status: AgentDefinitionStatus = AgentDefinitionStatus.DRAFT,
    execution_mode: ExecutionMode = ExecutionMode.EPHEMERAL,
    model_name: str | None = None,
    config: dict[str, Any] | None = None,
    allow_outbound_a2a: bool = False,
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
) -> AgentDefinitionRead:
    """Create an AgentDefinitionRead instance with defaults.

    Args:
        id: Definition UUID (default: random UUID)
        agent_class_id: Parent agent class UUID (default: random UUID)
        system_prompt_id: System prompt UUID (default: None)
        structured_output_id: Structured output UUID (default: None)
        model_provider_id: Model provider UUID (default: None)
        name: Definition name (default: "TestDefinition-{n}")
        slug: URL-safe slug (default: "test-definition-{n}")
        description: Description (default: None)
        status: Definition status (default: DRAFT)
        execution_mode: Execution mode (default: EPHEMERAL)
        model_name: Model name (default: None)
        config: Configuration dict (default: {})
        allow_outbound_a2a: Allow outbound A2A (default: False)
        created_at: Creation timestamp (default: now)
        updated_at: Update timestamp (default: now)

    Returns:
        AgentDefinitionRead instance
    """
    now = _now()
    counter = _counter()
    return AgentDefinitionRead(
        id=id or uuid4(),
        agent_class_id=agent_class_id or uuid4(),
        system_prompt_id=system_prompt_id,
        structured_output_id=structured_output_id,
        model_provider_id=model_provider_id,
        name=name or f"TestDefinition-{counter}",
        slug=slug or f"test-definition-{counter}",
        description=description,
        status=status,
        execution_mode=execution_mode,
        model_name=model_name,
        config=config or {},
        allow_outbound_a2a=allow_outbound_a2a,
        created_at=created_at or now,
        updated_at=updated_at or now,
    )


def factory_agent_definition_config(
    *,
    id: UUID | None = None,
    name: str | None = None,
    slug: str | None = None,
    description: str | None = None,
    status: AgentDefinitionStatus = AgentDefinitionStatus.PUBLISHED,
    execution_mode: ExecutionMode = ExecutionMode.EPHEMERAL,
    model_name: str | None = "gpt-4",
    config: dict[str, Any] | None = None,
    system_prompt: str | None = "You are a helpful assistant.",
    structured_output_schema: dict[str, Any] | None = None,
    tools: list[dict[str, Any]] | None = None,
) -> AgentDefinitionConfig:
    """Create an AgentDefinitionConfig instance with defaults.

    This is the configuration returned when fetching agent definition config
    for runtime use.

    Args:
        id: Definition UUID (default: random UUID)
        name: Definition name (default: "TestDefinition-{n}")
        slug: URL-safe slug (default: "test-definition-{n}")
        description: Description (default: None)
        status: Definition status (default: PUBLISHED)
        execution_mode: Execution mode (default: EPHEMERAL)
        model_name: Model name (default: "gpt-4")
        config: Configuration dict (default: {})
        system_prompt: System prompt content (default: basic prompt)
        structured_output_schema: Output schema (default: None)
        tools: Tool definitions (default: [])

    Returns:
        AgentDefinitionConfig instance
    """
    counter = _counter()
    return AgentDefinitionConfig(
        id=id or uuid4(),
        name=name or f"TestDefinition-{counter}",
        slug=slug or f"test-definition-{counter}",
        description=description,
        status=status,
        execution_mode=execution_mode,
        model_name=model_name,
        config=config or {},
        system_prompt=system_prompt,
        structured_output_schema=structured_output_schema,
        tools=tools or [],
    )


# =============================================================================
# Agent Instance Factories
# =============================================================================


def factory_agent_instance_create(
    *,
    routing_key: str | None = None,
    input: dict[str, Any] | None = None,
) -> AgentInstanceCreate:
    """Create an AgentInstanceCreate instance with defaults.

    Args:
        routing_key: Routing key (default: "test-routing-key-{n}")
        input: Input data (default: {})

    Returns:
        AgentInstanceCreate instance
    """
    return AgentInstanceCreate(
        routing_key=routing_key or f"test-routing-key-{_counter()}",
        input=input or {},
    )


def factory_agent_instance(
    *,
    id: UUID | None = None,
    deployment_id: UUID | None = None,
    agent_definition_id: UUID | None = None,
    routing_key: str | None = None,
    status: AgentInstanceStatus = AgentInstanceStatus.ACTIVE,
    input: dict[str, Any] | None = None,
    output: dict[str, Any] | None = None,
    error: str | None = None,
    exit_code: int | None = None,
    metrics: dict[str, Any] | None = None,
    created_at: datetime | None = None,
    started_at: datetime | None = None,
    completed_at: datetime | None = None,
) -> AgentInstanceRead:
    """Create an AgentInstanceRead instance with defaults.

    Args:
        id: Instance UUID (default: random UUID)
        deployment_id: Deployment UUID (default: random UUID)
        agent_definition_id: Definition UUID (default: random UUID)
        routing_key: Routing key (default: "test-routing-key-{n}")
        status: Instance status (default: ACTIVE)
        input: Input data (default: {})
        output: Output data (default: None)
        error: Error message (default: None)
        exit_code: Exit code (default: None)
        metrics: Metrics dict (default: {})
        created_at: Creation timestamp (default: now)
        started_at: Start timestamp (default: None)
        completed_at: Completion timestamp (default: None)

    Returns:
        AgentInstanceRead instance
    """
    now = _now()
    return AgentInstanceRead(
        id=id or uuid4(),
        deployment_id=deployment_id or uuid4(),
        agent_definition_id=agent_definition_id or uuid4(),
        routing_key=routing_key or f"test-routing-key-{_counter()}",
        status=status,
        input=input or {},
        output=output,
        error=error,
        exit_code=exit_code,
        metrics=metrics or {},
        created_at=created_at or now,
        started_at=started_at,
        completed_at=completed_at,
    )


# =============================================================================
# Deployment Factories
# =============================================================================


def factory_deployment_create(
    *,
    agent_definition_id: UUID | None = None,
    blueprint_id: UUID | None = None,
    name: str | None = None,
    description: str | None = None,
    environment: str = "production",
    config: dict[str, Any] | None = None,
    project_context: dict[str, Any] | None = None,
    spec_md_path: str | None = None,
) -> DeploymentCreate:
    """Create a DeploymentCreate instance with defaults.

    Args:
        agent_definition_id: Agent definition UUID (default: random UUID)
        blueprint_id: Blueprint UUID (default: None)
        name: Deployment name (default: "TestDeployment-{n}")
        description: Description (default: None)
        environment: Target environment (default: "production")
        config: Configuration dict (default: {})
        project_context: Project context (default: {})
        spec_md_path: Spec path (default: None)

    Returns:
        DeploymentCreate instance
    """
    return DeploymentCreate(
        agent_definition_id=agent_definition_id or uuid4(),
        blueprint_id=blueprint_id,
        name=name or f"TestDeployment-{_counter()}",
        description=description,
        environment=environment,
        config=config or {},
        project_context=project_context or {},
        spec_md_path=spec_md_path,
    )


def factory_deployment(
    *,
    id: UUID | None = None,
    agent_definition_id: UUID | None = None,
    blueprint_id: UUID | None = None,
    name: str | None = None,
    description: str | None = None,
    environment: str = "production",
    status: DeploymentStatus = DeploymentStatus.ACTIVE,
    config: dict[str, Any] | None = None,
    project_context: dict[str, Any] | None = None,
    spec_md_path: str | None = None,
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
) -> DeploymentRead:
    """Create a DeploymentRead instance with defaults.

    Args:
        id: Deployment UUID (default: random UUID)
        agent_definition_id: Agent definition UUID (default: random UUID)
        blueprint_id: Blueprint UUID (default: None)
        name: Deployment name (default: "TestDeployment-{n}")
        description: Description (default: None)
        environment: Target environment (default: "production")
        status: Deployment status (default: ACTIVE)
        config: Configuration dict (default: {})
        project_context: Project context (default: {})
        spec_md_path: Spec path (default: None)
        created_at: Creation timestamp (default: now)
        updated_at: Update timestamp (default: now)

    Returns:
        DeploymentRead instance
    """
    now = _now()
    return DeploymentRead(
        id=id or uuid4(),
        agent_definition_id=agent_definition_id or uuid4(),
        blueprint_id=blueprint_id,
        name=name or f"TestDeployment-{_counter()}",
        description=description,
        environment=environment,
        status=status,
        config=config or {},
        project_context=project_context or {},
        spec_md_path=spec_md_path,
        created_at=created_at or now,
        updated_at=updated_at or now,
    )


# =============================================================================
# Plan Factories
# =============================================================================


def factory_task_create(
    *,
    sequence: int = 0,
    description: str | None = None,
    validation: str | None = None,
    assignee_agent_definition_id: UUID | None = None,
    meta: dict[str, Any] | None = None,
) -> PlanTaskCreate:
    """Create a PlanTaskCreate instance with defaults.

    Args:
        sequence: Task sequence (default: 0)
        description: Task description (default: "Test task {n}")
        validation: Validation criteria (default: "Task completed successfully")
        assignee_agent_definition_id: Assignee UUID (default: None)
        meta: Metadata (default: {})

    Returns:
        PlanTaskCreate instance
    """
    counter = _counter()
    return PlanTaskCreate(
        sequence=sequence,
        description=description or f"Test task {counter}",
        validation=validation or "Task completed successfully",
        assignee_agent_definition_id=assignee_agent_definition_id,
        meta=meta or {},
    )


def factory_plan_create(
    *,
    goal: str | None = None,
    constraints: dict[str, Any] | None = None,
    state: dict[str, Any] | None = None,
    spec_reference: str | None = None,
    tasks: list[PlanTaskCreate] | None = None,
) -> PlanCreate:
    """Create a PlanCreate instance with defaults.

    Args:
        goal: Plan goal (default: "Test goal {n}")
        constraints: Constraints dict (default: {})
        state: State dict (default: {})
        spec_reference: Spec reference (default: None)
        tasks: Initial tasks (default: [])

    Returns:
        PlanCreate instance
    """
    return PlanCreate(
        goal=goal or f"Test goal {_counter()}",
        constraints=constraints or {},
        state=state or {},
        spec_reference=spec_reference,
        tasks=tasks or [],
    )


def factory_task(
    *,
    id: UUID | None = None,
    plan_id: UUID | None = None,
    sequence: int = 0,
    description: str | None = None,
    validation: str | None = None,
    assignee_agent_definition_id: UUID | None = None,
    status: PlanTaskStatus = PlanTaskStatus.PENDING,
    result: str | None = None,
    meta: dict[str, Any] | None = None,
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
) -> PlanTaskRead:
    """Create a PlanTaskRead instance with defaults.

    Args:
        id: Task UUID (default: random UUID)
        plan_id: Plan UUID (default: random UUID)
        sequence: Task sequence (default: 0)
        description: Task description (default: "Test task {n}")
        validation: Validation criteria (default: "Task completed successfully")
        assignee_agent_definition_id: Assignee UUID (default: None)
        status: Task status (default: PENDING)
        result: Task result (default: None)
        meta: Metadata (default: {})
        created_at: Creation timestamp (default: now)
        updated_at: Update timestamp (default: now)

    Returns:
        PlanTaskRead instance
    """
    now = _now()
    counter = _counter()
    return PlanTaskRead(
        id=id or uuid4(),
        plan_id=plan_id or uuid4(),
        sequence=sequence,
        description=description or f"Test task {counter}",
        validation=validation or "Task completed successfully",
        assignee_agent_definition_id=assignee_agent_definition_id,
        status=status,
        result=result,
        meta=meta or {},
        created_at=created_at or now,
        updated_at=updated_at or now,
    )


def factory_plan(
    *,
    id: UUID | None = None,
    deployment_id: UUID | None = None,
    created_by_instance_id: UUID | None = None,
    goal: str | None = None,
    constraints: dict[str, Any] | None = None,
    state: dict[str, Any] | None = None,
    status: PlanStatus = PlanStatus.ACTIVE,
    spec_reference: str | None = None,
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
) -> PlanRead:
    """Create a PlanRead instance with defaults.

    Args:
        id: Plan UUID (default: random UUID)
        deployment_id: Deployment UUID (default: random UUID)
        created_by_instance_id: Creator instance UUID (default: random UUID)
        goal: Plan goal (default: "Test goal {n}")
        constraints: Constraints dict (default: {})
        state: State dict (default: {})
        status: Plan status (default: ACTIVE)
        spec_reference: Spec reference (default: None)
        created_at: Creation timestamp (default: now)
        updated_at: Update timestamp (default: now)

    Returns:
        PlanRead instance
    """
    now = _now()
    return PlanRead(
        id=id or uuid4(),
        deployment_id=deployment_id or uuid4(),
        created_by_instance_id=created_by_instance_id or uuid4(),
        goal=goal or f"Test goal {_counter()}",
        constraints=constraints or {},
        state=state or {},
        status=status,
        spec_reference=spec_reference,
        created_at=created_at or now,
        updated_at=updated_at or now,
    )


def factory_plan_with_tasks(
    *,
    id: UUID | None = None,
    deployment_id: UUID | None = None,
    created_by_instance_id: UUID | None = None,
    goal: str | None = None,
    constraints: dict[str, Any] | None = None,
    state: dict[str, Any] | None = None,
    status: PlanStatus = PlanStatus.ACTIVE,
    spec_reference: str | None = None,
    tasks: list[PlanTaskRead] | None = None,
    num_tasks: int = 3,
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
) -> PlanReadWithTasks:
    """Create a PlanReadWithTasks instance with defaults.

    If tasks is not provided, creates num_tasks tasks automatically.

    Args:
        id: Plan UUID (default: random UUID)
        deployment_id: Deployment UUID (default: random UUID)
        created_by_instance_id: Creator instance UUID (default: random UUID)
        goal: Plan goal (default: "Test goal {n}")
        constraints: Constraints dict (default: {})
        state: State dict (default: {})
        status: Plan status (default: ACTIVE)
        spec_reference: Spec reference (default: None)
        tasks: Task list (default: auto-generated)
        num_tasks: Number of tasks to generate if tasks not provided (default: 3)
        created_at: Creation timestamp (default: now)
        updated_at: Update timestamp (default: now)

    Returns:
        PlanReadWithTasks instance
    """
    now = _now()
    plan_id = id or uuid4()

    if tasks is None:
        tasks = [factory_task(plan_id=plan_id, sequence=i) for i in range(num_tasks)]

    return PlanReadWithTasks(
        id=plan_id,
        deployment_id=deployment_id or uuid4(),
        created_by_instance_id=created_by_instance_id or uuid4(),
        goal=goal or f"Test goal {_counter()}",
        constraints=constraints or {},
        state=state or {},
        status=status,
        spec_reference=spec_reference,
        tasks=tasks,
        created_at=created_at or now,
        updated_at=updated_at or now,
    )


# =============================================================================
# Model Provider Factories
# =============================================================================


def factory_model_provider_create(
    *,
    name: str | None = None,
    api_base_url: str | None = None,
    description: str | None = None,
    config: dict[str, Any] | None = None,
) -> ModelProviderCreate:
    """Create a ModelProviderCreate instance with defaults.

    Args:
        name: Provider name (default: "TestProvider-{n}")
        api_base_url: API base URL (default: None)
        description: Description (default: None)
        config: Configuration dict (default: {})

    Returns:
        ModelProviderCreate instance
    """
    return ModelProviderCreate(
        name=name or f"TestProvider-{_counter()}",
        api_base_url=api_base_url,
        description=description,
        config=config or {},
    )


def factory_model_provider(
    *,
    id: UUID | None = None,
    name: str | None = None,
    api_base_url: str | None = None,
    description: str | None = None,
    config: dict[str, Any] | None = None,
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
) -> ModelProviderRead:
    """Create a ModelProviderRead instance with defaults.

    Args:
        id: Provider UUID (default: random UUID)
        name: Provider name (default: "TestProvider-{n}")
        api_base_url: API base URL (default: None)
        description: Description (default: None)
        config: Configuration dict (default: {})
        created_at: Creation timestamp (default: now)
        updated_at: Update timestamp (default: now)

    Returns:
        ModelProviderRead instance
    """
    now = _now()
    return ModelProviderRead(
        id=id or uuid4(),
        name=name or f"TestProvider-{_counter()}",
        api_base_url=api_base_url,
        description=description,
        config=config or {},
        created_at=created_at or now,
        updated_at=updated_at or now,
    )


# =============================================================================
# System Prompt Factories
# =============================================================================


def factory_system_prompt_create(
    *,
    name: str | None = None,
    description: str | None = None,
    status: SystemPromptStatus = SystemPromptStatus.DRAFT,
    content: str | None = None,
    content_storage_type: SystemPromptStorageType = SystemPromptStorageType.INLINE,
    meta: dict[str, Any] | None = None,
    agent_class_id: UUID | None = None,
) -> SystemPromptCreate:
    """Create a SystemPromptCreate instance with defaults.

    Args:
        name: Prompt name (default: "TestPrompt-{n}")
        description: Description (default: None)
        status: Prompt status (default: DRAFT)
        content: Prompt content (default: "You are a helpful assistant.")
        content_storage_type: Storage type (default: INLINE)
        meta: Metadata (default: None)
        agent_class_id: Agent class UUID (default: None)

    Returns:
        SystemPromptCreate instance
    """
    return SystemPromptCreate(
        name=name or f"TestPrompt-{_counter()}",
        description=description,
        status=status,
        content=content or "You are a helpful assistant.",
        content_storage_type=content_storage_type,
        meta=meta,
        agent_class_id=agent_class_id,
    )


def factory_system_prompt(
    *,
    id: UUID | None = None,
    agent_class_id: UUID | None = None,
    name: str | None = None,
    description: str | None = None,
    status: SystemPromptStatus = SystemPromptStatus.DRAFT,
    content: str | None = None,
    content_storage_type: SystemPromptStorageType = SystemPromptStorageType.INLINE,
    meta: dict[str, Any] | None = None,
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
) -> SystemPromptRead:
    """Create a SystemPromptRead instance with defaults.

    Args:
        id: Prompt UUID (default: random UUID)
        agent_class_id: Agent class UUID (default: None)
        name: Prompt name (default: "TestPrompt-{n}")
        description: Description (default: None)
        status: Prompt status (default: DRAFT)
        content: Prompt content (default: "You are a helpful assistant.")
        content_storage_type: Storage type (default: INLINE)
        meta: Metadata (default: None)
        created_at: Creation timestamp (default: now)
        updated_at: Update timestamp (default: now)

    Returns:
        SystemPromptRead instance
    """
    now = _now()
    return SystemPromptRead(
        id=id or uuid4(),
        agent_class_id=agent_class_id,
        name=name or f"TestPrompt-{_counter()}",
        description=description,
        status=status,
        content=content or "You are a helpful assistant.",
        content_storage_type=content_storage_type,
        meta=meta,
        created_at=created_at or now,
        updated_at=updated_at or now,
    )


# =============================================================================
# Tool Factories
# =============================================================================


def factory_tool_create(
    *,
    name: str | None = None,
    description: str | None = None,
    json_schema: dict[str, Any] | None = None,
    safety_policy: str | None = None,
    risk_level: str = "low",
) -> ToolCreate:
    """Create a ToolCreate instance with defaults.

    Args:
        name: Tool name (default: "test_tool_{n}")
        description: Description (default: None)
        json_schema: Tool schema (default: basic schema)
        safety_policy: Safety policy (default: None)
        risk_level: Risk level (default: "low")

    Returns:
        ToolCreate instance
    """
    counter = _counter()
    return ToolCreate(
        name=name or f"test_tool_{counter}",
        description=description,
        json_schema=json_schema
        or {
            "type": "object",
            "properties": {
                "input": {"type": "string", "description": "Input parameter"}
            },
            "required": ["input"],
        },
        safety_policy=safety_policy,
        risk_level=risk_level,  # type: ignore[arg-type]
    )


def factory_tool(
    *,
    id: UUID | None = None,
    name: str | None = None,
    description: str | None = None,
    json_schema: dict[str, Any] | None = None,
    safety_policy: str | None = None,
    risk_level: str = "low",
) -> ToolRead:
    """Create a ToolRead instance with defaults.

    Args:
        id: Tool UUID (default: random UUID)
        name: Tool name (default: "test_tool_{n}")
        description: Description (default: None)
        json_schema: Tool schema (default: basic schema)
        safety_policy: Safety policy (default: None)
        risk_level: Risk level (default: "low")

    Returns:
        ToolRead instance
    """
    counter = _counter()
    return ToolRead(
        id=id or uuid4(),
        name=name or f"test_tool_{counter}",
        description=description,
        json_schema=json_schema
        or {
            "type": "object",
            "properties": {
                "input": {"type": "string", "description": "Input parameter"}
            },
            "required": ["input"],
        },
        safety_policy=safety_policy,
        risk_level=risk_level,
    )
