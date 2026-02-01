"""Unit tests for response parsing with various JSON payloads.

These tests validate that Pydantic models correctly parse API responses,
including edge cases like missing optional fields, type mismatches, and
malformed data.

This addresses issue 1.1 from the v0.1.0 release review: tests should
independently verify response parsing with various valid/invalid payloads.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from atlas_sdk.models.agent_definition import (
    AgentDefinitionConfig,
    AgentDefinitionRead,
)
from atlas_sdk.models.control_plane import (
    AgentClassRead,
    GraspAnalysisRead,
    ModelProviderRead,
    SystemPromptRead,
    ToolRead,
)
from atlas_sdk.models.deployment import DeploymentRead
from atlas_sdk.models.enums import (
    AgentDefinitionStatus,
    DeploymentStatus,
    ExecutionMode,
    GraspAnalysisStatus,
    SystemPromptStatus,
    SystemPromptStorageType,
)


class TestAgentClassReadParsing:
    """Test AgentClassRead model parsing."""

    def test_parse_full_response(self) -> None:
        """Parse response with all fields present."""
        agent_class_id = uuid4()
        now = datetime.now(timezone.utc)
        data = {
            "id": str(agent_class_id),
            "name": "BugHunter",
            "description": "Security vulnerability detection",
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

        result = AgentClassRead.model_validate(data)

        assert result.id == agent_class_id
        assert result.name == "BugHunter"
        assert result.description == "Security vulnerability detection"
        assert result.created_at == now
        assert result.updated_at == now

    def test_parse_with_optional_description_null(self) -> None:
        """Parse response with optional description as null."""
        agent_class_id = uuid4()
        now = datetime.now(timezone.utc)
        data = {
            "id": str(agent_class_id),
            "name": "MinimalClass",
            "description": None,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

        result = AgentClassRead.model_validate(data)

        assert result.id == agent_class_id
        assert result.name == "MinimalClass"
        assert result.description is None

    def test_parse_with_optional_description_missing(self) -> None:
        """Parse response with optional description field absent."""
        agent_class_id = uuid4()
        now = datetime.now(timezone.utc)
        data = {
            "id": str(agent_class_id),
            "name": "MinimalClass",
            # description field not present
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

        result = AgentClassRead.model_validate(data)

        assert result.description is None

    def test_parse_missing_required_field_id(self) -> None:
        """Parsing fails when required 'id' field is missing."""
        now = datetime.now(timezone.utc)
        data = {
            "name": "BugHunter",
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

        with pytest.raises(ValidationError) as exc_info:
            AgentClassRead.model_validate(data)

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("id",)
        assert errors[0]["type"] == "missing"

    def test_parse_missing_required_field_name(self) -> None:
        """Parsing fails when required 'name' field is missing."""
        agent_class_id = uuid4()
        now = datetime.now(timezone.utc)
        data = {
            "id": str(agent_class_id),
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

        with pytest.raises(ValidationError) as exc_info:
            AgentClassRead.model_validate(data)

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("name",)

    def test_parse_invalid_uuid_format(self) -> None:
        """Parsing fails with invalid UUID format."""
        now = datetime.now(timezone.utc)
        data = {
            "id": "not-a-valid-uuid",
            "name": "BugHunter",
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

        with pytest.raises(ValidationError) as exc_info:
            AgentClassRead.model_validate(data)

        errors = exc_info.value.errors()
        assert errors[0]["loc"] == ("id",)
        assert "uuid" in errors[0]["type"].lower()

    def test_parse_invalid_datetime_format(self) -> None:
        """Parsing fails with invalid datetime format."""
        agent_class_id = uuid4()
        data = {
            "id": str(agent_class_id),
            "name": "BugHunter",
            "created_at": "not-a-datetime",
            "updated_at": "2024-01-01",  # This might work depending on Pydantic
        }

        with pytest.raises(ValidationError) as exc_info:
            AgentClassRead.model_validate(data)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("created_at",) for e in errors)

    def test_parse_wrong_type_for_name(self) -> None:
        """Parsing fails when name is wrong type (int instead of str)."""
        agent_class_id = uuid4()
        now = datetime.now(timezone.utc)
        data = {
            "id": str(agent_class_id),
            "name": 12345,  # Int, should be string
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

        # Pydantic v2 with strict string validation rejects int
        with pytest.raises(ValidationError) as exc_info:
            AgentClassRead.model_validate(data)

        errors = exc_info.value.errors()
        assert errors[0]["loc"] == ("name",)
        assert errors[0]["type"] == "string_type"


class TestAgentDefinitionReadParsing:
    """Test AgentDefinitionRead model parsing."""

    def test_parse_full_response(self) -> None:
        """Parse response with all fields present."""
        definition_id = uuid4()
        agent_class_id = uuid4()
        prompt_id = uuid4()
        provider_id = uuid4()
        now = datetime.now(timezone.utc)

        data = {
            "id": str(definition_id),
            "agent_class_id": str(agent_class_id),
            "system_prompt_id": str(prompt_id),
            "structured_output_id": None,
            "model_provider_id": str(provider_id),
            "name": "researcher-v1",
            "slug": "researcher-v1",
            "description": "Research agent definition",
            "status": "published",
            "execution_mode": "stateful",
            "model_name": "gpt-4",
            "config": {"temperature": 0.7},
            "allow_outbound_a2a": True,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

        result = AgentDefinitionRead.model_validate(data)

        assert result.id == definition_id
        assert result.agent_class_id == agent_class_id
        assert result.system_prompt_id == prompt_id
        assert result.model_provider_id == provider_id
        assert result.name == "researcher-v1"
        assert result.status == AgentDefinitionStatus.PUBLISHED
        assert result.execution_mode == ExecutionMode.STATEFUL
        assert result.config == {"temperature": 0.7}
        assert result.allow_outbound_a2a is True

    def test_parse_with_minimal_optional_fields(self) -> None:
        """Parse response with optional fields as null."""
        definition_id = uuid4()
        agent_class_id = uuid4()
        now = datetime.now(timezone.utc)

        data = {
            "id": str(definition_id),
            "agent_class_id": str(agent_class_id),
            "system_prompt_id": None,
            "structured_output_id": None,
            "model_provider_id": None,
            "name": "minimal-def",
            "slug": "minimal-def",
            "description": None,
            "status": "draft",
            "execution_mode": "ephemeral",
            "model_name": None,
            "config": {},
            "allow_outbound_a2a": False,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

        result = AgentDefinitionRead.model_validate(data)

        assert result.system_prompt_id is None
        assert result.model_provider_id is None
        assert result.description is None
        assert result.model_name is None
        assert result.config == {}

    def test_parse_invalid_status_enum(self) -> None:
        """Parsing fails with invalid status enum value."""
        definition_id = uuid4()
        agent_class_id = uuid4()
        now = datetime.now(timezone.utc)

        data = {
            "id": str(definition_id),
            "agent_class_id": str(agent_class_id),
            "name": "test",
            "slug": "test",
            "status": "invalid_status",  # Not a valid enum value
            "execution_mode": "ephemeral",
            "config": {},
            "allow_outbound_a2a": False,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

        with pytest.raises(ValidationError) as exc_info:
            AgentDefinitionRead.model_validate(data)

        errors = exc_info.value.errors()
        assert errors[0]["loc"] == ("status",)
        assert errors[0]["type"] == "enum"

    def test_parse_invalid_execution_mode_enum(self) -> None:
        """Parsing fails with invalid execution_mode enum value."""
        definition_id = uuid4()
        agent_class_id = uuid4()
        now = datetime.now(timezone.utc)

        data = {
            "id": str(definition_id),
            "agent_class_id": str(agent_class_id),
            "name": "test",
            "slug": "test",
            "status": "draft",
            "execution_mode": "invalid_mode",  # Not a valid enum value
            "config": {},
            "allow_outbound_a2a": False,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

        with pytest.raises(ValidationError) as exc_info:
            AgentDefinitionRead.model_validate(data)

        errors = exc_info.value.errors()
        assert errors[0]["loc"] == ("execution_mode",)


class TestDeploymentReadParsing:
    """Test DeploymentRead model parsing."""

    def test_parse_full_response(self) -> None:
        """Parse response with all fields present."""
        deployment_id = uuid4()
        definition_id = uuid4()
        blueprint_id = uuid4()
        now = datetime.now(timezone.utc)

        data = {
            "id": str(deployment_id),
            "agent_definition_id": str(definition_id),
            "blueprint_id": str(blueprint_id),
            "name": "prod-deployment",
            "description": "Production deployment",
            "environment": "production",
            "status": "active",
            "config": {"replicas": 3, "memory": "2Gi"},
            "project_context": {"team": "platform"},
            "spec_md_path": "/path/to/spec.md",
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

        result = DeploymentRead.model_validate(data)

        assert result.id == deployment_id
        assert result.agent_definition_id == definition_id
        assert result.blueprint_id == blueprint_id
        assert result.name == "prod-deployment"
        assert result.status == DeploymentStatus.ACTIVE
        assert result.config == {"replicas": 3, "memory": "2Gi"}
        assert result.project_context == {"team": "platform"}

    def test_parse_all_status_values(self) -> None:
        """Verify all DeploymentStatus enum values can be parsed."""
        base_data = {
            "id": str(uuid4()),
            "agent_definition_id": str(uuid4()),
            "name": "test",
            "environment": "test",
            "config": {},
            "project_context": {},
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        for status in DeploymentStatus:
            data = {**base_data, "status": status.value}
            result = DeploymentRead.model_validate(data)
            assert result.status == status

    def test_parse_invalid_status(self) -> None:
        """Parsing fails with invalid status value."""
        data = {
            "id": str(uuid4()),
            "agent_definition_id": str(uuid4()),
            "name": "test",
            "environment": "test",
            "status": "pending",  # Not a valid DeploymentStatus
            "config": {},
            "project_context": {},
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        with pytest.raises(ValidationError) as exc_info:
            DeploymentRead.model_validate(data)

        errors = exc_info.value.errors()
        assert errors[0]["loc"] == ("status",)

    def test_parse_complex_nested_config(self) -> None:
        """Parse response with deeply nested config object."""
        data = {
            "id": str(uuid4()),
            "agent_definition_id": str(uuid4()),
            "name": "test",
            "environment": "test",
            "status": "active",
            "config": {
                "resources": {
                    "limits": {"cpu": "2", "memory": "4Gi"},
                    "requests": {"cpu": "500m", "memory": "1Gi"},
                },
                "environment_variables": [
                    {
                        "name": "API_KEY",
                        "valueFrom": {"secretKeyRef": {"name": "api-secret"}},
                    },
                ],
            },
            "project_context": {},
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        result = DeploymentRead.model_validate(data)
        assert result.config["resources"]["limits"]["memory"] == "4Gi"


class TestSystemPromptReadParsing:
    """Test SystemPromptRead model parsing."""

    def test_parse_full_response(self) -> None:
        """Parse response with all fields present."""
        prompt_id = uuid4()
        agent_class_id = uuid4()
        now = datetime.now(timezone.utc)

        data = {
            "id": str(prompt_id),
            "agent_class_id": str(agent_class_id),
            "name": "security-researcher-prompt",
            "description": "A prompt for security research",
            "content": "You are a security researcher...",
            "status": "published",
            "content_storage_type": "inline",
            "meta": {"version": 2},
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

        result = SystemPromptRead.model_validate(data)

        assert result.id == prompt_id
        assert result.agent_class_id == agent_class_id
        assert result.status == SystemPromptStatus.PUBLISHED
        assert result.content_storage_type == SystemPromptStorageType.INLINE
        assert result.meta == {"version": 2}

    def test_parse_s3_storage_type(self) -> None:
        """Parse response with S3 storage type."""
        data = {
            "id": str(uuid4()),
            "agent_class_id": str(uuid4()),
            "name": "large-prompt",
            "content": "s3://bucket/prompts/large.txt",
            "status": "draft",
            "content_storage_type": "s3",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        result = SystemPromptRead.model_validate(data)
        assert result.content_storage_type == SystemPromptStorageType.S3


class TestToolReadParsing:
    """Test ToolRead model parsing."""

    def test_parse_full_response(self) -> None:
        """Parse response with all fields including JSON schema."""
        tool_id = uuid4()

        data = {
            "id": str(tool_id),
            "name": "read_file",
            "description": "Read contents of a file",
            "json_schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path"},
                    "encoding": {"type": "string", "default": "utf-8"},
                },
                "required": ["path"],
            },
            "safety_policy": "No destructive operations",
            "risk_level": "low",
        }

        result = ToolRead.model_validate(data)

        assert result.id == tool_id
        assert result.name == "read_file"
        assert result.json_schema["properties"]["path"]["type"] == "string"
        assert "path" in result.json_schema["required"]
        assert result.risk_level == "low"

    def test_parse_empty_json_schema(self) -> None:
        """Parse response with empty JSON schema."""
        data = {
            "id": str(uuid4()),
            "name": "simple_tool",
            "description": "A simple tool with no parameters",
            "json_schema": {},
            "risk_level": "low",
        }

        result = ToolRead.model_validate(data)
        assert result.json_schema == {}


class TestModelProviderReadParsing:
    """Test ModelProviderRead model parsing."""

    def test_parse_full_response(self) -> None:
        """Parse response with all fields present."""
        provider_id = uuid4()
        now = datetime.now(timezone.utc)

        data = {
            "id": str(provider_id),
            "name": "openai-prod",
            "api_base_url": "https://api.openai.com/v1",
            "description": "OpenAI production provider",
            "config": {"default_model": "gpt-4"},
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

        result = ModelProviderRead.model_validate(data)

        assert result.id == provider_id
        assert result.name == "openai-prod"
        assert result.api_base_url == "https://api.openai.com/v1"
        assert result.config == {"default_model": "gpt-4"}


class TestGraspAnalysisReadParsing:
    """Test GraspAnalysisRead model parsing."""

    def test_parse_full_response(self) -> None:
        """Parse response with all GRASP dimensions present."""
        analysis_id = uuid4()
        deployment_id = uuid4()
        now = datetime.now(timezone.utc)

        data = {
            "id": str(analysis_id),
            "deployment_id": str(deployment_id),
            "blueprint_id": None,
            "agent_definition_id": None,
            "status": "completed",
            # GRASP dimensions
            "governance_value": 85,
            "governance_summary": "High visibility and control",
            "governance_evidence": {"logs": True, "monitoring": True},
            "reach_value": 40,
            "reach_summary": "Limited scope",
            "reach_evidence": {},
            "agency_value": 60,
            "agency_summary": "Moderate autonomy",
            "agency_evidence": {},
            "safeguards_value": 90,
            "safeguards_summary": "Strong safeguards in place",
            "safeguards_evidence": {"rate_limiting": True},
            "potential_damage_value": 30,
            "potential_damage_summary": "Low risk",
            "potential_damage_evidence": {},
            "analysis_context": {"query": "analyze this"},
            "error_message": None,
            "created_at": now.isoformat(),
            "completed_at": now.isoformat(),
        }

        result = GraspAnalysisRead.model_validate(data)

        assert result.id == analysis_id
        assert result.deployment_id == deployment_id
        assert result.status == GraspAnalysisStatus.COMPLETED
        assert result.governance_value == 85
        assert result.safeguards_value == 90

    def test_parse_failed_analysis(self) -> None:
        """Parse response for a failed analysis with error message."""
        now = datetime.now(timezone.utc)
        data = {
            "id": str(uuid4()),
            "deployment_id": str(uuid4()),
            "status": "failed",
            "analysis_context": {"query": "analyze this"},
            "error_message": "Model timeout exceeded",
            "created_at": now.isoformat(),
            "completed_at": None,
        }

        result = GraspAnalysisRead.model_validate(data)

        assert result.status == GraspAnalysisStatus.FAILED
        assert result.error_message == "Model timeout exceeded"
        assert result.governance_value is None


class TestAgentDefinitionConfigParsing:
    """Test AgentDefinitionConfig model parsing."""

    def test_parse_full_config(self) -> None:
        """Parse full agent configuration for runtime."""
        config_id = uuid4()

        data = {
            "id": str(config_id),
            "name": "researcher-v1",
            "slug": "researcher-v1",
            "description": "Research agent",
            "status": "published",
            "execution_mode": "stateful",
            "model_name": "gpt-4",
            "config": {"temperature": 0.7, "max_tokens": 4096},
            "system_prompt": "You are a research assistant...",
            "structured_output_schema": {
                "type": "object",
                "properties": {"summary": {"type": "string"}},
            },
            "tools": [
                {"name": "search", "parameters_schema": {}},
                {"name": "read_file", "parameters_schema": {}},
            ],
        }

        result = AgentDefinitionConfig.model_validate(data)

        assert result.id == config_id
        assert result.status == AgentDefinitionStatus.PUBLISHED
        assert result.system_prompt == "You are a research assistant..."
        assert len(result.tools) == 2
        assert result.tools[0]["name"] == "search"

    def test_parse_minimal_config(self) -> None:
        """Parse minimal configuration with no tools or prompt."""
        data = {
            "id": str(uuid4()),
            "name": "minimal",
            "slug": "minimal",
            "description": None,
            "status": "draft",
            "execution_mode": "ephemeral",
            "model_name": None,
            "config": {},
            "system_prompt": None,
            "structured_output_schema": None,
            "tools": [],
        }

        result = AgentDefinitionConfig.model_validate(data)

        assert result.system_prompt is None
        assert result.structured_output_schema is None
        assert result.tools == []


class TestListResponseParsing:
    """Test parsing of list responses."""

    def test_parse_empty_list(self) -> None:
        """Parse empty list response."""
        data: list[dict] = []
        result = [AgentClassRead.model_validate(item) for item in data]
        assert result == []

    def test_parse_list_with_multiple_items(self) -> None:
        """Parse list with multiple items."""
        now = datetime.now(timezone.utc)
        data = [
            {
                "id": str(uuid4()),
                "name": "Class1",
                "description": "First class",
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
            },
            {
                "id": str(uuid4()),
                "name": "Class2",
                "description": None,
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
            },
            {
                "id": str(uuid4()),
                "name": "Class3",
                "description": "Third class",
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
            },
        ]

        result = [AgentClassRead.model_validate(item) for item in data]

        assert len(result) == 3
        assert result[0].name == "Class1"
        assert result[1].description is None
        assert result[2].name == "Class3"

    def test_parse_list_fails_on_invalid_item(self) -> None:
        """Parsing list fails if any item is invalid."""
        now = datetime.now(timezone.utc)
        data = [
            {
                "id": str(uuid4()),
                "name": "Valid",
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
            },
            {
                # Missing required 'id' field
                "name": "Invalid",
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
            },
        ]

        # First item succeeds
        AgentClassRead.model_validate(data[0])

        # Second item fails
        with pytest.raises(ValidationError):
            AgentClassRead.model_validate(data[1])


class TestMultipleValidationErrors:
    """Test handling of multiple validation errors."""

    def test_multiple_missing_fields(self) -> None:
        """Parsing reports all missing required fields."""
        data = {
            # Missing: id, name, created_at, updated_at
            "description": "Only optional field provided",
        }

        with pytest.raises(ValidationError) as exc_info:
            AgentClassRead.model_validate(data)

        errors = exc_info.value.errors()
        # Should report multiple missing fields
        assert len(errors) >= 3
        error_locs = {e["loc"][0] for e in errors}
        assert "id" in error_locs
        assert "name" in error_locs
        assert "created_at" in error_locs

    def test_multiple_type_errors(self) -> None:
        """Parsing reports multiple type errors."""
        data = {
            "id": "not-a-uuid",
            "agent_class_id": "also-not-a-uuid",
            "name": "test",
            "slug": "test",
            "status": "draft",
            "execution_mode": "ephemeral",
            "config": {},
            "allow_outbound_a2a": False,
            "created_at": "not-a-datetime",
            "updated_at": "also-not-a-datetime",
        }

        with pytest.raises(ValidationError) as exc_info:
            AgentDefinitionRead.model_validate(data)

        errors = exc_info.value.errors()
        # Should report multiple validation errors
        assert len(errors) >= 2
