"""Presentation validation and design best practices.

Validates presentations against design rules and provides
actionable suggestions for improvement.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .presentation import Presentation


class IssueSeverity(str, Enum):
    """Severity levels for validation issues."""

    ERROR = "error"  # Will likely cause problems
    WARNING = "warning"  # Should be fixed
    INFO = "info"  # Suggestion for improvement


class IssueCategory(str, Enum):
    """Categories of validation issues."""

    CONTENT = "content"  # Too much/little text
    STRUCTURE = "structure"  # Missing elements
    DESIGN = "design"  # Visual/layout issues
    ACCESSIBILITY = "accessibility"  # Readability concerns


@dataclass
class ValidationIssue:
    """A single validation issue."""

    severity: IssueSeverity
    category: IssueCategory
    slide_number: int | None  # None for presentation-level issues
    message: str
    suggestion: str
    rule: str = ""  # Rule identifier for programmatic access
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON/AI consumption."""
        return {
            "severity": self.severity.value,
            "category": self.category.value,
            "slide_number": self.slide_number,
            "message": self.message,
            "suggestion": self.suggestion,
            "rule": self.rule,
            "details": self.details,
        }


@dataclass
class ValidationResult:
    """Result of validating a presentation or slide."""

    is_valid: bool  # No errors (warnings OK)
    issues: list[ValidationIssue] = field(default_factory=list)
    score: float = 100.0  # 0-100 quality score

    @property
    def errors(self) -> list[ValidationIssue]:
        """Get all error-level issues."""
        return [i for i in self.issues if i.severity == IssueSeverity.ERROR]

    @property
    def warnings(self) -> list[ValidationIssue]:
        """Get all warning-level issues."""
        return [i for i in self.issues if i.severity == IssueSeverity.WARNING]

    @property
    def info(self) -> list[ValidationIssue]:
        """Get all info-level issues."""
        return [i for i in self.issues if i.severity == IssueSeverity.INFO]

    def by_slide(self, n: int) -> list[ValidationIssue]:
        """Get issues for a specific slide."""
        return [i for i in self.issues if i.slide_number == n]

    def by_category(self, category: IssueCategory) -> list[ValidationIssue]:
        """Get issues by category."""
        return [i for i in self.issues if i.category == category]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON/AI consumption."""
        return {
            "is_valid": self.is_valid,
            "score": round(self.score, 1),
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "info_count": len(self.info),
            "issues": [i.to_dict() for i in self.issues],
        }

    def summary(self) -> str:
        """Get a human-readable summary."""
        status = "VALID" if self.is_valid else "NEEDS ATTENTION"
        parts = [f"{status} (score: {self.score:.0f}/100)"]
        if self.errors:
            parts.append(f"{len(self.errors)} error(s)")
        if self.warnings:
            parts.append(f"{len(self.warnings)} warning(s)")
        if self.info:
            parts.append(f"{len(self.info)} suggestion(s)")
        return " | ".join(parts)

    def __repr__(self) -> str:
        return f"ValidationResult({self.summary()})"


# =============================================================================
# Design thresholds - these define "good" presentation design
# =============================================================================

MAX_BULLETS_PER_SLIDE = 7
MAX_WORDS_PER_BULLET = 15
MAX_CHARS_PER_BULLET = 100
IDEAL_WORDS_PER_SLIDE = 50
MAX_WORDS_PER_SLIDE = 100
MIN_SLIDES = 2
MAX_SLIDES_WITHOUT_SECTION = 5
MIN_LAYOUTS_FOR_VARIETY = 2


def validate_slide(
    slide_info: dict[str, Any],
    strict: bool = False,
) -> list[ValidationIssue]:
    """Validate a single slide against design rules.

    Args:
        slide_info: Slide description dict from describe_slide()
        strict: If True, treat some warnings as errors

    Returns:
        List of validation issues for this slide
    """
    issues = []
    n = slide_info.get("slide_number", 0)
    content = slide_info.get("content", [])
    title = slide_info.get("title", "")
    notes = slide_info.get("notes", "")
    layout = slide_info.get("layout", "").lower()
    has_table = slide_info.get("has_table", False)
    has_chart = slide_info.get("has_chart", False)

    # Skip some checks for special layouts
    is_blank = "blank" in layout
    is_title_slide = "title slide" in layout or "title side" in layout
    is_section = "section" in layout

    # --- Rule: Missing title ---
    if not title and not is_blank:
        issues.append(
            ValidationIssue(
                severity=IssueSeverity.WARNING if not strict else IssueSeverity.ERROR,
                category=IssueCategory.STRUCTURE,
                slide_number=n,
                message="Slide has no title",
                suggestion="Add a descriptive title to help your audience follow along",
                rule="missing_title",
            )
        )

    # --- Rule: Too many bullets ---
    bullet_count = len(content)
    if bullet_count > MAX_BULLETS_PER_SLIDE and not has_table:
        issues.append(
            ValidationIssue(
                severity=IssueSeverity.WARNING,
                category=IssueCategory.CONTENT,
                slide_number=n,
                message=f"Slide has {bullet_count} bullets (max recommended: {MAX_BULLETS_PER_SLIDE})",
                suggestion="Split content across multiple slides or summarize key points",
                rule="too_many_bullets",
                details={
                    "bullet_count": bullet_count,
                    "max_recommended": MAX_BULLETS_PER_SLIDE,
                },
            )
        )

    # --- Rule: Long bullets ---
    for i, bullet in enumerate(content):
        if isinstance(bullet, str):
            word_count = len(bullet.split())
            char_count = len(bullet)

            if char_count > MAX_CHARS_PER_BULLET:
                issues.append(
                    ValidationIssue(
                        severity=IssueSeverity.WARNING,
                        category=IssueCategory.CONTENT,
                        slide_number=n,
                        message=f"Bullet {i + 1} is very long ({char_count} chars)",
                        suggestion="Break into multiple points or simplify language",
                        rule="bullet_too_long",
                        details={"bullet_index": i, "char_count": char_count},
                    )
                )
            elif word_count > MAX_WORDS_PER_BULLET:
                issues.append(
                    ValidationIssue(
                        severity=IssueSeverity.INFO,
                        category=IssueCategory.CONTENT,
                        slide_number=n,
                        message=f"Bullet {i + 1} has {word_count} words",
                        suggestion="Aim for concise phrases under 15 words",
                        rule="bullet_wordy",
                        details={"bullet_index": i, "word_count": word_count},
                    )
                )

    # --- Rule: Missing speaker notes ---
    if not notes and not is_blank and not is_title_slide:
        issues.append(
            ValidationIssue(
                severity=IssueSeverity.INFO,
                category=IssueCategory.STRUCTURE,
                slide_number=n,
                message="Slide has no speaker notes",
                suggestion="Add notes to help presenters deliver this slide effectively",
                rule="missing_notes",
            )
        )

    # --- Rule: Too much text ---
    total_words = sum(
        len(b.split()) if isinstance(b, str) else 0 for b in content
    ) + len(title.split())

    if total_words > MAX_WORDS_PER_SLIDE and not has_table:
        issues.append(
            ValidationIssue(
                severity=IssueSeverity.WARNING,
                category=IssueCategory.CONTENT,
                slide_number=n,
                message=f"Slide has {total_words} words — may overwhelm audience",
                suggestion="Consider visuals, splitting content, or summarizing",
                rule="too_much_text",
                details={"word_count": total_words, "max_recommended": MAX_WORDS_PER_SLIDE},
            )
        )
    elif total_words > IDEAL_WORDS_PER_SLIDE and not has_table and not has_chart:
        issues.append(
            ValidationIssue(
                severity=IssueSeverity.INFO,
                category=IssueCategory.CONTENT,
                slide_number=n,
                message=f"Slide has {total_words} words",
                suggestion="Slides work best with under 50 words — consider trimming",
                rule="text_heavy",
                details={"word_count": total_words},
            )
        )

    # --- Rule: Empty content slide ---
    if not content and not has_table and not has_chart and not is_blank and not is_title_slide and not is_section:
        issues.append(
            ValidationIssue(
                severity=IssueSeverity.INFO,
                category=IssueCategory.CONTENT,
                slide_number=n,
                message="Slide has a title but no content",
                suggestion="Add supporting content or use a section header layout",
                rule="empty_content",
            )
        )

    return issues


def validate_presentation(
    presentation: "Presentation",
    strict: bool = False,
) -> ValidationResult:
    """Validate an entire presentation against design rules.

    Args:
        presentation: The Presentation object to validate
        strict: If True, treat warnings as errors

    Returns:
        ValidationResult with all issues and quality score

    Example:
        >>> result = pres.validate()
        >>> if not result.is_valid:
        ...     for issue in result.errors:
        ...         print(f"Slide {issue.slide_number}: {issue.message}")
    """
    issues: list[ValidationIssue] = []
    slide_count = presentation.slide_count

    # --- Rule: No slides ---
    if slide_count == 0:
        issues.append(
            ValidationIssue(
                severity=IssueSeverity.ERROR,
                category=IssueCategory.STRUCTURE,
                slide_number=None,
                message="Presentation has no slides",
                suggestion="Add at least a title slide and content",
                rule="no_slides",
            )
        )
        return ValidationResult(is_valid=False, issues=issues, score=0)

    # --- Rule: Too few slides ---
    if slide_count < MIN_SLIDES:
        issues.append(
            ValidationIssue(
                severity=IssueSeverity.WARNING,
                category=IssueCategory.STRUCTURE,
                slide_number=None,
                message=f"Presentation only has {slide_count} slide(s)",
                suggestion="Consider adding more context or supporting content",
                rule="few_slides",
                details={"slide_count": slide_count},
            )
        )

    # Validate each slide and track patterns
    all_slides = presentation.describe_all_slides()
    content_slides_since_break = 0
    layouts_used: set[str] = set()
    has_title_slide = False
    has_closing = False
    last_layout = ""
    consecutive_same_layout = 0

    for slide_info in all_slides:
        # Per-slide validation
        slide_issues = validate_slide(slide_info, strict)
        issues.extend(slide_issues)

        # Track patterns
        layout = slide_info.get("layout", "").lower()
        layouts_used.add(layout)
        slide_num = slide_info["slide_number"]

        # Check for title slide
        if slide_num == 1 and "title" in layout:
            has_title_slide = True

        # Check for closing
        if slide_num == slide_count:
            title_lower = slide_info.get("title", "").lower()
            if any(
                w in title_lower
                for w in ["thank", "q&a", "questions", "summary", "conclusion"]
            ) or "thank" in layout or "q&a" in layout:
                has_closing = True

        # Track section breaks
        if "section" in layout or "divider" in layout:
            content_slides_since_break = 0
        else:
            content_slides_since_break += 1

            if content_slides_since_break > MAX_SLIDES_WITHOUT_SECTION:
                issues.append(
                    ValidationIssue(
                        severity=IssueSeverity.INFO,
                        category=IssueCategory.STRUCTURE,
                        slide_number=slide_num,
                        message=f"{content_slides_since_break} slides without a section break",
                        suggestion="Add a section divider to help pace your presentation",
                        rule="needs_section_break",
                        details={"slides_since_break": content_slides_since_break},
                    )
                )
                content_slides_since_break = 0  # Reset

        # Track layout repetition
        if layout == last_layout:
            consecutive_same_layout += 1
            if consecutive_same_layout >= 4:
                issues.append(
                    ValidationIssue(
                        severity=IssueSeverity.INFO,
                        category=IssueCategory.DESIGN,
                        slide_number=slide_num,
                        message=f"Same layout used for {consecutive_same_layout} consecutive slides",
                        suggestion="Vary layouts to maintain visual interest",
                        rule="repetitive_layout",
                        details={"layout": layout, "consecutive_count": consecutive_same_layout},
                    )
                )
        else:
            consecutive_same_layout = 1
            last_layout = layout

    # --- Rule: Missing title slide ---
    if not has_title_slide and slide_count > 1:
        issues.append(
            ValidationIssue(
                severity=IssueSeverity.WARNING,
                category=IssueCategory.STRUCTURE,
                slide_number=None,
                message="Presentation may be missing a title slide",
                suggestion="Start with a title slide to introduce your topic",
                rule="missing_title_slide",
            )
        )

    # --- Rule: Missing closing ---
    if not has_closing and slide_count > 3:
        issues.append(
            ValidationIssue(
                severity=IssueSeverity.INFO,
                category=IssueCategory.STRUCTURE,
                slide_number=None,
                message="Presentation may be missing a closing slide",
                suggestion="End with a summary, call to action, or Q&A slide",
                rule="missing_closing",
            )
        )

    # --- Rule: Lack of layout variety ---
    if len(layouts_used) < MIN_LAYOUTS_FOR_VARIETY and slide_count > 4:
        issues.append(
            ValidationIssue(
                severity=IssueSeverity.INFO,
                category=IssueCategory.DESIGN,
                slide_number=None,
                message=f"Only {len(layouts_used)} different layout(s) used",
                suggestion="Try comparison, two-column, or image slides for variety",
                rule="low_layout_variety",
                details={"layouts_used": list(layouts_used)},
            )
        )

    # Calculate quality score
    score = _calculate_score(issues)

    # Determine validity
    error_count = len([i for i in issues if i.severity == IssueSeverity.ERROR])
    warning_count = len([i for i in issues if i.severity == IssueSeverity.WARNING])

    if strict:
        is_valid = error_count == 0 and warning_count == 0
    else:
        is_valid = error_count == 0

    return ValidationResult(
        is_valid=is_valid,
        issues=issues,
        score=score,
    )


def _calculate_score(issues: list[ValidationIssue]) -> float:
    """Calculate a quality score from 0-100 based on issues."""
    score = 100.0

    for issue in issues:
        if issue.severity == IssueSeverity.ERROR:
            score -= 25
        elif issue.severity == IssueSeverity.WARNING:
            score -= 8
        elif issue.severity == IssueSeverity.INFO:
            score -= 2

    return max(0.0, min(100.0, score))


def validate_presentation_extended(
    presentation: "Presentation",
    *,
    strict: bool = False,
    include_accessibility: bool = False,
    brand_rules: dict | None = None,
) -> ValidationResult:
    """Extended validation with accessibility and brand rules.

    Args:
        presentation: The Presentation to validate
        strict: If True, treat warnings as errors
        include_accessibility: Include accessibility checks
        brand_rules: Brand guidelines to enforce

    Returns:
        ValidationResult with all issues
    """
    # Get base validation result
    result = validate_presentation(presentation, strict=strict)
    all_issues = list(result.issues)

    # Add accessibility checks if requested
    if include_accessibility:
        from .accessibility import check_accessibility

        access_result = check_accessibility(presentation)
        all_issues.extend(access_result.issues)

    # Check brand rules if provided
    if brand_rules:
        brand_issues = _check_brand_rules(presentation, brand_rules)
        all_issues.extend(brand_issues)

    # Recalculate score
    score = _calculate_score(all_issues)

    # Determine validity
    error_count = len([i for i in all_issues if i.severity == IssueSeverity.ERROR])
    warning_count = len([i for i in all_issues if i.severity == IssueSeverity.WARNING])

    if strict:
        is_valid = error_count == 0 and warning_count == 0
    else:
        is_valid = error_count == 0

    return ValidationResult(
        is_valid=is_valid,
        issues=all_issues,
        score=score,
    )


def _check_brand_rules(
    presentation: "Presentation",
    brand_rules: dict,
) -> list[ValidationIssue]:
    """Check presentation against brand rules."""
    issues = []

    allowed_fonts = brand_rules.get("allowed_fonts")
    min_font_size = brand_rules.get("min_font_size")
    max_bullets = brand_rules.get("max_bullets")

    for i in range(1, presentation.slide_count + 1):
        slide = presentation._pptx.slides[i - 1]
        slide_info = presentation.describe_slide(i)

        # Check fonts
        if allowed_fonts:
            fonts_used = set()
            for shape in slide.shapes:
                try:
                    if shape.has_text_frame:
                        for para in shape.text_frame.paragraphs:
                            for run in para.runs:
                                if run.font.name:
                                    fonts_used.add(run.font.name)
                except Exception:
                    continue

            for font in fonts_used:
                if font not in allowed_fonts:
                    issues.append(
                        ValidationIssue(
                            severity=IssueSeverity.WARNING,
                            category=IssueCategory.DESIGN,
                            slide_number=i,
                            message=f"Font '{font}' is not in allowed fonts",
                            suggestion=f"Use: {', '.join(allowed_fonts)}",
                            rule="brand_font_violation",
                            details={"font": font},
                        )
                    )

        # Check font size
        if min_font_size:
            for shape in slide.shapes:
                try:
                    if shape.has_text_frame:
                        for para in shape.text_frame.paragraphs:
                            for run in para.runs:
                                if run.font.size and run.font.size.pt < min_font_size:
                                    issues.append(
                                        ValidationIssue(
                                            severity=IssueSeverity.WARNING,
                                            category=IssueCategory.DESIGN,
                                            slide_number=i,
                                            message=f"Font size {run.font.size.pt:.0f}pt below minimum {min_font_size}pt",
                                            suggestion=f"Use at least {min_font_size}pt font",
                                            rule="brand_font_size",
                                        )
                                    )
                except Exception:
                    continue

        # Check bullet count
        if max_bullets:
            content = slide_info.get("content", [])
            if len(content) > max_bullets:
                issues.append(
                    ValidationIssue(
                        severity=IssueSeverity.WARNING,
                        category=IssueCategory.CONTENT,
                        slide_number=i,
                        message=f"Slide has {len(content)} bullets, max is {max_bullets}",
                        suggestion="Reduce content or split across slides",
                        rule="brand_max_bullets",
                        details={"bullet_count": len(content), "max": max_bullets},
                    )
                )

    return issues
