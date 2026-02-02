"""Text formatting helpers.

Provides utilities for converting flexible input formats into
properly formatted PowerPoint content.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class FormattedRun:
    """A run of text with formatting."""

    text: str
    bold: bool = False
    italic: bool = False
    underline: bool = False
    strikethrough: bool = False
    font_size: int | None = None
    font_family: str | None = None
    color: str | None = None
    hyperlink: str | None = None


@dataclass
class FormattedParagraph:
    """A paragraph with multiple formatted runs."""

    runs: list[FormattedRun] = field(default_factory=list)
    level: int = 0  # Bullet level (0 = top level)
    alignment: str = "left"  # left, center, right

    def add_text(self, text: str, **formatting) -> None:
        """Add a text run to this paragraph."""
        self.runs.append(FormattedRun(text=text, **formatting))

    @property
    def plain_text(self) -> str:
        """Get the plain text without formatting."""
        return "".join(run.text for run in self.runs)


def parse_content_item(item: str | tuple | dict | list) -> FormattedParagraph:
    """Parse a single content item into a formatted paragraph.

    Accepts flexible input formats:
    - "Simple text" -> plain paragraph
    - ("Text with level", 1) -> paragraph at indent level 1
    - {"text": "Formatted", "bold": True} -> formatted paragraph
    - [{"text": "Mixed", "bold": True}, {"text": " formatting"}] -> rich text

    Args:
        item: Content item in any supported format

    Returns:
        FormattedParagraph with parsed content
    """
    para = FormattedParagraph()

    if isinstance(item, str):
        # Simple string
        para.add_text(item)

    elif isinstance(item, tuple):
        # Tuple: (text, level) or (text, level, formatting)
        if len(item) >= 2:
            text = item[0]
            para.level = int(item[1])
            if len(item) >= 3 and isinstance(item[2], dict):
                para.add_text(text, **item[2])
            else:
                para.add_text(str(text))

    elif isinstance(item, dict):
        # Dict with text and formatting
        text = item.get("text", "")
        formatting = {k: v for k, v in item.items() if k != "text" and k != "level"}
        para.level = item.get("level", 0)
        para.add_text(text, **formatting)

    elif isinstance(item, list):
        # List of dicts for rich text
        for segment in item:
            if isinstance(segment, dict):
                text = segment.get("text", "")
                formatting = {k: v for k, v in segment.items() if k != "text"}
                para.add_text(text, **formatting)
            elif isinstance(segment, str):
                para.add_text(segment)

    return para


def parse_content(
    content: str | list[str | tuple | dict | list],
    levels: list[int] | None = None,
) -> list[FormattedParagraph]:
    """Parse content into a list of formatted paragraphs.

    Args:
        content: Content in various formats
        levels: Optional list of indent levels (overrides per-item levels)

    Returns:
        List of FormattedParagraph objects

    Examples:
        >>> # Simple bullets
        >>> parse_content(["Point 1", "Point 2", "Point 3"])

        >>> # With levels
        >>> parse_content(["Main", "Sub 1", "Sub 2", "Main 2"], levels=[0, 1, 1, 0])

        >>> # Tuple format
        >>> parse_content([
        ...     "Main point",
        ...     ("Sub-point", 1),
        ...     ("Deep sub", 2),
        ... ])

        >>> # Rich text
        >>> parse_content([
        ...     [{"text": "Bold: ", "bold": True}, {"text": "normal"}],
        ...     "Plain bullet",
        ... ])
    """
    if isinstance(content, str):
        # Single string - split by newlines
        lines = content.split("\n")
        content = [line for line in lines if line.strip()]

    paragraphs = []
    for i, item in enumerate(content):
        para = parse_content_item(item)

        # Override level if provided
        if levels and i < len(levels):
            para.level = levels[i]

        paragraphs.append(para)

    return paragraphs


def format_for_py2ppt(paragraphs: list[FormattedParagraph]) -> tuple[list, list[int]]:
    """Convert formatted paragraphs to py2ppt format.

    Args:
        paragraphs: List of FormattedParagraph objects

    Returns:
        Tuple of (content_list, levels_list) for py2ppt's set_body()
    """
    content = []
    levels = []

    for para in paragraphs:
        if len(para.runs) == 1 and not _has_special_formatting(para.runs[0]):
            # Simple text
            content.append(para.runs[0].text)
        else:
            # Rich text - convert to list of dicts
            rich_text = []
            for run in para.runs:
                run_dict = {"text": run.text}
                if run.bold:
                    run_dict["bold"] = True
                if run.italic:
                    run_dict["italic"] = True
                if run.underline:
                    run_dict["underline"] = True
                if run.strikethrough:
                    run_dict["strikethrough"] = True
                if run.font_size:
                    run_dict["font_size"] = run.font_size
                if run.font_family:
                    run_dict["font_family"] = run.font_family
                if run.color:
                    run_dict["color"] = run.color
                if run.hyperlink:
                    run_dict["hyperlink"] = run.hyperlink
                rich_text.append(run_dict)
            content.append(rich_text)

        levels.append(para.level)

    return content, levels


def _has_special_formatting(run: FormattedRun) -> bool:
    """Check if a run has any special formatting."""
    return (
        run.bold
        or run.italic
        or run.underline
        or run.strikethrough
        or run.font_size is not None
        or run.font_family is not None
        or run.color is not None
        or run.hyperlink is not None
    )


def auto_bullets(items: list[str], auto_level: bool = True) -> list[FormattedParagraph]:
    """Convert a simple list to properly leveled bullets.

    Automatically detects indentation from leading spaces or dashes.

    Args:
        items: List of bullet point strings
        auto_level: If True, detect levels from indentation

    Returns:
        List of formatted paragraphs with appropriate levels
    """
    paragraphs = []

    for item in items:
        para = FormattedParagraph()
        level = 0

        if auto_level:
            # Count leading spaces (4 spaces = 1 level)
            stripped = item.lstrip()
            spaces = len(item) - len(stripped)
            level = spaces // 4

            # Also check for dash prefixes
            if stripped.startswith("- "):
                stripped = stripped[2:]
            elif stripped.startswith("* "):
                stripped = stripped[2:]

            para.add_text(stripped)
        else:
            para.add_text(item)

        para.level = level
        paragraphs.append(para)

    return paragraphs


def format_comparison_content(
    left_items: list[str | dict],
    right_items: list[str | dict],
) -> dict[str, list[FormattedParagraph]]:
    """Format content for a comparison slide.

    Args:
        left_items: Items for left column
        right_items: Items for right column

    Returns:
        Dict with 'left' and 'right' lists of paragraphs
    """
    return {
        "left": parse_content(left_items),
        "right": parse_content(right_items),
    }
