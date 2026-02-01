# Concurrent Operations

This example demonstrates patterns for running multiple SDK operations in parallel.

## Use Case: Dashboard Data Aggregation

You're building a dashboard that needs to display:

- System health status
- Resource counts
- Recent activity

All data should load quickly with a single network round-trip time.

## Prerequisites

- Atlas SDK installed
- Running Control Plane instance

## Complete Example

```python
"""
Example: Concurrent Operations
Use Case: Build a fast-loading dashboard with parallel data fetching

This example shows how to:
- Fetch multiple resources concurrently with asyncio.gather
- Use TaskGroups for structured concurrency (Python 3.11+)
- Handle partial failures in concurrent operations
- Implement fan-out/fan-in patterns
"""

import asyncio
from dataclasses import dataclass
from typing import Any

from atlas_sdk import ControlPlaneClient, WorkflowClient
from atlas_sdk.pagination import paginate


# =============================================================================
# Dashboard Data Structure
# =============================================================================


@dataclass
class DashboardData:
    """All data needed for the dashboard."""

    # System health
    health_status: str | None = None

    # Resource counts
    agent_class_count: int = 0
    definition_count: int = 0
    provider_count: int = 0
    deployment_count: int = 0

    # Recent items
    recent_classes: list = None
    recent_deployments: list = None

    # Errors (for partial success)
    errors: list = None

    def __post_init__(self):
        self.recent_classes = self.recent_classes or []
        self.recent_deployments = self.recent_deployments or []
        self.errors = self.errors or []


# =============================================================================
# Pattern 1: asyncio.gather
# =============================================================================


async def fetch_dashboard_gather(
    client: ControlPlaneClient,
) -> DashboardData:
    """
    Fetch all dashboard data using asyncio.gather.

    This is the simplest approach for parallel operations.
    All operations run concurrently, results are collected together.
    """
    # Run all fetches in parallel
    results = await asyncio.gather(
        client.health(),
        client.list_agent_classes(limit=100),
        client.list_agent_definitions(limit=100),
        client.list_model_providers(limit=100),
        client.list_deployments(limit=5),  # Recent 5
        return_exceptions=True,  # Don't fail if one fails
    )

    # Unpack results
    health, classes, definitions, providers, deployments = results

    # Build dashboard data, handling errors
    data = DashboardData()

    if isinstance(health, Exception):
        data.errors.append(f"Health check failed: {health}")
    else:
        data.health_status = health.get("status", "unknown")

    if isinstance(classes, Exception):
        data.errors.append(f"Failed to fetch classes: {classes}")
    else:
        data.agent_class_count = len(classes)
        data.recent_classes = classes[:5]

    if isinstance(definitions, Exception):
        data.errors.append(f"Failed to fetch definitions: {definitions}")
    else:
        data.definition_count = len(definitions)

    if isinstance(providers, Exception):
        data.errors.append(f"Failed to fetch providers: {providers}")
    else:
        data.provider_count = len(providers)

    if isinstance(deployments, Exception):
        data.errors.append(f"Failed to fetch deployments: {deployments}")
    else:
        data.deployment_count = len(deployments)
        data.recent_deployments = deployments

    return data


# =============================================================================
# Pattern 2: TaskGroup (Python 3.11+)
# =============================================================================


async def fetch_dashboard_taskgroup(
    client: ControlPlaneClient,
) -> DashboardData:
    """
    Fetch dashboard data using TaskGroup.

    TaskGroups provide structured concurrency with better error handling.
    If any task fails, all other tasks are cancelled.
    """
    data = DashboardData()

    async def fetch_health():
        result = await client.health()
        data.health_status = result.get("status", "unknown")

    async def fetch_classes():
        classes = await client.list_agent_classes(limit=100)
        data.agent_class_count = len(classes)
        data.recent_classes = classes[:5]

    async def fetch_definitions():
        definitions = await client.list_agent_definitions(limit=100)
        data.definition_count = len(definitions)

    async def fetch_providers():
        providers = await client.list_model_providers(limit=100)
        data.provider_count = len(providers)

    async def fetch_deployments():
        deployments = await client.list_deployments(limit=5)
        data.deployment_count = len(deployments)
        data.recent_deployments = deployments

    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(fetch_health())
            tg.create_task(fetch_classes())
            tg.create_task(fetch_definitions())
            tg.create_task(fetch_providers())
            tg.create_task(fetch_deployments())
    except* Exception as eg:
        # Handle multiple exceptions
        for exc in eg.exceptions:
            data.errors.append(str(exc))

    return data


# =============================================================================
# Pattern 3: Fan-out with Semaphore
# =============================================================================


async def process_all_definitions_parallel(
    client: ControlPlaneClient,
    processor: callable,
    max_concurrency: int = 20,
) -> list[Any]:
    """
    Process all definitions in parallel with controlled concurrency.

    Fan-out pattern: paginate through all items, process each concurrently.
    """
    semaphore = asyncio.Semaphore(max_concurrency)
    tasks = []

    async def process_with_limit(definition):
        async with semaphore:
            return await processor(definition)

    # Collect all definitions first (or process as stream)
    async for definition in paginate(
        lambda limit, offset: client.list_agent_definitions(limit=limit, offset=offset),
        limit=100,
    ):
        task = asyncio.create_task(process_with_limit(definition))
        tasks.append(task)

    # Wait for all to complete
    results = await asyncio.gather(*tasks, return_exceptions=True)

    return results


# =============================================================================
# Pattern 4: Chunked Parallel Processing
# =============================================================================


async def process_in_chunks(
    client: ControlPlaneClient,
    ids: list[str],
    chunk_size: int = 10,
) -> list[Any]:
    """
    Process items in parallel chunks.

    Process chunk_size items at a time, wait for all to complete,
    then process the next chunk. Good for rate-limited APIs.
    """
    results = []

    for i in range(0, len(ids), chunk_size):
        chunk = ids[i : i + chunk_size]

        # Process chunk in parallel
        chunk_results = await asyncio.gather(
            *[client.get_agent_class(id_) for id_ in chunk],
            return_exceptions=True,
        )
        results.extend(chunk_results)

        # Optional: add delay between chunks for rate limiting
        if i + chunk_size < len(ids):
            await asyncio.sleep(0.1)

    return results


# =============================================================================
# Pattern 5: First Completed
# =============================================================================


async def get_from_any_client(
    clients: list[ControlPlaneClient],
    operation: str,
) -> Any:
    """
    Get result from the first client that responds.

    Useful for redundant services where you want the fastest response.
    """
    tasks = []
    for client in clients:
        task = asyncio.create_task(client.health())
        tasks.append(task)

    # Wait for first to complete
    done, pending = await asyncio.wait(
        tasks, return_when=asyncio.FIRST_COMPLETED
    )

    # Cancel remaining tasks
    for task in pending:
        task.cancel()

    # Return first result
    for task in done:
        try:
            return task.result()
        except Exception:
            continue

    raise Exception("All clients failed")


# =============================================================================
# Pattern 6: Timeout per Operation
# =============================================================================


async def fetch_with_timeouts(
    client: ControlPlaneClient,
) -> DashboardData:
    """
    Fetch data with individual timeouts per operation.
    """
    data = DashboardData()

    async def with_timeout(coro, timeout: float, default: Any = None):
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            return default

    # Different timeouts for different operations
    health, classes, deployments = await asyncio.gather(
        with_timeout(client.health(), timeout=5.0, default={"status": "unknown"}),
        with_timeout(client.list_agent_classes(limit=100), timeout=10.0, default=[]),
        with_timeout(client.list_deployments(limit=5), timeout=10.0, default=[]),
    )

    data.health_status = health.get("status") if health else "timeout"
    data.agent_class_count = len(classes)
    data.recent_classes = classes[:5]
    data.recent_deployments = deployments

    return data


# =============================================================================
# Main
# =============================================================================


async def main():
    """Demonstrate concurrent operation patterns."""

    async with ControlPlaneClient(base_url="http://localhost:8000") as client:
        # Pattern 1: asyncio.gather
        print("=== Pattern 1: asyncio.gather ===")
        import time

        start = time.time()
        data = await fetch_dashboard_gather(client)
        elapsed = time.time() - start

        print(f"Fetched in {elapsed:.3f}s:")
        print(f"  Health: {data.health_status}")
        print(f"  Classes: {data.agent_class_count}")
        print(f"  Definitions: {data.definition_count}")
        print(f"  Providers: {data.provider_count}")
        if data.errors:
            print(f"  Errors: {data.errors}")

        # Pattern 2: TaskGroup
        print("\n=== Pattern 2: TaskGroup ===")
        start = time.time()
        data = await fetch_dashboard_taskgroup(client)
        elapsed = time.time() - start
        print(f"Fetched in {elapsed:.3f}s")

        # Pattern 3: Fan-out
        print("\n=== Pattern 3: Fan-out Processing ===")

        async def analyze(definition):
            return {"name": definition.name, "model": definition.model_name}

        results = await process_all_definitions_parallel(
            client, analyze, max_concurrency=20
        )
        print(f"Processed {len(results)} definitions")

        # Pattern 6: With timeouts
        print("\n=== Pattern 6: With Timeouts ===")
        data = await fetch_with_timeouts(client)
        print(f"Health: {data.health_status}")


if __name__ == "__main__":
    asyncio.run(main())
```

## Key Points

### asyncio.gather

Simplest approach for parallel operations:

```python
a, b, c = await asyncio.gather(
    client.operation_a(),
    client.operation_b(),
    client.operation_c(),
    return_exceptions=True,  # Don't fail if one fails
)
```

### TaskGroup (Python 3.11+)

Structured concurrency with automatic cleanup:

```python
async with asyncio.TaskGroup() as tg:
    tg.create_task(operation_a())
    tg.create_task(operation_b())
# All tasks complete or all are cancelled on error
```

### Controlling Concurrency

Use semaphores to limit parallel operations:

```python
semaphore = asyncio.Semaphore(20)

async def limited_op():
    async with semaphore:
        return await client.operation()

# Max 20 concurrent
await asyncio.gather(*[limited_op() for _ in range(100)])
```

### Error Handling

| Pattern | Behavior on Error |
|---------|-------------------|
| `gather(return_exceptions=True)` | Continues, returns exceptions |
| `gather(return_exceptions=False)` | Fails fast, raises first error |
| `TaskGroup` | Cancels all tasks, raises ExceptionGroup |

### When to Use Each Pattern

| Pattern | Use Case |
|---------|----------|
| `gather` | Independent operations, partial success OK |
| `TaskGroup` | Dependent operations, all-or-nothing |
| Semaphore | Many operations, need concurrency control |
| Chunked | Rate-limited APIs, batch processing |
| First completed | Redundant services, fastest wins |

## Best Practices

1. **Use `return_exceptions=True`** when partial success is acceptable
2. **Limit concurrency** to avoid overwhelming services
3. **Set timeouts** on individual operations for reliability
4. **Cancel pending tasks** when using `FIRST_COMPLETED`
5. **Consider TaskGroup** for Python 3.11+ projects

## Next Steps

- [High-Throughput Configuration](08_connection_pool.md) - Configure for scale
- [Custom Metrics Collection](11_custom_metrics.md) - Monitor concurrent operations
