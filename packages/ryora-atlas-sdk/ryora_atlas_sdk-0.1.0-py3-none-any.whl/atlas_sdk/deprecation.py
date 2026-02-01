"""Deprecation utilities for the Atlas SDK.

This module provides utilities for marking features as deprecated and emitting
warnings when they are used. The SDK follows a strict deprecation policy:

- Deprecated features emit `DeprecationWarning` when used
- Deprecated features are documented in CHANGELOG.md
- Deprecated features are removed no sooner than 2 minor versions after deprecation
- Migration guides are provided for all breaking changes

Example:
    ```python
    from atlas_sdk.deprecation import deprecated, deprecated_parameter

    @deprecated("1.0.0", "2.0.0", alternative="new_function")
    def old_function():
        pass

    @deprecated_parameter("old_param", "1.0.0", alternative="new_param")
    def my_function(new_param=None, old_param=None):
        if old_param is not None:
            new_param = old_param
        ...
    ```
"""

from __future__ import annotations

import functools
import warnings
from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def _format_deprecation_message(
    name: str,
    deprecated_in: str,
    removed_in: str | None = None,
    alternative: str | None = None,
    reason: str | None = None,
) -> str:
    """Format a consistent deprecation message.

    Args:
        name: Name of the deprecated feature.
        deprecated_in: Version when the feature was deprecated.
        removed_in: Version when the feature will be removed (optional).
        alternative: Alternative to use instead (optional).
        reason: Reason for deprecation (optional).

    Returns:
        Formatted deprecation message.
    """
    msg = f"'{name}' is deprecated since version {deprecated_in}"

    if removed_in:
        msg += f" and will be removed in version {removed_in}"

    msg += "."

    if reason:
        msg += f" {reason}"

    if alternative:
        msg += f" Use '{alternative}' instead."

    return msg


def deprecated(
    deprecated_in: str,
    removed_in: str | None = None,
    *,
    alternative: str | None = None,
    reason: str | None = None,
    stacklevel: int = 2,
) -> Callable[[F], F]:
    """Decorator to mark a function or method as deprecated.

    When the decorated function is called, a DeprecationWarning is emitted
    with information about when the feature was deprecated, when it will
    be removed, and what to use instead.

    Args:
        deprecated_in: Version when the feature was deprecated (e.g., "1.0.0").
        removed_in: Version when the feature will be removed (e.g., "2.0.0").
        alternative: Name of the alternative function/method to use.
        reason: Additional explanation for why it's deprecated.
        stacklevel: Stack level for the warning (default 2 points to caller).

    Returns:
        Decorator function.

    Example:
        ```python
        @deprecated("1.0.0", "2.0.0", alternative="new_function")
        def old_function():
            pass
        ```
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            message = _format_deprecation_message(
                name=func.__qualname__,
                deprecated_in=deprecated_in,
                removed_in=removed_in,
                alternative=alternative,
                reason=reason,
            )
            warnings.warn(message, DeprecationWarning, stacklevel=stacklevel)
            return func(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator


def deprecated_parameter(
    param_name: str,
    deprecated_in: str,
    removed_in: str | None = None,
    *,
    alternative: str | None = None,
    reason: str | None = None,
    stacklevel: int = 2,
) -> Callable[[F], F]:
    """Decorator to mark a function parameter as deprecated.

    When the decorated function is called with the deprecated parameter,
    a DeprecationWarning is emitted. The function still works normally.

    Args:
        param_name: Name of the deprecated parameter.
        deprecated_in: Version when the parameter was deprecated.
        removed_in: Version when the parameter will be removed.
        alternative: Name of the alternative parameter to use.
        reason: Additional explanation for why it's deprecated.
        stacklevel: Stack level for the warning (default 2 points to caller).

    Returns:
        Decorator function.

    Example:
        ```python
        @deprecated_parameter("old_param", "1.0.0", alternative="new_param")
        def my_function(new_param=None, old_param=None):
            if old_param is not None:
                new_param = old_param
            ...
        ```
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if param_name in kwargs and kwargs[param_name] is not None:
                message = _format_deprecation_message(
                    name=f"{func.__qualname__}('{param_name}' parameter)",
                    deprecated_in=deprecated_in,
                    removed_in=removed_in,
                    alternative=f"'{alternative}' parameter" if alternative else None,
                    reason=reason,
                )
                warnings.warn(message, DeprecationWarning, stacklevel=stacklevel)
            return func(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator


class DeprecatedClass:
    """Wrapper for deprecated classes that emits a warning on instantiation.

    This class is used internally by `deprecated_class()` to wrap deprecated
    classes and emit warnings when they are instantiated.

    Attributes:
        _wrapped_class: The original deprecated class.
        _deprecation_message: The warning message to emit.
        _stacklevel: Stack level for the warning.
    """

    def __init__(
        self,
        wrapped_class: type,
        deprecation_message: str,
        stacklevel: int = 2,
    ) -> None:
        """Initialize the deprecated class wrapper.

        Args:
            wrapped_class: The original class being deprecated.
            deprecation_message: The warning message to emit.
            stacklevel: Stack level for the warning.
        """
        self._wrapped_class = wrapped_class
        self._deprecation_message = deprecation_message
        self._stacklevel = stacklevel

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Create an instance of the wrapped class, emitting a warning."""
        warnings.warn(
            self._deprecation_message,
            DeprecationWarning,
            stacklevel=self._stacklevel,
        )
        return self._wrapped_class(*args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        """Forward attribute access to the wrapped class."""
        return getattr(self._wrapped_class, name)

    def __instancecheck__(self, instance: Any) -> bool:
        """Support isinstance() checks against the deprecated class."""
        return isinstance(instance, self._wrapped_class)

    def __subclasscheck__(self, subclass: type) -> bool:
        """Support issubclass() checks against the deprecated class."""
        return issubclass(subclass, self._wrapped_class)


def deprecated_class(
    deprecated_in: str,
    removed_in: str | None = None,
    *,
    alternative: str | None = None,
    reason: str | None = None,
    stacklevel: int = 2,
) -> Callable[[type], DeprecatedClass]:
    """Mark a class as deprecated.

    When the decorated class is instantiated, a DeprecationWarning is emitted.
    The class remains fully functional.

    Args:
        deprecated_in: Version when the class was deprecated.
        removed_in: Version when the class will be removed.
        alternative: Name of the alternative class to use.
        reason: Additional explanation for why it's deprecated.
        stacklevel: Stack level for the warning (default 2 points to caller).

    Returns:
        Decorator function that returns a DeprecatedClass wrapper.

    Example:
        ```python
        @deprecated_class("1.0.0", "2.0.0", alternative="NewClass")
        class OldClass:
            pass
        ```
    """

    def decorator(cls: type) -> DeprecatedClass:
        message = _format_deprecation_message(
            name=cls.__qualname__,
            deprecated_in=deprecated_in,
            removed_in=removed_in,
            alternative=alternative,
            reason=reason,
        )
        return DeprecatedClass(cls, message, stacklevel)

    return decorator


def deprecated_alias(
    alias_name: str,
    target: Any,
    deprecated_in: str,
    removed_in: str | None = None,
    *,
    stacklevel: int = 2,
) -> type:
    """Create a deprecated alias for a class that emits warnings on use.

    Unlike `deprecated_class`, this creates a proper subclass that can be
    used with isinstance() and issubclass() while still emitting warnings.

    Args:
        alias_name: Name of the deprecated alias.
        target: The target class that the alias points to.
        deprecated_in: Version when the alias was deprecated.
        removed_in: Version when the alias will be removed.
        stacklevel: Stack level for the warning.

    Returns:
        A class that inherits from target and emits deprecation warnings.

    Example:
        ```python
        # Create a deprecated alias
        OldName = deprecated_alias(
            "OldName", NewName, "1.0.0", "2.0.0"
        )
        ```
    """
    message = _format_deprecation_message(
        name=alias_name,
        deprecated_in=deprecated_in,
        removed_in=removed_in,
        alternative=target.__name__,
    )

    class DeprecatedAlias(target):  # type: ignore[misc]
        """Deprecated alias class that emits warnings on instantiation."""

        def __new__(cls, *args: Any, **kwargs: Any) -> Any:
            warnings.warn(message, DeprecationWarning, stacklevel=stacklevel)
            return super().__new__(cls)

        def __init_subclass__(cls, **kwargs: Any) -> None:
            warnings.warn(
                f"Inheriting from deprecated class '{alias_name}'. {message}",
                DeprecationWarning,
                stacklevel=stacklevel,
            )
            super().__init_subclass__(**kwargs)

    DeprecatedAlias.__name__ = alias_name
    DeprecatedAlias.__qualname__ = alias_name
    DeprecatedAlias.__doc__ = f"Deprecated: Use {target.__name__} instead."

    return DeprecatedAlias


def warn_deprecated(
    name: str,
    deprecated_in: str,
    removed_in: str | None = None,
    *,
    alternative: str | None = None,
    reason: str | None = None,
    stacklevel: int = 2,
) -> None:
    """Emit a deprecation warning for a feature.

    This function can be called directly to warn about deprecated features
    that aren't easily covered by decorators (e.g., deprecated module-level
    constants, deprecated behaviors, etc.).

    Args:
        name: Name of the deprecated feature.
        deprecated_in: Version when the feature was deprecated.
        removed_in: Version when the feature will be removed.
        alternative: Alternative to use instead.
        reason: Additional explanation for why it's deprecated.
        stacklevel: Stack level for the warning (default 2 points to caller).

    Example:
        ```python
        # In a property getter
        @property
        def old_property(self):
            warn_deprecated("old_property", "1.0.0", alternative="new_property")
            return self._value
        ```
    """
    message = _format_deprecation_message(
        name=name,
        deprecated_in=deprecated_in,
        removed_in=removed_in,
        alternative=alternative,
        reason=reason,
    )
    warnings.warn(message, DeprecationWarning, stacklevel=stacklevel)


__all__ = [
    "deprecated",
    "deprecated_parameter",
    "deprecated_class",
    "deprecated_alias",
    "warn_deprecated",
    "DeprecatedClass",
]
