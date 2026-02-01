"""Tool models for Atlas SDK."""

from typing import Any, Annotated, Literal
from uuid import UUID

from pydantic import Field

from atlas_sdk.models.base import InputModel, ResponseModel


class ToolCreate(InputModel):
    """Tool creation model.

    Args:
        name: Human-readable name for the tool (required).
        description: Optional description of the tool's purpose.
        json_schema: JSON Schema defining the tool's parameters (required).
        safety_policy: Optional safety policy for the tool.
        risk_level: Risk level classification (default: "low").
    """

    name: Annotated[str, Field(min_length=1, description="Human-readable name")]
    description: str | None = None
    json_schema: Annotated[
        dict[str, Any], Field(description="JSON Schema for tool parameters")
    ]
    safety_policy: str | None = None
    risk_level: Literal["low", "medium", "high"] = "low"


class ToolUpdate(InputModel):
    """Tool update model.

    All fields are optional. Only provided fields will be updated.
    """

    description: str | None = None
    json_schema: dict[str, Any] | None = None
    safety_policy: str | None = None
    risk_level: Literal["low", "medium", "high"] | None = None


class ToolRead(ResponseModel):
    """Tool read model returned by the API."""

    id: UUID
    name: str
    description: str | None = None
    json_schema: dict[str, Any]
    safety_policy: str | None = None
    risk_level: str


class ToolSyncRequest(InputModel):
    """Request model for syncing tools."""

    tools: Annotated[list[ToolCreate], Field(min_length=1)]
