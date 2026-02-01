# Robust Error Recovery

This example demonstrates comprehensive error handling strategies for production applications.

## Use Case: Fault-Tolerant Agent Deployment

You're building a deployment automation system that must handle various failure scenarios gracefully:

- Network connectivity issues
- Rate limiting from the API
- Resources that don't exist
- Validation errors
- Server-side errors

## Prerequisites

- Running Control Plane instance
- Atlas SDK installed

## Complete Example

```python
"""
Example: Robust Error Recovery
Use Case: Build a fault-tolerant deployment automation system

This example shows how to:
- Handle different error types appropriately
- Implement retry strategies for transient failures
- Recover from partial failures
- Provide meaningful error messages to users
"""

import asyncio
import logging
from uuid import UUID

import httpx

from atlas_sdk import ControlPlaneClient
from atlas_sdk.exceptions import (
    AtlasAPIError,
    AtlasRateLimitError,
    AtlasTimeoutError,
)
from atlas_sdk.models import AgentClassCreate, AgentDefinitionCreate

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


class DeploymentError(Exception):
    """Application-level deployment error."""

    def __init__(self, message: str, recoverable: bool = False):
        super().__init__(message)
        self.recoverable = recoverable


async def get_or_create_agent_class(
    client: ControlPlaneClient,
    name: str,
    description: str,
) -> UUID:
    """
    Get an existing agent class or create a new one.
    Handles the common pattern of "create if not exists".
    """
    try:
        # Try to create the agent class
        agent_class = await client.create_agent_class(
            AgentClassCreate(name=name, description=description)
        )
        logger.info(f"Created new agent class: {name}")
        return agent_class.id

    except AtlasAPIError as e:
        if e.response.status_code == 409:
            # Conflict - already exists, find and return it
            logger.info(f"Agent class '{name}' already exists, fetching...")
            classes = await client.list_agent_classes(limit=1000)
            for cls in classes:
                if cls.name == name:
                    return cls.id
            # Shouldn't reach here, but handle defensively
            raise DeploymentError(
                f"Agent class '{name}' reported as existing but not found",
                recoverable=False,
            )

        elif e.response.status_code == 422:
            # Validation error - extract details
            try:
                error_body = e.response.json()
                details = error_body.get("detail", [])
                error_messages = [
                    f"{'.'.join(str(x) for x in d.get('loc', []))}: {d.get('msg')}"
                    for d in details
                ]
                raise DeploymentError(
                    f"Validation failed: {'; '.join(error_messages)}",
                    recoverable=False,
                )
            except (ValueError, KeyError):
                raise DeploymentError(
                    f"Validation failed: {e.response.text}",
                    recoverable=False,
                )

        elif e.response.status_code == 401:
            raise DeploymentError(
                "Authentication failed - check your credentials",
                recoverable=False,
            )

        elif e.response.status_code == 403:
            raise DeploymentError(
                "Permission denied - you don't have access to create agent classes",
                recoverable=False,
            )

        elif e.response.status_code >= 500:
            raise DeploymentError(
                f"Server error ({e.response.status_code}) - please try again later",
                recoverable=True,
            )

        # Unknown error
        raise DeploymentError(f"Unexpected error: {e}", recoverable=False)


async def create_definition_with_rollback(
    client: ControlPlaneClient,
    agent_class_id: UUID,
    model_provider_id: UUID,
    name: str,
) -> UUID:
    """
    Create an agent definition with rollback on failure.
    If creation fails partway through, clean up partial state.
    """
    definition_id = None

    try:
        definition = await client.create_agent_definition(
            AgentDefinitionCreate(
                name=name,
                agent_class_id=agent_class_id,
                model_provider_id=model_provider_id,
                model_name="gpt-4",
            )
        )
        definition_id = definition.id
        logger.info(f"Created agent definition: {name}")

        # Simulate additional setup that might fail
        # In real code, this might configure tools, prompts, etc.
        # await configure_definition(client, definition_id)

        return definition_id

    except Exception as e:
        # Rollback: delete the definition if it was created
        if definition_id:
            logger.warning(f"Rolling back definition creation: {name}")
            try:
                await client.delete_agent_definition(definition_id)
                logger.info("Rollback successful")
            except Exception as rollback_error:
                logger.error(f"Rollback failed: {rollback_error}")

        raise


async def deploy_with_rate_limit_handling(client: ControlPlaneClient):
    """
    Example of handling rate limiting with custom backoff.
    The SDK handles rate limits automatically, but this shows
    how to implement additional logic if needed.
    """
    try:
        # Make multiple requests that might trigger rate limiting
        results = []
        for i in range(10):
            result = await client.list_agent_classes(limit=100)
            results.append(result)
            logger.info(f"Fetched batch {i + 1}")

        return results

    except AtlasRateLimitError as e:
        # SDK already exhausted retries - this is the final failure
        logger.error(f"Rate limited after all retries. Retry after: {e.retry_after}s")

        if e.retry_after:
            logger.info(f"Scheduling retry in {e.retry_after} seconds...")
            # In a real app, you might queue this for later
            # await schedule_retry(operation, delay=e.retry_after)

        raise DeploymentError(
            f"Rate limited by API. Try again in {e.retry_after or 'unknown'} seconds.",
            recoverable=True,
        )


async def safe_get_resource(
    client: ControlPlaneClient,
    resource_id: UUID,
) -> dict | None:
    """
    Safely get a resource, returning None if not found.
    """
    try:
        return await client.get_agent_class(resource_id)
    except AtlasAPIError as e:
        if e.response.status_code == 404:
            return None
        raise


async def robust_operation(
    client: ControlPlaneClient,
    operation_name: str,
    operation,
    max_retries: int = 3,
):
    """
    Execute an operation with comprehensive error handling.
    """
    last_error = None

    for attempt in range(max_retries):
        try:
            result = await operation()
            logger.info(f"{operation_name} succeeded on attempt {attempt + 1}")
            return result

        except AtlasRateLimitError as e:
            # Rate limit errors are handled by SDK, if we get here
            # all retries were exhausted
            logger.error(f"{operation_name}: Rate limited, no more retries")
            raise

        except AtlasTimeoutError:
            logger.error(f"{operation_name}: Polling timeout")
            raise

        except AtlasAPIError as e:
            status = e.response.status_code
            last_error = e

            # Client errors (4xx) - don't retry
            if 400 <= status < 500:
                logger.error(f"{operation_name}: Client error {status}")
                raise

            # Server errors (5xx) - may retry
            logger.warning(
                f"{operation_name}: Server error {status} "
                f"(attempt {attempt + 1}/{max_retries})"
            )
            if attempt < max_retries - 1:
                wait_time = 2**attempt
                await asyncio.sleep(wait_time)

        except httpx.ConnectError:
            last_error = httpx.ConnectError("Connection failed")
            logger.warning(
                f"{operation_name}: Connection error "
                f"(attempt {attempt + 1}/{max_retries})"
            )
            if attempt < max_retries - 1:
                await asyncio.sleep(2**attempt)

        except httpx.ReadTimeout:
            last_error = httpx.ReadTimeout("Read timeout")
            logger.warning(
                f"{operation_name}: Timeout "
                f"(attempt {attempt + 1}/{max_retries})"
            )
            if attempt < max_retries - 1:
                await asyncio.sleep(2**attempt)

    raise DeploymentError(
        f"{operation_name} failed after {max_retries} attempts: {last_error}",
        recoverable=False,
    )


async def main():
    """Demonstrate error handling patterns."""

    async with ControlPlaneClient(
        base_url="http://localhost:8000",
        timeout=30.0,
    ) as client:
        # Pattern 1: Get or create
        print("\n=== Pattern 1: Get or Create ===")
        try:
            class_id = await get_or_create_agent_class(
                client,
                name="ErrorHandlingDemo",
                description="Demo agent class for error handling",
            )
            print(f"Agent class ID: {class_id}")
        except DeploymentError as e:
            print(f"Deployment error: {e}")
            if e.recoverable:
                print("  (This error is recoverable - try again later)")

        # Pattern 2: Safe get (returns None instead of raising)
        print("\n=== Pattern 2: Safe Get ===")
        fake_id = UUID("00000000-0000-0000-0000-000000000000")
        resource = await safe_get_resource(client, fake_id)
        if resource is None:
            print(f"Resource {fake_id} not found")
        else:
            print(f"Found resource: {resource.name}")

        # Pattern 3: Robust operation with retry
        print("\n=== Pattern 3: Robust Operation ===")
        try:
            result = await robust_operation(
                client,
                "Health check",
                client.health,
                max_retries=3,
            )
            print(f"Health check result: {result}")
        except DeploymentError as e:
            print(f"Operation failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
```

## Key Patterns

### Pattern 1: Get or Create

Handle the common case where a resource might already exist:

```python
try:
    resource = await client.create_resource(data)
except AtlasAPIError as e:
    if e.response.status_code == 409:  # Conflict
        # Find existing resource
        resources = await client.list_resources()
        resource = find_by_name(resources, name)
    else:
        raise
```

### Pattern 2: Safe Get (Return None)

Return `None` instead of raising for missing resources:

```python
async def safe_get(client, id):
    try:
        return await client.get_resource(id)
    except AtlasAPIError as e:
        if e.response.status_code == 404:
            return None
        raise
```

### Pattern 3: Rollback on Failure

Clean up partial state if an operation fails:

```python
resource_id = None
try:
    resource = await client.create_resource(data)
    resource_id = resource.id
    await configure_resource(resource_id)  # Might fail
except Exception:
    if resource_id:
        await client.delete_resource(resource_id)
    raise
```

### Pattern 4: Custom Retry Logic

Add application-level retry for specific scenarios:

```python
for attempt in range(max_retries):
    try:
        return await operation()
    except AtlasAPIError as e:
        if e.response.status_code >= 500 and attempt < max_retries - 1:
            await asyncio.sleep(2 ** attempt)
            continue
        raise
```

## Error Categorization

| Error Type | Retry? | User Action |
|------------|--------|-------------|
| 400 Bad Request | No | Fix input data |
| 401 Unauthorized | No | Check credentials |
| 403 Forbidden | No | Request access |
| 404 Not Found | No | Check resource exists |
| 409 Conflict | No | Handle existing resource |
| 422 Validation | No | Fix validation errors |
| 429 Rate Limit | Yes | Wait and retry |
| 500 Server Error | Maybe | Report issue |
| 502/503/504 | Yes | Retry with backoff |
| Connection Error | Yes | Check network |
| Timeout | Yes | Increase timeout or retry |

## Next Steps

- [Custom Retry Configuration](04_custom_retry.md) - Fine-tune retry behavior
- [Deployment Workflow](02_deployment_workflow.md) - Complete deployment example
