"""Placeholder semantic mapping.

Maps raw placeholder types and indices to human-readable semantic names
that AI agents can easily understand and use.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PlaceholderRole(str, Enum):
    """Semantic roles for placeholders."""

    TITLE = "title"
    SUBTITLE = "subtitle"
    CONTENT = "content"
    LEFT_CONTENT = "left"
    RIGHT_CONTENT = "right"
    TOP_CONTENT = "top"
    BOTTOM_CONTENT = "bottom"
    LEFT_HEADING = "left_heading"
    RIGHT_HEADING = "right_heading"
    IMAGE = "image"
    CHART = "chart"
    TABLE = "table"
    FOOTER = "footer"
    DATE = "date"
    SLIDE_NUMBER = "slide_number"
    UNKNOWN = "unknown"


@dataclass
class SemanticPlaceholder:
    """A placeholder with semantic meaning."""

    role: PlaceholderRole
    type: str  # Original placeholder type (title, body, etc.)
    idx: int | None  # Original placeholder index
    name: str  # Shape name
    x: int  # Position x in EMUs
    y: int  # Position y in EMUs
    width: int  # Width in EMUs
    height: int  # Height in EMUs

    @property
    def position_description(self) -> str:
        """Get human-readable position description."""
        # Convert EMUs to approximate position
        # Assuming standard slide: 9144000 x 6858000 EMUs (10x7.5 inches)
        slide_width = 9144000
        slide_height = 6858000

        center_x = self.x + self.width // 2
        center_y = self.y + self.height // 2

        # Determine horizontal position
        if center_x < slide_width * 0.33:
            h_pos = "left"
        elif center_x > slide_width * 0.67:
            h_pos = "right"
        else:
            h_pos = "center"

        # Determine vertical position
        if center_y < slide_height * 0.33:
            v_pos = "top"
        elif center_y > slide_height * 0.67:
            v_pos = "bottom"
        else:
            v_pos = "middle"

        return f"{v_pos}-{h_pos}"


# Mapping from placeholder types to potential roles
TYPE_TO_ROLE = {
    "title": PlaceholderRole.TITLE,
    "ctrTitle": PlaceholderRole.TITLE,
    "subTitle": PlaceholderRole.SUBTITLE,
    "body": PlaceholderRole.CONTENT,
    "obj": PlaceholderRole.CONTENT,
    "chart": PlaceholderRole.CHART,
    "tbl": PlaceholderRole.TABLE,
    "pic": PlaceholderRole.IMAGE,
    "clipArt": PlaceholderRole.IMAGE,
    "media": PlaceholderRole.IMAGE,
    "ftr": PlaceholderRole.FOOTER,
    "dt": PlaceholderRole.DATE,
    "sldNum": PlaceholderRole.SLIDE_NUMBER,
}


def map_placeholder_role(
    ph_type: str,
    ph_idx: int | None,
    x: int,
    y: int,
    width: int,
    height: int,
    all_placeholders: list[dict],
) -> PlaceholderRole:
    """Determine the semantic role of a placeholder.

    Args:
        ph_type: The placeholder type (title, body, etc.)
        ph_idx: The placeholder index
        x, y, width, height: Position and size in EMUs
        all_placeholders: List of all placeholders for context

    Returns:
        The semantic role for this placeholder
    """
    # First check direct type mapping
    if ph_type in TYPE_TO_ROLE:
        base_role = TYPE_TO_ROLE[ph_type]
    else:
        base_role = PlaceholderRole.UNKNOWN

    # For body placeholders, determine left/right/top/bottom based on position
    if base_role == PlaceholderRole.CONTENT:
        # Count how many body placeholders there are
        body_phs = [p for p in all_placeholders if p.get("type") in ("body", "obj")]

        if len(body_phs) == 1:
            return PlaceholderRole.CONTENT
        elif len(body_phs) == 2:
            # Two content areas - determine left/right or top/bottom
            other = [p for p in body_phs if p.get("idx") != ph_idx][0] if body_phs else None

            if other:
                other_x = other.get("x", 0)
                other_y = other.get("y", 0)

                # Check horizontal vs vertical arrangement
                x_diff = abs(x - other_x)
                y_diff = abs(y - other_y)

                if x_diff > y_diff:
                    # Side by side
                    return PlaceholderRole.LEFT_CONTENT if x < other_x else PlaceholderRole.RIGHT_CONTENT
                else:
                    # Stacked
                    return PlaceholderRole.TOP_CONTENT if y < other_y else PlaceholderRole.BOTTOM_CONTENT
        elif len(body_phs) >= 4:
            # Comparison layout: 2 headings + 2 content areas
            # Sort by y position to find headings (top) vs content (bottom)
            sorted_by_y = sorted(body_phs, key=lambda p: p.get("y", 0))
            top_row = sorted_by_y[:2]
            bottom_row = sorted_by_y[2:4]

            this_ph = {"idx": ph_idx, "x": x, "y": y}

            if any(p.get("idx") == ph_idx for p in top_row):
                # This is a heading
                sorted_top = sorted(top_row, key=lambda p: p.get("x", 0))
                return (PlaceholderRole.LEFT_HEADING
                        if x <= sorted_top[0].get("x", 0) + 100000
                        else PlaceholderRole.RIGHT_HEADING)
            else:
                # This is content
                sorted_bottom = sorted(bottom_row, key=lambda p: p.get("x", 0))
                return (PlaceholderRole.LEFT_CONTENT
                        if x <= sorted_bottom[0].get("x", 0) + 100000
                        else PlaceholderRole.RIGHT_CONTENT)

    return base_role


def map_placeholders(placeholders: list[dict]) -> dict[str, SemanticPlaceholder]:
    """Map a list of raw placeholders to semantic placeholders.

    Args:
        placeholders: List of placeholder dicts with type, idx, name, x, y, cx, cy

    Returns:
        Dict mapping semantic name to SemanticPlaceholder
    """
    result = {}

    # Build context for position-based mapping
    all_ph_info = [
        {
            "type": p.get("type"),
            "idx": p.get("idx"),
            "x": p.get("x", 0),
            "y": p.get("y", 0),
        }
        for p in placeholders
    ]

    for ph in placeholders:
        ph_type = ph.get("type", "unknown")
        ph_idx = ph.get("idx")
        name = ph.get("name", "")
        x = ph.get("x", 0)
        y = ph.get("y", 0)
        width = ph.get("cx", 0)
        height = ph.get("cy", 0)

        role = map_placeholder_role(ph_type, ph_idx, x, y, width, height, all_ph_info)

        semantic = SemanticPlaceholder(
            role=role,
            type=ph_type,
            idx=ph_idx,
            name=name,
            x=x,
            y=y,
            width=width,
            height=height,
        )

        # Use role value as key, but handle duplicates
        key = role.value
        if key in result:
            # Add index suffix for duplicates
            suffix = 2
            while f"{key}_{suffix}" in result:
                suffix += 1
            key = f"{key}_{suffix}"

        result[key] = semantic

    return result


def get_placeholder_purpose(role: PlaceholderRole) -> str:
    """Get a human-readable description of a placeholder's purpose.

    Args:
        role: The placeholder role

    Returns:
        Description of what content goes in this placeholder
    """
    purposes = {
        PlaceholderRole.TITLE: "Main slide title or heading",
        PlaceholderRole.SUBTITLE: "Subtitle, presenter name, or tagline",
        PlaceholderRole.CONTENT: "Main content area for bullets, text, or objects",
        PlaceholderRole.LEFT_CONTENT: "Content for the left side of the slide",
        PlaceholderRole.RIGHT_CONTENT: "Content for the right side of the slide",
        PlaceholderRole.TOP_CONTENT: "Content for the top section",
        PlaceholderRole.BOTTOM_CONTENT: "Content for the bottom section",
        PlaceholderRole.LEFT_HEADING: "Heading for left column in comparison layout",
        PlaceholderRole.RIGHT_HEADING: "Heading for right column in comparison layout",
        PlaceholderRole.IMAGE: "Picture or image placeholder",
        PlaceholderRole.CHART: "Chart or graph placeholder",
        PlaceholderRole.TABLE: "Table placeholder",
        PlaceholderRole.FOOTER: "Footer text area",
        PlaceholderRole.DATE: "Date display area",
        PlaceholderRole.SLIDE_NUMBER: "Slide number display",
        PlaceholderRole.UNKNOWN: "Unknown placeholder type",
    }
    return purposes.get(role, "Unknown")
