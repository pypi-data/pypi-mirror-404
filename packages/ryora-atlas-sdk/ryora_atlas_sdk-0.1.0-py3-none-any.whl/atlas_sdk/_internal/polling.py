"""Polling utilities for waiting on resource state changes.

This module provides a generic polling helper used by various SDK components
to wait for resources to reach terminal states.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

from atlas_sdk.exceptions import AtlasTimeoutError

T = TypeVar("T")


async def poll_until(
    fetch: Callable[[], Awaitable[T]],
    is_terminal: Callable[[T], bool],
    *,
    poll_interval: float = 1.0,
    timeout: float | None = None,
    on_progress: Callable[[T], Awaitable[None] | None] | None = None,
    timeout_message: Callable[[T], str] | None = None,
    operation: str = "poll_until",
) -> T:
    """Poll until a resource reaches a terminal state.

    This is a generic polling helper that repeatedly fetches state and checks
    if a terminal condition is met. It handles progress callbacks (both sync
    and async), timeouts, and sleep intervals.

    Args:
        fetch: Async callable that fetches and returns the current state.
            Called at the start of each polling iteration.
        is_terminal: Callable that returns True if the state is terminal
            (i.e., polling should stop).
        poll_interval: Seconds between polling attempts. Defaults to 1.0.
        timeout: Maximum seconds to wait. None means wait indefinitely.
        on_progress: Optional callback invoked after each fetch with the
            current state. Can be sync or async.
        timeout_message: Optional callable that generates the timeout error
            message given the last state. If not provided, a generic message
            is used.
        operation: Name of the operation for the timeout error. Defaults to
            "poll_until".

    Returns:
        The final state once a terminal condition is reached.

    Raises:
        AtlasTimeoutError: If the timeout is exceeded before reaching a
            terminal state. The error includes the last known state via
            the `last_state` attribute.

    Example:
        # Wait for a plan to complete
        plan = await poll_until(
            fetch=lambda: client.get_plan(plan_id),
            is_terminal=lambda p: p.status in TERMINAL_STATUSES,
            poll_interval=2.0,
            timeout=600,
            on_progress=lambda p: print(f"Status: {p.status}"),
            timeout_message=lambda p: f"Plan {p.id} timed out: {p.status}",
            operation="wait_for_plan_completion",
        )
    """
    elapsed = 0.0
    state: T | None = None

    while True:
        state = await fetch()

        # Invoke progress callback if provided
        if on_progress is not None:
            result = on_progress(state)
            if asyncio.iscoroutine(result):
                await result

        if is_terminal(state):
            return state

        if timeout is not None and elapsed >= timeout:
            if timeout_message is not None:
                message = timeout_message(state)
            else:
                message = f"Operation '{operation}' timed out after {timeout}s"
            raise AtlasTimeoutError(
                message,
                operation=operation,
                timeout_seconds=timeout,
                last_state=state,
            )

        await asyncio.sleep(poll_interval)
        elapsed += poll_interval
