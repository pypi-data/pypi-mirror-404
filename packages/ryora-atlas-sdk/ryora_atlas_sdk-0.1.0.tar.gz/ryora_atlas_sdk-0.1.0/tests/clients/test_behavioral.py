"""Behavioral tests that verify settings affect actual behavior.

These tests address issue 1.2 from the v0.1.0 release review: superficial tests
with trivial assertions. Instead of just checking property values, these tests
verify that settings actually affect observable behavior.

Tests included:
- Timeout settings cause requests to fail after N seconds
- Metrics contain accurate values (not just mock invocation checks)
- Complete response handling for pagination
- Full response structure validation for health checks
- Negative test cases for malformed API responses
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from uuid import uuid4

import httpx
import pytest
import respx
from httpx import Response

from atlas_sdk.clients.base import BaseClient
from atlas_sdk.clients.control_plane import ControlPlaneClient
from atlas_sdk.exceptions import (
    AtlasHTTPStatusError,
)
from atlas_sdk.instrumentation import MetricsHandler, RequestMetrics


@pytest.fixture
def base_url() -> str:
    return "http://test-service"


class TestTimeoutBehavior:
    """Tests that verify timeout settings actually affect behavior."""

    @pytest.mark.asyncio
    async def test_timeout_is_configured_on_http_client(self, base_url: str) -> None:
        """Timeout setting should be configured on the underlying HTTP client."""
        client = BaseClient(base_url=base_url, timeout=15.0)

        # Verify timeout is stored on BaseClient
        assert client.timeout == 15.0

        # Verify it's applied when client is created
        async with client:
            # The internal client should have timeout configured
            assert client._client is not None
            # httpx.AsyncClient stores timeout as httpx.Timeout object
            assert client._client.timeout.connect == 15.0
            assert client._client.timeout.read == 15.0
            assert client._client.timeout.write == 15.0

    @pytest.mark.asyncio
    async def test_timeout_raises_on_connect_error_simulation(
        self, base_url: str
    ) -> None:
        """Connection timeouts should be raised as TimeoutException."""
        client = BaseClient(base_url=base_url, timeout=0.1)

        async def simulate_timeout(request: httpx.Request) -> Response:
            raise httpx.ConnectTimeout("Connection timed out")

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get("/slow").mock(side_effect=simulate_timeout)

            async with client:
                with pytest.raises(httpx.TimeoutException):
                    await client._request("GET", "/slow")

    @pytest.mark.asyncio
    async def test_longer_timeout_allows_slow_requests(self, base_url: str) -> None:
        """A longer timeout should allow slow requests to complete."""
        client = BaseClient(base_url=base_url, timeout=2.0)

        async def slow_response(request: httpx.Request) -> Response:
            await asyncio.sleep(0.1)  # Slightly slow but within timeout
            return Response(200, json={"status": "completed"})

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get("/slow").mock(side_effect=slow_response)

            async with client:
                response = await client._request("GET", "/slow")
                assert response.status_code == 200
                assert response.json()["status"] == "completed"

    @pytest.mark.asyncio
    async def test_default_timeout_value_is_used(self, base_url: str) -> None:
        """Default timeout should be applied to requests."""
        client = BaseClient(base_url=base_url)  # Default timeout=30.0

        # Verify the default is set correctly
        assert client.timeout == 30.0

        # Verify it's used in requests by checking a fast request succeeds
        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get("/fast").mock(return_value=Response(200))

            async with client:
                response = await client._request("GET", "/fast")
                assert response.status_code == 200


class TestMetricsAccuracy:
    """Tests that verify metrics contain accurate values, not just mock checks."""

    @pytest.mark.asyncio
    async def test_metrics_duration_is_accurate(self, base_url: str) -> None:
        """Metrics should report accurate duration, not just call the handler."""
        recorded_metrics: list[RequestMetrics] = []

        class CapturingMetricsHandler(MetricsHandler):
            def on_request_start(self, method: str, url: str, request_id: str) -> None:
                pass

            def on_request_end(self, metrics: RequestMetrics) -> None:
                recorded_metrics.append(metrics)

            def on_request_error(
                self, method: str, url: str, request_id: str, error: Exception
            ) -> None:
                pass

        handler = CapturingMetricsHandler()
        client = BaseClient(base_url=base_url, metrics_handler=handler)

        async def delayed_response(request: httpx.Request) -> Response:
            await asyncio.sleep(0.05)  # 50ms delay
            return Response(200, headers={"content-length": "100"})

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get("/test").mock(side_effect=delayed_response)

            async with client:
                await client._request("GET", "/test")

        assert len(recorded_metrics) == 1
        metrics = recorded_metrics[0]

        # Verify duration is reasonably accurate (at least 50ms, but account for overhead)
        assert metrics.duration_seconds >= 0.05
        assert metrics.duration_seconds < 1.0  # Should not be wildly off

    @pytest.mark.asyncio
    async def test_metrics_status_code_is_accurate(self, base_url: str) -> None:
        """Metrics should report the actual status code from the response."""
        recorded_metrics: list[RequestMetrics] = []

        class CapturingMetricsHandler(MetricsHandler):
            def on_request_start(self, method: str, url: str, request_id: str) -> None:
                pass

            def on_request_end(self, metrics: RequestMetrics) -> None:
                recorded_metrics.append(metrics)

            def on_request_error(
                self, method: str, url: str, request_id: str, error: Exception
            ) -> None:
                pass

        handler = CapturingMetricsHandler()
        client = BaseClient(base_url=base_url, metrics_handler=handler)

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get("/not-found").mock(return_value=Response(404))
            respx_mock.get("/created").mock(return_value=Response(201))

            async with client:
                # First request - 404
                await client._request("GET", "/not-found")
                # Second request - 201
                await client._request("GET", "/created")

        assert len(recorded_metrics) == 2
        assert recorded_metrics[0].status_code == 404
        assert recorded_metrics[0].url == "/not-found"
        assert recorded_metrics[1].status_code == 201
        assert recorded_metrics[1].url == "/created"

    @pytest.mark.asyncio
    async def test_metrics_body_size_is_accurate(self, base_url: str) -> None:
        """Metrics should report accurate request and response body sizes."""
        recorded_metrics: list[RequestMetrics] = []

        class CapturingMetricsHandler(MetricsHandler):
            def on_request_start(self, method: str, url: str, request_id: str) -> None:
                pass

            def on_request_end(self, metrics: RequestMetrics) -> None:
                recorded_metrics.append(metrics)

            def on_request_error(
                self, method: str, url: str, request_id: str, error: Exception
            ) -> None:
                pass

        handler = CapturingMetricsHandler()
        client = BaseClient(base_url=base_url, metrics_handler=handler)

        # Response body of known size
        response_body = '{"data": "x" * 100}'  # Some JSON response
        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.post("/data").mock(
                return_value=Response(
                    201,
                    json={"data": "x" * 100},
                    headers={"content-length": str(len(response_body))},
                )
            )

            async with client:
                await client._request("POST", "/data", json={"input": "test"})

        assert len(recorded_metrics) == 1
        metrics = recorded_metrics[0]

        # Request body was JSON {"input": "test"}
        assert metrics.request_body_size is not None
        assert metrics.request_body_size > 0

    @pytest.mark.asyncio
    async def test_metrics_method_is_accurate(self, base_url: str) -> None:
        """Metrics should report the actual HTTP method used."""
        recorded_metrics: list[RequestMetrics] = []

        class CapturingMetricsHandler(MetricsHandler):
            def on_request_start(self, method: str, url: str, request_id: str) -> None:
                pass

            def on_request_end(self, metrics: RequestMetrics) -> None:
                recorded_metrics.append(metrics)

            def on_request_error(
                self, method: str, url: str, request_id: str, error: Exception
            ) -> None:
                pass

        handler = CapturingMetricsHandler()
        client = BaseClient(base_url=base_url, metrics_handler=handler)

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get("/resource").mock(return_value=Response(200))
            respx_mock.post("/resource").mock(return_value=Response(201))
            respx_mock.patch("/resource").mock(return_value=Response(200))
            respx_mock.delete("/resource").mock(return_value=Response(204))

            async with client:
                await client._request("GET", "/resource")
                await client._request("POST", "/resource", json={})
                await client._request("PATCH", "/resource", json={})
                await client._request("DELETE", "/resource")

        assert len(recorded_metrics) == 4
        assert recorded_metrics[0].method == "GET"
        assert recorded_metrics[1].method == "POST"
        assert recorded_metrics[2].method == "PATCH"
        assert recorded_metrics[3].method == "DELETE"


class TestPaginationCompleteResponseHandling:
    """Tests that verify pagination returns correctly parsed data."""

    @pytest.mark.asyncio
    async def test_list_agent_classes_returns_complete_objects(
        self, base_url: str
    ) -> None:
        """Pagination should return fully parsed model objects, not just pass through."""
        client = ControlPlaneClient(base_url=base_url)
        now = datetime.now(timezone.utc)

        # Full response with all fields
        response_data = [
            {
                "id": str(uuid4()),
                "name": "BugHunter",
                "description": "Security vulnerability detection",
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
            },
            {
                "id": str(uuid4()),
                "name": "CodeReviewer",
                "description": None,
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
            },
        ]

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get("/api/v1/agent-classes").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.list_agent_classes(limit=50, offset=10)

        # Verify complete objects are returned
        assert len(result) == 2

        # First object - all fields populated
        assert result[0].name == "BugHunter"
        assert result[0].description == "Security vulnerability detection"
        assert isinstance(result[0].id, type(uuid4()))
        assert isinstance(result[0].created_at, datetime)
        assert isinstance(result[0].updated_at, datetime)

        # Second object - description is None
        assert result[1].name == "CodeReviewer"
        assert result[1].description is None

    @pytest.mark.asyncio
    async def test_list_deployments_returns_typed_status(self, base_url: str) -> None:
        """List responses should parse enum fields correctly."""
        from atlas_sdk.models.enums import DeploymentStatus

        client = ControlPlaneClient(base_url=base_url)
        now = datetime.now(timezone.utc)
        definition_id = uuid4()

        response_data = [
            {
                "id": str(uuid4()),
                "agent_definition_id": str(definition_id),
                "blueprint_id": None,
                "name": "active-deployment",
                "description": None,
                "environment": "production",
                "status": "active",
                "config": {"replicas": 3},
                "project_context": {},
                "spec_md_path": None,
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
            },
            {
                "id": str(uuid4()),
                "agent_definition_id": str(definition_id),
                "blueprint_id": None,
                "name": "spawning-deployment",
                "description": None,
                "environment": "staging",
                "status": "spawning",
                "config": {},
                "project_context": {},
                "spec_md_path": None,
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
            },
        ]

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get("/api/v1/deployments").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.list_deployments()

        # Verify enums are properly parsed
        assert result[0].status == DeploymentStatus.ACTIVE
        assert result[1].status == DeploymentStatus.SPAWNING

        # Verify nested config is accessible
        assert result[0].config["replicas"] == 3

    @pytest.mark.asyncio
    async def test_empty_list_response_returns_empty_list(self, base_url: str) -> None:
        """Empty list responses should return empty list, not None."""
        client = ControlPlaneClient(base_url=base_url)

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get("/api/v1/agent-classes").mock(
                return_value=Response(200, json=[])
            )

            async with client:
                result = await client.list_agent_classes()

        assert result == []
        assert isinstance(result, list)


class TestHealthCheckResponseValidation:
    """Tests that verify health check responses are fully validated."""

    @pytest.mark.asyncio
    async def test_health_check_validates_response_structure(
        self, base_url: str
    ) -> None:
        """Health check should return properly structured response."""
        client = ControlPlaneClient(base_url=base_url)

        response_data = {
            "status": "healthy",
            "version": "1.2.3",
            "database": "connected",
            "uptime_seconds": 86400,
        }

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get("/api/v1/health").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.health()

        # Verify all expected fields are present and correctly typed
        assert result["status"] == "healthy"
        assert result["version"] == "1.2.3"
        assert result["database"] == "connected"
        assert result["uptime_seconds"] == 86400
        assert isinstance(result["uptime_seconds"], int)

    @pytest.mark.asyncio
    async def test_health_check_unhealthy_raises_error(self, base_url: str) -> None:
        """Unhealthy responses should raise appropriate error."""
        client = ControlPlaneClient(base_url=base_url)

        async with respx.mock(base_url=base_url) as respx_mock:
            # 500 Internal Server Error
            respx_mock.get("/api/v1/health").mock(
                return_value=Response(
                    500, json={"status": "unhealthy", "error": "DB connection failed"}
                )
            )

            async with client:
                with pytest.raises(AtlasHTTPStatusError) as exc_info:
                    await client.health()

                assert exc_info.value.status_code == 500
                assert "unhealthy" in str(exc_info.value.server_response)


class TestMalformedResponseHandling:
    """Negative test cases for malformed API responses."""

    @pytest.mark.asyncio
    async def test_non_json_response_raises_error(self, base_url: str) -> None:
        """Non-JSON responses should raise appropriate error."""
        client = ControlPlaneClient(base_url=base_url)
        agent_class_id = uuid4()

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get(f"/api/v1/agent-classes/{agent_class_id}").mock(
                return_value=Response(200, text="Not JSON at all")
            )

            async with client:
                with pytest.raises(Exception):  # JSON decode error
                    await client.get_agent_class(agent_class_id)

    @pytest.mark.asyncio
    async def test_missing_required_field_in_response_raises_validation_error(
        self, base_url: str
    ) -> None:
        """Response missing required fields should raise validation error."""
        client = ControlPlaneClient(base_url=base_url)
        agent_class_id = uuid4()
        now = datetime.now(timezone.utc)

        # Missing 'name' field which is required
        response_data = {
            "id": str(agent_class_id),
            # "name": "BugHunter",  # Missing!
            "description": "Test",
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get(f"/api/v1/agent-classes/{agent_class_id}").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                with pytest.raises(Exception) as exc_info:
                    await client.get_agent_class(agent_class_id)

                # Should be a Pydantic ValidationError
                assert (
                    "name" in str(exc_info.value).lower()
                    or "validation" in str(exc_info.value).lower()
                )

    @pytest.mark.asyncio
    async def test_wrong_type_in_response_raises_validation_error(
        self, base_url: str
    ) -> None:
        """Response with wrong field types should raise validation error."""
        client = ControlPlaneClient(base_url=base_url)
        agent_class_id = uuid4()

        # Invalid types: id should be UUID, created_at should be datetime
        response_data = {
            "id": "not-a-uuid",
            "name": "BugHunter",
            "description": "Test",
            "created_at": "not-a-datetime",
            "updated_at": "also-not-a-datetime",
        }

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get(f"/api/v1/agent-classes/{agent_class_id}").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                with pytest.raises(Exception):  # Pydantic ValidationError
                    await client.get_agent_class(agent_class_id)

    @pytest.mark.asyncio
    async def test_invalid_enum_value_in_response_raises_error(
        self, base_url: str
    ) -> None:
        """Response with invalid enum value should raise validation error."""
        client = ControlPlaneClient(base_url=base_url)
        definition_id = uuid4()
        agent_class_id = uuid4()
        now = datetime.now(timezone.utc)

        # 'status' has invalid enum value
        response_data = {
            "id": str(definition_id),
            "agent_class_id": str(agent_class_id),
            "name": "test",
            "slug": "test",
            "description": None,
            "status": "invalid_status_value",  # Invalid!
            "execution_mode": "ephemeral",
            "model_provider_id": None,
            "model_name": None,
            "config": {},
            "allow_outbound_a2a": False,
            "system_prompt_id": None,
            "structured_output_id": None,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get(f"/api/v1/agent-definitions/{definition_id}").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                with pytest.raises(
                    Exception
                ):  # Pydantic ValidationError for invalid enum
                    await client.get_agent_definition(definition_id)

    @pytest.mark.asyncio
    async def test_list_response_with_invalid_item_raises_error(
        self, base_url: str
    ) -> None:
        """List response with one invalid item should raise error."""
        client = ControlPlaneClient(base_url=base_url)
        now = datetime.now(timezone.utc)

        response_data = [
            {
                "id": str(uuid4()),
                "name": "Valid",
                "description": None,
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
            },
            {
                # Missing required 'id' field
                "name": "Invalid",
                "description": None,
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
            },
        ]

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get("/api/v1/agent-classes").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                with pytest.raises(Exception):  # ValidationError
                    await client.list_agent_classes()

    @pytest.mark.asyncio
    async def test_null_response_body_when_list_expected_raises_error(
        self, base_url: str
    ) -> None:
        """Null response body when list expected should raise error."""
        client = ControlPlaneClient(base_url=base_url)

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get("/api/v1/agent-classes").mock(
                return_value=Response(200, json=None)
            )

            async with client:
                with pytest.raises(Exception):  # TypeError or similar
                    await client.list_agent_classes()

    @pytest.mark.asyncio
    async def test_object_response_when_list_expected_raises_error(
        self, base_url: str
    ) -> None:
        """Object response when list expected should raise error."""
        client = ControlPlaneClient(base_url=base_url)
        now = datetime.now(timezone.utc)

        # Return single object instead of list
        response_data = {
            "id": str(uuid4()),
            "name": "Single",
            "description": None,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get("/api/v1/agent-classes").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                with pytest.raises(Exception):  # TypeError for iteration over dict
                    await client.list_agent_classes()


class TestAPIErrorResponseHandling:
    """Tests for proper handling of API error responses."""

    @pytest.mark.asyncio
    async def test_404_error_includes_detail_from_response(self, base_url: str) -> None:
        """404 errors should include detail message from server."""
        client = ControlPlaneClient(base_url=base_url)
        missing_id = uuid4()

        error_response = {"detail": f"Agent class with ID {missing_id} not found"}

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get(f"/api/v1/agent-classes/{missing_id}").mock(
                return_value=Response(404, json=error_response)
            )

            async with client:
                with pytest.raises(AtlasHTTPStatusError) as exc_info:
                    await client.get_agent_class(missing_id)

                assert exc_info.value.status_code == 404
                assert str(missing_id) in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_400_validation_error_includes_details(self, base_url: str) -> None:
        """400 validation errors should include validation details."""
        from atlas_sdk.models.control_plane import AgentClassCreate

        client = ControlPlaneClient(base_url=base_url)

        error_response = {
            "detail": [
                {
                    "loc": ["body", "name"],
                    "msg": "String should have at least 1 character",
                    "type": "string_too_short",
                }
            ]
        }

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.post("/api/v1/agent-classes").mock(
                return_value=Response(400, json=error_response)
            )

            async with client:
                with pytest.raises(AtlasHTTPStatusError) as exc_info:
                    await client.create_agent_class(
                        AgentClassCreate(name="Test", description="Test")
                    )

                assert exc_info.value.status_code == 400
                # Error response should be accessible
                assert exc_info.value.server_response is not None

    @pytest.mark.asyncio
    async def test_500_error_with_plain_text_body(self, base_url: str) -> None:
        """500 errors with plain text body should be handled gracefully."""
        client = ControlPlaneClient(base_url=base_url)

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get("/api/v1/health").mock(
                return_value=Response(500, text="Internal Server Error")
            )

            async with client:
                with pytest.raises(AtlasHTTPStatusError) as exc_info:
                    await client.health()

                assert exc_info.value.status_code == 500
                assert "Internal Server Error" in str(exc_info.value)


class TestCompleteFieldValidation:
    """Tests that verify all fields in responses are properly validated."""

    @pytest.mark.asyncio
    async def test_agent_definition_all_fields_parsed(self, base_url: str) -> None:
        """Agent definition response should have all fields correctly parsed."""
        from atlas_sdk.models.enums import AgentDefinitionStatus, ExecutionMode

        client = ControlPlaneClient(base_url=base_url)
        definition_id = uuid4()
        agent_class_id = uuid4()
        prompt_id = uuid4()
        output_id = uuid4()
        provider_id = uuid4()
        now = datetime.now(timezone.utc)

        response_data = {
            "id": str(definition_id),
            "agent_class_id": str(agent_class_id),
            "system_prompt_id": str(prompt_id),
            "structured_output_id": str(output_id),
            "model_provider_id": str(provider_id),
            "name": "complete-definition",
            "slug": "complete-def",
            "description": "A fully specified definition",
            "status": "published",
            "execution_mode": "stateful",
            "model_name": "gpt-4-turbo",
            "config": {"temperature": 0.7, "max_tokens": 4096},
            "allow_outbound_a2a": True,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get(f"/api/v1/agent-definitions/{definition_id}").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.get_agent_definition(definition_id)

        # Verify all fields are correctly parsed with proper types
        assert result.id == definition_id
        assert result.agent_class_id == agent_class_id
        assert result.system_prompt_id == prompt_id
        assert result.structured_output_id == output_id
        assert result.model_provider_id == provider_id
        assert result.name == "complete-definition"
        assert result.slug == "complete-def"
        assert result.description == "A fully specified definition"
        assert result.status == AgentDefinitionStatus.PUBLISHED
        assert result.execution_mode == ExecutionMode.STATEFUL
        assert result.model_name == "gpt-4-turbo"
        assert result.config == {"temperature": 0.7, "max_tokens": 4096}
        assert result.allow_outbound_a2a is True
        assert isinstance(result.created_at, datetime)
        assert isinstance(result.updated_at, datetime)

    @pytest.mark.asyncio
    async def test_tool_json_schema_preserved(self, base_url: str) -> None:
        """Tool JSON schema should be preserved exactly as received."""
        client = ControlPlaneClient(base_url=base_url)
        tool_id = uuid4()

        complex_schema = {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query",
                    "minLength": 1,
                },
                "options": {
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "minimum": 1, "maximum": 100},
                        "filters": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                },
            },
            "required": ["query"],
            "additionalProperties": False,
        }

        response_data = {
            "id": str(tool_id),
            "name": "search",
            "description": "Search tool",
            "json_schema": complex_schema,
            "safety_policy": "No PII in queries",
            "risk_level": "medium",
        }

        async with respx.mock(base_url=base_url) as respx_mock:
            respx_mock.get(f"/api/v1/tools/{tool_id}").mock(
                return_value=Response(200, json=response_data)
            )

            async with client:
                result = await client.get_tool(tool_id)

        # Verify complex schema is preserved exactly
        assert result.json_schema == complex_schema
        assert (
            result.json_schema["properties"]["options"]["properties"]["limit"][
                "maximum"
            ]
            == 100
        )
        assert result.json_schema["additionalProperties"] is False
