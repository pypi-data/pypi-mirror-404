"""Tests for atlas_sdk._internal.http module."""

from __future__ import annotations

import time
from email.utils import formatdate


from atlas_sdk._internal.http import parse_retry_after


class TestParseRetryAfter:
    """Tests for the parse_retry_after function."""

    def test_parse_none_returns_none(self) -> None:
        """Returns None when header value is None."""
        assert parse_retry_after(None) is None

    def test_parse_empty_string_returns_none(self) -> None:
        """Returns None when header value is empty string."""
        # Empty string fails float conversion and date parsing
        assert parse_retry_after("") is None

    def test_parse_integer_seconds(self) -> None:
        """Parses integer number of seconds."""
        assert parse_retry_after("120") == 120.0

    def test_parse_float_seconds(self) -> None:
        """Parses floating point number of seconds."""
        assert parse_retry_after("30.5") == 30.5

    def test_parse_zero_seconds(self) -> None:
        """Parses zero seconds."""
        assert parse_retry_after("0") == 0.0

    def test_parse_large_seconds(self) -> None:
        """Parses large number of seconds."""
        assert parse_retry_after("3600") == 3600.0

    def test_parse_http_date_in_future(self) -> None:
        """Parses HTTP date in the future and returns seconds until then."""
        # Create a date 60 seconds in the future
        future_time = time.time() + 60
        http_date = formatdate(future_time, usegmt=True)

        result = parse_retry_after(http_date)

        assert result is not None
        # Allow some tolerance for test execution time
        assert 58 <= result <= 62

    def test_parse_http_date_in_past_returns_zero(self) -> None:
        """Returns 0 for HTTP dates in the past."""
        # Create a date 60 seconds in the past
        past_time = time.time() - 60
        http_date = formatdate(past_time, usegmt=True)

        result = parse_retry_after(http_date)

        assert result == 0.0

    def test_parse_invalid_string_returns_none(self) -> None:
        """Returns None for invalid strings that aren't numbers or dates."""
        assert parse_retry_after("not-a-number") is None
        assert parse_retry_after("abc123") is None
        assert parse_retry_after("foo bar baz") is None

    def test_parse_negative_seconds(self) -> None:
        """Parses negative seconds (though unusual, should work)."""
        # Negative values are technically invalid per RFC 7231 but we parse them
        assert parse_retry_after("-5") == -5.0

    def test_parse_whitespace_only_returns_none(self) -> None:
        """Returns None for whitespace-only strings."""
        assert parse_retry_after("   ") is None
        assert parse_retry_after("\t\n") is None

    def test_parse_seconds_with_whitespace(self) -> None:
        """Handles leading/trailing whitespace around number gracefully."""
        # Python's float() handles this
        assert parse_retry_after(" 120 ") == 120.0

    def test_parse_malformed_date_returns_none(self) -> None:
        """Returns None for malformed date strings."""
        assert parse_retry_after("Wed, 99 Foo 2015") is None
        assert parse_retry_after("2015-01-01T00:00:00Z") is None  # ISO format, not HTTP

    def test_parse_valid_rfc_1123_date(self) -> None:
        """Parses RFC 1123 date format (standard HTTP date)."""
        # Wed, 21 Oct 2015 07:28:00 GMT is a valid RFC 1123 date
        # This is in the past so should return 0
        result = parse_retry_after("Wed, 21 Oct 2015 07:28:00 GMT")
        assert result == 0.0
