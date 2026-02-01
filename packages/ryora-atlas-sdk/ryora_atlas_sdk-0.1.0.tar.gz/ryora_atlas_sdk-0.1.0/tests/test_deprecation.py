"""Tests for the deprecation utilities module."""

from __future__ import annotations

import warnings

from atlas_sdk.deprecation import (
    DeprecatedClass,
    deprecated,
    deprecated_alias,
    deprecated_class,
    deprecated_parameter,
    warn_deprecated,
)


class TestDeprecatedDecorator:
    """Tests for the @deprecated decorator."""

    def test_emits_warning_on_call(self) -> None:
        """Test that calling a deprecated function emits a warning."""

        @deprecated("1.0.0", "2.0.0", alternative="new_func")
        def old_func() -> str:
            return "result"

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = old_func()

            assert result == "result"
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "old_func" in str(w[0].message)
            assert "1.0.0" in str(w[0].message)
            assert "2.0.0" in str(w[0].message)
            assert "new_func" in str(w[0].message)

    def test_includes_version_info(self) -> None:
        """Test that the warning includes version information."""

        @deprecated("0.5.0", "1.0.0")
        def versioned_func() -> None:
            pass

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            versioned_func()

            assert "deprecated since version 0.5.0" in str(w[0].message)
            assert "removed in version 1.0.0" in str(w[0].message)

    def test_without_removal_version(self) -> None:
        """Test deprecation without a removal version specified."""

        @deprecated("1.0.0")
        def no_removal_version() -> None:
            pass

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            no_removal_version()

            assert "1.0.0" in str(w[0].message)
            assert "removed" not in str(w[0].message)

    def test_with_reason(self) -> None:
        """Test deprecation with a custom reason."""

        @deprecated("1.0.0", reason="This was a bad idea.")
        def bad_idea() -> None:
            pass

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            bad_idea()

            assert "bad idea" in str(w[0].message).lower()

    def test_preserves_function_metadata(self) -> None:
        """Test that the decorator preserves function metadata."""

        @deprecated("1.0.0")
        def documented_func() -> None:
            """This is the docstring."""
            pass

        assert documented_func.__name__ == "documented_func"
        assert documented_func.__doc__ == "This is the docstring."

    def test_with_method(self) -> None:
        """Test deprecation on a class method."""

        class MyClass:
            @deprecated("1.0.0", alternative="new_method")
            def old_method(self) -> str:
                return "method result"

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            obj = MyClass()
            result = obj.old_method()

            assert result == "method result"
            assert len(w) == 1
            assert "old_method" in str(w[0].message)


class TestDeprecatedParameterDecorator:
    """Tests for the @deprecated_parameter decorator."""

    def test_warns_when_deprecated_param_used(self) -> None:
        """Test that using a deprecated parameter emits a warning."""

        @deprecated_parameter("old_param", "1.0.0", alternative="new_param")
        def func_with_deprecated_param(
            new_param: str | None = None, old_param: str | None = None
        ) -> str:
            return new_param or old_param or "default"

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = func_with_deprecated_param(old_param="value")

            assert result == "value"
            assert len(w) == 1
            assert "old_param" in str(w[0].message)
            assert "new_param" in str(w[0].message)

    def test_no_warning_when_new_param_used(self) -> None:
        """Test that no warning is emitted when using the new parameter."""

        @deprecated_parameter("old_param", "1.0.0", alternative="new_param")
        def func_with_deprecated_param(
            new_param: str | None = None, old_param: str | None = None
        ) -> str:
            return new_param or old_param or "default"

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = func_with_deprecated_param(new_param="value")

            assert result == "value"
            assert len(w) == 0

    def test_no_warning_when_param_is_none(self) -> None:
        """Test that no warning is emitted when param is explicitly None."""

        @deprecated_parameter("old_param", "1.0.0")
        def func_with_deprecated_param(old_param: str | None = None) -> str:
            return old_param or "default"

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = func_with_deprecated_param(old_param=None)

            assert result == "default"
            assert len(w) == 0


class TestDeprecatedClass:
    """Tests for deprecated class utilities."""

    def test_deprecated_class_decorator(self) -> None:
        """Test the @deprecated_class decorator."""

        @deprecated_class("1.0.0", "2.0.0", alternative="NewClass")
        class OldClass:
            def __init__(self, value: int) -> None:
                self.value = value

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            obj = OldClass(42)

            assert obj.value == 42
            assert len(w) == 1
            assert "OldClass" in str(w[0].message)
            assert "NewClass" in str(w[0].message)

    def test_deprecated_class_wrapper_isinstance(self) -> None:
        """Test that isinstance works with DeprecatedClass wrapper."""

        class OriginalClass:
            pass

        wrapper = DeprecatedClass(OriginalClass, "test message")

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            obj = wrapper()
            assert isinstance(obj, OriginalClass)


class TestDeprecatedAlias:
    """Tests for the deprecated_alias function."""

    def test_alias_emits_warning(self) -> None:
        """Test that using a deprecated alias emits a warning."""

        class NewClass:
            def __init__(self, value: int) -> None:
                self.value = value

        OldName = deprecated_alias("OldName", NewClass, "1.0.0", "2.0.0")

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            obj = OldName(42)

            assert obj.value == 42
            assert len(w) == 1
            assert "OldName" in str(w[0].message)
            assert "NewClass" in str(w[0].message)

    def test_alias_isinstance(self) -> None:
        """Test that isinstance works with deprecated aliases."""

        class NewClass:
            pass

        OldName = deprecated_alias("OldName", NewClass, "1.0.0")

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            obj = OldName()

            assert isinstance(obj, NewClass)
            assert isinstance(obj, OldName)

    def test_alias_issubclass(self) -> None:
        """Test that issubclass works with deprecated aliases."""

        class NewClass:
            pass

        OldName = deprecated_alias("OldName", NewClass, "1.0.0")

        assert issubclass(OldName, NewClass)


class TestWarnDeprecated:
    """Tests for the warn_deprecated function."""

    def test_emits_warning(self) -> None:
        """Test that warn_deprecated emits a warning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            warn_deprecated("feature_name", "1.0.0", "2.0.0", alternative="new_feature")

            assert len(w) == 1
            assert "feature_name" in str(w[0].message)
            assert "new_feature" in str(w[0].message)

    def test_with_reason(self) -> None:
        """Test warn_deprecated with a custom reason."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            warn_deprecated("feature", "1.0.0", reason="Security concerns.")

            assert "Security concerns" in str(w[0].message)


class TestAtlasHTTPStatusErrorDeprecation:
    """Tests for the AtlasHTTPStatusError deprecation."""

    def test_imports_with_warning(self) -> None:
        """Test that importing AtlasHTTPStatusError emits a deprecation warning."""
        # The warning is emitted when accessing the attribute from the module
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            # Access the deprecated attribute - this triggers the warning
            import atlas_sdk

            _ = atlas_sdk.AtlasHTTPStatusError

            # Check for deprecation warning
            deprecation_warnings = [
                x for x in w if issubclass(x.category, DeprecationWarning)
            ]
            assert len(deprecation_warnings) >= 1
            assert any(
                "AtlasHTTPStatusError" in str(x.message) for x in deprecation_warnings
            )

    def test_instantiation_works(self) -> None:
        """Test that AtlasHTTPStatusError can still be instantiated."""
        import httpx

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            from atlas_sdk import AtlasHTTPStatusError

            request = httpx.Request("GET", "http://example.com")
            response = httpx.Response(404, request=request)

            exc = AtlasHTTPStatusError(
                "Not found",
                status_code=404,
                request=request,
                response=response,
            )
            assert exc.status_code == 404

    def test_isinstance_with_atlas_api_error(self) -> None:
        """Test that AtlasHTTPStatusError instances are also AtlasAPIError."""
        import httpx

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            from atlas_sdk import AtlasAPIError, AtlasHTTPStatusError

            request = httpx.Request("GET", "http://example.com")
            response = httpx.Response(404, request=request)

            exc = AtlasHTTPStatusError(
                "Not found",
                status_code=404,
                request=request,
                response=response,
            )
            assert isinstance(exc, AtlasAPIError)

    def test_is_same_class_as_atlas_api_error(self) -> None:
        """Test that AtlasHTTPStatusError is the same class as AtlasAPIError."""
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            from atlas_sdk import AtlasAPIError, AtlasHTTPStatusError

            # The deprecated alias should be the exact same class
            assert AtlasHTTPStatusError is AtlasAPIError
