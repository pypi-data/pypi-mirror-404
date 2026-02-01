"""Pagination utilities for Atlas SDK.

This module provides utilities for paginating through large result sets:
- PaginationState: Serializable state for pause/resume pagination
- Paginator: Stateful paginator class with pause/resume support
- paginate: Simple async iterator for one-shot pagination
"""

from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass, field
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass
class PaginationState:
    """Serializable state for resumable pagination.

    Use this to pause pagination and resume later by serializing the state.

    Attributes:
        offset: Current offset in the result set.
        cursor: Optional cursor for cursor-based pagination (future use).
        has_more: Whether there are more items to fetch.
        total_fetched: Total number of items fetched so far.
    """

    offset: int = 0
    cursor: str | None = None
    has_more: bool = True
    total_fetched: int = 0

    def to_dict(self) -> dict[str, int | str | bool | None]:
        """Serialize state to a dictionary."""
        return {
            "offset": self.offset,
            "cursor": self.cursor,
            "has_more": self.has_more,
            "total_fetched": self.total_fetched,
        }

    @classmethod
    def from_dict(cls, data: dict[str, int | str | bool | None]) -> "PaginationState":
        """Deserialize state from a dictionary."""
        offset_val = data.get("offset", 0)
        total_val = data.get("total_fetched", 0)
        cursor_val = data.get("cursor")
        return cls(
            offset=int(offset_val) if offset_val is not None else 0,
            cursor=str(cursor_val) if cursor_val else None,
            has_more=bool(data.get("has_more", True)),
            total_fetched=int(total_val) if total_val is not None else 0,
        )


# Type alias for page fetch function
PageFetcher = Callable[[int, int], Awaitable[list[T]]]


@dataclass
class Paginator(Generic[T]):
    """Stateful paginator with pause/resume support.

    The Paginator allows iterating through paginated results while maintaining
    state that can be serialized and resumed later.

    Example:
        # Create paginator
        paginator = Paginator(
            fetch_page=lambda limit, offset: client.list_agent_classes(
                limit=limit, offset=offset
            ),
            limit=50,
        )

        # Iterate through results
        async for item in paginator:
            print(item.name)

        # Pause and save state
        state = paginator.get_state()
        saved_state = state.to_dict()

        # Later, resume from saved state
        new_paginator = Paginator.from_state(
            state=PaginationState.from_dict(saved_state),
            fetch_page=lambda limit, offset: client.list_agent_classes(
                limit=limit, offset=offset
            ),
            limit=50,
        )
        async for item in new_paginator:
            print(item.name)
    """

    fetch_page: PageFetcher[T]
    limit: int = 100
    state: PaginationState = field(default_factory=PaginationState)

    def get_state(self) -> PaginationState:
        """Get current pagination state for serialization."""
        return self.state

    @classmethod
    def from_state(
        cls,
        state: PaginationState,
        fetch_page: PageFetcher[T],
        limit: int = 100,
    ) -> "Paginator[T]":
        """Create a paginator from a previously saved state.

        Args:
            state: Previously saved pagination state.
            fetch_page: Async function to fetch a page of results.
            limit: Maximum items per page.

        Returns:
            A new Paginator that will resume from the saved state.
        """
        return cls(fetch_page=fetch_page, limit=limit, state=state)

    async def next_page(self) -> list[T]:
        """Fetch the next page of results.

        Returns:
            List of items from the next page, or empty list if no more pages.
        """
        if not self.state.has_more:
            return []

        items = await self.fetch_page(self.limit, self.state.offset)

        if len(items) < self.limit:
            self.state.has_more = False

        self.state.offset += len(items)
        self.state.total_fetched += len(items)

        return items

    def __aiter__(self) -> AsyncIterator[T]:
        """Return async iterator for iterating through all items."""
        return self._iterate()

    async def _iterate(self) -> AsyncIterator[T]:
        """Internal async generator for iteration."""
        while self.state.has_more:
            items = await self.next_page()
            for item in items:
                yield item


async def paginate(
    fetch_page: PageFetcher[T],
    limit: int = 100,
) -> AsyncIterator[T]:
    """Simple async iterator for one-shot pagination.

    This is a convenience function for simple pagination scenarios where
    pause/resume is not needed.

    Args:
        fetch_page: Async function that takes (limit, offset) and returns a list.
        limit: Maximum items per page.

    Yields:
        Items from each page.

    Example:
        async for agent_class in paginate(
            lambda limit, offset: client.list_agent_classes(limit=limit, offset=offset)
        ):
            print(agent_class.name)
    """
    offset = 0
    while True:
        items = await fetch_page(limit, offset)
        if not items:
            break

        for item in items:
            yield item

        if len(items) < limit:
            break

        offset += len(items)
