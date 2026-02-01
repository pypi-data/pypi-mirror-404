"""Agent instance models for Atlas SDK."""

from datetime import datetime
from typing import Any, Annotated
from uuid import UUID

from pydantic import Field

from atlas_sdk.models.base import InputModel, ResponseModel
from atlas_sdk.models.enums import AgentInstanceStatus


class AgentInstanceCreate(InputModel):
    """Agent instance creation model.

    Args:
        routing_key: Key for routing the instance (required).
        input: Input data for the agent instance.
    """

    routing_key: Annotated[str, Field(min_length=1, description="Routing key")]
    input: dict[str, Any] = Field(default_factory=dict)


class AgentInstanceRead(ResponseModel):
    """Agent instance read model returned by the API."""

    id: UUID
    deployment_id: UUID
    agent_definition_id: UUID
    routing_key: str
    status: AgentInstanceStatus
    input: dict[str, Any]
    output: dict[str, Any] | None = None
    error: str | None = None
    exit_code: int | None = None
    metrics: dict[str, Any]
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None


class AgentInstanceUpdate(InputModel):
    """Agent instance update model.

    All fields are optional. Only provided fields will be updated.
    """

    status: AgentInstanceStatus | None = None
    output: dict[str, Any] | None = None
    error: str | None = None
    exit_code: int | None = None
    metrics: dict[str, Any] | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
