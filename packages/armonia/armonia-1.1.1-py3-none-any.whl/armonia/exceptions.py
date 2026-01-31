"""Exceptions for armonia."""


class ColorNotFoundError(Exception):
    """Raised when a color cannot be found or parsed."""


class ColorNameConflictError(Exception):
    """Raised when trying to set a color name that conflicts with existing names."""


class ColorRecursionError(Exception):
    """Raised when a computed color causes infinite recursion."""


class InvalidURIError(Exception):
    """Raised when an invalid URI is provided for a logotype."""


class LogotypeNotFoundError(Exception):
    """Raised when a logotype cannot be found."""


__all__ = [
    "ColorNameConflictError",
    "ColorNotFoundError",
    "ColorRecursionError",
    "InvalidURIError",
    "LogotypeNotFoundError",
]
