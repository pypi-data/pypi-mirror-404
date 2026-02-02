"""Presentation comparison and diff functionality.

Compares two presentations and reports differences
in slides, content, and structure.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .presentation import Presentation


@dataclass
class SlideDiff:
    """Difference in a single slide."""

    slide_number: int
    changes: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class PresentationDiff:
    """Complete diff between two presentations."""

    slides_added: list[int] = field(default_factory=list)
    slides_removed: list[int] = field(default_factory=list)
    slides_modified: list[SlideDiff] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON/AI consumption."""
        return {
            "slides_added": self.slides_added,
            "slides_removed": self.slides_removed,
            "slides_modified": [
                {
                    "slide": d.slide_number,
                    "changes": d.changes,
                    "details": d.details,
                }
                for d in self.slides_modified
            ],
            "summary": self.summary,
        }

    def to_text(self) -> str:
        """Generate human-readable diff text."""
        lines = ["Presentation Diff", "=" * 40]

        if not self.slides_added and not self.slides_removed and not self.slides_modified:
            lines.append("No differences found.")
            return "\n".join(lines)

        if self.slides_added:
            lines.append(f"\nSlides Added: {', '.join(str(s) for s in self.slides_added)}")

        if self.slides_removed:
            lines.append(f"\nSlides Removed: {', '.join(str(s) for s in self.slides_removed)}")

        if self.slides_modified:
            lines.append("\nModified Slides:")
            for diff in self.slides_modified:
                lines.append(f"  Slide {diff.slide_number}:")
                for change in diff.changes:
                    lines.append(f"    - {change}")

        lines.append(f"\n{self.summary}")

        return "\n".join(lines)


def diff_presentations(
    pres1: "Presentation",
    pres2: "Presentation",
    *,
    format: str = "dict",
) -> PresentationDiff | dict | str:
    """Compare two presentations and return differences.

    Args:
        pres1: First presentation (baseline)
        pres2: Second presentation (to compare)
        format: Output format - "dict", "text", or "object"

    Returns:
        PresentationDiff object, dict, or text string

    Example:
        >>> changes = diff_presentations(pres1, pres2)
        >>> print(changes["slides_added"])
        [4, 5]

        >>> text_diff = diff_presentations(pres1, pres2, format="text")
        >>> print(text_diff)
    """
    diff = PresentationDiff()

    count1 = pres1.slide_count
    count2 = pres2.slide_count

    # Get slide descriptions
    slides1 = pres1.describe_all_slides() if count1 > 0 else []
    slides2 = pres2.describe_all_slides() if count2 > 0 else []

    # Build lookup by slide number
    slides1_by_num = {s["slide_number"]: s for s in slides1}
    slides2_by_num = {s["slide_number"]: s for s in slides2}

    # Find added slides (in pres2 but not in pres1)
    for num in range(1, count2 + 1):
        if num > count1:
            diff.slides_added.append(num)

    # Find removed slides (in pres1 but not in pres2)
    for num in range(1, count1 + 1):
        if num > count2:
            diff.slides_removed.append(num)

    # Compare common slides
    common_count = min(count1, count2)
    for num in range(1, common_count + 1):
        slide1 = slides1_by_num.get(num, {})
        slide2 = slides2_by_num.get(num, {})

        changes = _compare_slides(slide1, slide2)
        if changes:
            diff.slides_modified.append(
                SlideDiff(
                    slide_number=num,
                    changes=changes,
                )
            )

    # Generate summary
    parts = []
    if diff.slides_added:
        parts.append(f"{len(diff.slides_added)} slide(s) added")
    if diff.slides_removed:
        parts.append(f"{len(diff.slides_removed)} slide(s) removed")
    if diff.slides_modified:
        parts.append(f"{len(diff.slides_modified)} slide(s) modified")

    diff.summary = ", ".join(parts) if parts else "No changes"

    if format == "text":
        return diff.to_text()
    elif format == "dict":
        return diff.to_dict()
    else:
        return diff


def _compare_slides(slide1: dict, slide2: dict) -> list[str]:
    """Compare two slide descriptions and return list of changes."""
    changes = []

    # Compare title
    title1 = slide1.get("title", "")
    title2 = slide2.get("title", "")
    if title1 != title2:
        changes.append(f"title changed: '{title1}' -> '{title2}'")

    # Compare layout
    layout1 = slide1.get("layout", "")
    layout2 = slide2.get("layout", "")
    if layout1 != layout2:
        changes.append(f"layout changed: '{layout1}' -> '{layout2}'")

    # Compare content
    content1 = slide1.get("content", [])
    content2 = slide2.get("content", [])
    if content1 != content2:
        added = len(content2) - len(content1)
        if added > 0:
            changes.append(f"content: {added} item(s) added")
        elif added < 0:
            changes.append(f"content: {-added} item(s) removed")
        else:
            changes.append("content: items modified")

    # Compare notes
    notes1 = slide1.get("notes", "")
    notes2 = slide2.get("notes", "")
    if notes1 != notes2:
        if notes1 and not notes2:
            changes.append("notes removed")
        elif not notes1 and notes2:
            changes.append("notes added")
        else:
            changes.append("notes modified")

    # Compare structural elements
    if slide1.get("has_table") != slide2.get("has_table"):
        if slide2.get("has_table"):
            changes.append("table added")
        else:
            changes.append("table removed")

    if slide1.get("has_chart") != slide2.get("has_chart"):
        if slide2.get("has_chart"):
            changes.append("chart added")
        else:
            changes.append("chart removed")

    if slide1.get("has_image") != slide2.get("has_image"):
        if slide2.get("has_image"):
            changes.append("image added")
        else:
            changes.append("image removed")

    return changes
