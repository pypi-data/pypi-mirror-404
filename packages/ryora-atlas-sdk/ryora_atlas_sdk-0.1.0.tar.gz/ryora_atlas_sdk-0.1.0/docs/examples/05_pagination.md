# Efficient Pagination

This example demonstrates efficient pagination patterns for working with large datasets.

## Use Case: Processing All Agent Definitions

You need to process all agent definitions in your Atlas deployment for:

- Generating a compliance report
- Migrating configurations
- Building a search index

## Prerequisites

- Running Control Plane instance with data
- Atlas SDK installed

## Complete Example

```python
"""
Example: Efficient Pagination
Use Case: Process all agent definitions for a compliance audit

This example shows how to:
- Use the simple paginate() helper for one-shot iteration
- Process large datasets memory-efficiently
- Handle pagination with different page sizes
- Track progress during pagination
"""

import asyncio
from dataclasses import dataclass, field
from typing import Any

from atlas_sdk import ControlPlaneClient
from atlas_sdk.pagination import paginate


@dataclass
class ComplianceReport:
    """Accumulates compliance findings."""

    total_definitions: int = 0
    by_model: dict[str, int] = field(default_factory=dict)
    missing_descriptions: list[str] = field(default_factory=list)
    high_temperature: list[str] = field(default_factory=list)

    def add_definition(self, definition: Any) -> None:
        """Process a single definition."""
        self.total_definitions += 1

        # Track model usage
        model = definition.model_name or "unknown"
        self.by_model[model] = self.by_model.get(model, 0) + 1

        # Check for missing description
        if not definition.description:
            self.missing_descriptions.append(definition.name)

        # Check for high temperature (risky for deterministic tasks)
        config = definition.config or {}
        temp = config.get("temperature", 0)
        if temp > 0.7:
            self.high_temperature.append(f"{definition.name} (temp={temp})")

    def print_summary(self) -> None:
        """Print the compliance report."""
        print("\n" + "=" * 50)
        print("COMPLIANCE REPORT")
        print("=" * 50)

        print(f"\nTotal definitions analyzed: {self.total_definitions}")

        print("\nModel distribution:")
        for model, count in sorted(
            self.by_model.items(), key=lambda x: x[1], reverse=True
        ):
            print(f"  {model}: {count}")

        if self.missing_descriptions:
            print(f"\n⚠ Definitions missing description ({len(self.missing_descriptions)}):")
            for name in self.missing_descriptions[:5]:
                print(f"  - {name}")
            if len(self.missing_descriptions) > 5:
                print(f"  ... and {len(self.missing_descriptions) - 5} more")

        if self.high_temperature:
            print(f"\n⚠ High temperature settings ({len(self.high_temperature)}):")
            for item in self.high_temperature[:5]:
                print(f"  - {item}")
            if len(self.high_temperature) > 5:
                print(f"  ... and {len(self.high_temperature) - 5} more")


async def audit_with_simple_pagination(client: ControlPlaneClient) -> ComplianceReport:
    """
    Audit using the simple paginate() helper.
    Best for one-shot iteration through all items.
    """
    report = ComplianceReport()
    processed = 0

    print("Starting audit with simple pagination...")

    async for definition in paginate(
        fetch_page=lambda limit, offset: client.list_agent_definitions(
            limit=limit, offset=offset
        ),
        limit=100,  # Fetch 100 items per page
    ):
        report.add_definition(definition)
        processed += 1

        # Progress indicator every 100 items
        if processed % 100 == 0:
            print(f"  Processed {processed} definitions...")

    print(f"  Completed: {processed} definitions")
    return report


async def audit_with_manual_pagination(client: ControlPlaneClient) -> ComplianceReport:
    """
    Audit using manual pagination.
    Gives more control over the pagination process.
    """
    report = ComplianceReport()
    offset = 0
    limit = 50  # Smaller page size for demonstration

    print("Starting audit with manual pagination...")

    while True:
        # Fetch a page
        page = await client.list_agent_definitions(limit=limit, offset=offset)

        if not page:
            break  # No more items

        # Process items in this page
        for definition in page:
            report.add_definition(definition)

        print(f"  Processed page at offset {offset} ({len(page)} items)")

        # Check if this was the last page
        if len(page) < limit:
            break

        offset += len(page)

    return report


async def audit_with_progress_callback(
    client: ControlPlaneClient,
    on_progress: callable,
) -> ComplianceReport:
    """
    Audit with a progress callback for UI updates.
    """
    report = ComplianceReport()

    async for definition in paginate(
        fetch_page=lambda limit, offset: client.list_agent_definitions(
            limit=limit, offset=offset
        ),
        limit=100,
    ):
        report.add_definition(definition)
        on_progress(report.total_definitions, definition.name)

    return report


async def count_all_resources(client: ControlPlaneClient) -> dict[str, int]:
    """
    Count all resources of each type.
    Demonstrates parallel pagination across different resource types.
    """
    async def count_items(fetch_page) -> int:
        count = 0
        async for _ in paginate(fetch_page=fetch_page, limit=100):
            count += 1
        return count

    # Count all resource types in parallel
    counts = await asyncio.gather(
        count_items(
            lambda limit, offset: client.list_agent_classes(limit=limit, offset=offset)
        ),
        count_items(
            lambda limit, offset: client.list_agent_definitions(
                limit=limit, offset=offset
            )
        ),
        count_items(
            lambda limit, offset: client.list_model_providers(
                limit=limit, offset=offset
            )
        ),
        count_items(
            lambda limit, offset: client.list_system_prompts(limit=limit, offset=offset)
        ),
        count_items(
            lambda limit, offset: client.list_tools(limit=limit, offset=offset)
        ),
    )

    return {
        "agent_classes": counts[0],
        "agent_definitions": counts[1],
        "model_providers": counts[2],
        "system_prompts": counts[3],
        "tools": counts[4],
    }


async def find_definitions_by_model(
    client: ControlPlaneClient,
    model_name: str,
) -> list:
    """
    Find all definitions using a specific model.
    Demonstrates filtering during pagination.
    """
    matches = []

    async for definition in paginate(
        fetch_page=lambda limit, offset: client.list_agent_definitions(
            limit=limit, offset=offset
        ),
        limit=100,
    ):
        if definition.model_name == model_name:
            matches.append(definition)

    return matches


async def main():
    """Run pagination examples."""

    async with ControlPlaneClient(base_url="http://localhost:8000") as client:
        # Example 1: Simple pagination
        print("\n=== Example 1: Simple Pagination ===")
        report = await audit_with_simple_pagination(client)
        report.print_summary()

        # Example 2: Manual pagination
        print("\n=== Example 2: Manual Pagination ===")
        report2 = await audit_with_manual_pagination(client)
        print(f"Total from manual: {report2.total_definitions}")

        # Example 3: Progress callback
        print("\n=== Example 3: With Progress Callback ===")

        def progress_handler(count: int, name: str):
            if count % 50 == 0:
                print(f"  [{count}] Processing: {name}")

        report3 = await audit_with_progress_callback(client, progress_handler)
        print(f"Total with callback: {report3.total_definitions}")

        # Example 4: Count all resources
        print("\n=== Example 4: Count All Resources ===")
        counts = await count_all_resources(client)
        print("Resource counts:")
        for resource, count in counts.items():
            print(f"  {resource}: {count}")

        # Example 5: Filter during pagination
        print("\n=== Example 5: Find by Model ===")
        gpt4_definitions = await find_definitions_by_model(client, "gpt-4")
        print(f"Definitions using GPT-4: {len(gpt4_definitions)}")


if __name__ == "__main__":
    asyncio.run(main())
```

## Key Points

### paginate() Helper

The simplest way to iterate through all items:

```python
async for item in paginate(
    fetch_page=lambda limit, offset: client.list_resources(limit=limit, offset=offset),
    limit=100,
):
    process(item)
```

### Page Size Selection

| Page Size | Use Case |
|-----------|----------|
| 10-50 | Interactive UI, quick response needed |
| 100 | General purpose (default) |
| 500-1000 | Batch processing, fewer API calls |

### Memory Efficiency

`paginate()` is memory-efficient because it:

1. Fetches one page at a time
2. Yields items individually
3. Doesn't store all items in memory

For even better memory usage, process items immediately:

```python
async for item in paginate(...):
    # Process immediately, don't collect into a list
    await save_to_database(item)
```

### Parallel Pagination

Count or process multiple resource types concurrently:

```python
results = await asyncio.gather(
    count_items(client.list_agent_classes),
    count_items(client.list_agent_definitions),
    count_items(client.list_tools),
)
```

## Next Steps

- [Resumable Processing](06_resumable_processing.md) - Pause and resume pagination
- [Concurrent Operations](09_concurrent_operations.md) - Parallel processing
