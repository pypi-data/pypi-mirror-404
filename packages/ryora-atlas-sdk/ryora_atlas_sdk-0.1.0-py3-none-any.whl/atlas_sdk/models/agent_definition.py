"""Agent definition models for Atlas SDK."""

from datetime import datetime
from typing import Any, Annotated
from uuid import UUID

from pydantic import Field

from atlas_sdk.models.base import InputModel, ResponseModel
from atlas_sdk.models.enums import AgentDefinitionStatus, ExecutionMode


class AgentDefinitionCreate(InputModel):
    """Agent definition creation model.

    Args:
        agent_class_id: UUID of the parent agent class (required).
        name: Human-readable name for the definition (required).
        description: Optional description of the definition's purpose.
        system_prompt_id: UUID of the system prompt to use.
        structured_output_id: UUID of the structured output schema to use.
        model_provider_id: UUID of the model provider to use.
        model_name: Name of the model to use (provider-specific).
        execution_mode: How agent instances should be managed.
        config: Additional configuration parameters.
        allow_outbound_a2a: Whether this agent can call other agents.
        tool_ids: List of tool UUIDs this agent can use.
    """

    agent_class_id: Annotated[UUID, Field(description="UUID of the parent agent class")]
    name: Annotated[str, Field(min_length=1, description="Human-readable name")]
    description: str | None = None
    system_prompt_id: UUID | None = None
    structured_output_id: UUID | None = None
    model_provider_id: UUID | None = None
    model_name: str | None = None
    execution_mode: ExecutionMode = ExecutionMode.EPHEMERAL
    config: dict[str, Any] = Field(default_factory=dict)
    allow_outbound_a2a: bool = False
    tool_ids: list[UUID] = Field(default_factory=list)


class AgentDefinitionUpdate(InputModel):
    """Agent definition update model.

    All fields are optional. Only provided fields will be updated.
    """

    name: Annotated[str, Field(min_length=1)] | None = None
    description: str | None = None
    status: AgentDefinitionStatus | None = None
    system_prompt_id: UUID | None = None
    structured_output_id: UUID | None = None
    model_provider_id: UUID | None = None
    model_name: str | None = None
    execution_mode: ExecutionMode | None = None
    config: dict[str, Any] | None = None
    allow_outbound_a2a: bool | None = None


class AgentDefinitionRead(ResponseModel):
    """Agent definition read model returned by the API."""

    id: UUID
    agent_class_id: UUID
    system_prompt_id: UUID | None = None
    structured_output_id: UUID | None = None
    model_provider_id: UUID | None = None
    name: str
    slug: str
    description: str | None = None
    status: AgentDefinitionStatus
    execution_mode: ExecutionMode
    model_name: str | None = None
    config: dict[str, Any]
    allow_outbound_a2a: bool
    created_at: datetime
    updated_at: datetime


class AgentDefinitionConfig(ResponseModel):
    """Agent definition configuration details for agent runtime."""

    id: UUID
    name: str
    slug: str
    description: str | None = None
    status: AgentDefinitionStatus
    execution_mode: ExecutionMode
    model_name: str | None = None
    config: dict[str, Any]
    system_prompt: str | None = None
    structured_output_schema: dict[str, Any] | None = None
    tools: list[dict[str, Any]] = Field(default_factory=list)
