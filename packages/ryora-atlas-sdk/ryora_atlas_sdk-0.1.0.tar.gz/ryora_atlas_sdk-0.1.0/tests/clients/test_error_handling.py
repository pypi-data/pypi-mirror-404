"""Tests for error handling in the control plane client."""

from typing import Any
from uuid import uuid4

import pytest
import respx
from httpx import Response

from atlas_sdk.clients.control_plane import ControlPlaneClient
from atlas_sdk.exceptions import (
    AtlasAPIError,
    AtlasError,
    AtlasNotFoundError,
    AtlasServerError,
    AtlasValidationError,
)


@pytest.fixture
def base_url() -> str:
    return "http://test-control-plane"


@pytest.fixture
def client(base_url: str) -> ControlPlaneClient:
    return ControlPlaneClient(base_url=base_url)


@pytest.mark.asyncio
async def test_error_handling_with_json_body(
    client: ControlPlaneClient, base_url: str
) -> None:
    definition_id = uuid4()
    error_data: dict[str, Any] = {
        "detail": "Definition not found",
        "code": "NOT_FOUND",
    }

    async with respx.mock(base_url=base_url) as respx_mock:
        respx_mock.get(f"/api/v1/agent-definitions/{definition_id}").mock(
            return_value=Response(404, json=error_data)
        )

        async with client:
            with pytest.raises(AtlasNotFoundError) as exc_info:
                await client.get_agent_definition(definition_id)

            error = exc_info.value
            assert "Definition not found" in str(error)
            assert error.status_code == 404
            assert error.server_response == error_data


@pytest.mark.asyncio
async def test_error_handling_with_text_body(
    client: ControlPlaneClient, base_url: str
) -> None:
    definition_id = uuid4()
    error_text = "Internal Server Error"

    async with respx.mock(base_url=base_url) as respx_mock:
        respx_mock.get(f"/api/v1/agent-definitions/{definition_id}").mock(
            return_value=Response(500, text=error_text)
        )

        async with client:
            with pytest.raises(AtlasServerError) as exc_info:
                await client.get_agent_definition(definition_id)

            error = exc_info.value
            assert "Internal Server Error" in str(error)
            assert error.status_code == 500
            assert error.server_response == error_text


@pytest.mark.asyncio
async def test_catch_as_atlas_api_error(
    client: ControlPlaneClient, base_url: str
) -> None:
    """Test that specific errors can be caught as the base AtlasAPIError."""
    definition_id = uuid4()
    error_data: dict[str, Any] = {"detail": "Something went wrong"}

    async with respx.mock(base_url=base_url) as respx_mock:
        respx_mock.get(f"/api/v1/agent-definitions/{definition_id}").mock(
            return_value=Response(400, json=error_data)
        )

        async with client:
            # Verify we can catch it as the base class
            with pytest.raises(AtlasAPIError) as exc_info:
                await client.get_agent_definition(definition_id)

            # And it is indeed the specific error type
            assert isinstance(exc_info.value, AtlasValidationError)
            assert "Something went wrong" in str(exc_info.value)


@pytest.mark.asyncio
async def test_catch_as_atlas_error(client: ControlPlaneClient, base_url: str) -> None:
    """Test that all errors can be caught as the root AtlasError."""
    definition_id = uuid4()
    error_data: dict[str, Any] = {"detail": "Not found"}

    async with respx.mock(base_url=base_url) as respx_mock:
        respx_mock.get(f"/api/v1/agent-definitions/{definition_id}").mock(
            return_value=Response(404, json=error_data)
        )

        async with client:
            with pytest.raises(AtlasError) as exc_info:
                await client.get_agent_definition(definition_id)

            # Should be an AtlasNotFoundError
            assert isinstance(exc_info.value, AtlasNotFoundError)
