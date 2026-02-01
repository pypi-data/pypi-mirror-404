"""System prompt models for Atlas SDK."""

from datetime import datetime
from typing import Any, Annotated
from uuid import UUID

from pydantic import Field

from atlas_sdk.models.base import InputModel, ResponseModel
from atlas_sdk.models.enums import SystemPromptStatus, SystemPromptStorageType


class SystemPromptCreate(InputModel):
    """System prompt creation model.

    Args:
        name: Human-readable name for the prompt (required).
        description: Optional description of the prompt's purpose.
        status: Initial status (default: draft).
        content: The prompt text content (required).
        content_storage_type: How content is stored (default: inline).
        meta: Additional metadata for the prompt.
        agent_class_id: UUID of the owning agent class.
    """

    name: Annotated[str, Field(min_length=1, description="Human-readable name")]
    description: str | None = None
    status: SystemPromptStatus = SystemPromptStatus.DRAFT
    content: Annotated[str, Field(min_length=1, description="The prompt text content")]
    content_storage_type: SystemPromptStorageType = SystemPromptStorageType.INLINE
    meta: dict[str, Any] | None = None
    agent_class_id: UUID | None = None


class SystemPromptUpdate(InputModel):
    """System prompt update model.

    All fields are optional. Only provided fields will be updated.
    """

    name: Annotated[str, Field(min_length=1)] | None = None
    description: str | None = None
    status: SystemPromptStatus | None = None
    content: Annotated[str, Field(min_length=1)] | None = None
    content_storage_type: SystemPromptStorageType | None = None
    meta: dict[str, Any] | None = None


class SystemPromptRead(ResponseModel):
    """System prompt read model returned by the API."""

    id: UUID
    agent_class_id: UUID | None = None
    name: str
    description: str | None = None
    status: SystemPromptStatus
    content: str
    content_storage_type: SystemPromptStorageType
    meta: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime
