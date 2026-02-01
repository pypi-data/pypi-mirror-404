"""Plan and task models for Atlas SDK."""

from datetime import datetime
from typing import Any, Annotated
from uuid import UUID

from pydantic import Field

from atlas_sdk.models.base import InputModel, ResponseModel
from atlas_sdk.models.enums import PlanStatus, PlanTaskStatus


class PlanTaskCreate(InputModel):
    """Plan task creation model.

    Args:
        sequence: Order of the task within the plan (default: 0).
        description: Human-readable description of the task (required).
        validation: Criteria for validating task completion (required).
        assignee_agent_definition_id: UUID of the agent to assign the task to.
        meta: Additional metadata for the task.
    """

    sequence: Annotated[int, Field(ge=0)] = 0
    description: Annotated[str, Field(min_length=1)]
    validation: Annotated[str, Field(min_length=1)]
    assignee_agent_definition_id: UUID | None = None
    meta: dict[str, Any] = Field(default_factory=dict)


class PlanCreate(InputModel):
    """Plan creation model.

    Args:
        goal: The objective of the plan (required).
        constraints: Constraints that must be respected during execution.
        state: Initial state data for the plan.
        spec_reference: Reference to a specification document.
        tasks: Initial tasks to create with the plan.
    """

    goal: Annotated[str, Field(min_length=1, description="The objective of the plan")]
    constraints: dict[str, Any] = Field(default_factory=dict)
    state: dict[str, Any] = Field(default_factory=dict)
    spec_reference: str | None = None
    tasks: list[PlanTaskCreate] = Field(default_factory=list)


class PlanCreateResponse(ResponseModel):
    """Response from creating a plan."""

    id: UUID
    deployment_id: UUID
    created_by_instance_id: UUID
    goal: str
    constraints: dict[str, Any]
    state: dict[str, Any]
    status: PlanStatus
    spec_reference: str | None = None
    created_at: datetime
    updated_at: datetime
    task_ids: list[UUID] = Field(default_factory=list)


class PlanRead(ResponseModel):
    """Plan read model returned by the API."""

    id: UUID
    deployment_id: UUID
    created_by_instance_id: UUID
    goal: str
    constraints: dict[str, Any]
    state: dict[str, Any]
    status: PlanStatus
    spec_reference: str | None = None
    created_at: datetime
    updated_at: datetime


class PlanTaskRead(ResponseModel):
    """Plan task read model returned by the API."""

    id: UUID
    plan_id: UUID
    sequence: int
    description: str
    validation: str
    assignee_agent_definition_id: UUID | None = None
    status: PlanTaskStatus
    result: str | None = None
    meta: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class PlanTaskReadEnriched(PlanTaskRead):
    """Plan task read model with enriched agent data."""

    assignee_agent_slug: str | None = None
    assignee_agent_name: str | None = None


class PlanReadWithTasks(PlanRead):
    """Plan read model with tasks included."""

    tasks: list[PlanTaskRead] = Field(default_factory=list)


class PlanUpdate(InputModel):
    """Plan update model.

    All fields are optional. Only provided fields will be updated.
    """

    goal: Annotated[str, Field(min_length=1)] | None = None
    constraints: dict[str, Any] | None = None
    state: dict[str, Any] | None = None
    status: PlanStatus | None = None
    spec_reference: str | None = None


class PlanTaskUpdate(InputModel):
    """Plan task update model.

    All fields are optional. Only provided fields will be updated.
    """

    sequence: Annotated[int, Field(ge=0)] | None = None
    description: Annotated[str, Field(min_length=1)] | None = None
    validation: Annotated[str, Field(min_length=1)] | None = None
    assignee_agent_definition_id: UUID | None = None
    status: PlanTaskStatus | None = None
    result: str | None = None
    meta: dict[str, Any] | None = None


class TasksAppend(InputModel):
    """Request model for appending tasks to a plan."""

    tasks: Annotated[list[PlanTaskCreate], Field(min_length=1)]


class TasksAppendResponse(ResponseModel):
    """Response from appending tasks."""

    task_ids: list[UUID]
