"""Content analysis for intelligent slide creation.

Analyzes content to detect type (comparison, quote, stats, etc.)
and recommend the best slide type and layout.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ContentType(str, Enum):
    """Detected content types."""

    BULLETS = "bullets"  # Simple list of points
    COMPARISON = "comparison"  # Two things being compared
    QUOTE = "quote"  # A quotation with attribution
    STATISTICS = "statistics"  # Numbers/metrics with labels
    TIMELINE = "timeline"  # Sequence of events/dates
    TABLE_DATA = "table_data"  # Key-value or tabular data
    TWO_COLUMN = "two_column"  # Content that splits naturally into two
    SINGLE_POINT = "single_point"  # One main idea
    PROCESS = "process"  # Step-by-step instructions
    UNKNOWN = "unknown"


@dataclass
class ContentAnalysis:
    """Result of content analysis."""

    content_type: ContentType
    confidence: float  # 0.0 to 1.0
    recommended_slide_type: str
    recommended_layout_type: str
    suggestions: list[str] = field(default_factory=list)
    extracted_data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON/AI consumption."""
        return {
            "content_type": self.content_type.value,
            "confidence": self.confidence,
            "recommended_slide_type": self.recommended_slide_type,
            "recommended_layout_type": self.recommended_layout_type,
            "suggestions": self.suggestions,
            "extracted_data": self.extracted_data,
        }


# Patterns for detection
COMPARISON_PATTERNS = [
    r"\bvs\.?\s",
    r"\bversus\b",
    r"\bcompared\s+to\b",
    r"\bbefore\b.*\bafter\b",
    r"\bpros?\b.*\bcons?\b",
    r"\badvantages?\b.*\bdisadvantages?\b",
    r"\bold\b.*\bnew\b",
    r"\bcurrent\b.*\bfuture\b",
    r"\bwith\b.*\bwithout\b",
    r"\boption\s*[ab12]\b.*\boption\s*[ab12]\b",
]

QUOTE_PATTERNS = [
    r'^["\u201c].{20,}["\u201d]',  # Starts with quote, substantial content
    r"^\u2014\s*[\w\s]+",  # Starts with em-dash attribution
    r'["\u201d]\s*\u2014\s*[\w\s,]+$',  # Ends with quote + attribution
    r"^—\s*[\w\s]+",  # ASCII em-dash
]

STATISTIC_PATTERNS = [
    r"\b\d+%",  # Percentages
    r"\$[\d,]+(?:\.\d+)?[BMKTbmkt]?\b",  # Dollar amounts
    r"\b\d+[xX]\b",  # Multipliers like 10x
    r"\b\d+(?:\.\d+)?[BMKTbmkt]\b",  # Numbers with B/M/K/T suffix
    r"\b\d{1,3}(?:,\d{3})+\b",  # Large numbers with commas
    r"\b\d+(?:\.\d+)?\s*(?:percent|million|billion|trillion)\b",
]

TIMELINE_PATTERNS = [
    r"\b(?:19|20)\d{2}\b",  # Years
    r"\b[Qq][1-4]\s*['']?\d{2,4}\b",  # Quarters
    r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d",
    r"\bstep\s*\d+\b",  # Steps
    r"\bphase\s*\d+\b",  # Phases
    r"\bstage\s*\d+\b",  # Stages
    r"\b(?:first|then|next|finally|after|before)\b",
]

PROCESS_PATTERNS = [
    r"^\s*\d+[\.\)]\s",  # Numbered steps
    r"^\s*step\s*\d",  # "Step 1"
    r"\bhow\s+to\b",
    r"\bprocess\b",
    r"\bworkflow\b",
    r"\bprocedure\b",
]

TABLE_PATTERNS = [
    r"^[\w\s]+:\s+.+$",  # "Key: Value"
    r"^[\w\s]+\s+[-–—]\s+.+$",  # "Key - Value"
    r"^[\w\s]+\s*\|\s*.+$",  # "Key | Value"
]


def analyze_content(
    content: str | list[str] | list[dict] | list[list],
    title: str = "",
) -> ContentAnalysis:
    """Analyze content to determine the best slide type.

    Args:
        content: The content to analyze (string, list of strings, or rich text)
        title: Optional title for additional context

    Returns:
        ContentAnalysis with recommendations

    Example:
        >>> analysis = analyze_content(["Before: slow", "After: fast"], "Migration")
        >>> analysis.content_type
        ContentType.COMPARISON
    """
    # Normalize content to string and list for analysis
    text, items = _normalize_content(content)
    full_text = f"{title} {text}".lower()
    item_count = len(items)

    # Score each content type
    scores: dict[ContentType, float] = {}

    # Comparison detection
    comparison_matches = sum(
        1 for p in COMPARISON_PATTERNS if re.search(p, full_text, re.IGNORECASE)
    )
    scores[ContentType.COMPARISON] = comparison_matches * 2.5

    # Quote detection
    quote_matches = sum(
        1
        for p in QUOTE_PATTERNS
        if re.search(p, text.strip(), re.IGNORECASE | re.MULTILINE)
    )
    if item_count <= 2 and len(text) > 50:
        scores[ContentType.QUOTE] = quote_matches * 3
    else:
        scores[ContentType.QUOTE] = 0

    # Statistics detection
    stat_matches = []
    for p in STATISTIC_PATTERNS:
        stat_matches.extend(re.findall(p, text, re.IGNORECASE))
    if len(stat_matches) >= 2:
        scores[ContentType.STATISTICS] = len(stat_matches) * 1.5
    else:
        scores[ContentType.STATISTICS] = 0

    # Timeline detection
    timeline_matches = sum(
        1 for p in TIMELINE_PATTERNS if re.search(p, full_text, re.IGNORECASE)
    )
    scores[ContentType.TIMELINE] = timeline_matches * 1.5

    # Process/steps detection
    process_matches = sum(
        1
        for p in PROCESS_PATTERNS
        if re.search(p, full_text, re.IGNORECASE | re.MULTILINE)
    )
    scores[ContentType.PROCESS] = process_matches * 2

    # Table data detection
    table_matches = 0
    for item in items:
        item_str = item if isinstance(item, str) else str(item)
        for p in TABLE_PATTERNS:
            if re.match(p, item_str.strip(), re.IGNORECASE):
                table_matches += 1
                break
    if table_matches >= 2:
        scores[ContentType.TABLE_DATA] = table_matches * 2
    else:
        scores[ContentType.TABLE_DATA] = 0

    # Find best type
    best_type = ContentType.BULLETS
    best_score = 0.0
    for content_type, score in scores.items():
        if score > best_score:
            best_score = score
            best_type = content_type

    # Special cases
    if item_count == 1 and len(text) < 100 and best_score < 2:
        best_type = ContentType.SINGLE_POINT
        best_score = 2.0
    elif item_count == 2 and best_score < 2:
        best_type = ContentType.TWO_COLUMN
        best_score = 1.5

    # Calculate confidence
    confidence = min(best_score / 5.0, 1.0) if best_score > 0 else 0.3

    # Map to slide type and layout
    type_mapping = {
        ContentType.BULLETS: ("content", "content"),
        ContentType.COMPARISON: ("comparison", "comparison"),
        ContentType.QUOTE: ("quote", "content"),
        ContentType.STATISTICS: ("stats", "title_only"),
        ContentType.TIMELINE: ("timeline", "content"),
        ContentType.TABLE_DATA: ("table", "title_only"),
        ContentType.TWO_COLUMN: ("two_column", "two_column"),
        ContentType.SINGLE_POINT: ("content", "content"),
        ContentType.PROCESS: ("content", "content"),
        ContentType.UNKNOWN: ("content", "content"),
    }

    slide_type, layout_type = type_mapping.get(best_type, ("content", "content"))

    # Generate suggestions
    suggestions = _generate_suggestions(
        item_count, stat_matches, comparison_matches, best_type
    )

    return ContentAnalysis(
        content_type=best_type,
        confidence=confidence,
        recommended_slide_type=slide_type,
        recommended_layout_type=layout_type,
        suggestions=suggestions,
        extracted_data={
            "item_count": item_count,
            "statistics_found": stat_matches[:5] if stat_matches else [],
            "scores": {k.value: v for k, v in scores.items() if v > 0},
        },
    )


def _normalize_content(
    content: str | list[str] | list[dict] | list[list],
) -> tuple[str, list[str]]:
    """Normalize content to (full_text, item_list)."""
    if isinstance(content, str):
        items = [line.strip() for line in content.split("\n") if line.strip()]
        return content, items

    text_parts = []
    items = []

    for item in content:
        if isinstance(item, str):
            text_parts.append(item)
            items.append(item)
        elif isinstance(item, dict):
            t = item.get("text", "")
            text_parts.append(t)
            items.append(t)
        elif isinstance(item, list):
            combined = ""
            for seg in item:
                if isinstance(seg, dict):
                    combined += seg.get("text", "")
                elif isinstance(seg, str):
                    combined += seg
            text_parts.append(combined)
            items.append(combined)

    return " ".join(text_parts), items


def _generate_suggestions(
    item_count: int,
    stat_matches: list[str],
    comparison_matches: int,
    best_type: ContentType,
) -> list[str]:
    """Generate improvement suggestions based on analysis."""
    suggestions = []

    if item_count > 7:
        suggestions.append(
            f"Content has {item_count} items — consider splitting across slides"
        )
    elif item_count > 5:
        suggestions.append(
            f"Content has {item_count} items — consider trimming to 5-6 key points"
        )

    if len(stat_matches) >= 3 and best_type != ContentType.STATISTICS:
        suggestions.append(
            "Multiple statistics detected — consider a dedicated stats slide"
        )

    if comparison_matches > 0 and best_type != ContentType.COMPARISON:
        suggestions.append(
            "Comparison language detected — consider a comparison layout"
        )

    return suggestions


def detect_comparison_parts(
    content: list[str],
    title: str = "",
) -> dict[str, Any] | None:
    """Try to split content into left/right comparison parts.

    Args:
        content: List of content strings
        title: Slide title for context

    Returns:
        Dict with left_heading, left_content, right_heading, right_content
        or None if not a clear comparison
    """
    if not content:
        return None

    title_lower = title.lower()
    content_lower = [c.lower() if isinstance(c, str) else "" for c in content]
    full_text = " ".join(content_lower)

    # Look for explicit markers in content
    markers = {
        "before": ("before", "after"),
        "after": ("before", "after"),
        "pro": ("pros", "cons"),
        "con": ("pros", "cons"),
        "advantage": ("advantages", "disadvantages"),
        "disadvantage": ("advantages", "disadvantages"),
        "old": ("old", "new"),
        "new": ("old", "new"),
        "current": ("current", "future"),
        "future": ("current", "future"),
    }

    # Find marker indices
    left_idx = right_idx = -1
    left_label = right_label = ""

    for i, item in enumerate(content_lower):
        for marker, (left_name, right_name) in markers.items():
            if marker in item and left_name.lower() in item:
                left_idx = i
                left_label = left_name.title()
            elif marker in item and right_name.lower() in item:
                right_idx = i
                right_label = right_name.title()

    if left_idx >= 0 and right_idx > left_idx:
        return {
            "left_heading": content[left_idx]
            if isinstance(content[left_idx], str)
            else left_label,
            "left_content": content[left_idx + 1 : right_idx],
            "right_heading": content[right_idx]
            if isinstance(content[right_idx], str)
            else right_label,
            "right_content": content[right_idx + 1 :],
        }

    # Check title for vs/versus pattern
    if re.search(r"\bvs\.?\b|\bversus\b", title_lower):
        # Split title to get headings
        parts = re.split(r"\s+vs\.?\s+|\s+versus\s+", title, flags=re.IGNORECASE)
        if len(parts) == 2:
            mid = len(content) // 2
            return {
                "left_heading": parts[0].strip(),
                "left_content": content[:mid],
                "right_heading": parts[1].strip(),
                "right_content": content[mid:],
            }

    # Simple split if content divides evenly
    if len(content) >= 4 and len(content) % 2 == 0:
        mid = len(content) // 2
        # Check if there's a natural break (empty string or heading-like item)
        for i in range(mid - 1, mid + 2):
            if 0 <= i < len(content):
                item = content[i]
                if isinstance(item, str) and (not item.strip() or len(item) < 20):
                    return {
                        "left_heading": "Option A",
                        "left_content": content[:i],
                        "right_heading": "Option B",
                        "right_content": content[i + 1 :]
                        if not item.strip()
                        else content[i:],
                    }

    return None


def suggest_slide_type(
    title: str,
    content: str | list | None = None,
    has_image: bool = False,
    has_data: bool = False,
) -> dict[str, Any]:
    """Suggest the best slide type based on inputs.

    Args:
        title: Slide title
        content: Optional content
        has_image: Whether an image will be included
        has_data: Whether tabular data will be included

    Returns:
        Dict with recommended slide_type, layout, and reasoning
    """
    title_lower = title.lower()

    # Quick pattern matching on title
    if any(w in title_lower for w in ["agenda", "outline", "overview", "contents"]):
        return {
            "slide_type": "agenda",
            "layout": "content",
            "reason": "Title suggests an agenda or outline",
        }

    if any(w in title_lower for w in ["quote", "said", "testimonial"]):
        return {
            "slide_type": "quote",
            "layout": "content",
            "reason": "Title suggests a quotation",
        }

    if any(
        w in title_lower for w in ["vs", "versus", "comparison", "compare", "vs."]
    ):
        return {
            "slide_type": "comparison",
            "layout": "comparison",
            "reason": "Title suggests a comparison",
        }

    if any(
        w in title_lower
        for w in ["timeline", "history", "roadmap", "milestones", "journey"]
    ):
        return {
            "slide_type": "timeline",
            "layout": "content",
            "reason": "Title suggests a timeline",
        }

    if any(
        w in title_lower
        for w in ["steps", "process", "how to", "workflow", "procedure"]
    ):
        return {
            "slide_type": "content",
            "layout": "content",
            "reason": "Title suggests a process or steps",
        }

    if any(
        w in title_lower
        for w in ["metrics", "results", "numbers", "stats", "by the numbers", "kpi"]
    ):
        return {
            "slide_type": "stats",
            "layout": "title_only",
            "reason": "Title suggests statistics or metrics",
        }

    if has_image:
        return {
            "slide_type": "image",
            "layout": "image_content",
            "reason": "Image content specified",
        }

    if has_data:
        return {
            "slide_type": "table",
            "layout": "title_only",
            "reason": "Tabular data specified",
        }

    # Analyze content if provided
    if content:
        analysis = analyze_content(content, title)
        return {
            "slide_type": analysis.recommended_slide_type,
            "layout": analysis.recommended_layout_type,
            "reason": f"Content analysis detected {analysis.content_type.value}",
            "confidence": analysis.confidence,
        }

    return {
        "slide_type": "content",
        "layout": "content",
        "reason": "Default content slide",
    }
