# Pagination

Utilities for paginating through large result sets.

## Overview

The pagination module provides:

- **`PaginationState`**: Serializable state for pause/resume pagination
- **`Paginator`**: Stateful paginator class with pause/resume support
- **`paginate`**: Simple async iterator for one-shot pagination

## Quick Example

### Simple Pagination

```python
from atlas_sdk.pagination import paginate

async for agent_class in paginate(
    lambda limit, offset: client.list_agent_classes(limit=limit, offset=offset)
):
    print(agent_class.name)
```

### Resumable Pagination

```python
from atlas_sdk.pagination import Paginator, PaginationState

# Create paginator
paginator = Paginator(
    fetch_page=lambda limit, offset: client.list_agent_classes(
        limit=limit, offset=offset
    ),
    limit=50,
)

# Process some items
async for item in paginator:
    process(item)
    if should_pause():
        break

# Save state
state = paginator.get_state().to_dict()
save_to_database(state)

# Later: resume
saved_state = load_from_database()
paginator = Paginator.from_state(
    state=PaginationState.from_dict(saved_state),
    fetch_page=lambda limit, offset: client.list_agent_classes(
        limit=limit, offset=offset
    ),
    limit=50,
)
async for item in paginator:
    process(item)
```

## API Reference

::: atlas_sdk.pagination
    options:
      show_root_heading: false
      members_order: source
