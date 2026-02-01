"""Deployment models for Atlas SDK."""

from datetime import datetime
from typing import Any, Annotated
from uuid import UUID

from pydantic import Field

from atlas_sdk.models.base import InputModel, ResponseModel
from atlas_sdk.models.enums import DeploymentStatus


class DeploymentCreate(InputModel):
    """Deployment creation model.

    Args:
        agent_definition_id: UUID of the agent definition to deploy (required).
        blueprint_id: Optional UUID of the blueprint to use.
        name: Human-readable name for the deployment (required).
        description: Optional description of the deployment's purpose.
        environment: Target environment (default: "production").
        config: Additional configuration parameters.
        project_context: Project-specific context data.
        spec_md_path: Path to specification markdown file.
    """

    agent_definition_id: Annotated[
        UUID, Field(description="UUID of the agent definition to deploy")
    ]
    blueprint_id: UUID | None = None
    name: Annotated[str, Field(min_length=1, description="Human-readable name")]
    description: str | None = None
    environment: str = "production"
    config: dict[str, Any] = Field(default_factory=dict)
    project_context: dict[str, Any] = Field(default_factory=dict)
    spec_md_path: str | None = None


class DeploymentRead(ResponseModel):
    """Deployment read model returned by the API."""

    id: UUID
    agent_definition_id: UUID
    blueprint_id: UUID | None = None
    name: str
    description: str | None = None
    environment: str
    status: DeploymentStatus
    config: dict[str, Any]
    project_context: dict[str, Any]
    spec_md_path: str | None = None
    created_at: datetime
    updated_at: datetime


class DeploymentUpdate(InputModel):
    """Deployment update model.

    All fields are optional. Only provided fields will be updated.
    """

    name: Annotated[str, Field(min_length=1)] | None = None
    description: str | None = None
    environment: str | None = None
    status: DeploymentStatus | None = None
    config: dict[str, Any] | None = None
    project_context: dict[str, Any] | None = None
    spec_md_path: str | None = None
