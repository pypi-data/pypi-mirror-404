"""HTTP-related utilities for the Atlas SDK.

This module contains internal helper functions for HTTP operations.
"""

from __future__ import annotations

import time
from email.utils import parsedate_to_datetime


def parse_retry_after(header_value: str | None) -> float | None:
    """Parse a Retry-After header value.

    The Retry-After header can be in one of two formats:
    - A number of seconds (e.g., "120")
    - An HTTP date (e.g., "Wed, 21 Oct 2015 07:28:00 GMT")

    Args:
        header_value: The value of the Retry-After header, or None.

    Returns:
        The number of seconds to wait, or None if the header is missing
        or cannot be parsed.

    Example:
        >>> parse_retry_after("120")
        120.0
        >>> parse_retry_after("Wed, 21 Oct 2015 07:28:00 GMT")
        # Returns seconds until that time (may be negative if in the past)
        >>> parse_retry_after(None)
        None
    """
    if header_value is None:
        return None

    # Try parsing as number of seconds first
    try:
        return float(header_value)
    except ValueError:
        pass

    # Try parsing as HTTP date
    try:
        retry_date = parsedate_to_datetime(header_value)
        delta: float = retry_date.timestamp() - time.time()
        return max(0.0, delta)
    except (ValueError, TypeError):
        return None
