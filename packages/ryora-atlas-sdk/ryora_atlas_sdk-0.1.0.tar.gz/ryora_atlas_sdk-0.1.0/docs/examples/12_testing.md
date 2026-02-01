# Testing with Mocked Clients

This example demonstrates how to unit test code that uses the Atlas SDK.

## Use Case: Test-Driven Development

You're building an application that uses the Atlas SDK and need to:

- Write unit tests without a running Control Plane
- Test error handling and edge cases
- Achieve high test coverage
- Run tests quickly in CI/CD

## Prerequisites

- Atlas SDK installed with test extras: `pip install ryora-atlas-sdk[test]`
- pytest and respx installed

## Complete Example

```python
"""
Example: Testing with Mocked Clients
Use Case: Unit test applications that use the Atlas SDK

This example shows how to:
- Mock HTTP responses with respx
- Test success paths
- Test error handling
- Test pagination
- Create reusable fixtures
"""

import pytest
import respx
from httpx import Response
from uuid import UUID

from atlas_sdk import ControlPlaneClient, WorkflowClient
from atlas_sdk.exceptions import AtlasAPIError, AtlasRateLimitError
from atlas_sdk.models import AgentClassCreate


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_api():
    """Create a respx mock context."""
    with respx.mock(base_url="http://test-api") as mock:
        yield mock


@pytest.fixture
async def client():
    """Create a test client."""
    async with ControlPlaneClient(base_url="http://test-api") as client:
        yield client


# =============================================================================
# Sample Response Data
# =============================================================================


def make_agent_class(
    id: str = "123e4567-e89b-12d3-a456-426614174000",
    name: str = "TestClass",
    description: str = "A test agent class",
):
    """Create sample agent class response data."""
    return {
        "id": id,
        "name": name,
        "description": description,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
    }


def make_agent_class_list(count: int = 3):
    """Create sample list of agent classes."""
    return [
        make_agent_class(
            id=f"123e4567-e89b-12d3-a456-42661417400{i}",
            name=f"TestClass{i}",
        )
        for i in range(count)
    ]


# =============================================================================
# Testing Success Paths
# =============================================================================


@pytest.mark.asyncio
async def test_health_check(mock_api, client):
    """Test the health check endpoint."""
    mock_api.get("/health").mock(
        return_value=Response(200, json={"status": "healthy"})
    )

    result = await client.health()

    assert result == {"status": "healthy"}


@pytest.mark.asyncio
async def test_create_agent_class(mock_api, client):
    """Test creating an agent class."""
    response_data = make_agent_class(name="NewClass")

    mock_api.post("/agent-classes").mock(
        return_value=Response(201, json=response_data)
    )

    result = await client.create_agent_class(
        AgentClassCreate(name="NewClass", description="Test")
    )

    assert result.name == "NewClass"
    assert str(result.id) == response_data["id"]


@pytest.mark.asyncio
async def test_list_agent_classes(mock_api, client):
    """Test listing agent classes."""
    response_data = make_agent_class_list(5)

    mock_api.get("/agent-classes").mock(
        return_value=Response(200, json=response_data)
    )

    result = await client.list_agent_classes(limit=10)

    assert len(result) == 5
    assert result[0].name == "TestClass0"


@pytest.mark.asyncio
async def test_get_agent_class(mock_api, client):
    """Test getting a single agent class."""
    class_id = "123e4567-e89b-12d3-a456-426614174000"
    response_data = make_agent_class(id=class_id)

    mock_api.get(f"/agent-classes/{class_id}").mock(
        return_value=Response(200, json=response_data)
    )

    result = await client.get_agent_class(UUID(class_id))

    assert str(result.id) == class_id


# =============================================================================
# Testing Error Handling
# =============================================================================


@pytest.mark.asyncio
async def test_not_found_error(mock_api, client):
    """Test handling 404 Not Found."""
    class_id = "123e4567-e89b-12d3-a456-426614174000"

    mock_api.get(f"/agent-classes/{class_id}").mock(
        return_value=Response(404, json={"detail": "Not found"})
    )

    with pytest.raises(AtlasAPIError) as exc_info:
        await client.get_agent_class(UUID(class_id))

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_validation_error(mock_api, client):
    """Test handling validation errors."""
    mock_api.post("/agent-classes").mock(
        return_value=Response(
            422,
            json={
                "detail": [
                    {
                        "loc": ["body", "name"],
                        "msg": "field required",
                        "type": "value_error.missing",
                    }
                ]
            },
        )
    )

    with pytest.raises(AtlasAPIError) as exc_info:
        await client.create_agent_class(
            AgentClassCreate(name="", description="")
        )

    assert exc_info.value.status_code == 422


@pytest.mark.asyncio
async def test_rate_limit_error(mock_api, client):
    """Test handling rate limiting."""
    # Mock rate limit response (retries exhausted)
    mock_api.get("/health").mock(
        return_value=Response(
            429,
            headers={"Retry-After": "60"},
            json={"detail": "Too many requests"},
        )
    )

    with pytest.raises(AtlasRateLimitError) as exc_info:
        await client.health()

    assert exc_info.value.retry_after == 60.0


@pytest.mark.asyncio
async def test_server_error(mock_api, client):
    """Test handling server errors."""
    mock_api.get("/health").mock(
        return_value=Response(500, json={"detail": "Internal server error"})
    )

    with pytest.raises(AtlasAPIError) as exc_info:
        await client.health()

    assert exc_info.value.status_code == 500


# =============================================================================
# Testing Pagination
# =============================================================================


@pytest.mark.asyncio
async def test_pagination_params(mock_api, client):
    """Test that pagination parameters are passed correctly."""
    mock_api.get("/agent-classes").mock(
        return_value=Response(200, json=[])
    )

    await client.list_agent_classes(limit=50, offset=100)

    # Verify the request was made with correct params
    request = mock_api.calls[0].request
    assert "limit=50" in str(request.url)
    assert "offset=100" in str(request.url)


@pytest.mark.asyncio
async def test_pagination_iteration():
    """Test paginating through multiple pages."""
    with respx.mock(base_url="http://test-api") as mock:
        # First page
        mock.get("/agent-classes").mock(
            side_effect=[
                Response(200, json=make_agent_class_list(100)),
                Response(200, json=make_agent_class_list(50)),
                Response(200, json=[]),  # Empty = done
            ]
        )

        from atlas_sdk.pagination import paginate

        async with ControlPlaneClient(base_url="http://test-api") as client:
            items = []
            async for item in paginate(
                lambda limit, offset: client.list_agent_classes(
                    limit=limit, offset=offset
                ),
                limit=100,
            ):
                items.append(item)

            assert len(items) == 150  # 100 + 50


# =============================================================================
# Testing Application Code
# =============================================================================


class AgentClassService:
    """Example application service that uses the SDK."""

    def __init__(self, client: ControlPlaneClient):
        self.client = client

    async def get_or_create(self, name: str, description: str):
        """Get an existing class or create a new one."""
        try:
            classes = await self.client.list_agent_classes(limit=1000)
            for cls in classes:
                if cls.name == name:
                    return cls
        except AtlasAPIError:
            pass

        return await self.client.create_agent_class(
            AgentClassCreate(name=name, description=description)
        )

    async def find_by_name(self, name: str):
        """Find a class by name, returns None if not found."""
        classes = await self.client.list_agent_classes(limit=1000)
        for cls in classes:
            if cls.name == name:
                return cls
        return None


@pytest.mark.asyncio
async def test_service_get_or_create_existing(mock_api, client):
    """Test get_or_create when class exists."""
    existing_class = make_agent_class(name="ExistingClass")

    mock_api.get("/agent-classes").mock(
        return_value=Response(200, json=[existing_class])
    )

    service = AgentClassService(client)
    result = await service.get_or_create("ExistingClass", "desc")

    assert result.name == "ExistingClass"
    # Verify create was not called
    assert len([c for c in mock_api.calls if c.request.method == "POST"]) == 0


@pytest.mark.asyncio
async def test_service_get_or_create_new(mock_api, client):
    """Test get_or_create when class doesn't exist."""
    new_class = make_agent_class(name="NewClass")

    mock_api.get("/agent-classes").mock(
        return_value=Response(200, json=[])
    )
    mock_api.post("/agent-classes").mock(
        return_value=Response(201, json=new_class)
    )

    service = AgentClassService(client)
    result = await service.get_or_create("NewClass", "desc")

    assert result.name == "NewClass"
    # Verify create was called
    assert len([c for c in mock_api.calls if c.request.method == "POST"]) == 1


@pytest.mark.asyncio
async def test_service_find_by_name_not_found(mock_api, client):
    """Test find_by_name returns None when not found."""
    mock_api.get("/agent-classes").mock(
        return_value=Response(200, json=[])
    )

    service = AgentClassService(client)
    result = await service.find_by_name("NonExistent")

    assert result is None


# =============================================================================
# Testing with Custom Fixtures
# =============================================================================


@pytest.fixture
def populated_mock_api():
    """Mock API with pre-populated data."""
    with respx.mock(base_url="http://test-api") as mock:
        # Health always healthy
        mock.get("/health").mock(
            return_value=Response(200, json={"status": "healthy"})
        )

        # Pre-populated classes
        mock.get("/agent-classes").mock(
            return_value=Response(200, json=make_agent_class_list(10))
        )

        yield mock


@pytest.mark.asyncio
async def test_with_populated_api(populated_mock_api):
    """Test using pre-configured mock."""
    async with ControlPlaneClient(base_url="http://test-api") as client:
        health = await client.health()
        assert health["status"] == "healthy"

        classes = await client.list_agent_classes()
        assert len(classes) == 10


# =============================================================================
# Run Tests
# =============================================================================


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

## Key Points

### Using respx

Mock HTTP responses at the transport layer:

```python
with respx.mock(base_url="http://test-api") as mock:
    mock.get("/health").mock(
        return_value=Response(200, json={"status": "ok"})
    )

    async with ControlPlaneClient(base_url="http://test-api") as client:
        result = await client.health()
```

### Testing Errors

Test exception handling:

```python
@pytest.mark.asyncio
async def test_not_found(mock_api, client):
    mock_api.get("/resource/123").mock(
        return_value=Response(404, json={"detail": "Not found"})
    )

    with pytest.raises(AtlasAPIError) as exc_info:
        await client.get_resource("123")

    assert exc_info.value.status_code == 404
```

### Verifying Requests

Check that correct parameters were sent:

```python
await client.list_resources(limit=50, offset=100)

request = mock_api.calls[0].request
assert "limit=50" in str(request.url)
assert "offset=100" in str(request.url)
```

### Reusable Fixtures

Create fixtures for common scenarios:

```python
@pytest.fixture
def mock_api():
    with respx.mock(base_url="http://test") as mock:
        yield mock

@pytest.fixture
async def client():
    async with ControlPlaneClient(base_url="http://test") as c:
        yield c
```

### Testing Application Code

Test your business logic, not just the SDK:

```python
class MyService:
    def __init__(self, client: ControlPlaneClient):
        self.client = client

    async def business_logic(self):
        # Your code that uses the SDK
        pass

@pytest.mark.asyncio
async def test_my_service(mock_api, client):
    # Mock the underlying API calls
    mock_api.get("/...").mock(return_value=Response(200, json={}))

    service = MyService(client)
    result = await service.business_logic()

    assert result == expected
```

## Best Practices

1. **Mock at HTTP level** - Use respx to mock responses, not SDK internals
2. **Test edge cases** - Empty responses, errors, pagination boundaries
3. **Use fixtures** - Reuse mock setups across tests
4. **Test your code** - Focus on your business logic, not SDK implementation
5. **Verify requests** - Check that correct parameters are sent
6. **Keep tests fast** - Mocks make tests run instantly

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=your_app

# Run verbose
pytest -v

# Run specific test
pytest test_myapp.py::test_specific_case
```

## See Also

- [respx documentation](https://lundberg.github.io/respx/)
- [pytest-asyncio documentation](https://pytest-asyncio.readthedocs.io/)
