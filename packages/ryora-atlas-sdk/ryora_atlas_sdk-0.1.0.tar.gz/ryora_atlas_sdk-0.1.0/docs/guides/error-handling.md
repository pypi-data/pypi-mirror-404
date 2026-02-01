# Error Handling

This guide covers all exception types in the Atlas SDK, when they're raised, and recommended handling patterns.

## Exception Hierarchy

```
AtlasError (base)
├── AtlasAPIError (all HTTP 4xx/5xx errors)
│   ├── AtlasNotFoundError (404)
│   ├── AtlasValidationError (400, 422)
│   ├── AtlasConflictError (409)
│   ├── AtlasAuthenticationError (401)
│   ├── AtlasAuthorizationError (403)
│   ├── AtlasRateLimitError (429)
│   └── AtlasServerError (5xx)
├── AtlasTimeoutError (polling timeouts)
└── AtlasConnectionError (network failures)
```

## Exception Types

### AtlasAPIError

**Raised when:** Any HTTP 4xx or 5xx response is received.

**Includes:**
- Original request and response objects
- Server-side error message (JSON body parsed if available)

```python
from atlas_sdk import ControlPlaneClient
from atlas_sdk.exceptions import AtlasAPIError

async with ControlPlaneClient(base_url="...") as client:
    try:
        await client.get_agent_class(non_existent_id)
    except AtlasAPIError as e:
        print(f"Status code: {e.response.status_code}")
        print(f"Request URL: {e.request.url}")
        print(f"Error details: {e}")  # Includes server response
```

**Common status codes:**

| Code | Meaning | Typical Cause |
|------|---------|---------------|
| 400 | Bad Request | Invalid request body or parameters |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Resource already exists or state conflict |
| 422 | Unprocessable Entity | Validation error |
| 500 | Internal Server Error | Server-side bug |

### AtlasRateLimitError

**Raised when:** HTTP 429 (Too Many Requests) is received after retry attempts are exhausted.

**Includes:**
- `retry_after` property: Seconds to wait (from Retry-After header)
- All properties from `AtlasAPIError`

```python
from atlas_sdk.exceptions import AtlasRateLimitError

try:
    await client.list_deployments()
except AtlasRateLimitError as e:
    if e.retry_after:
        print(f"Rate limited. Retry after {e.retry_after} seconds")
        await asyncio.sleep(e.retry_after)
        # Retry the operation
    else:
        print("Rate limited, but no Retry-After header provided")
```

!!! note "Automatic Retry"
    The SDK automatically retries on 429 responses up to 5 times, respecting
    the Retry-After header. `AtlasRateLimitError` is only raised when all
    retries are exhausted.

### AtlasTimeoutError

**Raised when:** A polling operation (`wait_for_plan_completion`, `wait_for_task_completion`) exceeds its timeout.

```python
from atlas_sdk.exceptions import AtlasTimeoutError

try:
    completed_plan = await client.wait_for_plan_completion(
        plan_id,
        timeout=60.0,  # 60 second timeout
        poll_interval=2.0
    )
except AtlasTimeoutError:
    print("Plan did not complete within 60 seconds")
    # Check current status
    plan = await client.get_plan(plan_id)
    print(f"Current status: {plan.status}")
```

## Recommended Patterns

### Basic Error Handling

```python
from atlas_sdk.exceptions import AtlasAPIError, AtlasRateLimitError

async def create_agent_class_safe(client, data):
    try:
        return await client.create_agent_class(data)
    except AtlasRateLimitError as e:
        # Rate limited after retries exhausted
        logger.warning(f"Rate limited, retry after: {e.retry_after}")
        raise
    except AtlasAPIError as e:
        if e.response.status_code == 409:
            # Already exists - fetch existing
            logger.info("Agent class already exists, fetching...")
            classes = await client.list_agent_classes()
            return next(c for c in classes if c.name == data.name)
        raise
```

### Status Code Branching

```python
from atlas_sdk.exceptions import AtlasAPIError

async def get_or_none(client, resource_id):
    """Get a resource, returning None if not found."""
    try:
        return await client.get_agent_class(resource_id)
    except AtlasAPIError as e:
        if e.response.status_code == 404:
            return None
        raise  # Re-raise other errors
```

### Handling Validation Errors

```python
from atlas_sdk.exceptions import AtlasAPIError
import json

async def create_with_validation_feedback(client, data):
    try:
        return await client.create_agent_definition(data)
    except AtlasAPIError as e:
        if e.response.status_code in (400, 422):
            try:
                error_body = e.response.json()
                # Extract validation details
                if "detail" in error_body:
                    for error in error_body["detail"]:
                        field = ".".join(str(x) for x in error.get("loc", []))
                        msg = error.get("msg", "Unknown error")
                        print(f"Validation error in '{field}': {msg}")
            except json.JSONDecodeError:
                print(f"Validation error: {e.response.text}")
        raise
```

### Retry with Custom Logic

```python
import asyncio
from atlas_sdk.exceptions import AtlasAPIError

async def create_with_retry(client, data, max_attempts=3):
    """Create resource with custom retry logic for specific errors."""
    for attempt in range(max_attempts):
        try:
            return await client.create_deployment(data)
        except AtlasAPIError as e:
            # Retry on 503 (service unavailable)
            if e.response.status_code == 503 and attempt < max_attempts - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                logger.warning(f"Service unavailable, retrying in {wait_time}s")
                await asyncio.sleep(wait_time)
                continue
            raise
```

### Comprehensive Error Handler

```python
from atlas_sdk.exceptions import (
    AtlasAPIError,
    AtlasRateLimitError,
    AtlasTimeoutError,
)
import httpx

async def robust_operation(client, operation):
    """Execute an operation with comprehensive error handling."""
    try:
        return await operation()

    except AtlasRateLimitError as e:
        # Rate limiting - could implement queue or notify
        logger.error(f"Rate limited. Retry after: {e.retry_after}s")
        raise

    except AtlasTimeoutError:
        # Polling timeout
        logger.error("Operation timed out waiting for completion")
        raise

    except AtlasAPIError as e:
        status = e.response.status_code
        if status == 401:
            logger.error("Authentication failed - check credentials")
        elif status == 403:
            logger.error("Permission denied - check access rights")
        elif status == 404:
            logger.error("Resource not found")
        elif status == 409:
            logger.error("Conflict - resource state invalid for operation")
        elif status >= 500:
            logger.error(f"Server error ({status}) - contact support")
        raise

    except httpx.ConnectError:
        logger.error("Connection failed - check network/service availability")
        raise

    except httpx.ReadTimeout:
        logger.error("Request timed out - try increasing timeout")
        raise
```

## Testing Error Handling

Use `respx` to mock error responses in tests:

```python
import pytest
import respx
from httpx import Response
from atlas_sdk import ControlPlaneClient
from atlas_sdk.exceptions import AtlasAPIError

@pytest.mark.asyncio
async def test_handles_not_found():
    with respx.mock:
        respx.get("http://test/agent-classes/123").mock(
            return_value=Response(404, json={"detail": "Not found"})
        )

        async with ControlPlaneClient(base_url="http://test") as client:
            with pytest.raises(AtlasAPIError) as exc_info:
                await client.get_agent_class("123")

            assert exc_info.value.response.status_code == 404
```

## See Also

- [Retry Behavior](retry-behavior.md) - Automatic retry configuration
- [API Reference: Exceptions](../api/exceptions.md) - Full exception API
