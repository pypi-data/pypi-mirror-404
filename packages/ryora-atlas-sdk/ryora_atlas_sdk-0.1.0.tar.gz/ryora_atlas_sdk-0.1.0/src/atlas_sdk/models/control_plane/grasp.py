"""GRASP analysis and Blueprint models for Atlas SDK."""

from datetime import datetime
from typing import Any, Annotated
from uuid import UUID

from pydantic import Field

from atlas_sdk.models.base import InputModel, ResponseModel
from atlas_sdk.models.enums import GraspAnalysisStatus


class GraspAnalysisCreate(InputModel):
    """Schema for triggering a new GRASP analysis.

    Args:
        analysis_context: Context data for the analysis.
    """

    analysis_context: dict[str, Any] = Field(default_factory=dict)


class GraspAnalysisRead(ResponseModel):
    """Schema for reading a GRASP analysis."""

    id: UUID
    deployment_id: UUID | None = None
    blueprint_id: UUID | None = None
    agent_definition_id: UUID | None = None
    status: GraspAnalysisStatus

    # Governance dimension: Can we see what it's doing and stop it?
    governance_value: Annotated[int, Field(ge=0, le=100)] | None = None
    governance_summary: str | None = None
    governance_evidence: dict[str, Any] = Field(default_factory=dict)

    # Reach dimension: What can it touch (explicit + implicit)?
    reach_value: Annotated[int, Field(ge=0, le=100)] | None = None
    reach_summary: str | None = None
    reach_evidence: dict[str, Any] = Field(default_factory=dict)

    # Agency dimension: How autonomous is it?
    agency_value: Annotated[int, Field(ge=0, le=100)] | None = None
    agency_summary: str | None = None
    agency_evidence: dict[str, Any] = Field(default_factory=dict)

    # Safeguards dimension: What limits damage when it acts unsupervised?
    safeguards_value: Annotated[int, Field(ge=0, le=100)] | None = None
    safeguards_summary: str | None = None
    safeguards_evidence: dict[str, Any] = Field(default_factory=dict)

    # Potential Damage dimension: What's the credible worst case?
    potential_damage_value: Annotated[int, Field(ge=0, le=100)] | None = None
    potential_damage_summary: str | None = None
    potential_damage_evidence: dict[str, Any] = Field(default_factory=dict)

    # Context snapshot and error info
    analysis_context: dict[str, Any] = Field(default_factory=dict)
    error_message: str | None = None

    created_at: datetime
    completed_at: datetime | None = None


class GraspAnalysisSummary(ResponseModel):
    """Lightweight schema for listing GRASP analyses."""

    id: UUID
    deployment_id: UUID | None = None
    blueprint_id: UUID | None = None
    agent_definition_id: UUID | None = None
    status: GraspAnalysisStatus
    governance_value: int | None = None
    reach_value: int | None = None
    agency_value: int | None = None
    safeguards_value: int | None = None
    potential_damage_value: int | None = None
    created_at: datetime
    completed_at: datetime | None = None


class BlueprintCreate(InputModel):
    """Schema for creating a new blueprint.

    Args:
        name: Human-readable name for the blueprint (required).
        description: Optional description of the blueprint's purpose.
        nomad_job_definition: Nomad job definition for the blueprint.
        entrypoint_script: Entrypoint script to run.
        docker_image: Docker image to use.
        registered: Whether the blueprint is registered.
        agent_definition_ids: List of agent definition UUIDs in this blueprint.
    """

    name: Annotated[str, Field(min_length=1, description="Human-readable name")]
    description: str | None = None
    nomad_job_definition: dict[str, Any] = Field(default_factory=dict)
    entrypoint_script: str | None = None
    docker_image: str | None = None
    registered: bool = False
    agent_definition_ids: list[UUID] = Field(default_factory=list)


class BlueprintRead(ResponseModel):
    """Schema for reading a blueprint."""

    id: UUID
    name: str
    description: str | None = None
    nomad_job_definition: dict[str, Any] = Field(default_factory=dict)
    entrypoint_script: str | None = None
    docker_image: str | None = None
    registered: bool
    agent_definition_ids: list[UUID] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class BlueprintUpdate(InputModel):
    """Schema for updating a blueprint.

    All fields are optional. Only provided fields will be updated.
    """

    name: Annotated[str, Field(min_length=1)] | None = None
    description: str | None = None
    nomad_job_definition: dict[str, Any] | None = None
    entrypoint_script: str | None = None
    docker_image: str | None = None
    registered: bool | None = None
    agent_definition_ids: list[UUID] | None = None
