# Resumable Processing

This example demonstrates how to pause and resume long-running pagination operations.

## Use Case: Large-Scale Data Migration

You're migrating thousands of agent definitions to a new format. The operation:

- Takes hours to complete
- Needs to survive process restarts
- Must not reprocess already-handled items

## Prerequisites

- Running Control Plane instance with data
- Atlas SDK installed

## Complete Example

```python
"""
Example: Resumable Processing
Use Case: Large-scale data migration that can be paused and resumed

This example shows how to:
- Use the Paginator class for stateful pagination
- Serialize and deserialize pagination state
- Resume processing after interruption
- Track progress persistently
"""

import asyncio
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Any

from atlas_sdk import ControlPlaneClient
from atlas_sdk.pagination import Paginator, PaginationState


# =============================================================================
# State Management
# =============================================================================


@dataclass
class MigrationState:
    """
    Complete migration state including pagination and processing progress.
    """

    pagination: dict  # Serialized PaginationState
    processed_ids: list[str]  # IDs of successfully processed items
    failed_ids: list[str]  # IDs of items that failed
    last_checkpoint: str  # Timestamp of last save

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, data: str) -> "MigrationState":
        d = json.loads(data)
        return cls(**d)

    @classmethod
    def new(cls) -> "MigrationState":
        from datetime import datetime

        return cls(
            pagination=PaginationState().to_dict(),
            processed_ids=[],
            failed_ids=[],
            last_checkpoint=datetime.now().isoformat(),
        )


def save_state(state: MigrationState, path: Path) -> None:
    """Persist state to disk."""
    path.write_text(state.to_json())


def load_state(path: Path) -> MigrationState | None:
    """Load state from disk, or None if not found."""
    if path.exists():
        return MigrationState.from_json(path.read_text())
    return None


# =============================================================================
# Migration Logic
# =============================================================================


async def migrate_definition(definition: Any) -> bool:
    """
    Migrate a single definition to the new format.
    Returns True on success, False on failure.
    """
    # Simulate migration work
    await asyncio.sleep(0.1)

    # Simulate occasional failures
    if "test" in definition.name.lower():
        return False  # Skip test definitions

    return True


async def run_migration(
    client: ControlPlaneClient,
    state_path: Path,
    checkpoint_interval: int = 100,
) -> MigrationState:
    """
    Run the migration with checkpoint support.

    Args:
        client: Atlas SDK client
        state_path: Path to save state file
        checkpoint_interval: Save state every N items
    """
    # Load existing state or create new
    state = load_state(state_path)
    if state:
        print(f"Resuming migration from checkpoint: {state.last_checkpoint}")
        print(f"  Already processed: {len(state.processed_ids)}")
        print(f"  Failed: {len(state.failed_ids)}")
        pagination_state = PaginationState.from_dict(state.pagination)
    else:
        print("Starting new migration")
        state = MigrationState.new()
        pagination_state = PaginationState()

    # Create paginator from state
    paginator = Paginator.from_state(
        state=pagination_state,
        fetch_page=lambda limit, offset: client.list_agent_definitions(
            limit=limit, offset=offset
        ),
        limit=50,
    )

    # Process items
    items_since_checkpoint = 0
    processed_set = set(state.processed_ids)  # For O(1) lookup

    try:
        async for definition in paginator:
            # Skip already processed
            if str(definition.id) in processed_set:
                continue

            # Migrate
            success = await migrate_definition(definition)

            # Track result
            if success:
                state.processed_ids.append(str(definition.id))
                processed_set.add(str(definition.id))
                print(f"✓ Migrated: {definition.name}")
            else:
                state.failed_ids.append(str(definition.id))
                print(f"✗ Failed: {definition.name}")

            # Periodic checkpoint
            items_since_checkpoint += 1
            if items_since_checkpoint >= checkpoint_interval:
                state.pagination = paginator.get_state().to_dict()
                from datetime import datetime

                state.last_checkpoint = datetime.now().isoformat()
                save_state(state, state_path)
                print(f"  [Checkpoint saved at {len(state.processed_ids)} items]")
                items_since_checkpoint = 0

    except KeyboardInterrupt:
        print("\n\nInterrupted! Saving checkpoint...")

    finally:
        # Always save final state
        state.pagination = paginator.get_state().to_dict()
        from datetime import datetime

        state.last_checkpoint = datetime.now().isoformat()
        save_state(state, state_path)
        print(f"Final state saved: {len(state.processed_ids)} processed, {len(state.failed_ids)} failed")

    return state


# =============================================================================
# Batch Processing with Resumability
# =============================================================================


async def process_in_batches(
    client: ControlPlaneClient,
    batch_size: int = 100,
    state_path: Path = Path("batch_state.json"),
) -> None:
    """
    Process items in batches with resumability.
    Better for operations that benefit from batch processing (e.g., bulk API calls).
    """
    # Load or create state
    state = load_state(state_path) or MigrationState.new()
    pagination_state = PaginationState.from_dict(state.pagination)

    paginator = Paginator.from_state(
        state=pagination_state,
        fetch_page=lambda limit, offset: client.list_agent_definitions(
            limit=limit, offset=offset
        ),
        limit=batch_size,
    )

    processed_set = set(state.processed_ids)
    batch_number = 0

    try:
        while paginator.state.has_more:
            # Get next batch
            batch = await paginator.next_page()
            batch_number += 1

            if not batch:
                break

            # Filter out already processed
            new_items = [
                item for item in batch if str(item.id) not in processed_set
            ]

            if not new_items:
                print(f"Batch {batch_number}: All items already processed, skipping")
                continue

            print(f"Batch {batch_number}: Processing {len(new_items)} items...")

            # Process batch (could be a bulk API call)
            for item in new_items:
                success = await migrate_definition(item)
                if success:
                    state.processed_ids.append(str(item.id))
                    processed_set.add(str(item.id))
                else:
                    state.failed_ids.append(str(item.id))

            # Save after each batch
            state.pagination = paginator.get_state().to_dict()
            from datetime import datetime

            state.last_checkpoint = datetime.now().isoformat()
            save_state(state, state_path)
            print(f"  Batch {batch_number} complete, checkpoint saved")

    except KeyboardInterrupt:
        print("\nInterrupted!")
    finally:
        state.pagination = paginator.get_state().to_dict()
        save_state(state, state_path)


# =============================================================================
# Progress Tracking
# =============================================================================


async def migration_with_progress(
    client: ControlPlaneClient,
    state_path: Path,
    on_progress: callable = None,
) -> MigrationState:
    """
    Migration with progress tracking callback.

    Args:
        client: Atlas SDK client
        state_path: Path for state persistence
        on_progress: Callback(processed, failed, total_fetched, has_more)
    """
    state = load_state(state_path) or MigrationState.new()
    pagination_state = PaginationState.from_dict(state.pagination)

    paginator = Paginator.from_state(
        state=pagination_state,
        fetch_page=lambda limit, offset: client.list_agent_definitions(
            limit=limit, offset=offset
        ),
        limit=100,
    )

    processed_set = set(state.processed_ids)

    async for definition in paginator:
        if str(definition.id) not in processed_set:
            success = await migrate_definition(definition)
            if success:
                state.processed_ids.append(str(definition.id))
                processed_set.add(str(definition.id))
            else:
                state.failed_ids.append(str(definition.id))

        # Report progress
        if on_progress:
            pag_state = paginator.get_state()
            on_progress(
                len(state.processed_ids),
                len(state.failed_ids),
                pag_state.total_fetched,
                pag_state.has_more,
            )

    # Final save
    state.pagination = paginator.get_state().to_dict()
    save_state(state, state_path)

    return state


# =============================================================================
# Main
# =============================================================================


async def main():
    """Demonstrate resumable processing patterns."""

    state_path = Path("migration_state.json")

    async with ControlPlaneClient(base_url="http://localhost:8000") as client:
        print("=== Resumable Migration Demo ===\n")

        # Run migration (can be interrupted with Ctrl+C)
        print("Starting migration (press Ctrl+C to interrupt)...")
        print("Run again to resume from checkpoint.\n")

        state = await run_migration(
            client,
            state_path,
            checkpoint_interval=50,
        )

        print("\n=== Migration Summary ===")
        print(f"Processed: {len(state.processed_ids)}")
        print(f"Failed: {len(state.failed_ids)}")
        print(f"Last checkpoint: {state.last_checkpoint}")

        # Check if complete
        pag = PaginationState.from_dict(state.pagination)
        if not pag.has_more:
            print("\n✓ Migration complete!")
            # Optionally clean up state file
            # state_path.unlink()
        else:
            print("\n→ Migration in progress. Run again to continue.")


if __name__ == "__main__":
    asyncio.run(main())
```

## Key Points

### PaginationState

The `PaginationState` class tracks:

```python
@dataclass
class PaginationState:
    offset: int = 0           # Current position
    cursor: str | None = None # For cursor-based pagination
    has_more: bool = True     # More items available?
    total_fetched: int = 0    # Items fetched so far
```

### Serialization

State can be serialized to JSON for persistence:

```python
# Save
state_dict = paginator.get_state().to_dict()
json.dumps(state_dict)

# Load
state = PaginationState.from_dict(json.loads(data))
paginator = Paginator.from_state(state, fetch_page, limit)
```

### Checkpoint Strategy

| Strategy | Use Case |
|----------|----------|
| Every N items | Consistent checkpoint frequency |
| After each batch | Batch processing with bulk operations |
| Time-based | Long-running processes (every 5 minutes) |
| Combined | Both item count and time thresholds |

### Idempotency

Track processed IDs to handle restarts safely:

```python
processed_set = set(state.processed_ids)

async for item in paginator:
    if str(item.id) in processed_set:
        continue  # Already processed
    # Process item...
```

## Best Practices

1. **Always save on interruption** - Use try/finally to save state
2. **Track failures separately** - Don't mix with processed items
3. **Use sets for lookups** - O(1) vs O(n) for checking processed items
4. **Include timestamps** - Know when checkpoints were made
5. **Test resume logic** - Ensure state loads correctly after restart

## Next Steps

- [Efficient Pagination](05_pagination.md) - Basic pagination patterns
- [Concurrent Operations](09_concurrent_operations.md) - Speed up processing
