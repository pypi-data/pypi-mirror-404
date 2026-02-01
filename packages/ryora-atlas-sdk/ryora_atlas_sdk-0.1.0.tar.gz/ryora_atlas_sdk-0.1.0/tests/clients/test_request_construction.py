"""Integration tests for request construction validation.

These tests use pytest-httpserver to run a real HTTP server and validate
that requests are constructed correctly (body, headers, path, query params).

This addresses issue 1.1 from the v0.1.0 release review: "Excessive Mocking"
where tests mock the entire HTTP layer without verifying actual request construction.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

import pytest
from pytest_httpserver import HTTPServer
from werkzeug import Request, Response

from atlas_sdk.clients.control_plane import ControlPlaneClient
from atlas_sdk.models.control_plane import (
    AgentClassCreate,
    AgentClassUpdate,
)
from atlas_sdk.models.deployment import DeploymentCreate
from atlas_sdk.models.enums import AgentDefinitionStatus, SystemPromptStatus

if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture(scope="session")
def httpserver_listen_address() -> tuple[str, int]:
    """Configure httpserver to listen on a specific port."""
    return ("127.0.0.1", 0)  # Use any available port


@pytest.fixture
def client(httpserver: HTTPServer) -> Generator[ControlPlaneClient, None, None]:
    """Create a client pointing to the test server."""
    yield ControlPlaneClient(base_url=httpserver.url_for(""))


class TestAgentClassRequestConstruction:
    """Validate request construction for agent class operations."""

    @pytest.mark.asyncio
    async def test_create_agent_class_request_body(
        self, client: ControlPlaneClient, httpserver: HTTPServer
    ) -> None:
        """Verify request body contains correct JSON from Pydantic model."""
        agent_class_id = uuid4()
        now = datetime.now(timezone.utc).isoformat()
        captured_body: dict | None = None

        def handler(request: Request) -> Response:
            nonlocal captured_body
            captured_body = json.loads(request.data)
            return Response(
                json.dumps(
                    {
                        "id": str(agent_class_id),
                        "name": "BugHunter",
                        "description": "Security scanner",
                        "created_at": now,
                        "updated_at": now,
                    }
                ),
                status=200,
                content_type="application/json",
            )

        httpserver.expect_request(
            "/api/v1/agent-classes",
            method="POST",
        ).respond_with_handler(handler)

        async with client:
            await client.create_agent_class(
                AgentClassCreate(name="BugHunter", description="Security scanner")
            )

        assert captured_body is not None
        assert captured_body["name"] == "BugHunter"
        assert captured_body["description"] == "Security scanner"
        # Verify exclude_unset behavior - only set fields should be present
        assert set(captured_body.keys()) == {"name", "description"}

    @pytest.mark.asyncio
    async def test_create_agent_class_minimal_body(
        self, client: ControlPlaneClient, httpserver: HTTPServer
    ) -> None:
        """Verify minimal request body when optional fields are not set."""
        agent_class_id = uuid4()
        now = datetime.now(timezone.utc).isoformat()
        captured_body: dict | None = None

        def handler(request: Request) -> Response:
            nonlocal captured_body
            captured_body = json.loads(request.data)
            return Response(
                json.dumps(
                    {
                        "id": str(agent_class_id),
                        "name": "MinimalClass",
                        "description": None,
                        "created_at": now,
                        "updated_at": now,
                    }
                ),
                status=200,
                content_type="application/json",
            )

        httpserver.expect_request(
            "/api/v1/agent-classes",
            method="POST",
        ).respond_with_handler(handler)

        async with client:
            # Only provide required field, leave description unset
            await client.create_agent_class(AgentClassCreate(name="MinimalClass"))

        assert captured_body is not None
        # Only 'name' should be in body since description was not set
        assert captured_body == {"name": "MinimalClass"}
        assert "description" not in captured_body  # Not included due to exclude_unset

    @pytest.mark.asyncio
    async def test_create_agent_class_idempotency_key_header(
        self, client: ControlPlaneClient, httpserver: HTTPServer
    ) -> None:
        """Verify Idempotency-Key header is correctly set."""
        agent_class_id = uuid4()
        now = datetime.now(timezone.utc).isoformat()
        captured_headers: dict | None = None

        def handler(request: Request) -> Response:
            nonlocal captured_headers
            captured_headers = dict(request.headers)
            return Response(
                json.dumps(
                    {
                        "id": str(agent_class_id),
                        "name": "Test",
                        "description": None,
                        "created_at": now,
                        "updated_at": now,
                    }
                ),
                status=200,
                content_type="application/json",
            )

        httpserver.expect_request(
            "/api/v1/agent-classes",
            method="POST",
        ).respond_with_handler(handler)

        async with client:
            await client.create_agent_class(
                AgentClassCreate(name="Test"),
                idempotency_key="my-unique-key-123",
            )

        assert captured_headers is not None
        assert "Idempotency-Key" in captured_headers
        assert captured_headers["Idempotency-Key"] == "my-unique-key-123"

    @pytest.mark.asyncio
    async def test_create_agent_class_request_id_header(
        self, client: ControlPlaneClient, httpserver: HTTPServer
    ) -> None:
        """Verify X-Request-ID header is automatically generated."""
        agent_class_id = uuid4()
        now = datetime.now(timezone.utc).isoformat()
        captured_headers: dict | None = None

        def handler(request: Request) -> Response:
            nonlocal captured_headers
            captured_headers = dict(request.headers)
            return Response(
                json.dumps(
                    {
                        "id": str(agent_class_id),
                        "name": "Test",
                        "description": None,
                        "created_at": now,
                        "updated_at": now,
                    }
                ),
                status=200,
                content_type="application/json",
            )

        httpserver.expect_request(
            "/api/v1/agent-classes",
            method="POST",
        ).respond_with_handler(handler)

        async with client:
            await client.create_agent_class(AgentClassCreate(name="Test"))

        assert captured_headers is not None
        assert "X-Request-Id" in captured_headers
        # Verify it's a valid UUID format
        request_id = captured_headers["X-Request-Id"]
        UUID(request_id)  # Will raise if not valid UUID

    @pytest.mark.asyncio
    async def test_get_agent_class_url_path_construction(
        self, client: ControlPlaneClient, httpserver: HTTPServer
    ) -> None:
        """Verify URL path correctly includes UUID parameter."""
        agent_class_id = uuid4()
        now = datetime.now(timezone.utc).isoformat()
        captured_path: str | None = None

        def handler(request: Request) -> Response:
            nonlocal captured_path
            captured_path = request.path
            return Response(
                json.dumps(
                    {
                        "id": str(agent_class_id),
                        "name": "Test",
                        "description": None,
                        "created_at": now,
                        "updated_at": now,
                    }
                ),
                status=200,
                content_type="application/json",
            )

        httpserver.expect_request(
            f"/api/v1/agent-classes/{agent_class_id}",
            method="GET",
        ).respond_with_handler(handler)

        async with client:
            await client.get_agent_class(agent_class_id)

        assert captured_path == f"/api/v1/agent-classes/{agent_class_id}"

    @pytest.mark.asyncio
    async def test_list_agent_classes_query_params(
        self, client: ControlPlaneClient, httpserver: HTTPServer
    ) -> None:
        """Verify query parameters are correctly serialized."""
        captured_args: dict | None = None

        def handler(request: Request) -> Response:
            nonlocal captured_args
            captured_args = dict(request.args)
            return Response(
                json.dumps([]),
                status=200,
                content_type="application/json",
            )

        httpserver.expect_request(
            "/api/v1/agent-classes",
            method="GET",
        ).respond_with_handler(handler)

        async with client:
            await client.list_agent_classes(limit=50, offset=25)

        assert captured_args is not None
        assert captured_args["limit"] == "50"
        assert captured_args["offset"] == "25"

    @pytest.mark.asyncio
    async def test_update_agent_class_patch_body(
        self, client: ControlPlaneClient, httpserver: HTTPServer
    ) -> None:
        """Verify PATCH request only includes fields that were set."""
        agent_class_id = uuid4()
        now = datetime.now(timezone.utc).isoformat()
        captured_body: dict | None = None
        captured_method: str | None = None

        def handler(request: Request) -> Response:
            nonlocal captured_body, captured_method
            captured_body = json.loads(request.data)
            captured_method = request.method
            return Response(
                json.dumps(
                    {
                        "id": str(agent_class_id),
                        "name": "UpdatedName",
                        "description": "Original description",
                        "created_at": now,
                        "updated_at": now,
                    }
                ),
                status=200,
                content_type="application/json",
            )

        httpserver.expect_request(
            f"/api/v1/agent-classes/{agent_class_id}",
            method="PATCH",
        ).respond_with_handler(handler)

        async with client:
            # Only update name, leave description unchanged
            await client.update_agent_class(
                agent_class_id,
                AgentClassUpdate(name="UpdatedName"),
            )

        assert captured_method == "PATCH"
        assert captured_body is not None
        # Only 'name' should be in body due to exclude_unset
        assert captured_body == {"name": "UpdatedName"}
        assert "description" not in captured_body

    @pytest.mark.asyncio
    async def test_delete_agent_class_method(
        self, client: ControlPlaneClient, httpserver: HTTPServer
    ) -> None:
        """Verify DELETE request uses correct method and path."""
        agent_class_id = uuid4()
        captured_method: str | None = None
        captured_path: str | None = None

        def handler(request: Request) -> Response:
            nonlocal captured_method, captured_path
            captured_method = request.method
            captured_path = request.path
            return Response("", status=204)

        httpserver.expect_request(
            f"/api/v1/agent-classes/{agent_class_id}",
            method="DELETE",
        ).respond_with_handler(handler)

        async with client:
            await client.delete_agent_class(agent_class_id)

        assert captured_method == "DELETE"
        assert captured_path == f"/api/v1/agent-classes/{agent_class_id}"


class TestAgentDefinitionRequestConstruction:
    """Validate request construction for agent definition operations."""

    @pytest.mark.asyncio
    async def test_list_agent_definitions_with_status_filter(
        self, client: ControlPlaneClient, httpserver: HTTPServer
    ) -> None:
        """Verify status enum is correctly serialized to query param."""
        captured_args: dict | None = None

        def handler(request: Request) -> Response:
            nonlocal captured_args
            captured_args = dict(request.args)
            return Response(
                json.dumps([]),
                status=200,
                content_type="application/json",
            )

        httpserver.expect_request(
            "/api/v1/agent-definitions",
            method="GET",
        ).respond_with_handler(handler)

        async with client:
            await client.list_agent_definitions(
                status=AgentDefinitionStatus.PUBLISHED,
                limit=10,
                offset=5,
            )

        assert captured_args is not None
        assert captured_args["status"] == "published"  # Enum value, not name
        assert captured_args["limit"] == "10"
        assert captured_args["offset"] == "5"

    @pytest.mark.asyncio
    async def test_add_tools_to_definition_uuid_serialization(
        self, client: ControlPlaneClient, httpserver: HTTPServer
    ) -> None:
        """Verify UUID list is correctly serialized to JSON strings."""
        definition_id = uuid4()
        tool_id_1 = uuid4()
        tool_id_2 = uuid4()
        now = datetime.now(timezone.utc).isoformat()
        captured_body: dict | None = None

        def handler(request: Request) -> Response:
            nonlocal captured_body
            captured_body = json.loads(request.data)
            return Response(
                json.dumps(
                    {
                        "id": str(definition_id),
                        "agent_class_id": str(uuid4()),
                        "name": "test-def",
                        "slug": "test-def",
                        "description": None,
                        "status": "draft",
                        "execution_mode": "ephemeral",
                        "model_provider_id": str(uuid4()),
                        "model_name": "gpt-4",
                        "system_prompt_id": None,
                        "structured_output_id": None,
                        "config": {},
                        "allow_outbound_a2a": False,
                        "created_at": now,
                        "updated_at": now,
                    }
                ),
                status=200,
                content_type="application/json",
            )

        httpserver.expect_request(
            f"/api/v1/agent-definitions/{definition_id}/tools",
            method="POST",
        ).respond_with_handler(handler)

        async with client:
            await client.add_tools_to_definition(definition_id, [tool_id_1, tool_id_2])

        assert captured_body is not None
        assert "tool_ids" in captured_body
        # UUIDs should be serialized as strings
        assert captured_body["tool_ids"] == [str(tool_id_1), str(tool_id_2)]


class TestSystemPromptRequestConstruction:
    """Validate request construction for system prompt operations."""

    @pytest.mark.asyncio
    async def test_list_system_prompts_with_filters(
        self, client: ControlPlaneClient, httpserver: HTTPServer
    ) -> None:
        """Verify multiple filter params are correctly serialized."""
        agent_class_id = uuid4()
        captured_args: dict | None = None

        def handler(request: Request) -> Response:
            nonlocal captured_args
            captured_args = dict(request.args)
            return Response(
                json.dumps([]),
                status=200,
                content_type="application/json",
            )

        httpserver.expect_request(
            "/api/v1/system-prompts",
            method="GET",
        ).respond_with_handler(handler)

        async with client:
            await client.list_system_prompts(
                agent_class_id=agent_class_id,
                status=SystemPromptStatus.PUBLISHED,
                limit=20,
                offset=10,
            )

        assert captured_args is not None
        assert captured_args["agent_class_id"] == str(agent_class_id)
        assert captured_args["status"] == "published"
        assert captured_args["limit"] == "20"
        assert captured_args["offset"] == "10"


class TestDeploymentRequestConstruction:
    """Validate request construction for deployment operations."""

    @pytest.mark.asyncio
    async def test_list_deployments_boolean_param(
        self, client: ControlPlaneClient, httpserver: HTTPServer
    ) -> None:
        """Verify boolean params are correctly serialized."""
        captured_args: dict | None = None

        def handler(request: Request) -> Response:
            nonlocal captured_args
            captured_args = dict(request.args)
            return Response(
                json.dumps([]),
                status=200,
                content_type="application/json",
            )

        httpserver.expect_request(
            "/api/v1/deployments",
            method="GET",
        ).respond_with_handler(handler)

        async with client:
            await client.list_deployments(
                environment="production",
                active_only=True,
                limit=50,
                offset=0,
            )

        assert captured_args is not None
        assert captured_args["environment"] == "production"
        # httpx serializes booleans as "true"/"false"
        assert captured_args["active_only"] == "true"
        assert captured_args["limit"] == "50"
        assert captured_args["offset"] == "0"

    @pytest.mark.asyncio
    async def test_create_deployment_full_body(
        self, client: ControlPlaneClient, httpserver: HTTPServer
    ) -> None:
        """Verify complex model serialization."""
        deployment_id = uuid4()
        definition_id = uuid4()
        now = datetime.now(timezone.utc).isoformat()
        captured_body: dict | None = None

        def handler(request: Request) -> Response:
            nonlocal captured_body
            captured_body = json.loads(request.data)
            return Response(
                json.dumps(
                    {
                        "id": str(deployment_id),
                        "agent_definition_id": str(definition_id),
                        "name": "prod-deployment",
                        "description": "Production deployment",
                        "environment": "production",
                        "status": "spawning",
                        "config": {"replicas": 3},
                        "project_context": {},
                        "created_at": now,
                        "updated_at": now,
                    }
                ),
                status=200,
                content_type="application/json",
            )

        httpserver.expect_request(
            "/api/v1/deployments",
            method="POST",
        ).respond_with_handler(handler)

        async with client:
            await client.create_deployment(
                DeploymentCreate(
                    agent_definition_id=definition_id,
                    name="prod-deployment",
                    description="Production deployment",
                    environment="production",
                    config={"replicas": 3},
                )
            )

        assert captured_body is not None
        # UUID should be serialized as string in JSON
        assert captured_body["agent_definition_id"] == str(definition_id)
        assert captured_body["name"] == "prod-deployment"
        assert captured_body["description"] == "Production deployment"
        assert captured_body["environment"] == "production"
        assert captured_body["config"] == {"replicas": 3}


class TestContentTypeHeaders:
    """Validate Content-Type headers are correctly set."""

    @pytest.mark.asyncio
    async def test_post_request_content_type(
        self, client: ControlPlaneClient, httpserver: HTTPServer
    ) -> None:
        """Verify POST requests have correct Content-Type header."""
        agent_class_id = uuid4()
        now = datetime.now(timezone.utc).isoformat()
        captured_headers: dict | None = None

        def handler(request: Request) -> Response:
            nonlocal captured_headers
            captured_headers = dict(request.headers)
            return Response(
                json.dumps(
                    {
                        "id": str(agent_class_id),
                        "name": "Test",
                        "description": None,
                        "created_at": now,
                        "updated_at": now,
                    }
                ),
                status=200,
                content_type="application/json",
            )

        httpserver.expect_request(
            "/api/v1/agent-classes",
            method="POST",
        ).respond_with_handler(handler)

        async with client:
            await client.create_agent_class(AgentClassCreate(name="Test"))

        assert captured_headers is not None
        assert "Content-Type" in captured_headers
        assert "application/json" in captured_headers["Content-Type"]

    @pytest.mark.asyncio
    async def test_patch_request_content_type(
        self, client: ControlPlaneClient, httpserver: HTTPServer
    ) -> None:
        """Verify PATCH requests have correct Content-Type header."""
        agent_class_id = uuid4()
        now = datetime.now(timezone.utc).isoformat()
        captured_headers: dict | None = None

        def handler(request: Request) -> Response:
            nonlocal captured_headers
            captured_headers = dict(request.headers)
            return Response(
                json.dumps(
                    {
                        "id": str(agent_class_id),
                        "name": "Updated",
                        "description": None,
                        "created_at": now,
                        "updated_at": now,
                    }
                ),
                status=200,
                content_type="application/json",
            )

        httpserver.expect_request(
            f"/api/v1/agent-classes/{agent_class_id}",
            method="PATCH",
        ).respond_with_handler(handler)

        async with client:
            await client.update_agent_class(
                agent_class_id, AgentClassUpdate(name="Updated")
            )

        assert captured_headers is not None
        assert "Content-Type" in captured_headers
        assert "application/json" in captured_headers["Content-Type"]
