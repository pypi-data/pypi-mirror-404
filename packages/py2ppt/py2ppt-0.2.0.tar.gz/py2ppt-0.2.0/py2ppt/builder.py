"""High-level presentation builder.

Build complete presentations from structured outlines,
with automatic section dividers and intelligent slide type selection.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from .analysis import analyze_content, detect_comparison_parts

if TYPE_CHECKING:
    from .presentation import Presentation
    from .template import Template


@dataclass
class SlideSpec:
    """Specification for a single slide.

    Attributes:
        title: Slide title
        content: Content items (strings, dicts, or rich text)
        slide_type: Explicit slide type or None for auto-detect
        layout: Layout name/index or None for auto
        notes: Speaker notes
        extra: Additional parameters for specific slide types
    """

    title: str
    content: list[str | dict | list] | None = None
    slide_type: str | None = None
    layout: str | int | None = None
    notes: str = ""
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class SectionSpec:
    """Specification for a presentation section.

    Attributes:
        title: Section title (shown on divider slide)
        slides: List of slides in this section
        include_divider: Whether to add a section divider slide
    """

    title: str
    slides: list[SlideSpec | dict] = field(default_factory=list)
    include_divider: bool = True


@dataclass
class PresentationSpec:
    """Specification for a complete presentation.

    Example:
        >>> spec = PresentationSpec(
        ...     title="My Talk",
        ...     subtitle="A great presentation",
        ...     sections=[
        ...         SectionSpec(
        ...             title="Introduction",
        ...             slides=[
        ...                 SlideSpec(title="Overview", content=["Point 1", "Point 2"]),
        ...             ],
        ...         ),
        ...     ],
        ...     closing_title="Thank You",
        ... )
    """

    title: str
    subtitle: str = ""
    sections: list[SectionSpec | dict] = field(default_factory=list)
    closing_title: str = ""
    closing_content: list[str] | None = None
    title_layout: str | int | None = None
    section_layout: str | int | None = None
    closing_layout: str | int | None = None


def build_presentation(
    template: "Template",
    spec: PresentationSpec | dict,
) -> "Presentation":
    """Build a complete presentation from a specification.

    Automatically:
    - Creates title slide
    - Adds section dividers
    - Auto-detects slide types from content
    - Adds closing slide

    Args:
        template: The Template to use
        spec: Presentation specification (PresentationSpec or dict)

    Returns:
        Complete Presentation object

    Example:
        >>> spec = {
        ...     "title": "Q4 Review",
        ...     "subtitle": "January 2025",
        ...     "sections": [
        ...         {
        ...             "title": "Results",
        ...             "slides": [
        ...                 {"title": "Revenue", "content": ["Up 20%", "Beat forecast"]},
        ...                 {"title": "By Region", "slide_type": "table",
        ...                  "extra": {"headers": ["Region", "Revenue"],
        ...                            "rows": [["North", "$10M"], ["South", "$8M"]]}},
        ...             ],
        ...         },
        ...     ],
        ...     "closing_title": "Questions?",
        ... }
        >>> pres = build_presentation(template, spec)
        >>> pres.save("q4_review.pptx")
    """
    # Normalize spec
    if isinstance(spec, dict):
        spec = _dict_to_presentation_spec(spec)

    pres = template.create_presentation()

    # Add title slide
    pres.add_title_slide(
        spec.title,
        spec.subtitle,
        layout=spec.title_layout,
    )

    # Add sections
    for section in spec.sections:
        if isinstance(section, dict):
            section = _dict_to_section_spec(section)

        # Add section divider
        if section.include_divider and section.title:
            pres.add_section_slide(
                section.title,
                layout=spec.section_layout,
            )

        # Add slides
        for slide in section.slides:
            if isinstance(slide, dict):
                slide = _dict_to_slide_spec(slide)

            _add_slide_from_spec(pres, slide)

    # Add closing slide
    if spec.closing_title:
        if spec.closing_content:
            pres.add_content_slide(
                spec.closing_title,
                spec.closing_content,
                layout=spec.closing_layout,
            )
        else:
            pres.add_title_slide(
                spec.closing_title,
                "",
                layout=spec.closing_layout or spec.title_layout,
            )

    return pres


def build_from_outline(
    template: "Template",
    title: str,
    outline: list[dict | str],
    *,
    subtitle: str = "",
    closing: str = "Thank You",
    auto_sections: bool = True,
) -> "Presentation":
    """Build a presentation from a simple outline.

    A more flexible alternative to build_presentation() that
    accepts a flat list of slides and optionally groups them
    into sections automatically.

    Args:
        template: The Template to use
        title: Presentation title
        outline: List of slide dicts or simple strings
        subtitle: Presentation subtitle
        closing: Closing slide title (empty to skip)
        auto_sections: If True, create sections from slides with "section": True

    Returns:
        Complete Presentation object

    Example:
        >>> outline = [
        ...     {"title": "Introduction", "section": True},
        ...     {"title": "Background", "content": ["Point 1", "Point 2"]},
        ...     {"title": "Details", "section": True},
        ...     {"title": "Deep Dive", "content": ["Detail A", "Detail B"]},
        ... ]
        >>> pres = build_from_outline(template, "My Talk", outline)
    """
    pres = template.create_presentation()

    # Title slide
    pres.add_title_slide(title, subtitle)

    # Process outline
    for item in outline:
        if isinstance(item, str):
            # Simple string → content slide with just title
            pres.add_content_slide(item, [])
        elif isinstance(item, dict):
            # Check if it's a section marker
            if auto_sections and item.get("section"):
                pres.add_section_slide(item.get("title", ""))
            else:
                slide_spec = _dict_to_slide_spec(item)
                _add_slide_from_spec(pres, slide_spec)

    # Closing
    if closing:
        pres.add_title_slide(closing, "")

    return pres


def _dict_to_presentation_spec(d: dict) -> PresentationSpec:
    """Convert a dict to PresentationSpec."""
    sections = []
    for s in d.get("sections", []):
        if isinstance(s, dict):
            sections.append(_dict_to_section_spec(s))
        else:
            sections.append(s)

    return PresentationSpec(
        title=d.get("title", "Untitled"),
        subtitle=d.get("subtitle", ""),
        sections=sections,
        closing_title=d.get("closing_title", d.get("closing", "")),
        closing_content=d.get("closing_content"),
        title_layout=d.get("title_layout"),
        section_layout=d.get("section_layout"),
        closing_layout=d.get("closing_layout"),
    )


def _dict_to_section_spec(d: dict) -> SectionSpec:
    """Convert a dict to SectionSpec."""
    slides = []
    for s in d.get("slides", []):
        if isinstance(s, dict):
            slides.append(_dict_to_slide_spec(s))
        else:
            slides.append(s)

    return SectionSpec(
        title=d.get("title", ""),
        slides=slides,
        include_divider=d.get("include_divider", True),
    )


def _dict_to_slide_spec(d: dict) -> SlideSpec:
    """Convert a dict to SlideSpec."""
    return SlideSpec(
        title=d.get("title", ""),
        content=d.get("content"),
        slide_type=d.get("slide_type") or d.get("type"),
        layout=d.get("layout"),
        notes=d.get("notes", ""),
        extra={k: v for k, v in d.items()
               if k not in ("title", "content", "slide_type", "type", "layout", "notes", "section")},
    )


def _add_slide_from_spec(pres: "Presentation", slide: SlideSpec) -> int:
    """Add a slide to the presentation based on spec."""
    slide_type = slide.slide_type

    # Auto-detect slide type from content if not specified
    if slide_type is None and slide.content:
        analysis = analyze_content(slide.content, slide.title)
        if analysis.confidence >= 0.5:
            slide_type = analysis.recommended_slide_type

    slide_type = slide_type or "content"

    # Dispatch to appropriate method
    slide_num = _dispatch_slide(pres, slide_type, slide)

    # Add notes if provided
    if slide.notes:
        pres.set_notes(slide_num, slide.notes)

    return slide_num


def _dispatch_slide(pres: "Presentation", slide_type: str, slide: SlideSpec) -> int:
    """Dispatch to the appropriate slide creation method."""

    if slide_type == "comparison":
        return _add_comparison_slide(pres, slide)

    elif slide_type == "table":
        return pres.add_table_slide(
            slide.title,
            slide.extra.get("headers", []),
            slide.extra.get("rows", []),
            col_widths=slide.extra.get("col_widths"),
            style=slide.extra.get("style", "theme"),
            layout=slide.layout,
        )

    elif slide_type == "chart":
        return pres.add_chart_slide(
            slide.title,
            slide.extra.get("chart_type", "column"),
            slide.extra.get("data", {}),
            layout=slide.layout,
        )

    elif slide_type == "quote":
        return pres.add_quote_slide(
            slide.content[0] if slide.content else slide.extra.get("quote", ""),
            slide.extra.get("attribution", ""),
            source=slide.extra.get("source"),
            layout=slide.layout,
        )

    elif slide_type == "stats":
        return pres.add_stats_slide(
            slide.title,
            slide.extra.get("stats", []),
            layout=slide.layout,
        )

    elif slide_type == "timeline":
        return pres.add_timeline_slide(
            slide.title,
            slide.extra.get("events", slide.content or []),
            layout=slide.layout,
        )

    elif slide_type == "agenda":
        return pres.add_agenda_slide(
            slide.title,
            slide.content or slide.extra.get("items", []),
            layout=slide.layout,
        )

    elif slide_type == "two_column":
        return _add_two_column_slide(pres, slide)

    elif slide_type == "image":
        return pres.add_image_slide(
            slide.title,
            slide.extra.get("image_path", ""),
            caption=slide.extra.get("caption", ""),
            layout=slide.layout,
        )

    elif slide_type == "blank":
        return pres.add_blank_slide(layout=slide.layout)

    elif slide_type == "section":
        return pres.add_section_slide(
            slide.title,
            slide.extra.get("subtitle", ""),
            layout=slide.layout,
        )

    elif slide_type == "title":
        return pres.add_title_slide(
            slide.title,
            slide.extra.get("subtitle", ""),
            layout=slide.layout,
        )

    else:
        # Default to content slide
        return pres.add_content_slide(
            slide.title,
            slide.content or [],
            levels=slide.extra.get("levels"),
            layout=slide.layout,
        )


def _add_comparison_slide(pres: "Presentation", slide: SlideSpec) -> int:
    """Add a comparison slide, auto-detecting parts if needed."""
    # Check if comparison parts are explicitly provided
    if "left_heading" in slide.extra:
        return pres.add_comparison_slide(
            slide.title,
            slide.extra.get("left_heading", "Option A"),
            slide.extra.get("left_content", []),
            slide.extra.get("right_heading", "Option B"),
            slide.extra.get("right_content", []),
            layout=slide.layout,
        )

    # Try to auto-detect comparison parts from content
    if slide.content:
        content_strs = [
            c if isinstance(c, str) else str(c) for c in slide.content
        ]
        parts = detect_comparison_parts(content_strs, slide.title)
        if parts:
            return pres.add_comparison_slide(
                slide.title,
                parts["left_heading"],
                parts["left_content"],
                parts["right_heading"],
                parts["right_content"],
                layout=slide.layout,
            )

    # Fall back to regular content
    return pres.add_content_slide(
        slide.title,
        slide.content or [],
        layout=slide.layout,
    )


def _add_two_column_slide(pres: "Presentation", slide: SlideSpec) -> int:
    """Add a two-column slide, splitting content if needed."""
    # Check if columns are explicitly provided
    if "left_content" in slide.extra:
        return pres.add_two_column_slide(
            slide.title,
            slide.extra.get("left_content", []),
            slide.extra.get("right_content", []),
            layout=slide.layout,
        )

    # Auto-split content
    if slide.content:
        mid = len(slide.content) // 2
        return pres.add_two_column_slide(
            slide.title,
            slide.content[:mid],
            slide.content[mid:],
            layout=slide.layout,
        )

    return pres.add_two_column_slide(
        slide.title,
        [],
        [],
        layout=slide.layout,
    )
