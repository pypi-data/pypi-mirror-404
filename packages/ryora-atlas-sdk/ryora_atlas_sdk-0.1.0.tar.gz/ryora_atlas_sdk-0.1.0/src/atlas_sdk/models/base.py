"""Base model classes for Atlas SDK models.

This module provides base classes with proper configuration for Pydantic models
used in the Atlas SDK.

Model Categories:
    - **InputModel**: For request models (Create/Update) - validates input
      with improved error messages but allows standard Pydantic coercion for
      backward compatibility.
    - **ResponseModel**: For response models (Read) - uses `from_attributes=True`
      for ORM compatibility and lenient parsing of server responses.

Type Coercion Behavior:
    InputModel (Create/Update models):
    - UUID fields accept both UUID objects and valid UUID strings
    - Standard Pydantic coercion applies (maintains backward compatibility)
    - Default values are validated
    - Unknown fields are rejected (extra="forbid")

    ResponseModel (Read models):
    - More lenient parsing for server responses
    - Compatible with SQLAlchemy ORM objects via `from_attributes=True`

For strict type enforcement that disables all coercion, use the
`validate_model()` function from `atlas_sdk.validation` with explicit types.

Example:
    from atlas_sdk.models.base import InputModel, ResponseModel
    from uuid import UUID

    class DeploymentCreate(InputModel):
        name: str
        agent_definition_id: UUID  # Accepts UUID or valid UUID string

    class DeploymentRead(ResponseModel):
        id: UUID
        name: str
"""

from pydantic import BaseModel, ConfigDict


class InputModel(BaseModel):
    """Base model for request schemas (Create/Update operations).

    Provides improved validation with clear error messages while maintaining
    backward compatibility with existing code that relies on Pydantic's
    standard type coercion (e.g., str -> UUID).

    Configuration:
        - validate_default=True: Validates default values
        - extra="forbid": Rejects unknown fields to catch typos

    For strict type enforcement that rejects all implicit coercion, use
    the `validate_model()` function from `atlas_sdk.validation`.

    Example:
        class AgentClassCreate(InputModel):
            name: str
            description: str | None = None
    """

    model_config = ConfigDict(
        validate_default=True,
        extra="forbid",
    )


class ResponseModel(BaseModel):
    """Base model for response schemas parsed from server responses.

    Use this as the base class for Read models. It uses lenient parsing
    appropriate for server responses and supports ORM object conversion.

    Configuration:
        - from_attributes=True: Enables ORM object conversion
        - validate_default=True: Validates default values

    Example:
        class AgentClassRead(ResponseModel):
            id: UUID
            name: str
            created_at: datetime
    """

    model_config = ConfigDict(
        from_attributes=True,
        validate_default=True,
    )


# Backward compatibility alias
StrictModel = InputModel

__all__ = ["InputModel", "ResponseModel", "StrictModel"]
