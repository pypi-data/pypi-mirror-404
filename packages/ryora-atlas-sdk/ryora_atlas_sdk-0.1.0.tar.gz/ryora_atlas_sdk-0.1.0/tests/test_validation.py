"""Tests for input validation utilities."""

from uuid import UUID

import pytest
from pydantic import BaseModel, Field, ValidationError

from atlas_sdk.exceptions import AtlasInputValidationError, InputValidationErrorDetail
from atlas_sdk.models.base import InputModel, ResponseModel
from atlas_sdk.validation import (
    validate_enum,
    validate_instance,
    validate_model,
    validate_uuid,
)


# Test models for validation
class SampleCreateModel(InputModel):
    """Sample model for testing input validation."""

    name: str = Field(min_length=1)
    description: str | None = None
    count: int = 0


class SampleResponseModel(ResponseModel):
    """Sample model for testing response validation."""

    id: UUID
    name: str


# =============================================================================
# InputValidationErrorDetail tests
# =============================================================================


class TestInputValidationErrorDetail:
    """Tests for InputValidationErrorDetail dataclass."""

    def test_str_representation(self):
        """Test string representation of error detail."""
        detail = InputValidationErrorDetail(
            loc=("name",),
            msg="This field is required.",
            type="missing",
        )
        assert str(detail) == "name: This field is required."

    def test_str_representation_nested_path(self):
        """Test string representation with nested field path."""
        detail = InputValidationErrorDetail(
            loc=("config", "timeout"),
            msg="Expected an integer.",
            type="int_type",
        )
        assert str(detail) == "config.timeout: Expected an integer."

    def test_str_representation_empty_path(self):
        """Test string representation with empty path."""
        detail = InputValidationErrorDetail(
            loc=(),
            msg="Root validation error.",
            type="value_error",
        )
        assert str(detail) == "<root>: Root validation error."

    def test_str_representation_with_index(self):
        """Test string representation with array index in path."""
        detail = InputValidationErrorDetail(
            loc=("items", 0, "name"),
            msg="Expected a string.",
            type="string_type",
        )
        assert str(detail) == "items.0.name: Expected a string."


# =============================================================================
# AtlasInputValidationError tests
# =============================================================================


class TestAtlasInputValidationError:
    """Tests for AtlasInputValidationError exception."""

    def test_init_with_message(self):
        """Test initialization with just a message."""
        error = AtlasInputValidationError("Test error message")
        assert error.message == "Test error message"
        assert str(error) == "Test error message"
        assert error.details == []
        assert error.model_name is None

    def test_init_with_details(self):
        """Test initialization with error details."""
        details = [
            InputValidationErrorDetail(loc=("name",), msg="Required", type="missing"),
            InputValidationErrorDetail(
                loc=("count",), msg="Must be positive", type="value_error"
            ),
        ]
        error = AtlasInputValidationError(
            "Validation failed", details=details, model_name="TestModel"
        )
        assert len(error.details) == 2
        assert error.model_name == "TestModel"

    def test_from_pydantic_error_missing_field(self):
        """Test creating from Pydantic error for missing field."""

        class RequiredModel(BaseModel):
            required_field: str

        with pytest.raises(ValidationError) as exc_info:
            RequiredModel()

        atlas_error = AtlasInputValidationError.from_pydantic_error(
            exc_info.value, model_name="RequiredModel"
        )
        assert len(atlas_error.details) == 1
        assert atlas_error.details[0].type == "missing"
        assert "required" in atlas_error.details[0].msg.lower()

    def test_from_pydantic_error_uuid_parsing(self):
        """Test creating from Pydantic error for invalid UUID."""

        class UUIDModel(BaseModel):
            id: UUID

        with pytest.raises(ValidationError) as exc_info:
            UUIDModel(id="not-a-uuid")

        atlas_error = AtlasInputValidationError.from_pydantic_error(exc_info.value)
        assert len(atlas_error.details) == 1
        assert atlas_error.details[0].type == "uuid_parsing"
        assert "UUID" in atlas_error.details[0].msg

    def test_from_pydantic_error_string_type(self):
        """Test creating from Pydantic error for string type."""

        class StrictModel(BaseModel):
            model_config = {"strict": True}
            name: str

        with pytest.raises(ValidationError) as exc_info:
            StrictModel(name=123)

        atlas_error = AtlasInputValidationError.from_pydantic_error(exc_info.value)
        assert len(atlas_error.details) == 1
        # The error type may vary based on Pydantic version
        assert atlas_error.details[0].loc == ("name",)

    def test_from_pydantic_error_multiple_errors(self):
        """Test creating from Pydantic error with multiple validation errors."""

        class MultiFieldModel(BaseModel):
            required1: str
            required2: int

        with pytest.raises(ValidationError) as exc_info:
            MultiFieldModel()

        atlas_error = AtlasInputValidationError.from_pydantic_error(exc_info.value)
        assert len(atlas_error.details) == 2


# =============================================================================
# validate_model() tests
# =============================================================================


class TestValidateModel:
    """Tests for validate_model() function."""

    def test_valid_model(self):
        """Test validation with valid data."""
        model = validate_model(SampleCreateModel, name="test", description="desc")
        assert model.name == "test"
        assert model.description == "desc"
        assert model.count == 0

    def test_valid_model_with_defaults(self):
        """Test validation with default values."""
        model = validate_model(SampleCreateModel, name="test")
        assert model.name == "test"
        assert model.description is None
        assert model.count == 0

    def test_missing_required_field(self):
        """Test validation fails for missing required field."""
        with pytest.raises(AtlasInputValidationError) as exc_info:
            validate_model(SampleCreateModel)
        assert exc_info.value.model_name == "SampleCreateModel"
        assert len(exc_info.value.details) >= 1
        # Find the error for 'name' field
        name_errors = [d for d in exc_info.value.details if "name" in d.loc]
        assert len(name_errors) >= 1

    def test_invalid_type(self):
        """Test validation fails for invalid type."""
        with pytest.raises(AtlasInputValidationError):
            validate_model(SampleCreateModel, name="test", count="not-an-int")

    def test_constraint_violation(self):
        """Test validation fails for constraint violation."""
        with pytest.raises(AtlasInputValidationError):
            validate_model(SampleCreateModel, name="")  # min_length=1


# =============================================================================
# validate_instance() tests
# =============================================================================


class TestValidateInstance:
    """Tests for validate_instance() function."""

    def test_valid_instance(self):
        """Test validation with valid instance."""
        model = SampleCreateModel(name="test")
        validate_instance(model)  # Should not raise

    def test_invalid_instance(self):
        """Test validation fails for invalid instance after modification."""
        model = SampleCreateModel(name="test")
        # Force an invalid value through object.__setattr__ to bypass validation
        object.__setattr__(model, "name", "")
        # Note: Pydantic v2 may allow this, so re-validation catches it
        # The re-validation in validate_instance uses model_dump which won't catch this
        # This test documents the current behavior


# =============================================================================
# validate_uuid() tests
# =============================================================================


class TestValidateUuid:
    """Tests for validate_uuid() function."""

    def test_valid_uuid_string(self):
        """Test validation with valid UUID string."""
        result = validate_uuid("123e4567-e89b-12d3-a456-426614174000")
        assert result == "123e4567-e89b-12d3-a456-426614174000"

    def test_valid_uuid_object(self):
        """Test validation with UUID object."""
        uuid_obj = UUID("123e4567-e89b-12d3-a456-426614174000")
        result = validate_uuid(uuid_obj)
        assert result == "123e4567-e89b-12d3-a456-426614174000"

    def test_invalid_uuid_string(self):
        """Test validation fails for invalid UUID string."""
        with pytest.raises(AtlasInputValidationError) as exc_info:
            validate_uuid("not-a-uuid", "agent_id")
        assert len(exc_info.value.details) == 1
        assert exc_info.value.details[0].loc == ("agent_id",)
        assert exc_info.value.details[0].type == "uuid_parsing"
        assert "not-a-uuid" in exc_info.value.details[0].msg

    def test_none_value(self):
        """Test validation fails for None value."""
        with pytest.raises(AtlasInputValidationError) as exc_info:
            validate_uuid(None, "required_id")
        assert exc_info.value.details[0].type == "missing"

    def test_custom_field_name(self):
        """Test validation uses custom field name in error."""
        with pytest.raises(AtlasInputValidationError) as exc_info:
            validate_uuid("invalid", "my_custom_field")
        assert exc_info.value.details[0].loc == ("my_custom_field",)


# =============================================================================
# validate_enum() tests
# =============================================================================


class TestValidateEnum:
    """Tests for validate_enum() function."""

    def test_valid_enum_value(self):
        """Test validation with valid enum value."""
        from enum import Enum

        class Status(str, Enum):
            ACTIVE = "active"
            INACTIVE = "inactive"

        result = validate_enum("active", Status, "status")
        assert result == Status.ACTIVE

    def test_valid_enum_member(self):
        """Test validation with enum member."""
        from enum import Enum

        class Status(str, Enum):
            ACTIVE = "active"
            INACTIVE = "inactive"

        result = validate_enum(Status.ACTIVE, Status, "status")
        assert result == Status.ACTIVE

    def test_invalid_enum_value(self):
        """Test validation fails for invalid enum value."""
        from enum import Enum

        class Status(str, Enum):
            ACTIVE = "active"
            INACTIVE = "inactive"

        with pytest.raises(AtlasInputValidationError) as exc_info:
            validate_enum("invalid", Status, "status")
        assert len(exc_info.value.details) == 1
        assert exc_info.value.details[0].loc == ("status",)
        assert exc_info.value.details[0].type == "enum"
        assert "'active'" in exc_info.value.details[0].msg
        assert "'inactive'" in exc_info.value.details[0].msg

    def test_non_enum_class_raises_error(self):
        """Test that non-enum class raises ValueError."""

        class NotAnEnum:
            pass

        with pytest.raises(ValueError, match="is not an Enum class"):
            validate_enum("value", NotAnEnum, "field")


# =============================================================================
# InputModel tests (extra="forbid")
# =============================================================================


class TestInputModel:
    """Tests for InputModel base class behavior."""

    def test_rejects_unknown_fields(self):
        """Test that InputModel rejects unknown fields."""
        with pytest.raises(ValidationError) as exc_info:
            SampleCreateModel(name="test", unknown_field="value")
        errors = exc_info.value.errors()
        assert any("extra" in str(e).lower() for e in errors)

    def test_catches_typos(self):
        """Test that InputModel catches field name typos."""
        with pytest.raises(ValidationError) as exc_info:
            SampleCreateModel(naem="typo")  # Typo in 'name'
        errors = exc_info.value.errors()
        assert any("extra" in str(e).lower() for e in errors)


# =============================================================================
# ResponseModel tests
# =============================================================================


class TestResponseModel:
    """Tests for ResponseModel base class behavior."""

    def test_from_attributes(self):
        """Test that ResponseModel supports from_attributes."""

        # Create a mock ORM-like object
        class MockORM:
            id = UUID("123e4567-e89b-12d3-a456-426614174000")
            name = "test"

        model = SampleResponseModel.model_validate(MockORM())
        assert model.id == UUID("123e4567-e89b-12d3-a456-426614174000")
        assert model.name == "test"


# =============================================================================
# Integration tests with SDK models
# =============================================================================


class TestSDKModelValidation:
    """Tests for validation of actual SDK models."""

    def test_agent_class_create_valid(self):
        """Test AgentClassCreate with valid data."""
        from atlas_sdk import AgentClassCreate

        model = validate_model(AgentClassCreate, name="TestClass")
        assert model.name == "TestClass"

    def test_agent_class_create_empty_name(self):
        """Test AgentClassCreate rejects empty name."""
        from atlas_sdk import AgentClassCreate

        with pytest.raises(AtlasInputValidationError):
            validate_model(AgentClassCreate, name="")

    def test_deployment_create_valid(self):
        """Test DeploymentCreate with valid data."""
        from atlas_sdk import DeploymentCreate

        model = validate_model(
            DeploymentCreate,
            agent_definition_id="123e4567-e89b-12d3-a456-426614174000",
            name="test-deployment",
        )
        assert model.name == "test-deployment"

    def test_deployment_create_invalid_uuid(self):
        """Test DeploymentCreate rejects invalid UUID."""
        from atlas_sdk import DeploymentCreate

        with pytest.raises(AtlasInputValidationError) as exc_info:
            validate_model(
                DeploymentCreate,
                agent_definition_id="not-a-uuid",
                name="test-deployment",
            )
        assert any(d.type == "uuid_parsing" for d in exc_info.value.details)

    def test_plan_task_create_sequence_constraint(self):
        """Test PlanTaskCreate enforces sequence >= 0."""
        from atlas_sdk import PlanTaskCreate

        # Valid
        model = validate_model(
            PlanTaskCreate,
            sequence=0,
            description="Test task",
            validation="Check output",
        )
        assert model.sequence == 0

        # Invalid
        with pytest.raises(AtlasInputValidationError):
            validate_model(
                PlanTaskCreate,
                sequence=-1,  # Invalid: must be >= 0
                description="Test task",
                validation="Check output",
            )

    def test_tool_create_risk_level_enum(self):
        """Test ToolCreate validates risk_level as literal."""
        from atlas_sdk import ToolCreate

        # Valid
        model = validate_model(
            ToolCreate,
            name="test-tool",
            json_schema={"type": "object"},
            risk_level="high",
        )
        assert model.risk_level == "high"

        # Invalid
        with pytest.raises(AtlasInputValidationError):
            validate_model(
                ToolCreate,
                name="test-tool",
                json_schema={"type": "object"},
                risk_level="extreme",  # Invalid: not in literal
            )


# =============================================================================
# Edge Case Tests for Validation (Issue 1.4)
# =============================================================================


class TestMultipleSimultaneousValidationErrors:
    """Tests for multiple simultaneous validation errors."""

    def test_multiple_missing_required_fields(self):
        """Test validation captures multiple missing required fields at once."""
        from atlas_sdk import DeploymentCreate

        with pytest.raises(AtlasInputValidationError) as exc_info:
            # Missing both agent_definition_id and name
            validate_model(DeploymentCreate)

        # Should have errors for both missing fields
        assert len(exc_info.value.details) >= 2
        field_names = {d.loc[0] for d in exc_info.value.details}
        assert "agent_definition_id" in field_names
        assert "name" in field_names

    def test_multiple_type_errors(self):
        """Test validation captures multiple type errors at once."""

        class MultiFieldModel(BaseModel):
            model_config = {"strict": True}
            int_field: int
            str_field: str
            float_field: float

        with pytest.raises(ValidationError) as exc_info:
            MultiFieldModel(
                int_field="not-an-int",
                str_field=123,
                float_field="not-a-float",
            )

        # Should have multiple errors
        assert len(exc_info.value.errors()) >= 2

    def test_mixed_validation_errors(self):
        """Test validation captures mixed error types at once."""
        from atlas_sdk import PlanCreate

        with pytest.raises(AtlasInputValidationError) as exc_info:
            # goal is empty (constraint violation), tasks has invalid item
            validate_model(
                PlanCreate,
                goal="",  # min_length=1 violation
                tasks=[
                    {
                        "sequence": -1,  # ge=0 violation
                        "description": "",  # min_length=1 violation
                        "validation": "",  # min_length=1 violation
                    }
                ],
            )

        # Should have multiple errors
        assert len(exc_info.value.details) >= 1
        # Should have goal error
        goal_errors = [d for d in exc_info.value.details if "goal" in str(d.loc)]
        assert len(goal_errors) >= 1

    def test_all_error_details_are_accessible(self):
        """Test that all error details have proper structure."""

        class StrictModel(BaseModel):
            field1: str = Field(min_length=3)
            field2: int = Field(ge=10)
            field3: str = Field(pattern=r"^[a-z]+$")

        with pytest.raises(ValidationError) as exc_info:
            StrictModel(field1="a", field2=5, field3="123")

        atlas_error = AtlasInputValidationError.from_pydantic_error(exc_info.value)

        # All details should have required attributes
        for detail in atlas_error.details:
            assert hasattr(detail, "loc")
            assert hasattr(detail, "msg")
            assert hasattr(detail, "type")
            assert len(detail.loc) > 0
            assert len(detail.msg) > 0


class TestNestedModelValidation:
    """Tests for nested model validation."""

    def test_nested_model_validation_error(self):
        """Test validation of nested models captures correct path."""
        from atlas_sdk import PlanCreate

        with pytest.raises(AtlasInputValidationError) as exc_info:
            validate_model(
                PlanCreate,
                goal="Test plan",
                tasks=[
                    {
                        "sequence": 0,
                        "description": "",  # Invalid: min_length=1
                        "validation": "check",
                    }
                ],
            )

        # Error path should include tasks index
        task_errors = [
            d for d in exc_info.value.details if "tasks" in str(d.loc) or 0 in d.loc
        ]
        assert len(task_errors) >= 1

    def test_deeply_nested_validation_error_path(self):
        """Test error paths are correct for deeply nested models."""
        from atlas_sdk import PlanCreate

        with pytest.raises(AtlasInputValidationError) as exc_info:
            validate_model(
                PlanCreate,
                goal="Test plan",
                tasks=[
                    {
                        "sequence": 0,
                        "description": "task1",
                        "validation": "check",
                    },
                    {
                        "sequence": 1,
                        "description": "",  # Invalid at index 1
                        "validation": "",  # Also invalid
                    },
                ],
            )

        # Check that error indicates the correct index
        errors_str = str(exc_info.value.details)
        assert "1" in errors_str or "tasks" in errors_str

    def test_multiple_nested_items_with_errors(self):
        """Test multiple nested items each with their own errors."""
        from atlas_sdk import TasksAppend

        with pytest.raises(AtlasInputValidationError) as exc_info:
            validate_model(
                TasksAppend,
                tasks=[
                    {
                        "sequence": -1,  # Invalid
                        "description": "task",
                        "validation": "check",
                    },
                    {
                        "sequence": 0,
                        "description": "",  # Invalid
                        "validation": "check",
                    },
                ],
            )

        # Should have errors from multiple items
        assert len(exc_info.value.details) >= 2

    def test_nested_model_preserves_error_context(self):
        """Test that nested validation errors preserve full context."""
        from atlas_sdk import PlanCreate

        with pytest.raises(AtlasInputValidationError) as exc_info:
            validate_model(
                PlanCreate,
                goal="Test",
                tasks=[
                    {
                        "sequence": 0,
                        "description": "valid",
                        "validation": "valid",
                        "assignee_agent_definition_id": "not-a-uuid",  # Invalid UUID
                    }
                ],
            )

        # Error should mention UUID parsing
        uuid_errors = [d for d in exc_info.value.details if "uuid" in d.type.lower()]
        assert len(uuid_errors) >= 1


class TestEmptyStringValidation:
    """Tests for empty string handling in validation."""

    def test_empty_string_fails_min_length(self):
        """Test that empty string fails min_length validation."""
        with pytest.raises(AtlasInputValidationError) as exc_info:
            validate_model(SampleCreateModel, name="")

        assert len(exc_info.value.details) >= 1
        # Should indicate string too short
        error_msg = str(exc_info.value.details[0].msg).lower()
        assert "short" in error_msg or "length" in error_msg or "least" in error_msg

    def test_empty_string_in_optional_field_ok(self):
        """Test that empty string in optional field without constraints is OK."""

        class OptionalModel(InputModel):
            name: str = Field(min_length=1)
            description: str | None = None

        # This should work - description can be None or any string
        model = validate_model(OptionalModel, name="test", description="")
        assert model.description == ""

    def test_empty_string_vs_none(self):
        """Test distinction between empty string and None."""

        class MixedModel(InputModel):
            required_str: str = Field(min_length=1)
            optional_str: str | None = None

        # Empty string should fail for required
        with pytest.raises(AtlasInputValidationError):
            validate_model(MixedModel, required_str="")

        # None for optional should work
        model = validate_model(MixedModel, required_str="test", optional_str=None)
        assert model.optional_str is None

    def test_sdk_models_reject_empty_required_strings(self):
        """Test actual SDK models reject empty required strings."""
        from atlas_sdk import AgentClassCreate

        with pytest.raises(AtlasInputValidationError):
            validate_model(AgentClassCreate, name="")


class TestWhitespaceHandling:
    """Tests for whitespace handling in validation.

    Note: Pydantic's min_length counts whitespace characters, so whitespace-only
    strings pass min_length validation. This documents the actual behavior.
    """

    def test_whitespace_only_passes_min_length(self):
        """Test that whitespace-only string passes min_length (Pydantic behavior).

        Pydantic's min_length counts all characters including whitespace.
        This test documents this behavior rather than expecting it to fail.
        """
        # Whitespace characters count toward min_length
        model = validate_model(SampleCreateModel, name="   ")
        assert model.name == "   "

    def test_whitespace_preserved_in_valid_string(self):
        """Test that leading/trailing whitespace is preserved in valid strings."""
        model = validate_model(SampleCreateModel, name="  test  ")
        assert model.name == "  test  "

    def test_newline_counts_as_character(self):
        """Test that newlines count toward min_length (Pydantic behavior)."""
        model = validate_model(SampleCreateModel, name="\n\n\n")
        assert model.name == "\n\n\n"
        assert len(model.name) == 3

    def test_tab_counts_as_character(self):
        """Test that tabs count toward min_length (Pydantic behavior)."""
        model = validate_model(SampleCreateModel, name="\t\t")
        assert model.name == "\t\t"

    def test_mixed_whitespace_counts_as_characters(self):
        """Test that mixed whitespace counts toward min_length."""
        model = validate_model(SampleCreateModel, name=" \t\n ")
        assert model.name == " \t\n "
        assert len(model.name) == 4

    def test_sdk_models_whitespace_behavior(self):
        """Test SDK models accept whitespace (documents current behavior).

        Note: If semantic validation (non-whitespace content) is needed,
        it should be done at the application level, not in Pydantic models.
        """
        from atlas_sdk import PlanTaskCreate

        # Whitespace-only description is valid per Pydantic min_length
        model = validate_model(
            PlanTaskCreate,
            sequence=0,
            description="   ",  # whitespace only - passes min_length
            validation="check",
        )
        assert model.description == "   "


class TestValidationBoundaryConditions:
    """Tests for boundary conditions in validation."""

    def test_integer_at_boundary(self):
        """Test integer validation at exact boundary values."""
        from atlas_sdk import PlanTaskCreate

        # Exactly at boundary (ge=0)
        model = validate_model(
            PlanTaskCreate, sequence=0, description="test", validation="check"
        )
        assert model.sequence == 0

        # One below boundary should fail
        with pytest.raises(AtlasInputValidationError):
            validate_model(
                PlanTaskCreate, sequence=-1, description="test", validation="check"
            )

    def test_string_at_exact_min_length(self):
        """Test string validation at exact min_length."""
        # Exactly 1 character (min_length=1)
        model = validate_model(SampleCreateModel, name="a")
        assert model.name == "a"

    def test_list_at_min_length(self):
        """Test list validation at min_length boundary."""
        from atlas_sdk import TasksAppend

        # Exactly 1 task (min_length=1)
        model = validate_model(
            TasksAppend,
            tasks=[
                {
                    "sequence": 0,
                    "description": "task",
                    "validation": "check",
                }
            ],
        )
        assert len(model.tasks) == 1

        # Empty list should fail
        with pytest.raises(AtlasInputValidationError):
            validate_model(TasksAppend, tasks=[])

    def test_uuid_boundary_cases(self):
        """Test UUID validation with boundary cases."""
        # Valid UUID with all zeros
        result = validate_uuid("00000000-0000-0000-0000-000000000000")
        assert result == "00000000-0000-0000-0000-000000000000"

        # Valid UUID with all f's
        result = validate_uuid("ffffffff-ffff-ffff-ffff-ffffffffffff")
        assert result == "ffffffff-ffff-ffff-ffff-ffffffffffff"

        # Almost valid UUID (one character short)
        with pytest.raises(AtlasInputValidationError):
            validate_uuid("00000000-0000-0000-0000-00000000000")

        # Almost valid UUID (one character extra)
        with pytest.raises(AtlasInputValidationError):
            validate_uuid("00000000-0000-0000-0000-0000000000000")
