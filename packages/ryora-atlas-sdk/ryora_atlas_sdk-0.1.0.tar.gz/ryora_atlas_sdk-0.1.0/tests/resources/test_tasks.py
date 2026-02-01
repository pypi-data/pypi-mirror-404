"""Tests for the tasks resource module."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
import respx
from httpx import Response

from atlas_sdk.clients.workflow import WorkflowClient
from atlas_sdk.models.enums import PlanTaskStatus
from atlas_sdk.models.plan import PlanTaskReadEnriched
from atlas_sdk.resources.tasks import Task, TasksResource


@pytest.fixture
def base_url() -> str:
    return "http://control-plane"


@pytest.fixture
def workflow_client(base_url: str) -> WorkflowClient:
    return WorkflowClient(base_url=base_url)


@pytest.fixture
def plan_id() -> UUID:
    return uuid4()


@pytest.fixture
def task_id() -> UUID:
    return uuid4()


@pytest.fixture
def sample_task_data(task_id: UUID, plan_id: UUID) -> dict:
    """Return sample enriched task data."""
    now = datetime.now(timezone.utc).isoformat()
    return {
        "id": str(task_id),
        "plan_id": str(plan_id),
        "sequence": 1,
        "description": "Test task",
        "validation": "Task is done",
        "assignee_agent_definition_id": None,
        "assignee_agent_slug": None,
        "assignee_agent_name": None,
        "status": "PENDING",
        "result": None,
        "meta": {"key": "value"},
        "created_at": now,
        "updated_at": now,
    }


class TestTask:
    """Tests for the Task resource class."""

    def test_id_property(
        self, sample_task_data: dict, task_id: UUID, workflow_client: WorkflowClient
    ):
        """Test that id property returns the correct UUID."""
        data = PlanTaskReadEnriched.model_validate(sample_task_data)
        task = Task(data, workflow_client)
        assert task.id == task_id

    def test_description_property(
        self, sample_task_data: dict, workflow_client: WorkflowClient
    ):
        """Test that description property returns the correct value."""
        data = PlanTaskReadEnriched.model_validate(sample_task_data)
        task = Task(data, workflow_client)
        assert task.description == "Test task"

    def test_status_property(
        self, sample_task_data: dict, workflow_client: WorkflowClient
    ):
        """Test that status property returns the correct enum."""
        data = PlanTaskReadEnriched.model_validate(sample_task_data)
        task = Task(data, workflow_client)
        assert task.status == PlanTaskStatus.PENDING

    def test_sequence_property(
        self, sample_task_data: dict, workflow_client: WorkflowClient
    ):
        """Test that sequence property returns the correct value."""
        data = PlanTaskReadEnriched.model_validate(sample_task_data)
        task = Task(data, workflow_client)
        assert task.sequence == 1

    def test_meta_property(
        self, sample_task_data: dict, workflow_client: WorkflowClient
    ):
        """Test that meta property returns the correct dict."""
        data = PlanTaskReadEnriched.model_validate(sample_task_data)
        task = Task(data, workflow_client)
        assert task.meta == {"key": "value"}

    def test_repr(
        self, sample_task_data: dict, task_id: UUID, workflow_client: WorkflowClient
    ):
        """Test string representation."""
        data = PlanTaskReadEnriched.model_validate(sample_task_data)
        task = Task(data, workflow_client)
        repr_str = repr(task)
        assert "Task" in repr_str
        assert str(task_id) in repr_str
        assert "PENDING" in repr_str

    @pytest.mark.asyncio
    async def test_refresh(
        self,
        base_url: str,
        sample_task_data: dict,
        task_id: UUID,
        workflow_client: WorkflowClient,
    ):
        """Test that refresh updates the internal data."""
        data = PlanTaskReadEnriched.model_validate(sample_task_data)
        task = Task(data, workflow_client)

        updated_data = sample_task_data.copy()
        updated_data["description"] = "Updated task"
        updated_data["status"] = "COMPLETED"
        updated_data["result"] = "Done!"

        async with respx.mock(base_url=base_url) as respx_mock:
            route = respx_mock.get(f"/api/v1/tasks/{task_id}").mock(
                return_value=Response(200, json=updated_data)
            )
            async with workflow_client:
                await task.refresh()

        assert route.called
        assert task.description == "Updated task"
        assert task.status == PlanTaskStatus.COMPLETED
        assert task.result == "Done!"

    @pytest.mark.asyncio
    async def test_save(
        self,
        base_url: str,
        sample_task_data: dict,
        task_id: UUID,
        workflow_client: WorkflowClient,
    ):
        """Test that save sends the correct data to the server."""
        data = PlanTaskReadEnriched.model_validate(sample_task_data)
        task = Task(data, workflow_client)
        task.data.status = PlanTaskStatus.COMPLETED
        task.data.result = "Done!"

        updated_data = sample_task_data.copy()
        updated_data["status"] = "COMPLETED"
        updated_data["result"] = "Done!"

        async with respx.mock(base_url=base_url) as respx_mock:
            # save() calls PATCH and then refresh()
            patch_route = respx_mock.patch(f"/api/v1/tasks/{task_id}").mock(
                return_value=Response(200, json=updated_data)
            )
            get_route = respx_mock.get(f"/api/v1/tasks/{task_id}").mock(
                return_value=Response(200, json=updated_data)
            )
            async with workflow_client:
                await task.save()

        assert patch_route.called
        assert get_route.called

    @pytest.mark.asyncio
    async def test_delete_raises_not_implemented(
        self, sample_task_data: dict, workflow_client: WorkflowClient
    ):
        """Test that delete raises NotImplementedError."""
        data = PlanTaskReadEnriched.model_validate(sample_task_data)
        task = Task(data, workflow_client)
        async with workflow_client:
            with pytest.raises(NotImplementedError):
                await task.delete()


class TestTasksResource:
    """Tests for the TasksResource manager class."""

    @pytest.mark.asyncio
    async def test_get(
        self,
        base_url: str,
        sample_task_data: dict,
        task_id: UUID,
        workflow_client: WorkflowClient,
    ):
        """Test getting a task by ID."""
        async with respx.mock(base_url=base_url) as respx_mock:
            route = respx_mock.get(f"/api/v1/tasks/{task_id}").mock(
                return_value=Response(200, json=sample_task_data)
            )
            async with workflow_client:
                resource = TasksResource(workflow_client)
                task = await resource.get(task_id)

        assert route.called
        assert isinstance(task, Task)
        assert task.id == task_id

    @pytest.mark.asyncio
    async def test_list(
        self,
        base_url: str,
        plan_id: UUID,
        workflow_client: WorkflowClient,
    ):
        """Test listing tasks."""
        now = datetime.now(timezone.utc).isoformat()
        task_data = {
            "id": str(uuid4()),
            "plan_id": str(plan_id),
            "sequence": 1,
            "description": "Test task",
            "validation": "Done",
            "assignee_agent_definition_id": None,
            "status": "PENDING",
            "result": None,
            "meta": {},
            "created_at": now,
            "updated_at": now,
        }

        async with respx.mock(base_url=base_url) as respx_mock:
            route = respx_mock.get(f"/api/v1/plans/{plan_id}/tasks").mock(
                return_value=Response(200, json=[task_data])
            )
            async with workflow_client:
                resource = TasksResource(workflow_client)
                tasks = await resource.list(plan_id)

        assert route.called
        assert len(tasks) == 1
        assert isinstance(tasks[0], Task)

    @pytest.mark.asyncio
    async def test_list_with_status_filter(
        self,
        base_url: str,
        plan_id: UUID,
        workflow_client: WorkflowClient,
    ):
        """Test listing tasks with status filter."""
        async with respx.mock(base_url=base_url) as respx_mock:
            route = respx_mock.get(f"/api/v1/plans/{plan_id}/tasks").mock(
                return_value=Response(200, json=[])
            )
            async with workflow_client:
                resource = TasksResource(workflow_client)
                await resource.list(plan_id, status=PlanTaskStatus.PENDING)

        assert route.called
        request = route.calls[0].request
        assert "status=PENDING" in str(request.url)


class TestClientTasksProperty:
    """Test that workflow_client.tasks returns the correct resource manager."""

    @pytest.mark.asyncio
    async def test_workflow_client_tasks(self, workflow_client: WorkflowClient):
        """Test that WorkflowClient has tasks property."""
        async with workflow_client as client:
            assert hasattr(client, "tasks")
            assert isinstance(client.tasks, TasksResource)

    @pytest.mark.asyncio
    async def test_tasks_cached(self, workflow_client: WorkflowClient):
        """Test that tasks property returns the same instance."""
        async with workflow_client as client:
            tasks1 = client.tasks
            tasks2 = client.tasks
            assert tasks1 is tasks2
