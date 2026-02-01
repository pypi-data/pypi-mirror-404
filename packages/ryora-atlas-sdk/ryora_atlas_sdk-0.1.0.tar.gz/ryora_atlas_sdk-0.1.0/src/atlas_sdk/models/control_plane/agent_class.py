"""Agent class models for Atlas SDK."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import Field

from atlas_sdk.models.base import InputModel, ResponseModel


class AgentClassCreate(InputModel):
    """Agent class creation model.

    Args:
        name: Human-readable name for the agent class (required).
        description: Optional description of the class's purpose.
    """

    name: Annotated[str, Field(min_length=1, description="Human-readable name")]
    description: str | None = None


class AgentClassUpdate(InputModel):
    """Agent class update model.

    All fields are optional. Only provided fields will be updated.
    """

    name: Annotated[str, Field(min_length=1)] | None = None
    description: str | None = None


class AgentClassRead(ResponseModel):
    """Agent class read model returned by the API."""

    id: UUID
    name: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime
