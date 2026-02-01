"""Tests for WorkflowClient."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

import pytest
import respx
from httpx import Response

from atlas_sdk.clients.workflow import WorkflowClient
from atlas_sdk.exceptions import AtlasHTTPStatusError, AtlasTimeoutError
from atlas_sdk.models.enums import (
    AgentDefinitionStatus,
    AgentInstanceStatus,
    PlanStatus,
    PlanTaskStatus,
)
from atlas_sdk.models.plan import (
    PlanCreate,
    PlanTaskCreate,
    PlanUpdate,
    PlanTaskUpdate,
    TasksAppend,
)


@pytest.fixture
def base_url() -> str:
    return "http://control-plane"


@pytest.fixture
def client(base_url: str) -> WorkflowClient:
    return WorkflowClient(base_url=base_url)


@pytest.fixture
def deployment_id() -> UUID:
    return uuid4()


@pytest.fixture
def plan_id() -> UUID:
    return uuid4()


@pytest.fixture
def task_id() -> UUID:
    return uuid4()


@pytest.fixture
def definition_id() -> UUID:
    return uuid4()


@pytest.fixture
def instance_id() -> UUID:
    return uuid4()


@pytest.fixture
def agent_class_id() -> UUID:
    return uuid4()


class TestWorkflowClientPlans:
    """Tests for plan methods."""

    @pytest.mark.asyncio
    async def test_create_plan_success(
        self,
        client: WorkflowClient,
        base_url: str,
        deployment_id: UUID,
        plan_id: UUID,
        task_id: UUID,
        instance_id: UUID,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        response_data = {
            "id": str(plan_id),
            "deployment_id": str(deployment_id),
            "created_by_instance_id": str(instance_id),
            "goal": "Test plan",
            "constraints": {},
            "state": {},
            "status": "DRAFT",
            "spec_reference": None,
            "created_at": now,
            "updated_at": now,
            "task_ids": [str(task_id)],
        }

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.post(f"/api/v1/deployments/{deployment_id}/plans").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.create_plan(
                    deployment_id,
                    PlanCreate(
                        goal="Test plan",
                        tasks=[
                            PlanTaskCreate(
                                sequence=1,
                                description="Task 1",
                                validation="Check task completion",
                            )
                        ],
                    ),
                )

            assert result.id == plan_id
            assert result.goal == "Test plan"
            assert len(result.task_ids) == 1
            assert result.task_ids[0] == task_id

    @pytest.mark.asyncio
    async def test_get_plan_success(
        self,
        client: WorkflowClient,
        base_url: str,
        deployment_id: UUID,
        plan_id: UUID,
        task_id: UUID,
        instance_id: UUID,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        response_data = {
            "id": str(plan_id),
            "deployment_id": str(deployment_id),
            "created_by_instance_id": str(instance_id),
            "goal": "Test plan",
            "constraints": {},
            "state": {},
            "status": "ACTIVE",
            "spec_reference": None,
            "created_at": now,
            "updated_at": now,
            "tasks": [
                {
                    "id": str(task_id),
                    "plan_id": str(plan_id),
                    "sequence": 1,
                    "description": "Task 1",
                    "validation": "Check completion",
                    "assignee_agent_definition_id": None,
                    "status": "PENDING",
                    "result": None,
                    "meta": {},
                    "created_at": now,
                    "updated_at": now,
                }
            ],
        }

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get(f"/api/v1/plans/{plan_id}").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.get_plan(plan_id)

            assert result.id == plan_id
            assert result.status == PlanStatus.ACTIVE
            assert len(result.tasks) == 1

    @pytest.mark.asyncio
    async def test_list_plans_success(
        self,
        client: WorkflowClient,
        base_url: str,
        deployment_id: UUID,
        plan_id: UUID,
        instance_id: UUID,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        response_data = [
            {
                "id": str(plan_id),
                "deployment_id": str(deployment_id),
                "created_by_instance_id": str(instance_id),
                "goal": "Test plan",
                "constraints": {},
                "state": {},
                "status": "ACTIVE",
                "spec_reference": None,
                "created_at": now,
                "updated_at": now,
            }
        ]

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get(f"/api/v1/deployments/{deployment_id}/plans").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.list_plans(deployment_id)

            assert len(result) == 1
            assert result[0].id == plan_id

    @pytest.mark.asyncio
    async def test_list_plans_with_status_filter(
        self,
        client: WorkflowClient,
        base_url: str,
        deployment_id: UUID,
    ) -> None:
        async with respx.mock(base_url=base_url) as respx_mock:
            route = respx_mock.get(f"/api/v1/deployments/{deployment_id}/plans").mock(
                return_value=Response(200, json=[])
            )

            async with client:
                await client.list_plans(deployment_id, status=PlanStatus.ACTIVE)

            assert route.calls.last.request.url.params["status"] == "ACTIVE"

    @pytest.mark.asyncio
    async def test_list_plans_with_pagination(
        self,
        client: WorkflowClient,
        base_url: str,
        deployment_id: UUID,
    ) -> None:
        async with respx.mock(base_url=base_url) as respx_mock:
            route = respx_mock.get(f"/api/v1/deployments/{deployment_id}/plans").mock(
                return_value=Response(200, json=[])
            )

            async with client:
                await client.list_plans(deployment_id, limit=25, offset=50)

            params = route.calls.last.request.url.params
            assert params["limit"] == "25"
            assert params["offset"] == "50"

    @pytest.mark.asyncio
    async def test_update_plan_success(
        self,
        client: WorkflowClient,
        base_url: str,
        deployment_id: UUID,
        plan_id: UUID,
        instance_id: UUID,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        response_data = {
            "id": str(plan_id),
            "deployment_id": str(deployment_id),
            "created_by_instance_id": str(instance_id),
            "goal": "Updated plan",
            "constraints": {},
            "state": {},
            "status": "ACTIVE",
            "spec_reference": None,
            "created_at": now,
            "updated_at": now,
        }

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.patch(f"/api/v1/plans/{plan_id}").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.update_plan(
                    plan_id, PlanUpdate(status=PlanStatus.ACTIVE)
                )

            assert result.status == PlanStatus.ACTIVE


class TestWorkflowClientTasks:
    """Tests for task methods."""

    @pytest.mark.asyncio
    async def test_append_tasks_success(
        self,
        client: WorkflowClient,
        base_url: str,
        plan_id: UUID,
        task_id: UUID,
    ) -> None:
        response_data = {
            "task_ids": [str(task_id)],
        }

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.post(f"/api/v1/plans/{plan_id}/tasks").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.append_tasks(
                    plan_id,
                    TasksAppend(
                        tasks=[
                            PlanTaskCreate(
                                sequence=2,
                                description="New task",
                                validation="Validate new task",
                            )
                        ]
                    ),
                )

            assert len(result.task_ids) == 1
            assert result.task_ids[0] == task_id

    @pytest.mark.asyncio
    async def test_get_task_success(
        self,
        client: WorkflowClient,
        base_url: str,
        plan_id: UUID,
        task_id: UUID,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        response_data = {
            "id": str(task_id),
            "plan_id": str(plan_id),
            "sequence": 1,
            "description": "Task 1",
            "validation": "Check completion",
            "assignee_agent_definition_id": None,
            "status": "IN_PROGRESS",
            "result": None,
            "meta": {},
            "created_at": now,
            "updated_at": now,
            "assignee_agent_slug": None,
            "assignee_agent_name": None,
        }

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get(f"/api/v1/tasks/{task_id}").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.get_task(task_id)

            assert result.id == task_id
            assert result.status == PlanTaskStatus.IN_PROGRESS

    @pytest.mark.asyncio
    async def test_list_tasks_success(
        self,
        client: WorkflowClient,
        base_url: str,
        plan_id: UUID,
        task_id: UUID,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        response_data = [
            {
                "id": str(task_id),
                "plan_id": str(plan_id),
                "sequence": 1,
                "description": "Task 1",
                "validation": "Check completion",
                "assignee_agent_definition_id": None,
                "status": "PENDING",
                "result": None,
                "meta": {},
                "created_at": now,
                "updated_at": now,
            }
        ]

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get(f"/api/v1/plans/{plan_id}/tasks").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.list_tasks(plan_id)

            assert len(result) == 1
            assert result[0].id == task_id

    @pytest.mark.asyncio
    async def test_list_tasks_with_pagination(
        self,
        client: WorkflowClient,
        base_url: str,
        plan_id: UUID,
    ) -> None:
        async with respx.mock(base_url=base_url) as respx_mock:
            route = respx_mock.get(f"/api/v1/plans/{plan_id}/tasks").mock(
                return_value=Response(200, json=[])
            )

            async with client:
                await client.list_tasks(plan_id, limit=30, offset=10)

            params = route.calls.last.request.url.params
            assert params["limit"] == "30"
            assert params["offset"] == "10"

    @pytest.mark.asyncio
    async def test_update_task_success(
        self,
        client: WorkflowClient,
        base_url: str,
        plan_id: UUID,
        task_id: UUID,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        response_data = {
            "id": str(task_id),
            "plan_id": str(plan_id),
            "sequence": 1,
            "description": "Task 1",
            "validation": "Check completion",
            "assignee_agent_definition_id": None,
            "status": "COMPLETED",
            "result": "Done",
            "meta": {},
            "created_at": now,
            "updated_at": now,
        }

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.patch(f"/api/v1/tasks/{task_id}").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.update_task(
                    task_id, PlanTaskUpdate(status=PlanTaskStatus.COMPLETED)
                )

            assert result.status == PlanTaskStatus.COMPLETED


class TestWorkflowClientAgentDefinitions:
    """Tests for agent definition methods (read-only)."""

    @pytest.mark.asyncio
    async def test_get_agent_definition_success(
        self,
        client: WorkflowClient,
        base_url: str,
        definition_id: UUID,
        agent_class_id: UUID,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        response_data = {
            "id": str(definition_id),
            "agent_class_id": str(agent_class_id),
            "system_prompt_id": None,
            "structured_output_id": None,
            "model_provider_id": None,
            "name": "test-agent",
            "slug": "test-agent",
            "description": "A test agent",
            "status": "published",
            "execution_mode": "ephemeral",
            "model_name": "gpt-4",
            "config": {},
            "allow_outbound_a2a": False,
            "created_at": now,
            "updated_at": now,
        }

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get(f"/api/v1/agent-definitions/{definition_id}").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.get_agent_definition(definition_id)

            assert result.id == definition_id
            assert result.name == "test-agent"

    @pytest.mark.asyncio
    async def test_list_agent_definitions_success(
        self,
        client: WorkflowClient,
        base_url: str,
        definition_id: UUID,
        agent_class_id: UUID,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        response_data = [
            {
                "id": str(definition_id),
                "agent_class_id": str(agent_class_id),
                "system_prompt_id": None,
                "structured_output_id": None,
                "model_provider_id": None,
                "name": "test-agent",
                "slug": "test-agent",
                "description": "A test agent",
                "status": "published",
                "execution_mode": "ephemeral",
                "model_name": "gpt-4",
                "config": {},
                "allow_outbound_a2a": False,
                "created_at": now,
                "updated_at": now,
            }
        ]

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get("/api/v1/agent-definitions").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.list_agent_definitions()

            assert len(result) == 1
            assert result[0].id == definition_id

    @pytest.mark.asyncio
    async def test_list_agent_definitions_with_status_filter(
        self,
        client: WorkflowClient,
        base_url: str,
    ) -> None:
        async with respx.mock(base_url=base_url) as respx_mock:
            route = respx_mock.get("/api/v1/agent-definitions").mock(
                return_value=Response(200, json=[])
            )

            async with client:
                await client.list_agent_definitions(
                    status=AgentDefinitionStatus.PUBLISHED
                )

            assert route.calls.last.request.url.params["status"] == "published"

    @pytest.mark.asyncio
    async def test_list_agent_definitions_with_pagination(
        self,
        client: WorkflowClient,
        base_url: str,
    ) -> None:
        async with respx.mock(base_url=base_url) as respx_mock:
            route = respx_mock.get("/api/v1/agent-definitions").mock(
                return_value=Response(200, json=[])
            )

            async with client:
                await client.list_agent_definitions(limit=15, offset=30)

            params = route.calls.last.request.url.params
            assert params["limit"] == "15"
            assert params["offset"] == "30"

    @pytest.mark.asyncio
    async def test_get_agent_definition_config_success(
        self,
        client: WorkflowClient,
        base_url: str,
        definition_id: UUID,
    ) -> None:
        response_data = {
            "id": str(definition_id),
            "name": "test-agent",
            "slug": "test-agent",
            "description": "A test agent",
            "status": "published",
            "execution_mode": "ephemeral",
            "model_name": "gpt-4",
            "config": {"temperature": 0.7},
            "system_prompt": "You are a helpful assistant.",
            "structured_output_schema": None,
            "tools": [],
        }

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get(f"/api/v1/agent-definitions/{definition_id}/config").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.get_agent_definition_config(definition_id)

            assert result.model_name == "gpt-4"
            assert result.config == {"temperature": 0.7}


class TestWorkflowClientDeployments:
    """Tests for deployment methods (read-only)."""

    @pytest.mark.asyncio
    async def test_get_deployment_success(
        self,
        client: WorkflowClient,
        base_url: str,
        deployment_id: UUID,
        definition_id: UUID,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        response_data = {
            "id": str(deployment_id),
            "agent_definition_id": str(definition_id),
            "blueprint_id": None,
            "name": "test-deployment",
            "description": "A test deployment",
            "environment": "production",
            "status": "active",
            "config": {},
            "project_context": {},
            "spec_md_path": None,
            "created_at": now,
            "updated_at": now,
        }

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get(f"/api/v1/deployments/{deployment_id}").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.get_deployment(deployment_id)

            assert result.id == deployment_id
            assert result.name == "test-deployment"

    @pytest.mark.asyncio
    async def test_list_deployments_success(
        self,
        client: WorkflowClient,
        base_url: str,
        deployment_id: UUID,
        definition_id: UUID,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        response_data = [
            {
                "id": str(deployment_id),
                "agent_definition_id": str(definition_id),
                "blueprint_id": None,
                "name": "test-deployment",
                "description": "A test deployment",
                "environment": "production",
                "status": "active",
                "config": {},
                "project_context": {},
                "spec_md_path": None,
                "created_at": now,
                "updated_at": now,
            }
        ]

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get("/api/v1/deployments").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.list_deployments()

            assert len(result) == 1
            assert result[0].id == deployment_id

    @pytest.mark.asyncio
    async def test_list_deployments_with_filters(
        self,
        client: WorkflowClient,
        base_url: str,
    ) -> None:
        async with respx.mock(base_url=base_url) as respx_mock:
            route = respx_mock.get("/api/v1/deployments").mock(
                return_value=Response(200, json=[])
            )

            async with client:
                await client.list_deployments(
                    environment="production",
                    active_only=True,
                    limit=50,
                    offset=10,
                )

            params = route.calls.last.request.url.params
            assert params["environment"] == "production"
            assert params["active_only"] == "true"
            assert params["limit"] == "50"
            assert params["offset"] == "10"


class TestWorkflowClientAgentInstances:
    """Tests for agent instance methods (read-only)."""

    @pytest.mark.asyncio
    async def test_get_agent_instance_success(
        self,
        client: WorkflowClient,
        base_url: str,
        instance_id: UUID,
        definition_id: UUID,
        deployment_id: UUID,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        response_data = {
            "id": str(instance_id),
            "deployment_id": str(deployment_id),
            "agent_definition_id": str(definition_id),
            "routing_key": "default",
            "status": "active",
            "input": {},
            "output": None,
            "error": None,
            "exit_code": None,
            "metrics": {},
            "created_at": now,
            "started_at": now,
            "completed_at": None,
        }

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get(f"/api/v1/instances/{instance_id}").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.get_agent_instance(instance_id)

            assert result.id == instance_id
            assert result.status == AgentInstanceStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_list_agent_instances_success(
        self,
        client: WorkflowClient,
        base_url: str,
        instance_id: UUID,
        definition_id: UUID,
        deployment_id: UUID,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        response_data = [
            {
                "id": str(instance_id),
                "deployment_id": str(deployment_id),
                "agent_definition_id": str(definition_id),
                "routing_key": "default",
                "status": "active",
                "input": {},
                "output": None,
                "error": None,
                "exit_code": None,
                "metrics": {},
                "created_at": now,
                "started_at": now,
                "completed_at": None,
            }
        ]

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get("/api/v1/instances").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.list_agent_instances()

            assert len(result) == 1
            assert result[0].id == instance_id

    @pytest.mark.asyncio
    async def test_list_agent_instances_with_filters(
        self,
        client: WorkflowClient,
        base_url: str,
        deployment_id: UUID,
    ) -> None:
        async with respx.mock(base_url=base_url) as respx_mock:
            route = respx_mock.get("/api/v1/instances").mock(
                return_value=Response(200, json=[])
            )

            async with client:
                await client.list_agent_instances(
                    deployment_id=deployment_id,
                    status=AgentInstanceStatus.ACTIVE,
                    limit=50,
                    offset=10,
                )

            params = route.calls.last.request.url.params
            assert params["deployment_id"] == str(deployment_id)
            assert params["status"] == "active"
            assert params["limit"] == "50"
            assert params["offset"] == "10"


class TestWorkflowClientHealth:
    """Tests for health method."""

    @pytest.mark.asyncio
    async def test_health_success(
        self,
        client: WorkflowClient,
        base_url: str,
    ) -> None:
        response_data = {
            "status": "healthy",
            "version": "1.0.0",
        }

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get("/api/v1/health").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.health()

            assert result["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_health_error(
        self,
        client: WorkflowClient,
        base_url: str,
    ) -> None:
        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get("/api/v1/health").mock(
                return_value=Response(500, json={"status": "unhealthy"})
            )

            async with client:
                with pytest.raises(AtlasHTTPStatusError):
                    await client.health()


class TestWorkflowClientWaitForPlanCompletion:
    """Tests for wait_for_plan_completion method."""

    @pytest.mark.asyncio
    async def test_wait_for_plan_completion_immediate(
        self,
        client: WorkflowClient,
        base_url: str,
        deployment_id: UUID,
        plan_id: UUID,
        instance_id: UUID,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        response_data = {
            "id": str(plan_id),
            "deployment_id": str(deployment_id),
            "created_by_instance_id": str(instance_id),
            "goal": "Test plan",
            "constraints": {},
            "state": {},
            "status": "COMPLETED",
            "spec_reference": None,
            "created_at": now,
            "updated_at": now,
            "tasks": [],
        }

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get(f"/api/v1/plans/{plan_id}").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.wait_for_plan_completion(plan_id)

            assert result.status == PlanStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_wait_for_plan_completion_polls_until_done(
        self,
        client: WorkflowClient,
        base_url: str,
        deployment_id: UUID,
        plan_id: UUID,
        instance_id: UUID,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        active_response = {
            "id": str(plan_id),
            "deployment_id": str(deployment_id),
            "created_by_instance_id": str(instance_id),
            "goal": "Test plan",
            "constraints": {},
            "state": {},
            "status": "ACTIVE",
            "spec_reference": None,
            "created_at": now,
            "updated_at": now,
            "tasks": [],
        }
        completed_response = {
            "id": str(plan_id),
            "deployment_id": str(deployment_id),
            "created_by_instance_id": str(instance_id),
            "goal": "Test plan",
            "constraints": {},
            "state": {},
            "status": "COMPLETED",
            "spec_reference": None,
            "created_at": now,
            "updated_at": now,
            "tasks": [],
        }

        call_count = 0

        def response_callback(request):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                return Response(200, json=active_response)
            return Response(200, json=completed_response)

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get(f"/api/v1/plans/{plan_id}").mock(
                side_effect=response_callback
            )

            async with client:
                with patch("asyncio.sleep", new_callable=AsyncMock):
                    result = await client.wait_for_plan_completion(
                        plan_id, poll_interval=0.01
                    )

            assert result.status == PlanStatus.COMPLETED
            assert call_count == 3

    @pytest.mark.asyncio
    async def test_wait_for_plan_completion_timeout(
        self,
        client: WorkflowClient,
        base_url: str,
        deployment_id: UUID,
        plan_id: UUID,
        instance_id: UUID,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        response_data = {
            "id": str(plan_id),
            "deployment_id": str(deployment_id),
            "created_by_instance_id": str(instance_id),
            "goal": "Test plan",
            "constraints": {},
            "state": {},
            "status": "ACTIVE",
            "spec_reference": None,
            "created_at": now,
            "updated_at": now,
            "tasks": [],
        }

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get(f"/api/v1/plans/{plan_id}").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                with patch("asyncio.sleep", new_callable=AsyncMock):
                    with pytest.raises(AtlasTimeoutError) as exc_info:
                        await client.wait_for_plan_completion(
                            plan_id, poll_interval=0.5, timeout=1.0
                        )

            assert str(plan_id) in str(exc_info.value)
            assert "ACTIVE" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_wait_for_plan_completion_failed_status(
        self,
        client: WorkflowClient,
        base_url: str,
        deployment_id: UUID,
        plan_id: UUID,
        instance_id: UUID,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        response_data = {
            "id": str(plan_id),
            "deployment_id": str(deployment_id),
            "created_by_instance_id": str(instance_id),
            "goal": "Test plan",
            "constraints": {},
            "state": {},
            "status": "FAILED",
            "spec_reference": None,
            "created_at": now,
            "updated_at": now,
            "tasks": [],
        }

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get(f"/api/v1/plans/{plan_id}").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.wait_for_plan_completion(plan_id)

            assert result.status == PlanStatus.FAILED


class TestWorkflowClientWaitForTaskCompletion:
    """Tests for wait_for_task_completion method."""

    @pytest.mark.asyncio
    async def test_wait_for_task_completion_immediate(
        self,
        client: WorkflowClient,
        base_url: str,
        plan_id: UUID,
        task_id: UUID,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        response_data = {
            "id": str(task_id),
            "plan_id": str(plan_id),
            "sequence": 1,
            "description": "Task 1",
            "validation": "Check completion",
            "assignee_agent_definition_id": None,
            "status": "COMPLETED",
            "result": "Done",
            "meta": {},
            "created_at": now,
            "updated_at": now,
            "assignee_agent_slug": None,
            "assignee_agent_name": None,
        }

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get(f"/api/v1/tasks/{task_id}").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.wait_for_task_completion(task_id)

            assert result.status == PlanTaskStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_wait_for_task_completion_polls_until_done(
        self,
        client: WorkflowClient,
        base_url: str,
        plan_id: UUID,
        task_id: UUID,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        in_progress_response = {
            "id": str(task_id),
            "plan_id": str(plan_id),
            "sequence": 1,
            "description": "Task 1",
            "validation": "Check completion",
            "assignee_agent_definition_id": None,
            "status": "IN_PROGRESS",
            "result": None,
            "meta": {},
            "created_at": now,
            "updated_at": now,
            "assignee_agent_slug": None,
            "assignee_agent_name": None,
        }
        completed_response = {
            "id": str(task_id),
            "plan_id": str(plan_id),
            "sequence": 1,
            "description": "Task 1",
            "validation": "Check completion",
            "assignee_agent_definition_id": None,
            "status": "COMPLETED",
            "result": "Done",
            "meta": {},
            "created_at": now,
            "updated_at": now,
            "assignee_agent_slug": None,
            "assignee_agent_name": None,
        }

        call_count = 0

        def response_callback(request):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                return Response(200, json=in_progress_response)
            return Response(200, json=completed_response)

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get(f"/api/v1/tasks/{task_id}").mock(
                side_effect=response_callback
            )

            async with client:
                with patch("asyncio.sleep", new_callable=AsyncMock):
                    result = await client.wait_for_task_completion(
                        task_id, poll_interval=0.01
                    )

            assert result.status == PlanTaskStatus.COMPLETED
            assert call_count == 2

    @pytest.mark.asyncio
    async def test_wait_for_task_completion_timeout(
        self,
        client: WorkflowClient,
        base_url: str,
        plan_id: UUID,
        task_id: UUID,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        response_data = {
            "id": str(task_id),
            "plan_id": str(plan_id),
            "sequence": 1,
            "description": "Task 1",
            "validation": "Check completion",
            "assignee_agent_definition_id": None,
            "status": "PENDING",
            "result": None,
            "meta": {},
            "created_at": now,
            "updated_at": now,
            "assignee_agent_slug": None,
            "assignee_agent_name": None,
        }

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get(f"/api/v1/tasks/{task_id}").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                with patch("asyncio.sleep", new_callable=AsyncMock):
                    with pytest.raises(AtlasTimeoutError) as exc_info:
                        await client.wait_for_task_completion(
                            task_id, poll_interval=0.5, timeout=1.0
                        )

            assert str(task_id) in str(exc_info.value)
            assert "PENDING" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_wait_for_task_completion_skipped_status(
        self,
        client: WorkflowClient,
        base_url: str,
        plan_id: UUID,
        task_id: UUID,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        response_data = {
            "id": str(task_id),
            "plan_id": str(plan_id),
            "sequence": 1,
            "description": "Task 1",
            "validation": "Check completion",
            "assignee_agent_definition_id": None,
            "status": "SKIPPED",
            "result": None,
            "meta": {},
            "created_at": now,
            "updated_at": now,
            "assignee_agent_slug": None,
            "assignee_agent_name": None,
        }

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get(f"/api/v1/tasks/{task_id}").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.wait_for_task_completion(task_id)

            assert result.status == PlanTaskStatus.SKIPPED

    @pytest.mark.asyncio
    async def test_wait_for_task_completion_timeout_includes_last_state(
        self,
        client: WorkflowClient,
        base_url: str,
        plan_id: UUID,
        task_id: UUID,
    ) -> None:
        """Test that timeout error includes last_state, timeout_seconds, operation."""
        now = datetime.now(timezone.utc).isoformat()
        response_data = {
            "id": str(task_id),
            "plan_id": str(plan_id),
            "sequence": 1,
            "description": "Task 1",
            "validation": "Check completion",
            "assignee_agent_definition_id": None,
            "status": "IN_PROGRESS",
            "result": None,
            "meta": {},
            "created_at": now,
            "updated_at": now,
            "assignee_agent_slug": None,
            "assignee_agent_name": None,
        }

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get(f"/api/v1/tasks/{task_id}").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                with patch("asyncio.sleep", new_callable=AsyncMock):
                    with pytest.raises(AtlasTimeoutError) as exc_info:
                        await client.wait_for_task_completion(
                            task_id, poll_interval=0.5, timeout=1.0
                        )

            assert exc_info.value.operation == "wait_for_task_completion"
            assert exc_info.value.timeout_seconds == 1.0
            assert exc_info.value.last_state is not None
            assert exc_info.value.last_state.status == PlanTaskStatus.IN_PROGRESS

    @pytest.mark.asyncio
    async def test_wait_for_task_completion_with_progress_callback(
        self,
        client: WorkflowClient,
        base_url: str,
        plan_id: UUID,
        task_id: UUID,
    ) -> None:
        """Test wait_for_task_completion calls progress callback."""
        now = datetime.now(timezone.utc).isoformat()
        response_data = {
            "id": str(task_id),
            "plan_id": str(plan_id),
            "sequence": 1,
            "description": "Task 1",
            "validation": "Check completion",
            "assignee_agent_definition_id": None,
            "status": "COMPLETED",
            "result": "Done",
            "meta": {},
            "created_at": now,
            "updated_at": now,
            "assignee_agent_slug": None,
            "assignee_agent_name": None,
        }

        callback_calls: list = []

        def on_progress(task) -> None:
            callback_calls.append(task.status)

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get(f"/api/v1/tasks/{task_id}").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.wait_for_task_completion(
                    task_id, on_progress=on_progress
                )

            assert result.status == PlanTaskStatus.COMPLETED
            assert len(callback_calls) == 1
            assert callback_calls[0] == PlanTaskStatus.COMPLETED


class TestWorkflowClientWaitForPlanCompletionEnhanced:
    """Additional tests for enhanced wait_for_plan_completion."""

    @pytest.mark.asyncio
    async def test_wait_for_plan_completion_timeout_includes_last_state(
        self,
        client: WorkflowClient,
        base_url: str,
        deployment_id: UUID,
        plan_id: UUID,
        instance_id: UUID,
    ) -> None:
        """Test that timeout error includes last_state, timeout_seconds, operation."""
        now = datetime.now(timezone.utc).isoformat()
        response_data = {
            "id": str(plan_id),
            "deployment_id": str(deployment_id),
            "created_by_instance_id": str(instance_id),
            "goal": "Test plan",
            "constraints": {},
            "state": {},
            "status": "ACTIVE",
            "spec_reference": None,
            "created_at": now,
            "updated_at": now,
            "tasks": [],
        }

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get(f"/api/v1/plans/{plan_id}").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                with patch("asyncio.sleep", new_callable=AsyncMock):
                    with pytest.raises(AtlasTimeoutError) as exc_info:
                        await client.wait_for_plan_completion(
                            plan_id, poll_interval=0.5, timeout=1.0
                        )

            assert exc_info.value.operation == "wait_for_plan_completion"
            assert exc_info.value.timeout_seconds == 1.0
            assert exc_info.value.last_state is not None
            assert exc_info.value.last_state.status == PlanStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_wait_for_plan_completion_with_progress_callback(
        self,
        client: WorkflowClient,
        base_url: str,
        deployment_id: UUID,
        plan_id: UUID,
        instance_id: UUID,
    ) -> None:
        """Test wait_for_plan_completion calls progress callback."""
        now = datetime.now(timezone.utc).isoformat()
        response_data = {
            "id": str(plan_id),
            "deployment_id": str(deployment_id),
            "created_by_instance_id": str(instance_id),
            "goal": "Test plan",
            "constraints": {},
            "state": {},
            "status": "COMPLETED",
            "spec_reference": None,
            "created_at": now,
            "updated_at": now,
            "tasks": [],
        }

        callback_calls: list = []

        def on_progress(plan) -> None:
            callback_calls.append(plan.status)

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get(f"/api/v1/plans/{plan_id}").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.wait_for_plan_completion(
                    plan_id, on_progress=on_progress
                )

            assert result.status == PlanStatus.COMPLETED
            assert len(callback_calls) == 1
            assert callback_calls[0] == PlanStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_wait_for_plan_completion_with_async_progress_callback(
        self,
        client: WorkflowClient,
        base_url: str,
        deployment_id: UUID,
        plan_id: UUID,
        instance_id: UUID,
    ) -> None:
        """Test wait_for_plan_completion calls async progress callback."""
        now = datetime.now(timezone.utc).isoformat()
        response_data = {
            "id": str(plan_id),
            "deployment_id": str(deployment_id),
            "created_by_instance_id": str(instance_id),
            "goal": "Test plan",
            "constraints": {},
            "state": {},
            "status": "COMPLETED",
            "spec_reference": None,
            "created_at": now,
            "updated_at": now,
            "tasks": [],
        }

        callback_calls: list = []

        async def on_progress(plan) -> None:
            callback_calls.append(plan.status)

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get(f"/api/v1/plans/{plan_id}").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.wait_for_plan_completion(
                    plan_id, on_progress=on_progress
                )

            assert result.status == PlanStatus.COMPLETED
            assert len(callback_calls) == 1


# =============================================================================
# Comprehensive Callback Tests (Issue 1.4)
# =============================================================================


class TestCallbacksWithMultipleStateChanges:
    """Tests for callbacks with multiple state changes during polling."""

    @pytest.mark.asyncio
    async def test_callback_called_on_each_poll(
        self,
        client: WorkflowClient,
        base_url: str,
        deployment_id: UUID,
        plan_id: UUID,
        instance_id: UUID,
    ) -> None:
        """Test that callback is called on each polling iteration."""
        now = datetime.now(timezone.utc).isoformat()

        # Different states for each poll
        states = [
            {"status": "DRAFT"},
            {"status": "ACTIVE"},
            {"status": "ACTIVE"},
            {"status": "COMPLETED"},
        ]
        call_idx = 0

        def response_callback(request):
            nonlocal call_idx
            status = states[min(call_idx, len(states) - 1)]["status"]
            call_idx += 1
            return Response(
                200,
                json={
                    "id": str(plan_id),
                    "deployment_id": str(deployment_id),
                    "created_by_instance_id": str(instance_id),
                    "goal": "Test plan",
                    "constraints": {},
                    "state": {},
                    "status": status,
                    "spec_reference": None,
                    "created_at": now,
                    "updated_at": now,
                    "tasks": [],
                },
            )

        callback_statuses: list[PlanStatus] = []

        def on_progress(plan) -> None:
            callback_statuses.append(plan.status)

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get(f"/api/v1/plans/{plan_id}").mock(
                side_effect=response_callback
            )

            async with client:
                with patch("asyncio.sleep", new_callable=AsyncMock):
                    result = await client.wait_for_plan_completion(
                        plan_id, on_progress=on_progress, poll_interval=0.01
                    )

        assert result.status == PlanStatus.COMPLETED
        # Callback should have been called for each state
        assert len(callback_statuses) == 4
        assert callback_statuses[0] == PlanStatus.DRAFT
        assert callback_statuses[1] == PlanStatus.ACTIVE
        assert callback_statuses[2] == PlanStatus.ACTIVE
        assert callback_statuses[3] == PlanStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_task_callback_called_on_state_transitions(
        self,
        client: WorkflowClient,
        base_url: str,
        plan_id: UUID,
        task_id: UUID,
    ) -> None:
        """Test task callback is called during state transitions."""
        now = datetime.now(timezone.utc).isoformat()

        states = ["PENDING", "IN_PROGRESS", "IN_PROGRESS", "COMPLETED"]
        call_idx = 0

        def response_callback(request):
            nonlocal call_idx
            status = states[min(call_idx, len(states) - 1)]
            call_idx += 1
            return Response(
                200,
                json={
                    "id": str(task_id),
                    "plan_id": str(plan_id),
                    "sequence": 1,
                    "description": "Task 1",
                    "validation": "Check",
                    "assignee_agent_definition_id": None,
                    "status": status,
                    "result": "Done" if status == "COMPLETED" else None,
                    "meta": {},
                    "created_at": now,
                    "updated_at": now,
                    "assignee_agent_slug": None,
                    "assignee_agent_name": None,
                },
            )

        callback_statuses: list[PlanTaskStatus] = []

        def on_progress(task) -> None:
            callback_statuses.append(task.status)

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get(f"/api/v1/tasks/{task_id}").mock(
                side_effect=response_callback
            )

            async with client:
                with patch("asyncio.sleep", new_callable=AsyncMock):
                    result = await client.wait_for_task_completion(
                        task_id, on_progress=on_progress, poll_interval=0.01
                    )

        assert result.status == PlanTaskStatus.COMPLETED
        assert len(callback_statuses) == 4
        assert callback_statuses[0] == PlanTaskStatus.PENDING
        assert callback_statuses[1] == PlanTaskStatus.IN_PROGRESS


class TestCallbackErrorHandling:
    """Tests for error handling in callbacks."""

    @pytest.mark.asyncio
    async def test_sync_callback_exception_propagates(
        self,
        client: WorkflowClient,
        base_url: str,
        deployment_id: UUID,
        plan_id: UUID,
        instance_id: UUID,
    ) -> None:
        """Test that exceptions in sync callbacks propagate to caller."""
        now = datetime.now(timezone.utc).isoformat()
        response_data = {
            "id": str(plan_id),
            "deployment_id": str(deployment_id),
            "created_by_instance_id": str(instance_id),
            "goal": "Test plan",
            "constraints": {},
            "state": {},
            "status": "ACTIVE",
            "spec_reference": None,
            "created_at": now,
            "updated_at": now,
            "tasks": [],
        }

        def on_progress(plan) -> None:
            raise ValueError("Callback error")

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get(f"/api/v1/plans/{plan_id}").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                with pytest.raises(ValueError, match="Callback error"):
                    await client.wait_for_plan_completion(
                        plan_id, on_progress=on_progress
                    )

    @pytest.mark.asyncio
    async def test_async_callback_exception_propagates(
        self,
        client: WorkflowClient,
        base_url: str,
        deployment_id: UUID,
        plan_id: UUID,
        instance_id: UUID,
    ) -> None:
        """Test that exceptions in async callbacks propagate to caller."""
        now = datetime.now(timezone.utc).isoformat()
        response_data = {
            "id": str(plan_id),
            "deployment_id": str(deployment_id),
            "created_by_instance_id": str(instance_id),
            "goal": "Test plan",
            "constraints": {},
            "state": {},
            "status": "ACTIVE",
            "spec_reference": None,
            "created_at": now,
            "updated_at": now,
            "tasks": [],
        }

        async def on_progress(plan) -> None:
            raise RuntimeError("Async callback error")

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get(f"/api/v1/plans/{plan_id}").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                with pytest.raises(RuntimeError, match="Async callback error"):
                    await client.wait_for_plan_completion(
                        plan_id, on_progress=on_progress
                    )

    @pytest.mark.asyncio
    async def test_callback_exception_after_state_changes(
        self,
        client: WorkflowClient,
        base_url: str,
        deployment_id: UUID,
        plan_id: UUID,
        instance_id: UUID,
    ) -> None:
        """Test callback exception after several successful state changes."""
        now = datetime.now(timezone.utc).isoformat()

        def response_callback(request):
            return Response(
                200,
                json={
                    "id": str(plan_id),
                    "deployment_id": str(deployment_id),
                    "created_by_instance_id": str(instance_id),
                    "goal": "Test plan",
                    "constraints": {},
                    "state": {},
                    "status": "ACTIVE",  # Never completes
                    "spec_reference": None,
                    "created_at": now,
                    "updated_at": now,
                    "tasks": [],
                },
            )

        callback_call_count = 0

        def on_progress(plan) -> None:
            nonlocal callback_call_count
            callback_call_count += 1
            if callback_call_count == 3:
                raise ValueError("Error on third callback")

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get(f"/api/v1/plans/{plan_id}").mock(
                side_effect=response_callback
            )

            async with client:
                with patch("asyncio.sleep", new_callable=AsyncMock):
                    with pytest.raises(ValueError, match="Error on third callback"):
                        await client.wait_for_plan_completion(
                            plan_id, on_progress=on_progress, poll_interval=0.01
                        )

        assert callback_call_count == 3

    @pytest.mark.asyncio
    async def test_task_callback_exception_propagates(
        self,
        client: WorkflowClient,
        base_url: str,
        plan_id: UUID,
        task_id: UUID,
    ) -> None:
        """Test that exceptions in task callbacks propagate to caller."""
        now = datetime.now(timezone.utc).isoformat()
        response_data = {
            "id": str(task_id),
            "plan_id": str(plan_id),
            "sequence": 1,
            "description": "Task 1",
            "validation": "Check",
            "assignee_agent_definition_id": None,
            "status": "IN_PROGRESS",
            "result": None,
            "meta": {},
            "created_at": now,
            "updated_at": now,
            "assignee_agent_slug": None,
            "assignee_agent_name": None,
        }

        def on_progress(task) -> None:
            raise KeyError("Task callback error")

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get(f"/api/v1/tasks/{task_id}").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                with pytest.raises(KeyError, match="Task callback error"):
                    await client.wait_for_task_completion(
                        task_id, on_progress=on_progress
                    )


class TestAsyncCallbackEdgeCases:
    """Tests for async callback edge cases."""

    @pytest.mark.asyncio
    async def test_slow_async_callback_does_not_block_polling(
        self,
        client: WorkflowClient,
        base_url: str,
        deployment_id: UUID,
        plan_id: UUID,
        instance_id: UUID,
    ) -> None:
        """Test that slow async callbacks are properly awaited."""
        import asyncio

        now = datetime.now(timezone.utc).isoformat()
        call_count = 0

        def response_callback(request):
            nonlocal call_count
            call_count += 1
            status = "COMPLETED" if call_count >= 2 else "ACTIVE"
            return Response(
                200,
                json={
                    "id": str(plan_id),
                    "deployment_id": str(deployment_id),
                    "created_by_instance_id": str(instance_id),
                    "goal": "Test plan",
                    "constraints": {},
                    "state": {},
                    "status": status,
                    "spec_reference": None,
                    "created_at": now,
                    "updated_at": now,
                    "tasks": [],
                },
            )

        callback_completed = []

        async def slow_callback(plan) -> None:
            await asyncio.sleep(0.01)  # Simulate slow async work
            callback_completed.append(plan.status)

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get(f"/api/v1/plans/{plan_id}").mock(
                side_effect=response_callback
            )

            async with client:
                with patch("asyncio.sleep", new_callable=AsyncMock):
                    result = await client.wait_for_plan_completion(
                        plan_id, on_progress=slow_callback, poll_interval=0.01
                    )

        assert result.status == PlanStatus.COMPLETED
        # Both callbacks should have completed
        assert len(callback_completed) == 2

    @pytest.mark.asyncio
    async def test_callback_with_coroutine_return_value(
        self,
        client: WorkflowClient,
        base_url: str,
        deployment_id: UUID,
        plan_id: UUID,
        instance_id: UUID,
    ) -> None:
        """Test callback that returns a coroutine is properly awaited."""
        now = datetime.now(timezone.utc).isoformat()
        response_data = {
            "id": str(plan_id),
            "deployment_id": str(deployment_id),
            "created_by_instance_id": str(instance_id),
            "goal": "Test plan",
            "constraints": {},
            "state": {},
            "status": "COMPLETED",
            "spec_reference": None,
            "created_at": now,
            "updated_at": now,
            "tasks": [],
        }

        callback_result = []

        async def async_callback(plan):
            callback_result.append(f"processed_{plan.status.value}")

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get(f"/api/v1/plans/{plan_id}").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.wait_for_plan_completion(
                    plan_id, on_progress=async_callback
                )

        assert result.status == PlanStatus.COMPLETED
        assert callback_result == ["processed_COMPLETED"]

    @pytest.mark.asyncio
    async def test_none_callback_is_handled(
        self,
        client: WorkflowClient,
        base_url: str,
        deployment_id: UUID,
        plan_id: UUID,
        instance_id: UUID,
    ) -> None:
        """Test that None callback is handled gracefully."""
        now = datetime.now(timezone.utc).isoformat()
        response_data = {
            "id": str(plan_id),
            "deployment_id": str(deployment_id),
            "created_by_instance_id": str(instance_id),
            "goal": "Test plan",
            "constraints": {},
            "state": {},
            "status": "COMPLETED",
            "spec_reference": None,
            "created_at": now,
            "updated_at": now,
            "tasks": [],
        }

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get(f"/api/v1/plans/{plan_id}").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                # Explicitly passing None should work
                result = await client.wait_for_plan_completion(
                    plan_id, on_progress=None
                )

        assert result.status == PlanStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_callback_receives_full_state_object(
        self,
        client: WorkflowClient,
        base_url: str,
        deployment_id: UUID,
        plan_id: UUID,
        instance_id: UUID,
    ) -> None:
        """Test that callback receives the full state object with all fields."""
        now = datetime.now(timezone.utc).isoformat()
        response_data = {
            "id": str(plan_id),
            "deployment_id": str(deployment_id),
            "created_by_instance_id": str(instance_id),
            "goal": "Test plan with full data",
            "constraints": {"max_time": 3600},
            "state": {"progress": 50},
            "status": "COMPLETED",
            "spec_reference": "spec-123",
            "created_at": now,
            "updated_at": now,
            "tasks": [],
        }

        received_plan = None

        def on_progress(plan) -> None:
            nonlocal received_plan
            received_plan = plan

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get(f"/api/v1/plans/{plan_id}").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                await client.wait_for_plan_completion(plan_id, on_progress=on_progress)

        # Verify callback received full object
        assert received_plan is not None
        assert received_plan.id == plan_id
        assert received_plan.goal == "Test plan with full data"
        assert received_plan.constraints == {"max_time": 3600}
        assert received_plan.state == {"progress": 50}
        assert received_plan.spec_reference == "spec-123"

    @pytest.mark.asyncio
    async def test_mixed_sync_async_callbacks_handled(
        self,
        client: WorkflowClient,
        base_url: str,
        deployment_id: UUID,
        plan_id: UUID,
        instance_id: UUID,
    ) -> None:
        """Test that the same endpoint handles both sync and async callbacks."""
        now = datetime.now(timezone.utc).isoformat()
        response_data = {
            "id": str(plan_id),
            "deployment_id": str(deployment_id),
            "created_by_instance_id": str(instance_id),
            "goal": "Test plan",
            "constraints": {},
            "state": {},
            "status": "COMPLETED",
            "spec_reference": None,
            "created_at": now,
            "updated_at": now,
            "tasks": [],
        }

        sync_calls = []
        async_calls = []

        def sync_callback(plan) -> None:
            sync_calls.append(plan.status)

        async def async_callback(plan) -> None:
            async_calls.append(plan.status)

        # Test sync callback
        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get(f"/api/v1/plans/{plan_id}").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                await client.wait_for_plan_completion(
                    plan_id, on_progress=sync_callback
                )

        # Test async callback
        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get(f"/api/v1/plans/{plan_id}").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                await client.wait_for_plan_completion(
                    plan_id, on_progress=async_callback
                )

        assert len(sync_calls) == 1
        assert len(async_calls) == 1
        assert sync_calls[0] == PlanStatus.COMPLETED
        assert async_calls[0] == PlanStatus.COMPLETED
