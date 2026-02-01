"""Tests for Atlas SDK core models (agent_definition, agent_instance, deployment, plan)."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from atlas_sdk.models.agent_definition import (
    AgentDefinitionConfig,
    AgentDefinitionCreate,
    AgentDefinitionRead,
    AgentDefinitionUpdate,
)
from atlas_sdk.models.agent_instance import (
    AgentInstanceCreate,
    AgentInstanceRead,
    AgentInstanceUpdate,
)
from atlas_sdk.models.deployment import (
    DeploymentCreate,
    DeploymentRead,
    DeploymentUpdate,
)
from atlas_sdk.models.enums import (
    AgentDefinitionStatus,
    AgentInstanceStatus,
    DeploymentStatus,
    ExecutionMode,
    PlanStatus,
    PlanTaskStatus,
)
from atlas_sdk.models.plan import (
    PlanCreate,
    PlanCreateResponse,
    PlanRead,
    PlanReadWithTasks,
    PlanTaskCreate,
    PlanTaskRead,
    PlanTaskReadEnriched,
    PlanTaskUpdate,
    PlanUpdate,
    TasksAppend,
    TasksAppendResponse,
)


class TestAgentDefinitionCreate:
    """Tests for AgentDefinitionCreate model."""

    def test_valid_minimal_creation(self) -> None:
        """Should create with required fields only."""
        model = AgentDefinitionCreate(
            agent_class_id=uuid4(),
            name="Test Agent",
        )
        assert model.name == "Test Agent"
        assert model.description is None
        assert model.execution_mode == ExecutionMode.EPHEMERAL
        assert model.tool_ids == []

    def test_valid_full_creation(self) -> None:
        """Should create with all fields."""
        agent_class_id = uuid4()
        system_prompt_id = uuid4()
        tool_ids = [uuid4(), uuid4()]

        model = AgentDefinitionCreate(
            agent_class_id=agent_class_id,
            name="Full Agent",
            description="A test agent",
            system_prompt_id=system_prompt_id,
            structured_output_id=uuid4(),
            model_provider_id=uuid4(),
            model_name="gpt-4",
            execution_mode=ExecutionMode.STATEFUL,
            config={"temperature": 0.7},
            allow_outbound_a2a=True,
            tool_ids=tool_ids,
        )

        assert model.agent_class_id == agent_class_id
        assert model.execution_mode == ExecutionMode.STATEFUL
        assert model.allow_outbound_a2a is True
        assert len(model.tool_ids) == 2

    def test_missing_required_field_agent_class_id(self) -> None:
        """Should reject creation without agent_class_id."""
        with pytest.raises(ValidationError) as exc_info:
            AgentDefinitionCreate(name="Test")  # type: ignore[call-arg]

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("agent_class_id",) for e in errors)

    def test_missing_required_field_name(self) -> None:
        """Should reject creation without name."""
        with pytest.raises(ValidationError) as exc_info:
            AgentDefinitionCreate(agent_class_id=uuid4())  # type: ignore[call-arg]

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("name",) for e in errors)

    def test_invalid_uuid_format(self) -> None:
        """Should reject invalid UUID format."""
        with pytest.raises(ValidationError) as exc_info:
            AgentDefinitionCreate(
                agent_class_id="not-a-uuid",  # type: ignore[arg-type]
                name="Test",
            )

        errors = exc_info.value.errors()
        assert len(errors) >= 1

    def test_uuid_string_coercion(self) -> None:
        """Should coerce valid UUID strings to UUID objects."""
        uuid_str = "12345678-1234-5678-1234-567812345678"
        model = AgentDefinitionCreate(
            agent_class_id=uuid_str,  # type: ignore[arg-type]
            name="Test",
        )
        assert isinstance(model.agent_class_id, UUID)
        assert str(model.agent_class_id) == uuid_str

    def test_serialization(self) -> None:
        """Should serialize to dict correctly."""
        model = AgentDefinitionCreate(
            agent_class_id=uuid4(),
            name="Test",
            config={"key": "value"},
        )
        data = model.model_dump()

        assert "agent_class_id" in data
        assert data["name"] == "Test"
        assert data["config"] == {"key": "value"}

    def test_json_serialization(self) -> None:
        """Should serialize to JSON correctly."""
        model = AgentDefinitionCreate(
            agent_class_id=uuid4(),
            name="Test",
        )
        json_str = model.model_dump_json()
        assert '"name":"Test"' in json_str


class TestAgentDefinitionRead:
    """Tests for AgentDefinitionRead model."""

    def test_valid_creation(self) -> None:
        """Should create with all required fields."""
        now = datetime.now(timezone.utc)
        model = AgentDefinitionRead(
            id=uuid4(),
            agent_class_id=uuid4(),
            name="Test Agent",
            slug="test-agent",
            status=AgentDefinitionStatus.DRAFT,
            execution_mode=ExecutionMode.EPHEMERAL,
            config={},
            allow_outbound_a2a=False,
            created_at=now,
            updated_at=now,
        )
        assert model.status == AgentDefinitionStatus.DRAFT
        assert model.slug == "test-agent"

    def test_from_attributes_config(self) -> None:
        """Should have from_attributes=True in config."""
        assert AgentDefinitionRead.model_config.get("from_attributes") is True

    def test_status_enum_validation(self) -> None:
        """Should validate status is a valid enum value."""
        now = datetime.now(timezone.utc)
        with pytest.raises(ValidationError):
            AgentDefinitionRead(
                id=uuid4(),
                agent_class_id=uuid4(),
                name="Test",
                slug="test",
                status="invalid",  # type: ignore[arg-type]
                execution_mode=ExecutionMode.EPHEMERAL,
                config={},
                allow_outbound_a2a=False,
                created_at=now,
                updated_at=now,
            )


class TestAgentDefinitionUpdate:
    """Tests for AgentDefinitionUpdate model."""

    def test_all_fields_optional(self) -> None:
        """Should allow empty update."""
        model = AgentDefinitionUpdate()
        assert model.name is None
        assert model.status is None

    def test_partial_update(self) -> None:
        """Should allow partial updates."""
        model = AgentDefinitionUpdate(
            name="New Name",
            status=AgentDefinitionStatus.PUBLISHED,
        )
        assert model.name == "New Name"
        assert model.status == AgentDefinitionStatus.PUBLISHED
        assert model.description is None


class TestAgentDefinitionConfig:
    """Tests for AgentDefinitionConfig model."""

    def test_valid_creation(self) -> None:
        """Should create with required fields."""
        model = AgentDefinitionConfig(
            id=uuid4(),
            name="Test Agent",
            slug="test-agent",
            status=AgentDefinitionStatus.PUBLISHED,
            execution_mode=ExecutionMode.EPHEMERAL,
            config={"temperature": 0.5},
        )
        assert model.tools == []
        assert model.system_prompt is None

    def test_with_tools(self) -> None:
        """Should accept tools list."""
        model = AgentDefinitionConfig(
            id=uuid4(),
            name="Test",
            slug="test",
            status=AgentDefinitionStatus.DRAFT,
            execution_mode=ExecutionMode.EPHEMERAL,
            config={},
            tools=[{"name": "tool1", "json_schema": {}}],
        )
        assert len(model.tools) == 1


class TestAgentInstanceCreate:
    """Tests for AgentInstanceCreate model."""

    def test_valid_creation(self) -> None:
        """Should create with required fields."""
        model = AgentInstanceCreate(routing_key="test-key")
        assert model.routing_key == "test-key"
        assert model.input == {}

    def test_with_input(self) -> None:
        """Should accept input dict."""
        model = AgentInstanceCreate(
            routing_key="test",
            input={"prompt": "Hello"},
        )
        assert model.input["prompt"] == "Hello"

    def test_missing_routing_key(self) -> None:
        """Should reject creation without routing_key."""
        with pytest.raises(ValidationError):
            AgentInstanceCreate()  # type: ignore[call-arg]


class TestAgentInstanceRead:
    """Tests for AgentInstanceRead model."""

    def test_valid_creation(self) -> None:
        """Should create with all required fields."""
        now = datetime.now(timezone.utc)
        model = AgentInstanceRead(
            id=uuid4(),
            deployment_id=uuid4(),
            agent_definition_id=uuid4(),
            routing_key="test",
            status=AgentInstanceStatus.ACTIVE,
            input={},
            metrics={},
            created_at=now,
        )
        assert model.status == AgentInstanceStatus.ACTIVE
        assert model.output is None
        assert model.error is None

    def test_status_validation(self) -> None:
        """Should validate status enum."""
        now = datetime.now(timezone.utc)
        with pytest.raises(ValidationError):
            AgentInstanceRead(
                id=uuid4(),
                deployment_id=uuid4(),
                agent_definition_id=uuid4(),
                routing_key="test",
                status="running",  # type: ignore[arg-type]
                input={},
                metrics={},
                created_at=now,
            )


class TestAgentInstanceUpdate:
    """Tests for AgentInstanceUpdate model."""

    def test_all_fields_optional(self) -> None:
        """Should allow empty update."""
        model = AgentInstanceUpdate()
        assert model.status is None
        assert model.output is None

    def test_partial_update(self) -> None:
        """Should allow partial updates."""
        model = AgentInstanceUpdate(
            status=AgentInstanceStatus.COMPLETED,
            exit_code=0,
        )
        assert model.status == AgentInstanceStatus.COMPLETED
        assert model.exit_code == 0


class TestDeploymentCreate:
    """Tests for DeploymentCreate model."""

    def test_valid_minimal_creation(self) -> None:
        """Should create with required fields only."""
        model = DeploymentCreate(
            agent_definition_id=uuid4(),
            name="Test Deployment",
        )
        assert model.name == "Test Deployment"
        assert model.environment == "production"
        assert model.config == {}

    def test_valid_full_creation(self) -> None:
        """Should create with all fields."""
        model = DeploymentCreate(
            agent_definition_id=uuid4(),
            blueprint_id=uuid4(),
            name="Full Deployment",
            description="A test deployment",
            environment="staging",
            config={"replicas": 3},
            project_context={"version": "1.0"},
            spec_md_path="/path/to/spec.md",
        )
        assert model.environment == "staging"
        assert model.config["replicas"] == 3

    def test_missing_required_fields(self) -> None:
        """Should reject creation without required fields."""
        with pytest.raises(ValidationError) as exc_info:
            DeploymentCreate()  # type: ignore[call-arg]

        errors = exc_info.value.errors()
        assert len(errors) >= 2  # agent_definition_id and name


class TestDeploymentRead:
    """Tests for DeploymentRead model."""

    def test_valid_creation(self) -> None:
        """Should create with all required fields."""
        now = datetime.now(timezone.utc)
        model = DeploymentRead(
            id=uuid4(),
            agent_definition_id=uuid4(),
            name="Test",
            environment="production",
            status=DeploymentStatus.ACTIVE,
            config={},
            project_context={},
            created_at=now,
            updated_at=now,
        )
        assert model.status == DeploymentStatus.ACTIVE

    def test_status_validation(self) -> None:
        """Should validate status enum."""
        now = datetime.now(timezone.utc)
        with pytest.raises(ValidationError):
            DeploymentRead(
                id=uuid4(),
                agent_definition_id=uuid4(),
                name="Test",
                environment="production",
                status="running",  # type: ignore[arg-type]
                config={},
                project_context={},
                created_at=now,
                updated_at=now,
            )


class TestDeploymentUpdate:
    """Tests for DeploymentUpdate model."""

    def test_all_fields_optional(self) -> None:
        """Should allow empty update."""
        model = DeploymentUpdate()
        assert model.name is None
        assert model.status is None

    def test_status_update(self) -> None:
        """Should allow status update."""
        model = DeploymentUpdate(status=DeploymentStatus.COMPLETED)
        assert model.status == DeploymentStatus.COMPLETED


class TestPlanTaskCreate:
    """Tests for PlanTaskCreate model."""

    def test_valid_creation(self) -> None:
        """Should create with required fields."""
        model = PlanTaskCreate(
            description="Do something",
            validation="Check it worked",
        )
        assert model.sequence == 0
        assert model.meta == {}

    def test_with_assignee(self) -> None:
        """Should accept assignee."""
        model = PlanTaskCreate(
            description="Task",
            validation="Validate",
            assignee_agent_definition_id=uuid4(),
        )
        assert model.assignee_agent_definition_id is not None

    def test_missing_required_fields(self) -> None:
        """Should reject creation without required fields."""
        with pytest.raises(ValidationError):
            PlanTaskCreate(description="Task")  # type: ignore[call-arg]


class TestPlanCreate:
    """Tests for PlanCreate model."""

    def test_valid_minimal_creation(self) -> None:
        """Should create with required fields only."""
        model = PlanCreate(goal="Achieve something")
        assert model.goal == "Achieve something"
        assert model.tasks == []
        assert model.constraints == {}

    def test_with_tasks(self) -> None:
        """Should create with embedded tasks."""
        tasks = [
            PlanTaskCreate(description="Task 1", validation="V1"),
            PlanTaskCreate(description="Task 2", validation="V2"),
        ]
        model = PlanCreate(goal="Goal", tasks=tasks)
        assert len(model.tasks) == 2

    def test_missing_goal(self) -> None:
        """Should reject creation without goal."""
        with pytest.raises(ValidationError):
            PlanCreate()  # type: ignore[call-arg]


class TestPlanRead:
    """Tests for PlanRead model."""

    def test_valid_creation(self) -> None:
        """Should create with all required fields."""
        now = datetime.now(timezone.utc)
        model = PlanRead(
            id=uuid4(),
            deployment_id=uuid4(),
            created_by_instance_id=uuid4(),
            goal="Test goal",
            constraints={},
            state={},
            status=PlanStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        assert model.status == PlanStatus.ACTIVE

    def test_status_validation(self) -> None:
        """Should validate status enum."""
        now = datetime.now(timezone.utc)
        with pytest.raises(ValidationError):
            PlanRead(
                id=uuid4(),
                deployment_id=uuid4(),
                created_by_instance_id=uuid4(),
                goal="Goal",
                constraints={},
                state={},
                status="pending",  # type: ignore[arg-type]
                created_at=now,
                updated_at=now,
            )


class TestPlanReadWithTasks:
    """Tests for PlanReadWithTasks model."""

    def test_valid_creation_with_tasks(self) -> None:
        """Should create with embedded tasks."""
        now = datetime.now(timezone.utc)
        task = PlanTaskRead(
            id=uuid4(),
            plan_id=uuid4(),
            sequence=0,
            description="Task",
            validation="Validate",
            status=PlanTaskStatus.PENDING,
            meta={},
            created_at=now,
            updated_at=now,
        )
        model = PlanReadWithTasks(
            id=uuid4(),
            deployment_id=uuid4(),
            created_by_instance_id=uuid4(),
            goal="Goal",
            constraints={},
            state={},
            status=PlanStatus.ACTIVE,
            created_at=now,
            updated_at=now,
            tasks=[task],
        )
        assert len(model.tasks) == 1
        assert model.tasks[0].description == "Task"

    def test_inherits_from_plan_read(self) -> None:
        """Should inherit from PlanRead."""
        assert issubclass(PlanReadWithTasks, PlanRead)


class TestPlanTaskRead:
    """Tests for PlanTaskRead model."""

    def test_valid_creation(self) -> None:
        """Should create with all required fields."""
        now = datetime.now(timezone.utc)
        model = PlanTaskRead(
            id=uuid4(),
            plan_id=uuid4(),
            sequence=1,
            description="Test task",
            validation="Check it",
            status=PlanTaskStatus.IN_PROGRESS,
            meta={"key": "value"},
            created_at=now,
            updated_at=now,
        )
        assert model.sequence == 1
        assert model.status == PlanTaskStatus.IN_PROGRESS


class TestPlanTaskReadEnriched:
    """Tests for PlanTaskReadEnriched model."""

    def test_valid_creation_with_enriched_fields(self) -> None:
        """Should include enriched agent data."""
        now = datetime.now(timezone.utc)
        model = PlanTaskReadEnriched(
            id=uuid4(),
            plan_id=uuid4(),
            sequence=0,
            description="Task",
            validation="Validate",
            status=PlanTaskStatus.COMPLETED,
            meta={},
            created_at=now,
            updated_at=now,
            assignee_agent_slug="test-agent",
            assignee_agent_name="Test Agent",
        )
        assert model.assignee_agent_slug == "test-agent"
        assert model.assignee_agent_name == "Test Agent"

    def test_inherits_from_plan_task_read(self) -> None:
        """Should inherit from PlanTaskRead."""
        assert issubclass(PlanTaskReadEnriched, PlanTaskRead)


class TestPlanUpdate:
    """Tests for PlanUpdate model."""

    def test_all_fields_optional(self) -> None:
        """Should allow empty update."""
        model = PlanUpdate()
        assert model.goal is None
        assert model.status is None

    def test_status_update(self) -> None:
        """Should allow status update."""
        model = PlanUpdate(status=PlanStatus.COMPLETED)
        assert model.status == PlanStatus.COMPLETED


class TestPlanTaskUpdate:
    """Tests for PlanTaskUpdate model."""

    def test_all_fields_optional(self) -> None:
        """Should allow empty update."""
        model = PlanTaskUpdate()
        assert model.description is None

    def test_partial_update(self) -> None:
        """Should allow partial updates."""
        model = PlanTaskUpdate(
            status=PlanTaskStatus.SKIPPED,
            result="Skipped due to conditions",
        )
        assert model.status == PlanTaskStatus.SKIPPED


class TestTasksAppend:
    """Tests for TasksAppend model."""

    def test_valid_creation(self) -> None:
        """Should create with tasks list."""
        tasks = [
            PlanTaskCreate(description="T1", validation="V1"),
            PlanTaskCreate(description="T2", validation="V2"),
        ]
        model = TasksAppend(tasks=tasks)
        assert len(model.tasks) == 2

    def test_missing_tasks(self) -> None:
        """Should reject creation without tasks."""
        with pytest.raises(ValidationError):
            TasksAppend()  # type: ignore[call-arg]


class TestTasksAppendResponse:
    """Tests for TasksAppendResponse model."""

    def test_valid_creation(self) -> None:
        """Should create with task IDs."""
        model = TasksAppendResponse(task_ids=[uuid4(), uuid4()])
        assert len(model.task_ids) == 2


class TestPlanCreateResponse:
    """Tests for PlanCreateResponse model."""

    def test_valid_creation(self) -> None:
        """Should create with all required fields."""
        now = datetime.now(timezone.utc)
        model = PlanCreateResponse(
            id=uuid4(),
            deployment_id=uuid4(),
            created_by_instance_id=uuid4(),
            goal="Test goal",
            constraints={},
            state={},
            status=PlanStatus.DRAFT,
            created_at=now,
            updated_at=now,
            task_ids=[uuid4()],
        )
        assert len(model.task_ids) == 1
