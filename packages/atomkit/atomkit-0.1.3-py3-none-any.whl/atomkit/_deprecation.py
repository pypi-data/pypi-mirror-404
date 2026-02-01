"""
Deprecation utilities for atomkit.

Provides decorators and helpers for deprecating APIs with version tracking.
"""

from __future__ import annotations

import functools
import warnings
from typing import Callable, TypeVar

from atomkit._version import __version__

F = TypeVar("F", bound=Callable)


def _parse_version(version: str) -> tuple[int, ...]:
    """Parse version string to tuple of ints for comparison."""
    # Handle versions like "0.1.2", "1.0.0", "0.2.0-dev"
    version = version.split("-")[0]  # Strip -dev, -alpha, etc.
    return tuple(int(x) for x in version.split("."))


def deprecated(
    deprecated_in: str,
    removed_in: str,
    replacement: str | None = None,
    reason: str | None = None,
) -> Callable[[F], F]:
    """
    Decorator to mark a function/method as deprecated.

    Issues a DeprecationWarning when the decorated function is called.
    Raises a RuntimeError if the current version is >= removed_in.

    Parameters
    ----------
    deprecated_in : str
        Version when this was deprecated (e.g., "0.2.0").
    removed_in : str
        Version when this will be removed (e.g., "0.3.0").
    replacement : str, optional
        Suggested replacement function/method.
    reason : str, optional
        Additional context about why it was deprecated.

    Examples
    --------
    >>> @deprecated("0.2.0", "0.3.0", replacement="new_function")
    ... def old_function():
    ...     pass

    >>> @deprecated("0.2.0", "0.3.0", reason="Use the new API instead")
    ... def legacy_method(self):
    ...     pass
    """
    current = _parse_version(__version__)
    removed = _parse_version(removed_in)

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Check if we're past the removal version
            if current >= removed:
                raise RuntimeError(
                    f"{func.__qualname__} was removed in version {removed_in}. "
                    f"Current version is {__version__}. "
                    "Please update your code to use the replacement API."
                    + (f" Replacement: {replacement}" if replacement else "")
                )

            # Build warning message
            msg = (
                f"{func.__qualname__} is deprecated since version {deprecated_in} "
                f"and will be removed in version {removed_in}."
            )
            if replacement:
                msg += f" Use {replacement} instead."
            if reason:
                msg += f" Reason: {reason}"

            warnings.warn(msg, DeprecationWarning, stacklevel=2)
            return func(*args, **kwargs)

        # Add deprecation info to docstring
        original_doc = func.__doc__ or ""
        deprecation_note = (
            f"\n\n.. deprecated:: {deprecated_in}\n"
            f"   Will be removed in {removed_in}."
        )
        if replacement:
            deprecation_note += f" Use :func:`{replacement}` instead."
        if reason:
            deprecation_note += f" {reason}"
        wrapper.__doc__ = original_doc + deprecation_note

        return wrapper  # type: ignore

    return decorator


def deprecated_property(
    deprecated_in: str,
    removed_in: str,
    replacement: str | None = None,
) -> Callable[[F], property]:
    """
    Decorator to mark a property as deprecated.

    Similar to @deprecated but returns a property descriptor.

    Examples
    --------
    >>> class MyClass:
    ...     @deprecated_property("0.2.0", "0.3.0", replacement="new_prop")
    ...     def old_prop(self):
    ...         return self._value
    """
    current = _parse_version(__version__)
    removed = _parse_version(removed_in)

    def decorator(func: F) -> property:
        @functools.wraps(func)
        def wrapper(self):
            if current >= removed:
                raise RuntimeError(
                    f"{func.__qualname__} was removed in version {removed_in}. "
                    f"Current version is {__version__}."
                    + (f" Use {replacement} instead." if replacement else "")
                )

            msg = (
                f"{func.__qualname__} is deprecated since {deprecated_in} "
                f"and will be removed in {removed_in}."
            )
            if replacement:
                msg += f" Use {replacement} instead."

            warnings.warn(msg, DeprecationWarning, stacklevel=2)
            return func(self)

        # Add deprecation info to docstring
        original_doc = func.__doc__ or ""
        deprecation_note = (
            f"\n\n.. deprecated:: {deprecated_in}\n"
            f"   Will be removed in {removed_in}."
        )
        if replacement:
            deprecation_note += f" Use :attr:`{replacement}` instead."
        wrapper.__doc__ = original_doc + deprecation_note

        return property(wrapper)

    return decorator


def deprecated_alias(
    new_name: str,
    deprecated_in: str,
    removed_in: str,
) -> Callable[[F], F]:
    """
    Decorator for creating a deprecated alias to another function.

    Useful when renaming a function but keeping the old name temporarily.

    Examples
    --------
    >>> def new_function():
    ...     return "result"
    ...
    >>> @deprecated_alias("new_function", "0.2.0", "0.3.0")
    ... def old_function():
    ...     return new_function()
    """
    return deprecated(
        deprecated_in=deprecated_in,
        removed_in=removed_in,
        replacement=new_name,
        reason=f"Renamed to {new_name}.",
    )
