"""Tests for atlas_sdk._internal.params module."""

from __future__ import annotations

from enum import Enum
from uuid import UUID


from atlas_sdk._internal.params import build_list_params


class MockStatus(Enum):
    """Mock enum for testing."""

    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"


class TestBuildListParams:
    """Tests for the build_list_params function."""

    def test_basic_pagination_only(self) -> None:
        """Returns limit and offset with no filters."""
        result = build_list_params(100, 0)
        assert result == {"limit": 100, "offset": 0}

    def test_custom_pagination_values(self) -> None:
        """Accepts custom limit and offset values."""
        result = build_list_params(50, 25)
        assert result == {"limit": 50, "offset": 25}

    def test_none_filter_is_omitted(self) -> None:
        """None values in filters are not included."""
        result = build_list_params(100, 0, status=None, name=None)
        assert result == {"limit": 100, "offset": 0}

    def test_string_filter_passed_through(self) -> None:
        """String filter values are passed through unchanged."""
        result = build_list_params(100, 0, environment="production")
        assert result == {"limit": 100, "offset": 0, "environment": "production"}

    def test_boolean_filter_passed_through(self) -> None:
        """Boolean filter values are passed through unchanged."""
        result = build_list_params(100, 0, active_only=True)
        assert result == {"limit": 100, "offset": 0, "active_only": True}

    def test_boolean_false_is_included(self) -> None:
        """Boolean False is included (not treated as None)."""
        result = build_list_params(100, 0, active_only=False)
        assert result == {"limit": 100, "offset": 0, "active_only": False}

    def test_integer_filter_passed_through(self) -> None:
        """Integer filter values are passed through unchanged."""
        result = build_list_params(100, 0, page=5)
        assert result == {"limit": 100, "offset": 0, "page": 5}

    def test_uuid_converted_to_string(self) -> None:
        """UUID values are converted to strings."""
        test_uuid = UUID("12345678-1234-5678-1234-567812345678")
        result = build_list_params(100, 0, deployment_id=test_uuid)
        assert result == {
            "limit": 100,
            "offset": 0,
            "deployment_id": "12345678-1234-5678-1234-567812345678",
        }

    def test_enum_converted_to_value(self) -> None:
        """Enum values are converted to their .value."""
        result = build_list_params(100, 0, status=MockStatus.PENDING)
        assert result == {"limit": 100, "offset": 0, "status": "pending"}

    def test_multiple_filters(self) -> None:
        """Handles multiple filters of different types."""
        test_uuid = UUID("12345678-1234-5678-1234-567812345678")
        result = build_list_params(
            50,
            10,
            deployment_id=test_uuid,
            status=MockStatus.ACTIVE,
            environment="staging",
            active_only=True,
        )
        assert result == {
            "limit": 50,
            "offset": 10,
            "deployment_id": "12345678-1234-5678-1234-567812345678",
            "status": "active",
            "environment": "staging",
            "active_only": True,
        }

    def test_mixed_none_and_values(self) -> None:
        """None values are omitted while other values are included."""
        result = build_list_params(
            100, 0, status=MockStatus.COMPLETED, name=None, active=True
        )
        assert result == {
            "limit": 100,
            "offset": 0,
            "status": "completed",
            "active": True,
        }

    def test_empty_string_is_included(self) -> None:
        """Empty string is included (not treated as None)."""
        result = build_list_params(100, 0, name="")
        assert result == {"limit": 100, "offset": 0, "name": ""}

    def test_zero_is_included(self) -> None:
        """Zero is included (not treated as None)."""
        result = build_list_params(100, 0, count=0)
        assert result == {"limit": 100, "offset": 0, "count": 0}

    def test_list_filter_passed_through(self) -> None:
        """List values are passed through unchanged."""
        result = build_list_params(100, 0, tags=["a", "b", "c"])
        assert result == {"limit": 100, "offset": 0, "tags": ["a", "b", "c"]}

    def test_preserves_filter_order(self) -> None:
        """Filter keys maintain insertion order (Python 3.7+)."""
        result = build_list_params(100, 0, z_filter="z", a_filter="a", m_filter="m")
        keys = list(result.keys())
        # limit and offset come first, then filters in order passed
        assert keys == ["limit", "offset", "z_filter", "a_filter", "m_filter"]
