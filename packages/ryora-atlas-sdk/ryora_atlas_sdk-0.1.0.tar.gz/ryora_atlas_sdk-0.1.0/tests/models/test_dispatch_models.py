"""Tests for Atlas SDK dispatch models."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from atlas_sdk.models.dispatch.schemas import (
    A2ACallRequest,
    A2ACallResponse,
    A2ADirectoryResponse,
    AgentDirectoryEntry,
    AgentStatusResponse,
    SpawnRequest,
    SpawnResponse,
    StopResponse,
    WaitResponse,
)


class TestSpawnRequest:
    """Tests for SpawnRequest model."""

    def test_valid_creation(self) -> None:
        """Should create with all required fields."""
        model = SpawnRequest(
            agent_definition_id=uuid4(),
            deployment_id=uuid4(),
            prompt="Hello, agent!",
        )
        assert model.prompt == "Hello, agent!"

    def test_missing_required_fields(self) -> None:
        """Should reject creation without required fields."""
        with pytest.raises(ValidationError) as exc_info:
            SpawnRequest(prompt="Hello")  # type: ignore[call-arg]

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("agent_definition_id",) for e in errors)
        assert any(e["loc"] == ("deployment_id",) for e in errors)

    def test_uuid_string_coercion(self) -> None:
        """Should coerce valid UUID strings."""
        model = SpawnRequest(
            agent_definition_id="12345678-1234-5678-1234-567812345678",  # type: ignore[arg-type]
            deployment_id="87654321-4321-8765-4321-876543218765",  # type: ignore[arg-type]
            prompt="Test",
        )
        assert str(model.agent_definition_id) == "12345678-1234-5678-1234-567812345678"


class TestSpawnResponse:
    """Tests for SpawnResponse model."""

    def test_valid_creation(self) -> None:
        """Should create with all required fields."""
        model = SpawnResponse(
            status="running",
            port=8080,
            pid=12345,
            url="http://localhost:8080",
            deployment_id=uuid4(),
            instance_id=uuid4(),
        )
        assert model.status == "running"
        assert model.port == 8080
        assert model.pid == 12345

    def test_from_attributes_config(self) -> None:
        """Should have from_attributes=True in config."""
        assert SpawnResponse.model_config.get("from_attributes") is True

    def test_missing_required_fields(self) -> None:
        """Should reject creation without required fields."""
        with pytest.raises(ValidationError):
            SpawnResponse(status="running")  # type: ignore[call-arg]


class TestAgentStatusResponse:
    """Tests for AgentStatusResponse model."""

    def test_valid_creation_running(self) -> None:
        """Should create for running agent."""
        model = AgentStatusResponse(
            definition_id=uuid4(),
            instance_id=uuid4(),
            port=8080,
            pid=12345,
            running=True,
        )
        assert model.running is True

    def test_valid_creation_not_running(self) -> None:
        """Should create for non-running agent."""
        model = AgentStatusResponse(
            definition_id=uuid4(),
            running=False,
        )
        assert model.running is False
        assert model.instance_id is None
        assert model.port is None
        assert model.pid is None


class TestStopResponse:
    """Tests for StopResponse model."""

    def test_valid_creation(self) -> None:
        """Should create with required fields."""
        model = StopResponse(
            status="stopped",
            message="Agent stopped successfully",
        )
        assert model.status == "stopped"

    def test_missing_required_fields(self) -> None:
        """Should reject creation without required fields."""
        with pytest.raises(ValidationError):
            StopResponse(status="stopped")  # type: ignore[call-arg]


class TestWaitResponse:
    """Tests for WaitResponse model."""

    def test_valid_creation_success(self) -> None:
        """Should create for successful completion."""
        model = WaitResponse(
            status="completed",
            instance_id=uuid4(),
            output={"result": "success"},
            exit_code=0,
        )
        assert model.status == "completed"
        assert model.exit_code == 0
        assert model.error is None

    def test_valid_creation_failure(self) -> None:
        """Should create for failed completion."""
        model = WaitResponse(
            status="failed",
            instance_id=uuid4(),
            error="Task timed out",
            exit_code=1,
        )
        assert model.status == "failed"
        assert model.error == "Task timed out"

    def test_output_defaults_to_none(self) -> None:
        """Output should default to None."""
        model = WaitResponse(
            status="completed",
            instance_id=uuid4(),
        )
        assert model.output is None


class TestA2ACallRequest:
    """Tests for A2ACallRequest model."""

    def test_valid_minimal_creation(self) -> None:
        """Should create with required fields only."""
        model = A2ACallRequest(
            agent_definition_id=uuid4(),
            prompt="Analyze this code",
        )
        assert model.routing_key is None

    def test_valid_full_creation(self) -> None:
        """Should create with all fields."""
        model = A2ACallRequest(
            agent_definition_id=uuid4(),
            prompt="Analyze this code",
            routing_key="deployment-123",
        )
        assert model.routing_key == "deployment-123"

    def test_missing_required_fields(self) -> None:
        """Should reject creation without required fields."""
        with pytest.raises(ValidationError):
            A2ACallRequest(prompt="Hello")  # type: ignore[call-arg]


class TestA2ACallResponse:
    """Tests for A2ACallResponse model."""

    def test_valid_creation(self) -> None:
        """Should create with required fields."""
        model = A2ACallResponse(
            content="Analysis complete: no issues found",
            instance_id=uuid4(),
        )
        assert model.metadata is None

    def test_with_metadata(self) -> None:
        """Should accept metadata."""
        model = A2ACallResponse(
            content="Result",
            instance_id=uuid4(),
            metadata={"tokens_used": 150},
        )
        assert model.metadata["tokens_used"] == 150  # type: ignore[index]


class TestAgentDirectoryEntry:
    """Tests for AgentDirectoryEntry model."""

    def test_valid_creation(self) -> None:
        """Should create with all required fields."""
        model = AgentDirectoryEntry(
            agent_definition_id=uuid4(),
            instance_id=uuid4(),
            url="http://localhost:8080",
            port=8080,
            running=True,
            slug="bug-hunter",
            agent_class_id=uuid4(),
            execution_mode="ephemeral",
            allow_outbound_a2a=False,
        )
        assert model.slug == "bug-hunter"
        assert model.running is True

    def test_missing_required_fields(self) -> None:
        """Should reject creation without required fields."""
        with pytest.raises(ValidationError):
            AgentDirectoryEntry(
                agent_definition_id=uuid4(),
                running=True,
            )  # type: ignore[call-arg]


class TestA2ADirectoryResponse:
    """Tests for A2ADirectoryResponse model with nested models."""

    def test_valid_creation_empty(self) -> None:
        """Should create with empty agents list."""
        model = A2ADirectoryResponse(
            agents=[],
            deployment_id=uuid4(),
        )
        assert len(model.agents) == 0

    def test_valid_creation_with_agents(self) -> None:
        """Should create with populated agents list."""
        agent = AgentDirectoryEntry(
            agent_definition_id=uuid4(),
            instance_id=uuid4(),
            url="http://localhost:8080",
            port=8080,
            running=True,
            slug="test-agent",
            agent_class_id=uuid4(),
            execution_mode="stateful",
            allow_outbound_a2a=True,
        )
        model = A2ADirectoryResponse(
            agents=[agent],
            deployment_id=uuid4(),
        )
        assert len(model.agents) == 1
        assert model.agents[0].slug == "test-agent"

    def test_nested_model_validation(self) -> None:
        """Should validate nested model structure."""
        # Invalid nested agent entry
        with pytest.raises(ValidationError):
            A2ADirectoryResponse(
                agents=[{"invalid": "data"}],  # type: ignore[list-item]
                deployment_id=uuid4(),
            )

    def test_serialization_with_nested_models(self) -> None:
        """Should serialize nested models correctly."""
        agent = AgentDirectoryEntry(
            agent_definition_id=uuid4(),
            instance_id=uuid4(),
            url="http://localhost:8080",
            port=8080,
            running=True,
            slug="test",
            agent_class_id=uuid4(),
            execution_mode="ephemeral",
            allow_outbound_a2a=False,
        )
        model = A2ADirectoryResponse(
            agents=[agent],
            deployment_id=uuid4(),
        )

        data = model.model_dump()
        assert "agents" in data
        assert len(data["agents"]) == 1
        assert data["agents"][0]["slug"] == "test"

    def test_from_attributes_config(self) -> None:
        """Should have from_attributes=True in config."""
        assert A2ADirectoryResponse.model_config.get("from_attributes") is True
