"""Layout analysis and classification.

Provides intelligent layout classification based on placeholder patterns
and recommendations for content types.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .placeholders import PlaceholderRole, map_placeholders


class LayoutType(str, Enum):
    """Types of slide layouts."""

    TITLE = "title_slide"
    SECTION = "section_header"
    CONTENT = "content"
    TWO_COLUMN = "two_column"
    COMPARISON = "comparison"
    IMAGE_CONTENT = "image_content"
    BLANK = "blank"
    TITLE_ONLY = "title_only"
    UNKNOWN = "unknown"


@dataclass
class LayoutDescription:
    """AI-friendly description of a slide layout."""

    name: str
    index: int
    layout_type: LayoutType
    description: str
    placeholders: dict[str, dict[str, Any]]
    best_for: list[str]
    placeholder_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON/AI consumption."""
        return {
            "name": self.name,
            "index": self.index,
            "type": self.layout_type.value,
            "description": self.description,
            "placeholders": self.placeholders,
            "best_for": self.best_for,
        }


# Layout descriptions based on type
LAYOUT_DESCRIPTIONS = {
    LayoutType.TITLE: "Opening slide with large centered title and subtitle",
    LayoutType.SECTION: "Section divider with prominent title",
    LayoutType.CONTENT: "Standard slide with title and bullet content area",
    LayoutType.TWO_COLUMN: "Slide with title and two side-by-side content areas",
    LayoutType.COMPARISON: "Comparison slide with headings and content for two items",
    LayoutType.IMAGE_CONTENT: "Slide with title, content area, and image placeholder",
    LayoutType.BLANK: "Empty slide for custom content",
    LayoutType.TITLE_ONLY: "Slide with only a title, large open space below",
    LayoutType.UNKNOWN: "Custom or unknown layout type",
}

# What each layout type is best used for
LAYOUT_BEST_FOR = {
    LayoutType.TITLE: ["opening", "cover_page", "title_page"],
    LayoutType.SECTION: ["section_divider", "chapter_header", "transition"],
    LayoutType.CONTENT: ["bullet_points", "main_content", "explanation"],
    LayoutType.TWO_COLUMN: ["pros_cons", "two_topics", "split_content"],
    LayoutType.COMPARISON: ["before_after", "comparison", "versus"],
    LayoutType.IMAGE_CONTENT: ["photo_slide", "diagram_explanation", "visual_content"],
    LayoutType.BLANK: ["custom_layout", "full_image", "diagram"],
    LayoutType.TITLE_ONLY: ["agenda", "section_intro", "statement"],
}


def classify_layout(
    name: str,
    placeholders: list[dict],
) -> LayoutType:
    """Classify a layout based on its name and placeholders.

    Args:
        name: Layout name
        placeholders: List of placeholder info dicts

    Returns:
        The classified layout type
    """
    name_lower = name.lower()

    # First try name-based classification
    if "title slide" in name_lower or "cover" in name_lower:
        return LayoutType.TITLE
    if "section" in name_lower:
        return LayoutType.SECTION
    if "blank" in name_lower:
        return LayoutType.BLANK
    if "comparison" in name_lower:
        return LayoutType.COMPARISON
    if "two content" in name_lower or "two column" in name_lower:
        return LayoutType.TWO_COLUMN
    if "picture" in name_lower or "image" in name_lower:
        return LayoutType.IMAGE_CONTENT
    if "title only" in name_lower:
        return LayoutType.TITLE_ONLY

    # Fall back to placeholder analysis
    return _classify_by_placeholders(placeholders)


def _classify_by_placeholders(placeholders: list[dict]) -> LayoutType:
    """Classify layout based on placeholder patterns."""
    types = [p.get("type", "") for p in placeholders]

    has_title = any(t in ("title", "ctrTitle") for t in types)
    has_subtitle = any(t == "subTitle" for t in types)
    body_count = sum(1 for t in types if t in ("body", "obj"))
    has_picture = any(t == "pic" for t in types)

    # Center title + subtitle = title slide
    if "ctrTitle" in types and has_subtitle:
        return LayoutType.TITLE

    # No placeholders = blank
    if len(placeholders) == 0:
        return LayoutType.BLANK

    # Title only
    if has_title and body_count == 0 and not has_picture:
        return LayoutType.TITLE_ONLY

    # Picture with content
    if has_picture and body_count >= 1:
        return LayoutType.IMAGE_CONTENT

    # Multiple body placeholders
    if body_count >= 4:
        return LayoutType.COMPARISON
    if body_count == 2:
        return LayoutType.TWO_COLUMN

    # Standard content slide
    if has_title and body_count == 1:
        return LayoutType.CONTENT

    return LayoutType.UNKNOWN


def analyze_layout(
    name: str,
    index: int,
    placeholders: list[dict],
) -> LayoutDescription:
    """Analyze a layout and produce an AI-friendly description.

    Args:
        name: Layout name
        index: Layout index in the presentation
        placeholders: List of placeholder dicts with type, idx, name, bounds

    Returns:
        LayoutDescription with semantic information
    """
    # Classify the layout
    layout_type = classify_layout(name, placeholders)

    # Map placeholders to semantic names
    semantic_phs = map_placeholders(placeholders)

    # Build placeholder descriptions
    ph_descriptions = {}
    for role_name, ph in semantic_phs.items():
        ph_descriptions[role_name] = {
            "type": ph.type,
            "purpose": _get_purpose_for_role(ph.role),
            "position": ph.position_description,
        }

    return LayoutDescription(
        name=name,
        index=index,
        layout_type=layout_type,
        description=LAYOUT_DESCRIPTIONS.get(layout_type, "Custom layout"),
        placeholders=ph_descriptions,
        best_for=LAYOUT_BEST_FOR.get(layout_type, ["general_content"]),
        placeholder_count=len(placeholders),
    )


def _get_purpose_for_role(role: PlaceholderRole) -> str:
    """Get a brief purpose description for a placeholder role."""
    purposes = {
        PlaceholderRole.TITLE: "Main title",
        PlaceholderRole.SUBTITLE: "Subtitle or tagline",
        PlaceholderRole.CONTENT: "Main content area",
        PlaceholderRole.LEFT_CONTENT: "Left content area",
        PlaceholderRole.RIGHT_CONTENT: "Right content area",
        PlaceholderRole.LEFT_HEADING: "Left column heading",
        PlaceholderRole.RIGHT_HEADING: "Right column heading",
        PlaceholderRole.IMAGE: "Image placeholder",
        PlaceholderRole.CHART: "Chart placeholder",
        PlaceholderRole.TABLE: "Table placeholder",
        PlaceholderRole.FOOTER: "Footer text",
        PlaceholderRole.DATE: "Date field",
        PlaceholderRole.SLIDE_NUMBER: "Slide number",
    }
    return purposes.get(role, "Content placeholder")


@dataclass
class LayoutRecommendation:
    """A recommendation for which layout to use."""

    layout_name: str
    layout_index: int
    confidence: float  # 0.0 to 1.0
    reason: str


def recommend_layout(
    layouts: list[LayoutDescription],
    content_type: str,
    has_image: bool = False,
    bullet_count: int = 0,
) -> list[LayoutRecommendation]:
    """Recommend layouts for a given content type.

    Args:
        layouts: Available layouts
        content_type: Type of content ("bullets", "comparison", "title", etc.)
        has_image: Whether content includes an image
        bullet_count: Number of bullet points (affects layout choice)

    Returns:
        List of recommendations sorted by confidence
    """
    recommendations = []

    content_lower = content_type.lower()

    for layout in layouts:
        confidence = 0.0
        reason = ""

        # Match by content type
        if content_lower in ("title", "opening", "cover"):
            if layout.layout_type == LayoutType.TITLE:
                confidence = 1.0
                reason = "Title slide layout matches opening content"
            elif layout.layout_type == LayoutType.SECTION:
                confidence = 0.6
                reason = "Section header can work for title content"

        elif content_lower in ("section", "divider", "transition"):
            if layout.layout_type == LayoutType.SECTION:
                confidence = 1.0
                reason = "Section header is ideal for dividers"
            elif layout.layout_type == LayoutType.TITLE:
                confidence = 0.5
                reason = "Title slide can work as section divider"

        elif content_lower in ("comparison", "versus", "vs", "before_after"):
            if layout.layout_type == LayoutType.COMPARISON:
                confidence = 1.0
                reason = "Comparison layout designed for this content"
            elif layout.layout_type == LayoutType.TWO_COLUMN:
                confidence = 0.8
                reason = "Two-column can show comparison content"

        elif content_lower in ("two_column", "split", "side_by_side"):
            if layout.layout_type == LayoutType.TWO_COLUMN:
                confidence = 1.0
                reason = "Two-column layout matches split content"
            elif layout.layout_type == LayoutType.COMPARISON:
                confidence = 0.7
                reason = "Comparison layout has two content areas"

        elif content_lower in ("bullets", "content", "points", "list"):
            if layout.layout_type == LayoutType.CONTENT:
                confidence = 0.9
                reason = "Standard content slide for bullet points"
            elif layout.layout_type == LayoutType.TWO_COLUMN and bullet_count > 6:
                confidence = 0.7
                reason = "Two columns better for many bullets"

        elif content_lower in ("image", "photo", "picture"):
            if layout.layout_type == LayoutType.IMAGE_CONTENT:
                confidence = 1.0
                reason = "Image layout has picture placeholder"
            elif layout.layout_type == LayoutType.BLANK:
                confidence = 0.6
                reason = "Blank slide allows full-size images"

        # Adjust for has_image flag
        if has_image:
            if layout.layout_type == LayoutType.IMAGE_CONTENT:
                confidence = min(confidence + 0.3, 1.0)
            elif layout.layout_type == LayoutType.BLANK:
                confidence = max(confidence, 0.5)

        if confidence > 0:
            recommendations.append(
                LayoutRecommendation(
                    layout_name=layout.name,
                    layout_index=layout.index,
                    confidence=confidence,
                    reason=reason,
                )
            )

    # Sort by confidence descending
    recommendations.sort(key=lambda r: r.confidence, reverse=True)
    return recommendations
