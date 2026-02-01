"""Dispatch service schemas for agent lifecycle and A2A communication."""

from typing import Any, Annotated
from uuid import UUID

from pydantic import Field

from atlas_sdk.models.base import InputModel, ResponseModel


class SpawnRequest(InputModel):
    """Request to spawn a new agent process.

    Args:
        agent_definition_id: UUID of the agent definition to spawn (required).
        deployment_id: UUID of the deployment context (required).
        prompt: Initial prompt for the agent (required).
    """

    agent_definition_id: Annotated[
        UUID, Field(description="UUID of the agent definition to spawn")
    ]
    deployment_id: Annotated[UUID, Field(description="UUID of the deployment context")]
    prompt: Annotated[str, Field(min_length=1, description="Initial prompt")]


class SpawnResponse(ResponseModel):
    """Response from spawning an agent."""

    status: str
    port: int
    pid: int
    url: str
    deployment_id: UUID
    instance_id: UUID


class AgentStatusResponse(ResponseModel):
    """Response containing agent status information."""

    definition_id: UUID
    instance_id: UUID | None = None
    port: int | None = None
    pid: int | None = None
    running: bool


class StopResponse(ResponseModel):
    """Response from stopping an agent."""

    status: str
    message: str


class WaitResponse(ResponseModel):
    """Response from waiting for an agent to complete."""

    status: str
    instance_id: UUID
    output: dict[str, Any] | None = None
    error: str | None = None
    exit_code: int | None = None


class A2ACallRequest(InputModel):
    """Request for agent-to-agent communication.

    Args:
        agent_definition_id: UUID of the target agent definition (required).
        prompt: Message to send to the agent (required).
        routing_key: Optional routing key for the call.
    """

    agent_definition_id: Annotated[
        UUID, Field(description="UUID of the target agent definition")
    ]
    prompt: Annotated[str, Field(min_length=1, description="Message to send")]
    routing_key: str | None = None


class A2ACallResponse(ResponseModel):
    """Response from an agent-to-agent call."""

    content: str
    instance_id: UUID
    metadata: dict[str, Any] | None = None


class AgentDirectoryEntry(ResponseModel):
    """Entry in the agent directory listing."""

    agent_definition_id: UUID
    instance_id: UUID
    url: str
    port: int
    running: bool
    slug: str
    agent_class_id: UUID
    execution_mode: str
    allow_outbound_a2a: bool


class A2ADirectoryResponse(ResponseModel):
    """Response containing the agent directory."""

    agents: list[AgentDirectoryEntry]
    deployment_id: UUID
