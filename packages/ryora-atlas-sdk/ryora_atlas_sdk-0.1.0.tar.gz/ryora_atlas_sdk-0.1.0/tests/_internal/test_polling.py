"""Tests for the polling utility module."""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from atlas_sdk._internal.polling import poll_until
from atlas_sdk.exceptions import AtlasTimeoutError


class TestPollUntilBasicBehavior:
    """Tests for basic poll_until functionality."""

    @pytest.mark.asyncio
    async def test_returns_immediately_when_terminal(self) -> None:
        """Should return immediately when initial state is terminal."""
        fetch = AsyncMock(return_value={"status": "completed"})
        is_terminal = MagicMock(return_value=True)

        result = await poll_until(fetch=fetch, is_terminal=is_terminal)

        assert result == {"status": "completed"}
        fetch.assert_called_once()
        is_terminal.assert_called_once_with({"status": "completed"})

    @pytest.mark.asyncio
    async def test_polls_until_terminal(self) -> None:
        """Should poll multiple times until terminal condition is met."""
        states = [
            {"status": "pending"},
            {"status": "running"},
            {"status": "completed"},
        ]
        fetch = AsyncMock(side_effect=states)
        is_terminal = MagicMock(side_effect=[False, False, True])

        result = await poll_until(
            fetch=fetch,
            is_terminal=is_terminal,
            poll_interval=0.01,
        )

        assert result == {"status": "completed"}
        assert fetch.call_count == 3
        assert is_terminal.call_count == 3

    @pytest.mark.asyncio
    async def test_respects_poll_interval(self) -> None:
        """Should sleep for poll_interval between fetches."""
        states = [{"status": "pending"}, {"status": "completed"}]
        fetch = AsyncMock(side_effect=states)
        is_terminal = MagicMock(side_effect=[False, True])

        with pytest.MonkeyPatch().context() as mp:
            sleep_mock = AsyncMock()
            mp.setattr(asyncio, "sleep", sleep_mock)

            await poll_until(
                fetch=fetch,
                is_terminal=is_terminal,
                poll_interval=2.5,
            )

            sleep_mock.assert_called_once_with(2.5)


class TestPollUntilTimeout:
    """Tests for timeout behavior."""

    @pytest.mark.asyncio
    async def test_raises_timeout_error_when_exceeded(self) -> None:
        """Should raise AtlasTimeoutError when timeout is exceeded."""
        fetch = AsyncMock(return_value={"status": "pending"})
        is_terminal = MagicMock(return_value=False)

        with pytest.raises(AtlasTimeoutError) as exc_info:
            await poll_until(
                fetch=fetch,
                is_terminal=is_terminal,
                poll_interval=0.05,
                timeout=0.1,
            )

        error = exc_info.value
        assert error.timeout_seconds == 0.1
        assert error.operation == "poll_until"
        assert error.last_state == {"status": "pending"}

    @pytest.mark.asyncio
    async def test_timeout_error_includes_custom_message(self) -> None:
        """Should use custom timeout_message when provided."""
        fetch = AsyncMock(return_value={"id": "123", "status": "pending"})
        is_terminal = MagicMock(return_value=False)

        with pytest.raises(AtlasTimeoutError) as exc_info:
            await poll_until(
                fetch=fetch,
                is_terminal=is_terminal,
                poll_interval=0.05,
                timeout=0.1,
                timeout_message=lambda s: f"Resource {s['id']} timed out: {s['status']}",
                operation="wait_for_resource",
            )

        error = exc_info.value
        assert str(error) == "Resource 123 timed out: pending"
        assert error.operation == "wait_for_resource"

    @pytest.mark.asyncio
    async def test_no_timeout_when_none(self) -> None:
        """Should poll indefinitely when timeout is None."""
        call_count = 0

        async def counting_fetch() -> dict[str, Any]:
            nonlocal call_count
            call_count += 1
            if call_count >= 5:
                return {"status": "completed"}
            return {"status": "pending"}

        result = await poll_until(
            fetch=counting_fetch,
            is_terminal=lambda s: s["status"] == "completed",
            poll_interval=0.01,
            timeout=None,
        )

        assert result == {"status": "completed"}
        assert call_count == 5


class TestPollUntilProgressCallback:
    """Tests for progress callback functionality."""

    @pytest.mark.asyncio
    async def test_calls_sync_progress_callback(self) -> None:
        """Should invoke sync progress callback after each fetch."""
        states = [{"status": "pending"}, {"status": "completed"}]
        fetch = AsyncMock(side_effect=states)
        is_terminal = MagicMock(side_effect=[False, True])
        progress_calls: list[dict[str, str]] = []

        def on_progress(state: dict[str, str]) -> None:
            progress_calls.append(state)

        await poll_until(
            fetch=fetch,
            is_terminal=is_terminal,
            poll_interval=0.01,
            on_progress=on_progress,
        )

        assert progress_calls == [{"status": "pending"}, {"status": "completed"}]

    @pytest.mark.asyncio
    async def test_calls_async_progress_callback(self) -> None:
        """Should await async progress callback."""
        states = [{"status": "pending"}, {"status": "completed"}]
        fetch = AsyncMock(side_effect=states)
        is_terminal = MagicMock(side_effect=[False, True])
        progress_calls: list[dict[str, str]] = []

        async def on_progress(state: dict[str, str]) -> None:
            await asyncio.sleep(0.001)
            progress_calls.append(state)

        await poll_until(
            fetch=fetch,
            is_terminal=is_terminal,
            poll_interval=0.01,
            on_progress=on_progress,
        )

        assert progress_calls == [{"status": "pending"}, {"status": "completed"}]

    @pytest.mark.asyncio
    async def test_progress_callback_called_before_terminal_check(self) -> None:
        """Should call progress callback before checking terminal condition."""
        order: list[str] = []

        async def fetch() -> dict[str, str]:
            order.append("fetch")
            return {"status": "completed"}

        def on_progress(state: dict[str, str]) -> None:
            order.append("progress")

        def is_terminal(state: dict[str, str]) -> bool:
            order.append("terminal")
            return True

        await poll_until(
            fetch=fetch,
            is_terminal=is_terminal,
            on_progress=on_progress,
        )

        assert order == ["fetch", "progress", "terminal"]


class TestPollUntilEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_fetch_error_propagates(self) -> None:
        """Should propagate errors from fetch function."""

        async def failing_fetch() -> dict[str, str]:
            raise RuntimeError("Connection failed")

        with pytest.raises(RuntimeError, match="Connection failed"):
            await poll_until(
                fetch=failing_fetch,
                is_terminal=lambda s: True,
            )

    @pytest.mark.asyncio
    async def test_is_terminal_error_propagates(self) -> None:
        """Should propagate errors from is_terminal function."""
        fetch = AsyncMock(return_value={"status": "pending"})

        def failing_terminal(state: dict[str, str]) -> bool:
            raise ValueError("Invalid state")

        with pytest.raises(ValueError, match="Invalid state"):
            await poll_until(
                fetch=fetch,
                is_terminal=failing_terminal,
            )

    @pytest.mark.asyncio
    async def test_progress_callback_error_propagates(self) -> None:
        """Should propagate errors from progress callback."""
        fetch = AsyncMock(return_value={"status": "pending"})
        is_terminal = MagicMock(return_value=False)

        def failing_progress(state: dict[str, str]) -> None:
            raise RuntimeError("Progress error")

        with pytest.raises(RuntimeError, match="Progress error"):
            await poll_until(
                fetch=fetch,
                is_terminal=is_terminal,
                on_progress=failing_progress,
            )

    @pytest.mark.asyncio
    async def test_default_timeout_message(self) -> None:
        """Should use default timeout message when not provided."""
        fetch = AsyncMock(return_value={"status": "pending"})
        is_terminal = MagicMock(return_value=False)

        with pytest.raises(AtlasTimeoutError) as exc_info:
            await poll_until(
                fetch=fetch,
                is_terminal=is_terminal,
                poll_interval=0.05,
                timeout=0.1,
                operation="custom_operation",
            )

        assert "custom_operation" in str(exc_info.value)
        assert "0.1" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_timeout_at_boundary(self) -> None:
        """Should timeout when elapsed equals timeout exactly."""
        # This test verifies the >= comparison in the timeout check
        call_count = 0

        async def counting_fetch() -> dict[str, str]:
            nonlocal call_count
            call_count += 1
            return {"status": "pending"}

        with pytest.raises(AtlasTimeoutError):
            await poll_until(
                fetch=counting_fetch,
                is_terminal=lambda s: False,
                poll_interval=0.05,
                timeout=0.1,
            )

        # Should have polled at least twice before timeout
        assert call_count >= 2
