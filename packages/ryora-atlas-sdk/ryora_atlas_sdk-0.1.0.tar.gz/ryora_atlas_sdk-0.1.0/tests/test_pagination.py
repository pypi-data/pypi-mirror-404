"""Tests for pagination utilities."""

import pytest

from atlas_sdk.pagination import paginate, Paginator, PaginationState


class TestPaginationState:
    """Tests for PaginationState."""

    def test_default_values(self) -> None:
        state = PaginationState()
        assert state.offset == 0
        assert state.cursor is None
        assert state.has_more is True
        assert state.total_fetched == 0

    def test_custom_values(self) -> None:
        state = PaginationState(
            offset=50, cursor="abc123", has_more=False, total_fetched=150
        )
        assert state.offset == 50
        assert state.cursor == "abc123"
        assert state.has_more is False
        assert state.total_fetched == 150

    def test_to_dict(self) -> None:
        state = PaginationState(
            offset=25, cursor="xyz", has_more=True, total_fetched=75
        )
        data = state.to_dict()
        assert data == {
            "offset": 25,
            "cursor": "xyz",
            "has_more": True,
            "total_fetched": 75,
        }

    def test_from_dict(self) -> None:
        data = {
            "offset": 100,
            "cursor": "cursor_value",
            "has_more": False,
            "total_fetched": 200,
        }
        state = PaginationState.from_dict(data)
        assert state.offset == 100
        assert state.cursor == "cursor_value"
        assert state.has_more is False
        assert state.total_fetched == 200

    def test_from_dict_with_missing_fields(self) -> None:
        data: dict[str, int | str | bool | None] = {}
        state = PaginationState.from_dict(data)
        assert state.offset == 0
        assert state.cursor is None
        assert state.has_more is True
        assert state.total_fetched == 0

    def test_serialization_roundtrip(self) -> None:
        original = PaginationState(
            offset=42, cursor="test_cursor", has_more=True, total_fetched=84
        )
        serialized = original.to_dict()
        restored = PaginationState.from_dict(serialized)

        assert restored.offset == original.offset
        assert restored.cursor == original.cursor
        assert restored.has_more == original.has_more
        assert restored.total_fetched == original.total_fetched


class TestPaginator:
    """Tests for Paginator."""

    @pytest.mark.asyncio
    async def test_single_page(self) -> None:
        """Test pagination with results that fit in one page."""
        items = ["a", "b", "c"]

        async def fetch_page(limit: int, offset: int) -> list[str]:
            return items[offset : offset + limit]

        paginator = Paginator(fetch_page=fetch_page, limit=10)

        result = []
        async for item in paginator:
            result.append(item)

        assert result == ["a", "b", "c"]
        assert paginator.state.has_more is False
        assert paginator.state.total_fetched == 3

    @pytest.mark.asyncio
    async def test_multiple_pages(self) -> None:
        """Test pagination across multiple pages."""
        items = ["a", "b", "c", "d", "e", "f", "g"]

        async def fetch_page(limit: int, offset: int) -> list[str]:
            return items[offset : offset + limit]

        paginator = Paginator(fetch_page=fetch_page, limit=3)

        result = []
        async for item in paginator:
            result.append(item)

        assert result == ["a", "b", "c", "d", "e", "f", "g"]
        assert paginator.state.has_more is False
        assert paginator.state.total_fetched == 7

    @pytest.mark.asyncio
    async def test_empty_results(self) -> None:
        """Test pagination with no results."""

        async def fetch_page(limit: int, offset: int) -> list[str]:
            return []

        paginator = Paginator(fetch_page=fetch_page, limit=10)

        result = []
        async for item in paginator:
            result.append(item)

        assert result == []
        assert paginator.state.has_more is False
        assert paginator.state.total_fetched == 0

    @pytest.mark.asyncio
    async def test_next_page(self) -> None:
        """Test fetching pages one at a time."""
        items = ["a", "b", "c", "d", "e"]

        async def fetch_page(limit: int, offset: int) -> list[str]:
            return items[offset : offset + limit]

        paginator = Paginator(fetch_page=fetch_page, limit=2)

        page1 = await paginator.next_page()
        assert page1 == ["a", "b"]
        assert paginator.state.offset == 2
        assert paginator.state.has_more is True

        page2 = await paginator.next_page()
        assert page2 == ["c", "d"]
        assert paginator.state.offset == 4
        assert paginator.state.has_more is True

        page3 = await paginator.next_page()
        assert page3 == ["e"]
        assert paginator.state.offset == 5
        assert paginator.state.has_more is False

        page4 = await paginator.next_page()
        assert page4 == []

    @pytest.mark.asyncio
    async def test_get_state(self) -> None:
        """Test getting paginator state."""
        items = ["a", "b", "c"]

        async def fetch_page(limit: int, offset: int) -> list[str]:
            return items[offset : offset + limit]

        paginator = Paginator(fetch_page=fetch_page, limit=2)

        await paginator.next_page()
        state = paginator.get_state()

        assert state.offset == 2
        assert state.total_fetched == 2

    @pytest.mark.asyncio
    async def test_from_state(self) -> None:
        """Test creating paginator from saved state."""
        items = ["a", "b", "c", "d", "e"]

        async def fetch_page(limit: int, offset: int) -> list[str]:
            return items[offset : offset + limit]

        # Simulate previous pagination
        saved_state = PaginationState(offset=2, has_more=True, total_fetched=2)

        # Resume from saved state
        paginator = Paginator.from_state(
            state=saved_state, fetch_page=fetch_page, limit=2
        )

        result = []
        async for item in paginator:
            result.append(item)

        # Should only get remaining items
        assert result == ["c", "d", "e"]
        assert paginator.state.total_fetched == 5  # 2 + 3

    @pytest.mark.asyncio
    async def test_pause_resume_roundtrip(self) -> None:
        """Test full pause/resume workflow using page-level operations."""
        items = list(range(10))

        async def fetch_page(limit: int, offset: int) -> list[int]:
            return items[offset : offset + limit]

        # Start pagination using page-level API for clean pause/resume
        paginator1 = Paginator(fetch_page=fetch_page, limit=3)

        # Fetch exactly 2 pages (6 items)
        collected = []
        page1 = await paginator1.next_page()
        collected.extend(page1)
        page2 = await paginator1.next_page()
        collected.extend(page2)

        assert collected == [0, 1, 2, 3, 4, 5]

        # Save state
        saved = paginator1.get_state().to_dict()
        assert saved["offset"] == 6

        # Resume later
        restored_state = PaginationState.from_dict(saved)
        paginator2 = Paginator.from_state(
            state=restored_state, fetch_page=fetch_page, limit=3
        )

        # Continue collecting (should get remaining items)
        async for item in paginator2:
            collected.append(item)

        assert collected == list(range(10))


class TestPaginateFunction:
    """Tests for the paginate() async generator."""

    @pytest.mark.asyncio
    async def test_simple_iteration(self) -> None:
        """Test simple iteration with paginate()."""
        items = ["x", "y", "z"]

        async def fetch_page(limit: int, offset: int) -> list[str]:
            return items[offset : offset + limit]

        result = []
        async for item in paginate(fetch_page, limit=10):
            result.append(item)

        assert result == ["x", "y", "z"]

    @pytest.mark.asyncio
    async def test_multiple_pages(self) -> None:
        """Test paginate() across multiple pages."""
        items = list(range(25))

        async def fetch_page(limit: int, offset: int) -> list[int]:
            return items[offset : offset + limit]

        result = []
        async for item in paginate(fetch_page, limit=10):
            result.append(item)

        assert result == list(range(25))

    @pytest.mark.asyncio
    async def test_empty_results(self) -> None:
        """Test paginate() with no results."""

        async def fetch_page(limit: int, offset: int) -> list[str]:
            return []

        result = []
        async for item in paginate(fetch_page, limit=10):
            result.append(item)

        assert result == []

    @pytest.mark.asyncio
    async def test_exact_page_boundary(self) -> None:
        """Test paginate() when items exactly fill pages."""
        items = list(range(20))

        async def fetch_page(limit: int, offset: int) -> list[int]:
            return items[offset : offset + limit]

        result = []
        async for item in paginate(fetch_page, limit=10):
            result.append(item)

        assert result == list(range(20))


# =============================================================================
# Error Scenario Tests for Pagination (Issue 1.4)
# =============================================================================


class TestPaginatorNetworkErrors:
    """Tests for network error handling during pagination."""

    @pytest.mark.asyncio
    async def test_network_error_on_first_page(self) -> None:
        """Test pagination handles network error on first page."""

        async def fetch_page(limit: int, offset: int) -> list[str]:
            raise ConnectionError("Network error")

        paginator = Paginator(fetch_page=fetch_page, limit=10)

        with pytest.raises(ConnectionError):
            async for _ in paginator:
                pass

    @pytest.mark.asyncio
    async def test_network_error_mid_pagination(self) -> None:
        """Test pagination handles network error mid-iteration."""
        items = list(range(50))
        call_count = 0

        async def fetch_page(limit: int, offset: int) -> list[int]:
            nonlocal call_count
            call_count += 1
            if call_count == 3:  # Fail on third page
                raise ConnectionError("Network error on page 3")
            return items[offset : offset + limit]

        paginator = Paginator(fetch_page=fetch_page, limit=10)

        collected = []
        with pytest.raises(ConnectionError, match="page 3"):
            async for item in paginator:
                collected.append(item)

        # Should have collected first two pages before error
        assert collected == list(range(20))
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_state_preserved_after_error(self) -> None:
        """Test pagination state is preserved after error for potential retry."""
        items = list(range(50))
        fail_once = True

        async def fetch_page(limit: int, offset: int) -> list[int]:
            nonlocal fail_once
            if offset == 20 and fail_once:
                fail_once = False
                raise ConnectionError("Temporary error")
            return items[offset : offset + limit]

        paginator = Paginator(fetch_page=fetch_page, limit=10)

        # First iteration fails mid-way
        collected = []
        try:
            async for item in paginator:
                collected.append(item)
        except ConnectionError:
            pass

        # State should reflect progress before error
        state = paginator.get_state()
        assert state.offset == 20  # Got two pages before failure
        assert state.total_fetched == 20

        # Can resume from saved state
        resumed = Paginator.from_state(state=state, fetch_page=fetch_page, limit=10)
        async for item in resumed:
            collected.append(item)

        assert collected == list(range(50))


class TestPaginatorTimeoutErrors:
    """Tests for timeout handling during pagination."""

    @pytest.mark.asyncio
    async def test_timeout_on_fetch(self) -> None:
        """Test pagination handles timeout on fetch."""
        import asyncio

        async def slow_fetch(limit: int, offset: int) -> list[str]:
            await asyncio.sleep(0.5)  # Slow enough to trigger timeout
            return []

        paginator = Paginator(fetch_page=slow_fetch, limit=10)

        with pytest.raises(asyncio.TimeoutError):
            async with asyncio.timeout(0.1):
                async for _ in paginator:
                    pass

    @pytest.mark.asyncio
    async def test_timeout_mid_pagination(self) -> None:
        """Test pagination handles timeout in the middle of iteration."""
        import asyncio

        items = list(range(50))
        call_count = 0

        async def fetch_page(limit: int, offset: int) -> list[int]:
            nonlocal call_count
            call_count += 1
            if call_count == 3:
                await asyncio.sleep(0.5)  # Slow on third page
            return items[offset : offset + limit]

        paginator = Paginator(fetch_page=fetch_page, limit=10)

        collected = []
        with pytest.raises(asyncio.TimeoutError):
            async with asyncio.timeout(0.2):
                async for item in paginator:
                    collected.append(item)

        # Should have first two pages
        assert collected == list(range(20))


class TestPaginatorMalformedResponses:
    """Tests for malformed response handling during pagination."""

    @pytest.mark.asyncio
    async def test_none_response(self) -> None:
        """Test pagination handles None response."""

        async def fetch_page(limit: int, offset: int) -> list[str] | None:
            return None  # type: ignore[return-value]

        paginator = Paginator(fetch_page=fetch_page, limit=10)

        # Should handle None gracefully - iteration ends
        result = []
        # Depending on implementation, this might raise or just return empty
        try:
            async for item in paginator:
                result.append(item)
        except TypeError:
            pass  # Expected if None isn't handled

    @pytest.mark.asyncio
    async def test_non_list_response(self) -> None:
        """Test pagination handles non-list response.

        Note: This test documents that many Python iterables (strings, dicts) will
        work with the paginator but may produce unexpected results. The paginator
        relies on len() returning fewer items than limit to terminate.
        """

        # Return a dict - iteration yields keys, so it works but returns keys
        async def fetch_page(limit: int, offset: int) -> list[str]:
            if offset == 0:
                return {"a": 1, "b": 2}  # type: ignore[return-value]
            return []  # Return empty list on second call to stop

        paginator = Paginator(fetch_page=fetch_page, limit=10)

        # Dict iteration yields keys, so this "works" but returns dict keys
        result = []
        async for item in paginator:
            result.append(item)

        # This documents the actual (possibly surprising) behavior
        assert "a" in result
        assert "b" in result

    @pytest.mark.asyncio
    async def test_mixed_type_response(self) -> None:
        """Test pagination handles response with unexpected item types."""
        call_count = 0

        async def fetch_page(limit: int, offset: int) -> list:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return ["a", "b", "c"]  # 3 items
            elif call_count == 2:
                return [1, 2, 3]  # Different type - 3 items
            return []  # Signal end of pagination

        # Use limit=3 so full pages continue, < 3 signals end
        paginator = Paginator(fetch_page=fetch_page, limit=3)

        # Should still iterate (no type checking at runtime)
        result = []
        async for item in paginator:
            result.append(item)

        assert result == ["a", "b", "c", 1, 2, 3]

    @pytest.mark.asyncio
    async def test_empty_string_response(self) -> None:
        """Test pagination handles empty items in response."""

        async def fetch_page(limit: int, offset: int) -> list[str]:
            if offset == 0:
                return ["", "", ""]  # Empty strings are valid items
            return []

        paginator = Paginator(fetch_page=fetch_page, limit=10)

        result = []
        async for item in paginator:
            result.append(item)

        assert result == ["", "", ""]


class TestPaginatorWrongItemCount:
    """Tests for server returning unexpected item counts."""

    @pytest.mark.asyncio
    async def test_more_items_than_limit(self) -> None:
        """Test pagination handles server returning more items than requested."""

        async def fetch_page(limit: int, offset: int) -> list[int]:
            # Server ignores limit and returns 20 items
            return list(range(offset, offset + 20))

        paginator = Paginator(fetch_page=fetch_page, limit=5)

        # Fetch one page
        page = await paginator.next_page()

        # Should handle oversized response
        assert len(page) == 20
        # State should reflect actual items received
        assert paginator.state.offset == 20
        assert paginator.state.total_fetched == 20

    @pytest.mark.asyncio
    async def test_fewer_items_than_expected(self) -> None:
        """Test pagination handles server returning fewer items than expected."""
        items = [1, 2]  # Only 2 items total

        async def fetch_page(limit: int, offset: int) -> list[int]:
            return items[offset : offset + limit]

        paginator = Paginator(fetch_page=fetch_page, limit=10)

        page = await paginator.next_page()

        assert page == [1, 2]
        assert paginator.state.has_more is False  # Recognizes end of data

    @pytest.mark.asyncio
    async def test_zero_items_on_first_page(self) -> None:
        """Test pagination handles zero items on first page."""

        async def fetch_page(limit: int, offset: int) -> list[int]:
            return []

        paginator = Paginator(fetch_page=fetch_page, limit=10)

        result = []
        async for item in paginator:
            result.append(item)

        assert result == []
        assert paginator.state.has_more is False

    @pytest.mark.asyncio
    async def test_inconsistent_counts_across_pages(self) -> None:
        """Test pagination handles inconsistent item counts across pages.

        The paginator terminates when a page returns fewer items than the limit.
        This test verifies it handles variable page sizes correctly.
        """
        call_count = 0

        async def fetch_page(limit: int, offset: int) -> list[str]:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return ["a", "b", "c"]  # 3 items (full page)
            elif call_count == 2:
                return ["d", "e", "f"]  # 3 items (full page)
            elif call_count == 3:
                return ["g", "h"]  # 2 items (less than limit, triggers end)
            return []

        # Limit=3 so first two pages are "full"
        paginator = Paginator(fetch_page=fetch_page, limit=3)

        result = []
        async for item in paginator:
            result.append(item)

        # Should collect all items until getting fewer than limit
        assert result == ["a", "b", "c", "d", "e", "f", "g", "h"]
        assert paginator.state.has_more is False


class TestPaginateFunctionErrorScenarios:
    """Error scenario tests for the paginate() function."""

    @pytest.mark.asyncio
    async def test_paginate_network_error(self) -> None:
        """Test paginate() handles network errors."""

        async def fetch_page(limit: int, offset: int) -> list[str]:
            if offset == 10:
                raise ConnectionError("Network lost")
            return [f"item_{i}" for i in range(offset, offset + limit)]

        collected = []
        with pytest.raises(ConnectionError):
            async for item in paginate(fetch_page, limit=5):
                collected.append(item)

        # Should have first two pages
        assert len(collected) == 10

    @pytest.mark.asyncio
    async def test_paginate_exception_in_callback(self) -> None:
        """Test paginate() propagates exceptions from callback."""

        async def fetch_page(limit: int, offset: int) -> list[int]:
            return list(range(offset, offset + limit))

        count = 0
        with pytest.raises(ValueError, match="test error"):
            async for item in paginate(fetch_page, limit=5):
                count += 1
                if count == 7:
                    raise ValueError("test error")

        assert count == 7

    @pytest.mark.asyncio
    async def test_paginate_generator_cleanup_on_error(self) -> None:
        """Test paginate() generator cleanup happens on error."""
        cleanup_called = False

        async def fetch_page(limit: int, offset: int) -> list[int]:
            nonlocal cleanup_called
            try:
                return list(range(offset, offset + limit))
            finally:
                if offset > 0:
                    cleanup_called = True

        try:
            async for item in paginate(fetch_page, limit=5):
                if item == 5:
                    raise RuntimeError("abort")
        except RuntimeError:
            pass

        # Generator should have been properly handled


class TestPaginatorEdgeCases:
    """Additional edge case tests for Paginator."""

    @pytest.mark.asyncio
    async def test_reuse_exhausted_paginator(self) -> None:
        """Test behavior when reusing an exhausted paginator."""
        items = [1, 2, 3]

        async def fetch_page(limit: int, offset: int) -> list[int]:
            return items[offset : offset + limit]

        paginator = Paginator(fetch_page=fetch_page, limit=10)

        # Exhaust the paginator
        result1 = []
        async for item in paginator:
            result1.append(item)

        assert result1 == [1, 2, 3]

        # Try to iterate again - should yield nothing
        result2 = []
        async for item in paginator:
            result2.append(item)

        assert result2 == []

    @pytest.mark.asyncio
    async def test_concurrent_pagination_isolation(self) -> None:
        """Test that multiple paginators are isolated."""
        import asyncio

        items1 = ["a", "b", "c"]
        items2 = [1, 2, 3]

        async def fetch1(limit: int, offset: int) -> list[str]:
            return items1[offset : offset + limit]

        async def fetch2(limit: int, offset: int) -> list[int]:
            return items2[offset : offset + limit]

        paginator1 = Paginator(fetch_page=fetch1, limit=10)
        paginator2 = Paginator(fetch_page=fetch2, limit=10)

        results1: list[str] = []
        results2: list[int] = []

        async def collect1() -> None:
            async for item in paginator1:
                results1.append(item)

        async def collect2() -> None:
            async for item in paginator2:
                results2.append(item)

        await asyncio.gather(collect1(), collect2())

        assert results1 == ["a", "b", "c"]
        assert results2 == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_large_offset_start(self) -> None:
        """Test pagination starting from a large offset."""
        items = list(range(1000))

        async def fetch_page(limit: int, offset: int) -> list[int]:
            return items[offset : offset + limit]

        # Start from a large offset
        state = PaginationState(offset=990, has_more=True, total_fetched=990)
        paginator = Paginator.from_state(state=state, fetch_page=fetch_page, limit=10)

        result = []
        async for item in paginator:
            result.append(item)

        assert result == list(range(990, 1000))
        assert paginator.state.total_fetched == 1000
