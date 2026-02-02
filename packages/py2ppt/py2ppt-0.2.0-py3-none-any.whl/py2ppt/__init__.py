"""py2ppt: AI-Friendly PowerPoint Wrapper.

A high-level, AI-native wrapper for creating PowerPoint presentations
from corporate templates with semantic, intent-based APIs.

Features:
- Template analysis with AI-readable descriptions
- Semantic placeholder mapping (title, content, left, right)
- Layout recommendations based on content type
- Automatic bullet formatting
- High-level slide creation methods

Quick Start:
    >>> from py2ppt import Template
    >>>
    >>> # Load and analyze a template
    >>> template = Template("corporate.pptx")
    >>>
    >>> # See what layouts are available
    >>> for layout in template.describe():
    ...     print(f"{layout['name']}: {layout['description']}")
    ...     print(f"  Best for: {', '.join(layout['best_for'])}")
    >>>
    >>> # Create a presentation
    >>> pres = template.create_presentation()
    >>>
    >>> pres.add_title_slide("Q4 Business Review", "January 2025")
    >>> pres.add_content_slide("Key Highlights", [
    ...     "Revenue exceeded targets by 15%",
    ...     "Customer satisfaction at all-time high",
    ...     "Three new product launches completed"
    ... ])
    >>> pres.add_comparison_slide(
    ...     "Before vs After",
    ...     "Legacy System", ["Slow", "Manual", "Error-prone"],
    ...     "New Platform", ["Fast", "Automated", "Reliable"]
    ... )
    >>>
    >>> pres.save("output.pptx")

For AI Agents:
    The template.describe() method returns structured data that can
    be included in system prompts:

    >>> layouts = template.describe()
    >>> # Returns list of dicts with:
    >>> # - name: Layout name
    >>> # - type: Classified type (title_slide, content, etc.)
    >>> # - description: Human-readable description
    >>> # - placeholders: Semantic placeholder names
    >>> # - best_for: Content types this layout suits

    >>> # Get layout recommendations
    >>> recs = template.recommend_layout("comparison")
    >>> # Returns sorted list of {name, index, confidence, reason}
"""

__version__ = "0.2.0"

from .template import Template
from .presentation import Presentation
from .layout import (
    LayoutType,
    LayoutDescription,
    LayoutRecommendation,
    analyze_layout,
    classify_layout,
    recommend_layout,
)
from .placeholders import (
    PlaceholderRole,
    SemanticPlaceholder,
    map_placeholders,
    get_placeholder_purpose,
)
from .formatting import (
    FormattedParagraph,
    FormattedRun,
    parse_content,
    auto_bullets,
)
from .errors import (
    Py2PptError,
    SlideNotFoundError,
    LayoutNotFoundError,
    ContentOverflowError,
    InvalidDataError,
)
from .analysis import (
    ContentType,
    ContentAnalysis,
    analyze_content,
    detect_comparison_parts,
    suggest_slide_type,
)
from .theme import ThemeHelper
from .validation import (
    IssueSeverity,
    IssueCategory,
    ValidationIssue,
    ValidationResult,
    validate_slide,
    validate_presentation,
)
from .builder import (
    SlideSpec,
    SectionSpec,
    PresentationSpec,
    build_presentation,
    build_from_outline,
)
from .shapes import ShapeType, ConnectorType
from .markdown import build_from_markdown
from .diff import diff_presentations, PresentationDiff
from .export import save_pdf, is_pdf_export_available, ExportError

__all__ = [
    # Version
    "__version__",
    # Main classes
    "Template",
    "Presentation",
    # Layout
    "LayoutType",
    "LayoutDescription",
    "LayoutRecommendation",
    "analyze_layout",
    "classify_layout",
    "recommend_layout",
    # Placeholders
    "PlaceholderRole",
    "SemanticPlaceholder",
    "map_placeholders",
    "get_placeholder_purpose",
    # Formatting
    "FormattedParagraph",
    "FormattedRun",
    "parse_content",
    "auto_bullets",
    # Errors
    "Py2PptError",
    "SlideNotFoundError",
    "LayoutNotFoundError",
    "ContentOverflowError",
    "InvalidDataError",
    # Analysis
    "ContentType",
    "ContentAnalysis",
    "analyze_content",
    "detect_comparison_parts",
    "suggest_slide_type",
    # Theme
    "ThemeHelper",
    # Validation
    "IssueSeverity",
    "IssueCategory",
    "ValidationIssue",
    "ValidationResult",
    "validate_slide",
    "validate_presentation",
    # Builder
    "SlideSpec",
    "SectionSpec",
    "PresentationSpec",
    "build_presentation",
    "build_from_outline",
    # Shapes
    "ShapeType",
    "ConnectorType",
    # Markdown
    "build_from_markdown",
    # Diff
    "diff_presentations",
    "PresentationDiff",
    # Export
    "save_pdf",
    "is_pdf_export_available",
    "ExportError",
]
