"""Tests for the plans resource module."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
import respx
from httpx import Response

from atlas_sdk.clients.workflow import WorkflowClient
from atlas_sdk.models.enums import PlanStatus
from atlas_sdk.models.plan import PlanReadWithTasks, PlanTaskCreate
from atlas_sdk.resources.plans import Plan, PlansResource
from atlas_sdk.resources.tasks import Task


@pytest.fixture
def base_url() -> str:
    return "http://control-plane"


@pytest.fixture
def workflow_client(base_url: str) -> WorkflowClient:
    return WorkflowClient(base_url=base_url)


@pytest.fixture
def deployment_id() -> UUID:
    return uuid4()


@pytest.fixture
def plan_id() -> UUID:
    return uuid4()


@pytest.fixture
def instance_id() -> UUID:
    return uuid4()


@pytest.fixture
def task_id() -> UUID:
    return uuid4()


@pytest.fixture
def sample_task_data(task_id: UUID, plan_id: UUID) -> dict:
    """Return sample task data."""
    now = datetime.now(timezone.utc).isoformat()
    return {
        "id": str(task_id),
        "plan_id": str(plan_id),
        "sequence": 1,
        "description": "Test task",
        "validation": "Task is done",
        "assignee_agent_definition_id": None,
        "status": "PENDING",
        "result": None,
        "meta": {},
        "created_at": now,
        "updated_at": now,
    }


@pytest.fixture
def sample_plan_data(
    plan_id: UUID, deployment_id: UUID, instance_id: UUID, sample_task_data: dict
) -> dict:
    """Return sample plan data."""
    now = datetime.now(timezone.utc).isoformat()
    return {
        "id": str(plan_id),
        "deployment_id": str(deployment_id),
        "created_by_instance_id": str(instance_id),
        "goal": "Test goal",
        "constraints": {"key": "value"},
        "state": {},
        "status": "DRAFT",
        "spec_reference": None,
        "created_at": now,
        "updated_at": now,
        "tasks": [sample_task_data],
    }


@pytest.fixture
def sample_plan_create_response(
    plan_id: UUID, deployment_id: UUID, instance_id: UUID, task_id: UUID
) -> dict:
    """Return sample plan create response."""
    now = datetime.now(timezone.utc).isoformat()
    return {
        "id": str(plan_id),
        "deployment_id": str(deployment_id),
        "created_by_instance_id": str(instance_id),
        "goal": "Test goal",
        "constraints": {"key": "value"},
        "state": {},
        "status": "DRAFT",
        "spec_reference": None,
        "created_at": now,
        "updated_at": now,
        "task_ids": [str(task_id)],
    }


class TestPlan:
    """Tests for the Plan resource class."""

    def test_id_property(
        self, sample_plan_data: dict, plan_id: UUID, workflow_client: WorkflowClient
    ):
        """Test that id property returns the correct UUID."""
        data = PlanReadWithTasks.model_validate(sample_plan_data)
        plan = Plan(data, workflow_client)
        assert plan.id == plan_id

    def test_goal_property(
        self, sample_plan_data: dict, workflow_client: WorkflowClient
    ):
        """Test that goal property returns the correct value."""
        data = PlanReadWithTasks.model_validate(sample_plan_data)
        plan = Plan(data, workflow_client)
        assert plan.goal == "Test goal"

    def test_status_property(
        self, sample_plan_data: dict, workflow_client: WorkflowClient
    ):
        """Test that status property returns the correct enum."""
        data = PlanReadWithTasks.model_validate(sample_plan_data)
        plan = Plan(data, workflow_client)
        assert plan.status == PlanStatus.DRAFT

    def test_tasks_property(
        self, sample_plan_data: dict, workflow_client: WorkflowClient
    ):
        """Test that tasks property returns Task resources."""
        data = PlanReadWithTasks.model_validate(sample_plan_data)
        plan = Plan(data, workflow_client)
        tasks = plan.tasks
        assert len(tasks) == 1
        assert isinstance(tasks[0], Task)
        assert tasks[0].description == "Test task"

    def test_repr(
        self, sample_plan_data: dict, plan_id: UUID, workflow_client: WorkflowClient
    ):
        """Test string representation."""
        data = PlanReadWithTasks.model_validate(sample_plan_data)
        plan = Plan(data, workflow_client)
        repr_str = repr(plan)
        assert "Plan" in repr_str
        assert str(plan_id) in repr_str
        assert "DRAFT" in repr_str

    @pytest.mark.asyncio
    async def test_refresh(
        self,
        base_url: str,
        sample_plan_data: dict,
        plan_id: UUID,
        workflow_client: WorkflowClient,
    ):
        """Test that refresh updates the internal data."""
        data = PlanReadWithTasks.model_validate(sample_plan_data)
        plan = Plan(data, workflow_client)

        updated_data = sample_plan_data.copy()
        updated_data["goal"] = "Updated goal"
        updated_data["status"] = "ACTIVE"

        async with respx.mock(base_url=base_url) as respx_mock:
            route = respx_mock.get(f"/api/v1/plans/{plan_id}").mock(
                return_value=Response(200, json=updated_data)
            )
            async with workflow_client:
                await plan.refresh()

        assert route.called
        assert plan.goal == "Updated goal"
        assert plan.status == PlanStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_save(
        self,
        base_url: str,
        sample_plan_data: dict,
        plan_id: UUID,
        workflow_client: WorkflowClient,
    ):
        """Test that save sends the correct data to the server."""
        data = PlanReadWithTasks.model_validate(sample_plan_data)
        plan = Plan(data, workflow_client)
        plan.data.goal = "Updated goal"

        async with respx.mock(base_url=base_url) as respx_mock:
            # save() calls PATCH and then refresh()
            patch_route = respx_mock.patch(f"/api/v1/plans/{plan_id}").mock(
                return_value=Response(200, json={"id": str(plan_id)})
            )
            get_route = respx_mock.get(f"/api/v1/plans/{plan_id}").mock(
                return_value=Response(
                    200, json={**sample_plan_data, "goal": "Updated goal"}
                )
            )
            async with workflow_client:
                await plan.save()

        assert patch_route.called
        assert get_route.called

    @pytest.mark.asyncio
    async def test_delete_raises_not_implemented(
        self, sample_plan_data: dict, workflow_client: WorkflowClient
    ):
        """Test that delete raises NotImplementedError."""
        data = PlanReadWithTasks.model_validate(sample_plan_data)
        plan = Plan(data, workflow_client)
        async with workflow_client:
            with pytest.raises(NotImplementedError):
                await plan.delete()

    @pytest.mark.asyncio
    async def test_append_tasks(
        self,
        base_url: str,
        sample_plan_data: dict,
        plan_id: UUID,
        workflow_client: WorkflowClient,
    ):
        """Test appending tasks to a plan."""
        data = PlanReadWithTasks.model_validate(sample_plan_data)
        plan = Plan(data, workflow_client)
        new_task_id = uuid4()

        async with respx.mock(base_url=base_url) as respx_mock:
            post_route = respx_mock.post(f"/api/v1/plans/{plan_id}/tasks").mock(
                return_value=Response(200, json={"task_ids": [str(new_task_id)]})
            )
            get_route = respx_mock.get(f"/api/v1/plans/{plan_id}").mock(
                return_value=Response(200, json=sample_plan_data)
            )
            async with workflow_client:
                task_ids = await plan.append_tasks(
                    [PlanTaskCreate(description="New task", validation="Done")]
                )

        assert post_route.called
        assert get_route.called
        assert task_ids == [new_task_id]


class TestPlansResource:
    """Tests for the PlansResource manager class."""

    @pytest.mark.asyncio
    async def test_create(
        self,
        base_url: str,
        sample_plan_data: dict,
        sample_plan_create_response: dict,
        deployment_id: UUID,
        plan_id: UUID,
        workflow_client: WorkflowClient,
    ):
        """Test creating a plan through the resource manager."""
        async with respx.mock(base_url=base_url) as respx_mock:
            post_route = respx_mock.post(
                f"/api/v1/deployments/{deployment_id}/plans"
            ).mock(return_value=Response(200, json=sample_plan_create_response))
            get_route = respx_mock.get(f"/api/v1/plans/{plan_id}").mock(
                return_value=Response(200, json=sample_plan_data)
            )
            async with workflow_client:
                resource = PlansResource(workflow_client)
                plan = await resource.create(
                    deployment_id=deployment_id,
                    goal="Test goal",
                    constraints={"key": "value"},
                )

        assert post_route.called
        assert get_route.called
        assert isinstance(plan, Plan)
        assert plan.goal == "Test goal"

    @pytest.mark.asyncio
    async def test_get(
        self,
        base_url: str,
        sample_plan_data: dict,
        plan_id: UUID,
        workflow_client: WorkflowClient,
    ):
        """Test getting a plan by ID."""
        async with respx.mock(base_url=base_url) as respx_mock:
            route = respx_mock.get(f"/api/v1/plans/{plan_id}").mock(
                return_value=Response(200, json=sample_plan_data)
            )
            async with workflow_client:
                resource = PlansResource(workflow_client)
                plan = await resource.get(plan_id)

        assert route.called
        assert isinstance(plan, Plan)
        assert plan.id == plan_id

    @pytest.mark.asyncio
    async def test_list(
        self,
        base_url: str,
        deployment_id: UUID,
        workflow_client: WorkflowClient,
    ):
        """Test listing plans."""
        now = datetime.now(timezone.utc).isoformat()
        plan_read_data = {
            "id": str(uuid4()),
            "deployment_id": str(deployment_id),
            "created_by_instance_id": str(uuid4()),
            "goal": "Test goal",
            "constraints": {},
            "state": {},
            "status": "DRAFT",
            "spec_reference": None,
            "created_at": now,
            "updated_at": now,
        }

        async with respx.mock(base_url=base_url) as respx_mock:
            route = respx_mock.get(f"/api/v1/deployments/{deployment_id}/plans").mock(
                return_value=Response(200, json=[plan_read_data])
            )
            async with workflow_client:
                resource = PlansResource(workflow_client)
                plans = await resource.list(deployment_id)

        assert route.called
        assert len(plans) == 1
        assert isinstance(plans[0], Plan)


class TestClientPlansProperty:
    """Test that workflow_client.plans returns the correct resource manager."""

    @pytest.mark.asyncio
    async def test_workflow_client_plans(self, workflow_client: WorkflowClient):
        """Test that WorkflowClient has plans property."""
        async with workflow_client as client:
            assert hasattr(client, "plans")
            assert isinstance(client.plans, PlansResource)

    @pytest.mark.asyncio
    async def test_plans_cached(self, workflow_client: WorkflowClient):
        """Test that plans property returns the same instance."""
        async with workflow_client as client:
            plans1 = client.plans
            plans2 = client.plans
            assert plans1 is plans2
