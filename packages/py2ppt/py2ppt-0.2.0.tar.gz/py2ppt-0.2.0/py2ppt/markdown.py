"""Markdown import and export for py2ppt.

Supports converting presentations to Markdown format and
building presentations from Markdown outlines.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .template import Template
    from .presentation import Presentation


def to_markdown(presentation: "Presentation", path: str | Path | None = None) -> str:
    """Export a presentation to Markdown format.

    Args:
        presentation: The Presentation to export
        path: Optional file path to save (if None, returns string only)

    Returns:
        Markdown string representation

    Output format:
        # Presentation Title (from first slide)
        ## Slide 1: Title
        - Bullet 1
        - Bullet 2

        ## Slide 2: Another Title
        | Col1 | Col2 |
        |------|------|
        | A    | B    |

        <!-- notes: Speaker notes here -->
    """
    lines = []
    slides = presentation.describe_all_slides()

    # Try to get presentation title from first slide
    if slides and slides[0].get("title"):
        lines.append(f"# {slides[0]['title']}")
        lines.append("")

    for slide_info in slides:
        slide_num = slide_info["slide_number"]
        title = slide_info.get("title", "")
        content = slide_info.get("content", [])
        notes = slide_info.get("notes", "")
        has_table = slide_info.get("has_table", False)
        layout = slide_info.get("layout", "").lower()

        # Determine slide type header
        if "section" in layout:
            lines.append(f"## Section: {title}")
        elif slide_num == 1 and "title" in layout:
            # Already used as presentation title
            pass
        else:
            lines.append(f"## Slide {slide_num}: {title}")

        lines.append("")

        # Add content
        if content:
            for item in content:
                if isinstance(item, str) and item.strip():
                    lines.append(f"- {item}")
            lines.append("")

        # Add table if present
        if has_table:
            table_info = _extract_table_info(slide_info)
            if table_info:
                headers, rows = table_info
                lines.append(_format_markdown_table(headers, rows))
                lines.append("")

        # Add notes
        if notes and notes.strip():
            lines.append(f"<!-- notes: {notes.strip()} -->")
            lines.append("")

    result = "\n".join(lines)

    if path:
        Path(path).write_text(result, encoding="utf-8")

    return result


def _extract_table_info(
    slide_info: dict[str, Any]
) -> tuple[list[str], list[list[str]]] | None:
    """Extract table headers and rows from slide info."""
    for shape in slide_info.get("shapes", []):
        if "table" in shape:
            tbl = shape["table"]
            headers = tbl.get("headers", [])
            # We don't have full row data in shape info, just return headers
            if headers:
                return headers, []
    return None


def _format_markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    """Format a table as Markdown."""
    if not headers:
        return ""

    lines = []
    lines.append("| " + " | ".join(str(h) for h in headers) + " |")
    lines.append("|" + "|".join("------" for _ in headers) + "|")

    for row in rows:
        lines.append("| " + " | ".join(str(c) for c in row) + " |")

    return "\n".join(lines)


def build_from_markdown(
    template: "Template",
    markdown: str | Path,
) -> "Presentation":
    """Build a presentation from Markdown.

    Args:
        template: Template to use
        markdown: Markdown string or path to .md file

    Returns:
        New Presentation built from the Markdown

    Supported Markdown format:
        # Presentation Title -> title slide
        ## Slide: Name -> content slide
        ## Section: Name -> section slide
        - bullets -> bullet points
        > quote -> quote text (styled)
        | tables | -> table slide
        ![image](path) -> image slide
        <!-- notes: ... --> -> speaker notes
    """
    if isinstance(markdown, Path):
        markdown = markdown.read_text(encoding="utf-8")
    elif markdown and Path(markdown).exists() and Path(markdown).is_file():
        markdown = Path(markdown).read_text(encoding="utf-8")

    pres = template.create_presentation()
    lines = markdown.split("\n")

    current_slide_type = None
    current_title = ""
    current_content: list[str] = []
    current_notes = ""
    current_table_headers: list[str] = []
    current_table_rows: list[list[str]] = []
    in_table = False

    def flush_slide():
        """Create slide from accumulated content."""
        nonlocal current_slide_type, current_title, current_content
        nonlocal current_notes, current_table_headers, current_table_rows
        nonlocal in_table

        if current_slide_type is None:
            return

        slide_num = None

        if current_slide_type == "title":
            slide_num = pres.add_title_slide(current_title, "")

        elif current_slide_type == "section":
            slide_num = pres.add_section_slide(current_title)

        elif current_slide_type == "table" and current_table_headers:
            slide_num = pres.add_table_slide(
                current_title, current_table_headers, current_table_rows
            )

        elif current_slide_type == "quote" and current_content:
            quote = current_content[0] if current_content else ""
            attr = current_content[1] if len(current_content) > 1 else ""
            slide_num = pres.add_quote_slide(quote, attr)

        elif current_slide_type == "image":
            # Image slides need actual image files
            # For now, create a content slide with the image reference
            slide_num = pres.add_content_slide(current_title, current_content)

        else:
            # Default content slide
            if current_content:
                slide_num = pres.add_content_slide(current_title, current_content)
            elif current_title:
                slide_num = pres.add_content_slide(current_title, [])

        # Add notes if present
        if slide_num and current_notes:
            pres.set_notes(slide_num, current_notes)

        # Reset
        current_slide_type = None
        current_title = ""
        current_content = []
        current_notes = ""
        current_table_headers = []
        current_table_rows = []
        in_table = False

    for line in lines:
        line_stripped = line.strip()

        # Skip empty lines
        if not line_stripped:
            if in_table:
                in_table = False
            continue

        # H1: Presentation title (becomes title slide)
        if line_stripped.startswith("# ") and not line_stripped.startswith("## "):
            flush_slide()
            current_slide_type = "title"
            current_title = line_stripped[2:].strip()
            continue

        # H2: Slide header
        h2_match = re.match(r"^##\s+(.+)$", line_stripped)
        if h2_match:
            flush_slide()
            header_text = h2_match.group(1).strip()

            # Check for slide type prefix
            if header_text.lower().startswith("section:"):
                current_slide_type = "section"
                current_title = header_text[8:].strip()
            elif header_text.lower().startswith("slide:"):
                current_slide_type = "content"
                current_title = header_text[6:].strip()
            elif ":" in header_text:
                # "Slide N: Title" format
                parts = header_text.split(":", 1)
                current_slide_type = "content"
                current_title = parts[1].strip() if len(parts) > 1 else header_text
            else:
                current_slide_type = "content"
                current_title = header_text
            continue

        # Notes comment
        notes_match = re.match(r"^<!--\s*notes?:\s*(.+?)\s*-->$", line_stripped, re.IGNORECASE)
        if notes_match:
            current_notes = notes_match.group(1).strip()
            continue

        # Quote line
        if line_stripped.startswith(">"):
            if current_slide_type != "quote":
                flush_slide()
                current_slide_type = "quote"
                current_title = "Quote"
            quote_text = line_stripped[1:].strip()
            if quote_text.startswith(" "):
                quote_text = quote_text[1:]
            current_content.append(quote_text)
            continue

        # Table header
        if line_stripped.startswith("|") and line_stripped.endswith("|"):
            cells = [c.strip() for c in line_stripped[1:-1].split("|")]

            # Check if this is a separator line
            if all(re.match(r"^[-:]+$", c) for c in cells if c):
                in_table = True
                continue

            if not in_table and not current_table_headers:
                # This is the header row
                current_table_headers = cells
                current_slide_type = "table"
            elif in_table:
                # This is a data row
                current_table_rows.append(cells)
            continue

        # Image
        img_match = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)$", line_stripped)
        if img_match:
            flush_slide()
            current_slide_type = "image"
            current_title = img_match.group(1) or "Image"
            current_content = [f"Image: {img_match.group(2)}"]
            continue

        # Bullet point
        if line_stripped.startswith("- ") or line_stripped.startswith("* "):
            bullet_text = line_stripped[2:].strip()
            current_content.append(bullet_text)
            continue

        # Numbered list
        num_match = re.match(r"^\d+\.\s+(.+)$", line_stripped)
        if num_match:
            current_content.append(num_match.group(1).strip())
            continue

        # Plain text (add as content if we have a slide)
        if current_slide_type and line_stripped:
            current_content.append(line_stripped)

    # Flush any remaining slide
    flush_slide()

    return pres
