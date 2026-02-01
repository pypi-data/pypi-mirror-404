"""Tests for Atlas SDK enum models."""

import pytest
from pydantic import BaseModel, ValidationError

from atlas_sdk.models.enums import (
    AgentDefinitionStatus,
    AgentInstanceStatus,
    DeploymentStatus,
    ExecutionMode,
    GraspAnalysisStatus,
    PlanStatus,
    PlanTaskStatus,
    SystemPromptStatus,
    SystemPromptStorageType,
)


class TestAgentDefinitionStatus:
    """Tests for AgentDefinitionStatus enum."""

    def test_valid_values(self) -> None:
        """Should accept all valid status values."""
        assert AgentDefinitionStatus.DRAFT == "draft"
        assert AgentDefinitionStatus.PUBLISHED == "published"
        assert AgentDefinitionStatus.DEPRECATED == "deprecated"

    def test_all_values_are_strings(self) -> None:
        """All enum values should be strings."""
        for status in AgentDefinitionStatus:
            assert isinstance(status.value, str)

    def test_can_be_used_in_pydantic_model(self) -> None:
        """Should work as a Pydantic field type."""

        class TestModel(BaseModel):
            status: AgentDefinitionStatus

        model = TestModel(status=AgentDefinitionStatus.DRAFT)
        assert model.status == AgentDefinitionStatus.DRAFT

        # Should also accept string value
        model = TestModel(status="published")  # type: ignore[arg-type]
        assert model.status == AgentDefinitionStatus.PUBLISHED

    def test_rejects_invalid_value(self) -> None:
        """Should reject invalid status values."""

        class TestModel(BaseModel):
            status: AgentDefinitionStatus

        with pytest.raises(ValidationError) as exc_info:
            TestModel(status="invalid")  # type: ignore[arg-type]

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "enum"


class TestExecutionMode:
    """Tests for ExecutionMode enum."""

    def test_valid_values(self) -> None:
        """Should accept all valid execution modes."""
        assert ExecutionMode.STATEFUL == "stateful"
        assert ExecutionMode.EPHEMERAL == "ephemeral"

    def test_can_be_used_in_pydantic_model(self) -> None:
        """Should work as a Pydantic field type."""

        class TestModel(BaseModel):
            mode: ExecutionMode

        model = TestModel(mode=ExecutionMode.STATEFUL)
        assert model.mode == ExecutionMode.STATEFUL

        model = TestModel(mode="ephemeral")  # type: ignore[arg-type]
        assert model.mode == ExecutionMode.EPHEMERAL

    def test_rejects_invalid_value(self) -> None:
        """Should reject invalid execution mode values."""

        class TestModel(BaseModel):
            mode: ExecutionMode

        with pytest.raises(ValidationError):
            TestModel(mode="hybrid")  # type: ignore[arg-type]


class TestDeploymentStatus:
    """Tests for DeploymentStatus enum."""

    def test_valid_values(self) -> None:
        """Should accept all valid deployment status values."""
        assert DeploymentStatus.SPAWNING == "spawning"
        assert DeploymentStatus.ACTIVE == "active"
        assert DeploymentStatus.COMPLETED == "completed"
        assert DeploymentStatus.FAILED == "failed"

    def test_has_expected_count(self) -> None:
        """Should have exactly 4 status values."""
        assert len(DeploymentStatus) == 4

    def test_rejects_invalid_value(self) -> None:
        """Should reject invalid deployment status values."""

        class TestModel(BaseModel):
            status: DeploymentStatus

        with pytest.raises(ValidationError):
            TestModel(status="pending")  # type: ignore[arg-type]


class TestAgentInstanceStatus:
    """Tests for AgentInstanceStatus enum."""

    def test_valid_values(self) -> None:
        """Should accept all valid agent instance status values."""
        assert AgentInstanceStatus.SPAWNING == "spawning"
        assert AgentInstanceStatus.ACTIVE == "active"
        assert AgentInstanceStatus.COMPLETED == "completed"
        assert AgentInstanceStatus.FAILED == "failed"
        assert AgentInstanceStatus.CANCELLED == "cancelled"

    def test_has_expected_count(self) -> None:
        """Should have exactly 5 status values."""
        assert len(AgentInstanceStatus) == 5


class TestPlanStatus:
    """Tests for PlanStatus enum."""

    def test_valid_values(self) -> None:
        """Should accept all valid plan status values (uppercase)."""
        assert PlanStatus.DRAFT == "DRAFT"
        assert PlanStatus.ACTIVE == "ACTIVE"
        assert PlanStatus.COMPLETED == "COMPLETED"
        assert PlanStatus.FAILED == "FAILED"
        assert PlanStatus.CANCELLED == "CANCELLED"

    def test_has_expected_count(self) -> None:
        """Should have exactly 5 status values."""
        assert len(PlanStatus) == 5

    def test_values_are_uppercase(self) -> None:
        """Plan status values should be uppercase."""
        for status in PlanStatus:
            assert status.value == status.value.upper()


class TestPlanTaskStatus:
    """Tests for PlanTaskStatus enum."""

    def test_valid_values(self) -> None:
        """Should accept all valid plan task status values."""
        assert PlanTaskStatus.PENDING == "PENDING"
        assert PlanTaskStatus.IN_PROGRESS == "IN_PROGRESS"
        assert PlanTaskStatus.COMPLETED == "COMPLETED"
        assert PlanTaskStatus.FAILED == "FAILED"
        assert PlanTaskStatus.SKIPPED == "SKIPPED"

    def test_has_expected_count(self) -> None:
        """Should have exactly 5 status values."""
        assert len(PlanTaskStatus) == 5


class TestSystemPromptStatus:
    """Tests for SystemPromptStatus enum."""

    def test_valid_values(self) -> None:
        """Should accept all valid system prompt status values."""
        assert SystemPromptStatus.DRAFT == "draft"
        assert SystemPromptStatus.PUBLISHED == "published"
        assert SystemPromptStatus.DEPRECATED == "deprecated"

    def test_matches_agent_definition_status_values(self) -> None:
        """System prompt status values should match agent definition status values."""
        # Both use the same lifecycle: draft -> published -> deprecated
        assert SystemPromptStatus.DRAFT.value == AgentDefinitionStatus.DRAFT.value
        assert (
            SystemPromptStatus.PUBLISHED.value == AgentDefinitionStatus.PUBLISHED.value
        )
        assert (
            SystemPromptStatus.DEPRECATED.value
            == AgentDefinitionStatus.DEPRECATED.value
        )


class TestSystemPromptStorageType:
    """Tests for SystemPromptStorageType enum."""

    def test_valid_values(self) -> None:
        """Should accept all valid storage type values."""
        assert SystemPromptStorageType.INLINE == "inline"
        assert SystemPromptStorageType.S3 == "s3"

    def test_has_expected_count(self) -> None:
        """Should have exactly 2 storage types."""
        assert len(SystemPromptStorageType) == 2


class TestGraspAnalysisStatus:
    """Tests for GraspAnalysisStatus enum."""

    def test_valid_values(self) -> None:
        """Should accept all valid GRASP analysis status values."""
        assert GraspAnalysisStatus.PENDING == "pending"
        assert GraspAnalysisStatus.IN_PROGRESS == "in_progress"
        assert GraspAnalysisStatus.COMPLETED == "completed"
        assert GraspAnalysisStatus.FAILED == "failed"

    def test_has_expected_count(self) -> None:
        """Should have exactly 4 status values."""
        assert len(GraspAnalysisStatus) == 4

    def test_rejects_invalid_value(self) -> None:
        """Should reject invalid GRASP analysis status values."""

        class TestModel(BaseModel):
            status: GraspAnalysisStatus

        with pytest.raises(ValidationError):
            TestModel(status="cancelled")  # type: ignore[arg-type]
