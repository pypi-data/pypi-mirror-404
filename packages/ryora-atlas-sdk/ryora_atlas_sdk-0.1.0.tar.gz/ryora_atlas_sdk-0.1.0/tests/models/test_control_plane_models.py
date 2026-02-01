"""Tests for Atlas SDK control plane models."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from atlas_sdk.models.control_plane.agent_class import (
    AgentClassCreate,
    AgentClassRead,
    AgentClassUpdate,
)
from atlas_sdk.models.control_plane.grasp import (
    BlueprintCreate,
    BlueprintRead,
    BlueprintUpdate,
    GraspAnalysisCreate,
    GraspAnalysisRead,
    GraspAnalysisSummary,
)
from atlas_sdk.models.control_plane.model_provider import (
    ModelProviderCreate,
    ModelProviderRead,
    ModelProviderUpdate,
)
from atlas_sdk.models.control_plane.system_prompt import (
    SystemPromptCreate,
    SystemPromptRead,
    SystemPromptUpdate,
)
from atlas_sdk.models.control_plane.tool import (
    ToolCreate,
    ToolRead,
    ToolSyncRequest,
    ToolUpdate,
)
from atlas_sdk.models.enums import (
    GraspAnalysisStatus,
    SystemPromptStatus,
    SystemPromptStorageType,
)


class TestAgentClassCreate:
    """Tests for AgentClassCreate model."""

    def test_valid_creation(self) -> None:
        """Should create with required fields."""
        model = AgentClassCreate(name="BugHunter")
        assert model.name == "BugHunter"
        assert model.description is None

    def test_with_description(self) -> None:
        """Should accept description."""
        model = AgentClassCreate(
            name="BugHunter",
            description="Finds security bugs",
        )
        assert model.description == "Finds security bugs"

    def test_missing_name(self) -> None:
        """Should reject creation without name."""
        with pytest.raises(ValidationError) as exc_info:
            AgentClassCreate()  # type: ignore[call-arg]

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("name",) for e in errors)


class TestAgentClassRead:
    """Tests for AgentClassRead model."""

    def test_valid_creation(self) -> None:
        """Should create with all required fields."""
        now = datetime.now(timezone.utc)
        model = AgentClassRead(
            id=uuid4(),
            name="TestClass",
            created_at=now,
            updated_at=now,
        )
        assert model.name == "TestClass"
        assert model.description is None

    def test_from_attributes_config(self) -> None:
        """Should have from_attributes=True in config."""
        assert AgentClassRead.model_config.get("from_attributes") is True


class TestAgentClassUpdate:
    """Tests for AgentClassUpdate model."""

    def test_all_fields_optional(self) -> None:
        """Should allow empty update."""
        model = AgentClassUpdate()
        assert model.name is None
        assert model.description is None

    def test_partial_update(self) -> None:
        """Should allow partial updates."""
        model = AgentClassUpdate(name="NewName")
        assert model.name == "NewName"


class TestSystemPromptCreate:
    """Tests for SystemPromptCreate model."""

    def test_valid_minimal_creation(self) -> None:
        """Should create with required fields only."""
        model = SystemPromptCreate(
            name="Test Prompt",
            content="You are a helpful assistant.",
        )
        assert model.status == SystemPromptStatus.DRAFT
        assert model.content_storage_type == SystemPromptStorageType.INLINE

    def test_valid_full_creation(self) -> None:
        """Should create with all fields."""
        model = SystemPromptCreate(
            name="Production Prompt",
            description="Main system prompt",
            status=SystemPromptStatus.PUBLISHED,
            content="You are an expert.",
            content_storage_type=SystemPromptStorageType.S3,
            meta={"version": "1.0"},
            agent_class_id=uuid4(),
        )
        assert model.status == SystemPromptStatus.PUBLISHED
        assert model.content_storage_type == SystemPromptStorageType.S3

    def test_missing_required_fields(self) -> None:
        """Should reject creation without required fields."""
        with pytest.raises(ValidationError):
            SystemPromptCreate(name="Test")  # type: ignore[call-arg]


class TestSystemPromptRead:
    """Tests for SystemPromptRead model."""

    def test_valid_creation(self) -> None:
        """Should create with all required fields."""
        now = datetime.now(timezone.utc)
        model = SystemPromptRead(
            id=uuid4(),
            name="Test Prompt",
            content="Test content",
            status=SystemPromptStatus.DRAFT,
            content_storage_type=SystemPromptStorageType.INLINE,
            created_at=now,
            updated_at=now,
        )
        assert model.status == SystemPromptStatus.DRAFT

    def test_status_validation(self) -> None:
        """Should validate status enum."""
        now = datetime.now(timezone.utc)
        with pytest.raises(ValidationError):
            SystemPromptRead(
                id=uuid4(),
                name="Test",
                content="Content",
                status="active",  # type: ignore[arg-type]
                content_storage_type=SystemPromptStorageType.INLINE,
                created_at=now,
                updated_at=now,
            )


class TestSystemPromptUpdate:
    """Tests for SystemPromptUpdate model."""

    def test_all_fields_optional(self) -> None:
        """Should allow empty update."""
        model = SystemPromptUpdate()
        assert model.name is None
        assert model.status is None

    def test_status_transition(self) -> None:
        """Should allow status update."""
        model = SystemPromptUpdate(status=SystemPromptStatus.DEPRECATED)
        assert model.status == SystemPromptStatus.DEPRECATED


class TestModelProviderCreate:
    """Tests for ModelProviderCreate model."""

    def test_valid_minimal_creation(self) -> None:
        """Should create with required fields only."""
        model = ModelProviderCreate(name="OpenAI")
        assert model.name == "OpenAI"
        assert model.api_base_url is None
        assert model.config == {}

    def test_valid_full_creation(self) -> None:
        """Should create with all fields."""
        model = ModelProviderCreate(
            name="Local Ollama",
            api_base_url="http://localhost:11434",
            description="Local LLM",
            config={"timeout": 30},
        )
        assert model.api_base_url == "http://localhost:11434"

    def test_missing_name(self) -> None:
        """Should reject creation without name."""
        with pytest.raises(ValidationError):
            ModelProviderCreate()  # type: ignore[call-arg]


class TestModelProviderRead:
    """Tests for ModelProviderRead model."""

    def test_valid_creation(self) -> None:
        """Should create with all required fields."""
        now = datetime.now(timezone.utc)
        model = ModelProviderRead(
            id=uuid4(),
            name="TestProvider",
            created_at=now,
            updated_at=now,
        )
        assert model.config == {}


class TestModelProviderUpdate:
    """Tests for ModelProviderUpdate model."""

    def test_all_fields_optional(self) -> None:
        """Should allow empty update."""
        model = ModelProviderUpdate()
        assert model.name is None


class TestToolCreate:
    """Tests for ToolCreate model."""

    def test_valid_minimal_creation(self) -> None:
        """Should create with required fields only."""
        model = ToolCreate(
            name="read_file",
            json_schema={"type": "object", "properties": {}},
        )
        assert model.name == "read_file"
        assert model.risk_level == "low"

    def test_valid_full_creation(self) -> None:
        """Should create with all fields."""
        model = ToolCreate(
            name="execute_code",
            description="Execute arbitrary code",
            json_schema={
                "type": "object",
                "properties": {"code": {"type": "string"}},
            },
            safety_policy="Require user confirmation",
            risk_level="high",
        )
        assert model.risk_level == "high"
        assert model.safety_policy is not None

    def test_missing_json_schema(self) -> None:
        """Should reject creation without json_schema."""
        with pytest.raises(ValidationError):
            ToolCreate(name="test")  # type: ignore[call-arg]


class TestToolRead:
    """Tests for ToolRead model."""

    def test_valid_creation(self) -> None:
        """Should create with all required fields."""
        model = ToolRead(
            id=uuid4(),
            name="test_tool",
            json_schema={"type": "object"},
            risk_level="medium",
        )
        assert model.risk_level == "medium"


class TestToolUpdate:
    """Tests for ToolUpdate model."""

    def test_all_fields_optional(self) -> None:
        """Should allow empty update."""
        model = ToolUpdate()
        assert model.description is None
        assert model.json_schema is None


class TestToolSyncRequest:
    """Tests for ToolSyncRequest model."""

    def test_valid_creation(self) -> None:
        """Should create with tools list."""
        tools = [
            ToolCreate(name="t1", json_schema={}),
            ToolCreate(name="t2", json_schema={}),
        ]
        model = ToolSyncRequest(tools=tools)
        assert len(model.tools) == 2

    def test_missing_tools(self) -> None:
        """Should reject creation without tools."""
        with pytest.raises(ValidationError):
            ToolSyncRequest()  # type: ignore[call-arg]


class TestGraspAnalysisCreate:
    """Tests for GraspAnalysisCreate model."""

    def test_valid_creation(self) -> None:
        """Should create with default context."""
        model = GraspAnalysisCreate()
        assert model.analysis_context == {}

    def test_with_context(self) -> None:
        """Should accept analysis context."""
        model = GraspAnalysisCreate(analysis_context={"deployment_type": "production"})
        assert model.analysis_context["deployment_type"] == "production"


class TestGraspAnalysisRead:
    """Tests for GraspAnalysisRead model with Field constraints."""

    def test_valid_creation(self) -> None:
        """Should create with all required fields."""
        now = datetime.now(timezone.utc)
        model = GraspAnalysisRead(
            id=uuid4(),
            status=GraspAnalysisStatus.COMPLETED,
            created_at=now,
        )
        assert model.governance_value is None
        assert model.reach_value is None

    def test_valid_dimension_values_at_boundaries(self) -> None:
        """Should accept dimension values at boundaries (0 and 100)."""
        now = datetime.now(timezone.utc)
        model = GraspAnalysisRead(
            id=uuid4(),
            status=GraspAnalysisStatus.COMPLETED,
            governance_value=0,
            reach_value=100,
            agency_value=50,
            safeguards_value=75,
            potential_damage_value=25,
            created_at=now,
        )
        assert model.governance_value == 0
        assert model.reach_value == 100

    def test_reject_negative_dimension_value(self) -> None:
        """Should reject negative dimension values."""
        now = datetime.now(timezone.utc)
        with pytest.raises(ValidationError) as exc_info:
            GraspAnalysisRead(
                id=uuid4(),
                status=GraspAnalysisStatus.COMPLETED,
                governance_value=-1,
                created_at=now,
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("governance_value",) for e in errors)
        assert any("greater than or equal to 0" in str(e) for e in errors)

    def test_reject_dimension_value_over_100(self) -> None:
        """Should reject dimension values over 100."""
        now = datetime.now(timezone.utc)
        with pytest.raises(ValidationError) as exc_info:
            GraspAnalysisRead(
                id=uuid4(),
                status=GraspAnalysisStatus.COMPLETED,
                reach_value=101,
                created_at=now,
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("reach_value",) for e in errors)

    def test_reject_all_dimensions_over_100(self) -> None:
        """Should reject all dimension fields when over 100."""
        now = datetime.now(timezone.utc)
        dimension_fields = [
            "governance_value",
            "reach_value",
            "agency_value",
            "safeguards_value",
            "potential_damage_value",
        ]

        for field in dimension_fields:
            with pytest.raises(ValidationError):
                GraspAnalysisRead(
                    id=uuid4(),
                    status=GraspAnalysisStatus.COMPLETED,
                    created_at=now,
                    **{field: 150},
                )

    def test_status_validation(self) -> None:
        """Should validate status enum."""
        now = datetime.now(timezone.utc)
        with pytest.raises(ValidationError):
            GraspAnalysisRead(
                id=uuid4(),
                status="done",  # type: ignore[arg-type]
                created_at=now,
            )


class TestGraspAnalysisSummary:
    """Tests for GraspAnalysisSummary model."""

    def test_valid_creation(self) -> None:
        """Should create with required fields."""
        now = datetime.now(timezone.utc)
        model = GraspAnalysisSummary(
            id=uuid4(),
            status=GraspAnalysisStatus.IN_PROGRESS,
            created_at=now,
        )
        assert model.governance_value is None

    def test_does_not_have_field_constraints(self) -> None:
        """Summary model does not enforce ge/le constraints on values."""
        # Note: GraspAnalysisSummary doesn't have Field constraints
        # but values should still be validated if they match the type
        now = datetime.now(timezone.utc)
        model = GraspAnalysisSummary(
            id=uuid4(),
            status=GraspAnalysisStatus.COMPLETED,
            governance_value=50,
            created_at=now,
        )
        assert model.governance_value == 50


class TestBlueprintCreate:
    """Tests for BlueprintCreate model."""

    def test_valid_minimal_creation(self) -> None:
        """Should create with required fields only."""
        model = BlueprintCreate(name="Test Blueprint")
        assert model.name == "Test Blueprint"
        assert model.registered is False
        assert model.agent_definition_ids == []

    def test_valid_full_creation(self) -> None:
        """Should create with all fields."""
        model = BlueprintCreate(
            name="Production Blueprint",
            description="Main blueprint",
            nomad_job_definition={"job": "config"},
            entrypoint_script="#!/bin/bash\nstart.sh",
            docker_image="atlas/agent:latest",
            registered=True,
            agent_definition_ids=[uuid4(), uuid4()],
        )
        assert model.registered is True
        assert len(model.agent_definition_ids) == 2


class TestBlueprintRead:
    """Tests for BlueprintRead model."""

    def test_valid_creation(self) -> None:
        """Should create with all required fields."""
        now = datetime.now(timezone.utc)
        model = BlueprintRead(
            id=uuid4(),
            name="Test",
            registered=False,
            created_at=now,
            updated_at=now,
        )
        assert model.agent_definition_ids == []


class TestBlueprintUpdate:
    """Tests for BlueprintUpdate model."""

    def test_all_fields_optional(self) -> None:
        """Should allow empty update."""
        model = BlueprintUpdate()
        assert model.name is None
        assert model.registered is None

    def test_partial_update(self) -> None:
        """Should allow partial updates."""
        model = BlueprintUpdate(
            registered=True,
            agent_definition_ids=[uuid4()],
        )
        assert model.registered is True
        assert len(model.agent_definition_ids) == 1  # type: ignore[arg-type]
