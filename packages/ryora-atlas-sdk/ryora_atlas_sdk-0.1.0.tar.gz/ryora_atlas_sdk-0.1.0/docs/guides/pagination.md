# Pagination

This guide covers how to work with paginated results in the Atlas SDK.

## Overview

All list methods in the SDK support pagination through `limit` and `offset` parameters:

- **`limit`**: Maximum number of items to return (1-1000, default 100)
- **`offset`**: Number of items to skip (default 0)

## Basic Pagination

### Manual Pagination

Fetch pages manually using limit and offset:

```python
from atlas_sdk import ControlPlaneClient

async with ControlPlaneClient(base_url="...") as client:
    # First page
    page1 = await client.list_agent_classes(limit=50, offset=0)

    # Second page
    page2 = await client.list_agent_classes(limit=50, offset=50)

    # Third page
    page3 = await client.list_agent_classes(limit=50, offset=100)
```

### Loop Through All Pages

```python
async def get_all_agent_classes(client):
    all_classes = []
    offset = 0
    limit = 100

    while True:
        page = await client.list_agent_classes(limit=limit, offset=offset)
        if not page:
            break

        all_classes.extend(page)

        if len(page) < limit:
            break  # Last page

        offset += limit

    return all_classes
```

## Using the Paginate Helper

The `paginate()` function provides a simple async iterator for one-shot pagination:

```python
from atlas_sdk.pagination import paginate

async with ControlPlaneClient(base_url="...") as client:
    async for agent_class in paginate(
        lambda limit, offset: client.list_agent_classes(limit=limit, offset=offset),
        limit=50,  # Items per page
    ):
        print(agent_class.name)
        # Process each item as it's fetched
```

Benefits:
- Memory efficient - processes one page at a time
- Clean syntax - no manual loop management
- Automatic termination when no more items

## Resumable Pagination with Paginator

For long-running operations that might need to pause and resume, use the `Paginator` class:

### Basic Usage

```python
from atlas_sdk.pagination import Paginator

paginator = Paginator(
    fetch_page=lambda limit, offset: client.list_agent_classes(
        limit=limit, offset=offset
    ),
    limit=50,
)

async for agent_class in paginator:
    process(agent_class)
```

### Pause and Resume

```python
from atlas_sdk.pagination import Paginator, PaginationState
import json

# Start pagination
paginator = Paginator(
    fetch_page=lambda limit, offset: client.list_deployments(
        limit=limit, offset=offset
    ),
    limit=100,
)

processed = 0
async for deployment in paginator:
    process(deployment)
    processed += 1

    # Pause after processing 500 items
    if processed >= 500:
        break

# Save state to resume later
state_dict = paginator.get_state().to_dict()
save_to_storage(json.dumps(state_dict))

# ... Later, in another process or after restart ...

# Resume from saved state
saved_state = json.loads(load_from_storage())
paginator = Paginator.from_state(
    state=PaginationState.from_dict(saved_state),
    fetch_page=lambda limit, offset: client.list_deployments(
        limit=limit, offset=offset
    ),
    limit=100,
)

# Continue where we left off
async for deployment in paginator:
    process(deployment)
```

### State Properties

The `PaginationState` tracks:

| Property | Description |
|----------|-------------|
| `offset` | Current position in the result set |
| `cursor` | Optional cursor (for future cursor-based pagination) |
| `has_more` | Whether there are more items to fetch |
| `total_fetched` | Total number of items fetched so far |

## Page-by-Page Processing

If you need to process entire pages rather than individual items:

```python
from atlas_sdk.pagination import Paginator

paginator = Paginator(
    fetch_page=lambda limit, offset: client.list_tools(
        limit=limit, offset=offset
    ),
    limit=100,
)

while paginator.state.has_more:
    page = await paginator.next_page()
    print(f"Processing page with {len(page)} items")
    await process_batch(page)

print(f"Total fetched: {paginator.state.total_fetched}")
```

## Concurrent Pagination

For faster processing, fetch pages concurrently:

```python
import asyncio

async def fetch_all_pages_concurrent(client, total_expected: int, page_size: int = 100):
    """Fetch all pages concurrently (use when you know the approximate total)."""
    # Calculate number of pages needed
    num_pages = (total_expected + page_size - 1) // page_size

    # Create fetch tasks for all pages
    tasks = [
        client.list_agent_classes(limit=page_size, offset=i * page_size)
        for i in range(num_pages)
    ]

    # Fetch all pages concurrently
    pages = await asyncio.gather(*tasks)

    # Flatten results
    return [item for page in pages for item in page]
```

!!! warning "Rate Limiting"
    Concurrent pagination can trigger rate limiting. Consider adding delays
    or limiting concurrency for large datasets.

## Methods Supporting Pagination

All these client methods support `limit` and `offset`:

### ControlPlaneClient

- `list_agent_classes()`
- `list_agent_definitions()`
- `list_model_providers()`
- `list_system_prompts()`
- `list_tools()`
- `list_deployments()`
- `query_grasp_analyses()`
- `logs()`

### WorkflowClient

- `list_plans()`
- `list_tasks()`
- `list_agent_instances()`

## Best Practices

1. **Choose appropriate page sizes** - Larger pages (100-500) reduce API calls but use more memory

2. **Use async iteration** - Process items as they arrive rather than loading all into memory

3. **Handle empty pages** - Always check for empty results to detect the end

4. **Consider resumability** - For long operations, save state periodically

5. **Monitor progress** - Use `paginator.state.total_fetched` to track progress

## See Also

- [API Reference: Pagination](../api/pagination.md) - Full pagination API
- [Examples: Pagination](../examples/index.md#pagination) - Real-world examples
