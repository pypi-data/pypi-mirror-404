"""Input validation utilities for Atlas SDK.

This module provides utilities for validating input data before making HTTP requests,
enabling fail-fast behavior and clear error messages.

Features:
- Pre-flight validation of Pydantic models
- Enhanced error messages for common validation failures
- Support for strict type enforcement

Example:
    from atlas_sdk.validation import validate_model
    from atlas_sdk.models import AgentDefinitionCreate

    # Validate before making HTTP call
    try:
        model = validate_model(
            AgentDefinitionCreate,
            agent_class_id="not-a-uuid",  # Will fail validation
            name="test"
        )
    except AtlasInputValidationError as e:
        for detail in e.details:
            print(f"{detail}")
        # Output: agent_class_id: Invalid UUID format. Expected a UUID like
        #         '123e4567-e89b-12d3-a456-426614174000', got 'not-a-uuid'.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar

from pydantic import BaseModel, ValidationError

from atlas_sdk.exceptions import AtlasInputValidationError

if TYPE_CHECKING:
    pass

T = TypeVar("T", bound=BaseModel)


def validate_model(model_class: type[T], **data: Any) -> T:
    """Validate input data by constructing a Pydantic model.

    This function provides fail-fast validation with enhanced error messages.
    Use it to validate data before making HTTP requests to catch errors early
    with clear, actionable error messages.

    Args:
        model_class: The Pydantic model class to validate against.
        **data: The data to validate (field names and values).

    Returns:
        A validated instance of the model class.

    Raises:
        AtlasInputValidationError: If validation fails. Contains a list of
            InputValidationErrorDetail objects with field paths and enhanced
            error messages.

    Example:
        from atlas_sdk.validation import validate_model
        from atlas_sdk.models import DeploymentCreate

        # Valid data
        deployment = validate_model(
            DeploymentCreate,
            agent_definition_id="123e4567-e89b-12d3-a456-426614174000",
            name="my-deployment"
        )

        # Invalid data - will raise AtlasInputValidationError
        try:
            validate_model(DeploymentCreate, name="test")  # Missing required field
        except AtlasInputValidationError as e:
            print(e.details[0].msg)  # "This field is required."
    """
    try:
        return model_class(**data)
    except ValidationError as e:
        raise AtlasInputValidationError.from_pydantic_error(
            e, model_name=model_class.__name__
        ) from e


def validate_instance(model: BaseModel) -> None:
    """Validate an existing Pydantic model instance.

    This function re-validates a model instance to ensure it meets all
    constraints. Use it before making HTTP requests when you have an
    existing model instance that may have been modified.

    Args:
        model: A Pydantic model instance to validate.

    Raises:
        AtlasInputValidationError: If validation fails.

    Example:
        from atlas_sdk.validation import validate_instance
        from atlas_sdk.models import PlanCreate

        plan = PlanCreate(goal="Build feature X")
        # ... possibly modify the plan ...
        validate_instance(plan)  # Re-validate before sending
    """
    try:
        model.model_validate(model.model_dump())
    except ValidationError as e:
        raise AtlasInputValidationError.from_pydantic_error(
            e, model_name=type(model).__name__
        ) from e


def validate_uuid(value: Any, field_name: str = "id") -> str:
    """Validate that a value is a valid UUID string.

    Args:
        value: The value to validate.
        field_name: The field name for error messages.

    Returns:
        The validated UUID as a string.

    Raises:
        AtlasInputValidationError: If the value is not a valid UUID.

    Example:
        from atlas_sdk.validation import validate_uuid

        # Valid UUID
        uuid_str = validate_uuid("123e4567-e89b-12d3-a456-426614174000")

        # Invalid UUID - raises AtlasInputValidationError
        validate_uuid("not-a-uuid", "agent_class_id")
    """
    from uuid import UUID

    from atlas_sdk.exceptions import InputValidationErrorDetail

    if value is None:
        raise AtlasInputValidationError(
            f"Validation failed: {field_name}: This field is required.",
            details=[
                InputValidationErrorDetail(
                    loc=(field_name,),
                    msg="This field is required.",
                    type="missing",
                    input=value,
                )
            ],
        )

    # If already a UUID, convert to string
    if isinstance(value, UUID):
        return str(value)

    # Try to parse as UUID
    if isinstance(value, str):
        try:
            return str(UUID(value))
        except ValueError:
            pass

    # Invalid UUID format
    raise AtlasInputValidationError(
        f"Validation failed: {field_name}: Invalid UUID format.",
        details=[
            InputValidationErrorDetail(
                loc=(field_name,),
                msg=(
                    f"Invalid UUID format. Expected a UUID like "
                    f"'123e4567-e89b-12d3-a456-426614174000', got {value!r}."
                ),
                type="uuid_parsing",
                input=value,
            )
        ],
    )


def validate_enum(
    value: Any,
    enum_class: type,
    field_name: str = "value",
) -> Any:
    """Validate that a value is a valid enum member.

    Args:
        value: The value to validate.
        enum_class: The Enum class to validate against.
        field_name: The field name for error messages.

    Returns:
        The validated enum member.

    Raises:
        AtlasInputValidationError: If the value is not a valid enum member.

    Example:
        from atlas_sdk.validation import validate_enum
        from atlas_sdk.models.enums import DeploymentStatus

        # Valid enum value
        status = validate_enum("active", DeploymentStatus, "status")

        # Invalid enum - raises AtlasInputValidationError with valid options
        validate_enum("invalid", DeploymentStatus, "status")
        # Error message: "Invalid value 'invalid' for status. Valid options are:
        #               'spawning', 'active', 'completed', 'failed'."
    """
    from enum import Enum

    from atlas_sdk.exceptions import InputValidationErrorDetail

    if not issubclass(enum_class, Enum):
        raise ValueError(f"{enum_class} is not an Enum class")

    # Get valid options
    valid_values = [member.value for member in enum_class]

    # If already the correct enum type, return it
    if isinstance(value, enum_class):
        return value

    # Try to convert string/value to enum
    try:
        return enum_class(value)
    except ValueError:
        pass

    # Invalid enum value
    options_str = ", ".join(repr(v) for v in valid_values)
    raise AtlasInputValidationError(
        f"Validation failed: {field_name}: Invalid enum value.",
        details=[
            InputValidationErrorDetail(
                loc=(field_name,),
                msg=f"Invalid value {value!r} for {field_name}. Valid options are: {options_str}.",
                type="enum",
                input=value,
            )
        ],
    )


__all__ = [
    "validate_model",
    "validate_instance",
    "validate_uuid",
    "validate_enum",
]
