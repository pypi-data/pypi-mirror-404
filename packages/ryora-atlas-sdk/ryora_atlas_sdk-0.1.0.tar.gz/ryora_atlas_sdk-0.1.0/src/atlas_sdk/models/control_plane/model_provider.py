"""Model provider models for Atlas SDK."""

from datetime import datetime
from typing import Any, Annotated
from uuid import UUID

from pydantic import Field

from atlas_sdk.models.base import InputModel, ResponseModel


class ModelProviderCreate(InputModel):
    """Model provider creation model.

    Args:
        name: Human-readable name for the provider (required).
        api_base_url: Base URL for the provider's API.
        description: Optional description of the provider.
        config: Provider-specific configuration parameters.
    """

    name: Annotated[str, Field(min_length=1, description="Human-readable name")]
    api_base_url: str | None = None
    description: str | None = None
    config: dict[str, Any] = Field(default_factory=dict)


class ModelProviderUpdate(InputModel):
    """Model provider update model.

    All fields are optional. Only provided fields will be updated.
    """

    name: Annotated[str, Field(min_length=1)] | None = None
    api_base_url: str | None = None
    description: str | None = None
    config: dict[str, Any] | None = None


class ModelProviderRead(ResponseModel):
    """Model provider read model returned by the API."""

    id: UUID
    name: str
    api_base_url: str | None = None
    description: str | None = None
    config: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
