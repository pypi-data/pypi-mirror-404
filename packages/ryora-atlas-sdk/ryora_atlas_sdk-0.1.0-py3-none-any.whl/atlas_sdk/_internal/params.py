"""Query parameter building utilities for the Atlas SDK.

This module contains internal helper functions for constructing HTTP query parameters.
"""

from __future__ import annotations

from enum import Enum
from typing import Any
from uuid import UUID


def build_list_params(
    limit: int,
    offset: int,
    **filters: Any,
) -> dict[str, Any]:
    """Build query parameters for list endpoints.

    Handles common transformations:
    - UUID values are converted to strings
    - Enum values are converted to their .value
    - None values are omitted
    - Other values are passed through as-is

    Args:
        limit: Maximum number of results to return.
        offset: Number of results to skip.
        **filters: Optional filter parameters. None values are omitted.

    Returns:
        A dictionary of query parameters ready for HTTP requests.

    Example:
        >>> from uuid import UUID
        >>> from atlas_sdk.models.enums import PlanStatus
        >>> build_list_params(100, 0)
        {'limit': 100, 'offset': 0}
        >>> build_list_params(50, 10, status=PlanStatus.PENDING)
        {'limit': 50, 'offset': 10, 'status': 'pending'}
        >>> build_list_params(100, 0, deployment_id=UUID('...'), name=None)
        {'limit': 100, 'offset': 0, 'deployment_id': '...'}
    """
    params: dict[str, Any] = {"limit": limit, "offset": offset}

    for key, value in filters.items():
        if value is None:
            continue
        elif isinstance(value, UUID):
            params[key] = str(value)
        elif isinstance(value, Enum):
            params[key] = value.value
        else:
            params[key] = value

    return params
