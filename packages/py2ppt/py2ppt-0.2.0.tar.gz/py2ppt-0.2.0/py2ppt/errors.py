"""Structured errors with AI-friendly suggestions.

Provides error classes that include actionable suggestions
and error codes, making it easy for AI agents to handle
errors programmatically.
"""

from __future__ import annotations

from typing import Any


class Py2PptError(Exception):
    """Base error for py2ppt with AI-friendly metadata.

    Attributes:
        message: Human-readable error description
        suggestion: Actionable suggestion for fixing the error
        code: Machine-readable error code
    """

    def __init__(
        self,
        message: str,
        suggestion: str = "",
        code: str = "",
    ) -> None:
        super().__init__(message)
        self.message = message
        self.suggestion = suggestion
        self.code = code

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON/AI consumption."""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "suggestion": self.suggestion,
            "code": self.code,
        }


class SlideNotFoundError(Py2PptError):
    """Raised when a slide number is out of range."""

    pass


class LayoutNotFoundError(Py2PptError):
    """Raised when a layout name or index cannot be found."""

    pass


class ContentOverflowError(Py2PptError):
    """Raised when content exceeds placeholder capacity."""

    pass


class InvalidDataError(Py2PptError):
    """Raised when data format is invalid for the requested operation."""

    pass
