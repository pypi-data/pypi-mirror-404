"""Export functionality for py2ppt.

Provides PDF export and other format conversions.
"""

from __future__ import annotations

import subprocess
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

from .errors import Py2PptError

if TYPE_CHECKING:
    from .presentation import Presentation


class ExportError(Py2PptError):
    """Error during export operation."""

    pass


def save_pdf(
    presentation: "Presentation",
    path: str | Path,
    *,
    engine: str = "libreoffice",
) -> None:
    """Export presentation to PDF.

    Requires LibreOffice installed on the system.

    Args:
        presentation: The Presentation to export
        path: Output PDF file path
        engine: Export engine to use - "libreoffice" or "unoconv"

    Raises:
        ExportError: If LibreOffice is not installed or export fails

    Example:
        >>> from py2ppt.export import save_pdf
        >>> save_pdf(pres, "output.pdf")
    """
    path = Path(path)

    # Save presentation to temp file first
    import tempfile

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_pptx = Path(temp_dir) / "temp.pptx"
        presentation.save(temp_pptx)

        if engine == "libreoffice":
            _export_with_libreoffice(temp_pptx, path)
        elif engine == "unoconv":
            _export_with_unoconv(temp_pptx, path)
        else:
            raise ExportError(
                f"Unknown export engine: {engine}",
                suggestion="Use 'libreoffice' or 'unoconv'",
                code="UNKNOWN_ENGINE",
            )


def _find_libreoffice() -> str | None:
    """Find LibreOffice executable."""
    # Try common paths
    candidates = [
        "libreoffice",
        "soffice",
        "/usr/bin/libreoffice",
        "/usr/bin/soffice",
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
        "/opt/libreoffice/program/soffice",
    ]

    for candidate in candidates:
        if shutil.which(candidate):
            return candidate

    return None


def _export_with_libreoffice(pptx_path: Path, pdf_path: Path) -> None:
    """Export using LibreOffice headless."""
    libreoffice = _find_libreoffice()

    if libreoffice is None:
        raise ExportError(
            "LibreOffice not found on system",
            suggestion="Install LibreOffice: brew install libreoffice (macOS) or apt install libreoffice (Linux)",
            code="LIBREOFFICE_NOT_FOUND",
        )

    # Create output directory if needed
    pdf_path.parent.mkdir(parents=True, exist_ok=True)

    # Run LibreOffice in headless mode
    try:
        result = subprocess.run(
            [
                libreoffice,
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                str(pdf_path.parent),
                str(pptx_path),
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode != 0:
            raise ExportError(
                f"LibreOffice export failed: {result.stderr}",
                suggestion="Check LibreOffice installation and file permissions",
                code="EXPORT_FAILED",
            )

        # LibreOffice outputs to {input_name}.pdf, rename if needed
        expected_output = pdf_path.parent / f"{pptx_path.stem}.pdf"
        if expected_output != pdf_path and expected_output.exists():
            expected_output.rename(pdf_path)

        if not pdf_path.exists():
            raise ExportError(
                "PDF file was not created",
                suggestion="Check LibreOffice output and permissions",
                code="OUTPUT_MISSING",
            )

    except subprocess.TimeoutExpired:
        raise ExportError(
            "LibreOffice export timed out",
            suggestion="The presentation may be too large or LibreOffice is stuck",
            code="EXPORT_TIMEOUT",
        )
    except FileNotFoundError:
        raise ExportError(
            f"Could not execute LibreOffice: {libreoffice}",
            suggestion="Verify LibreOffice installation",
            code="LIBREOFFICE_NOT_FOUND",
        )


def _export_with_unoconv(pptx_path: Path, pdf_path: Path) -> None:
    """Export using unoconv."""
    unoconv = shutil.which("unoconv")

    if unoconv is None:
        raise ExportError(
            "unoconv not found on system",
            suggestion="Install unoconv: pip install unoconv or apt install unoconv",
            code="UNOCONV_NOT_FOUND",
        )

    try:
        result = subprocess.run(
            [
                unoconv,
                "-f",
                "pdf",
                "-o",
                str(pdf_path),
                str(pptx_path),
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode != 0:
            raise ExportError(
                f"unoconv export failed: {result.stderr}",
                suggestion="Check unoconv installation",
                code="EXPORT_FAILED",
            )

        if not pdf_path.exists():
            raise ExportError(
                "PDF file was not created",
                suggestion="Check unoconv output",
                code="OUTPUT_MISSING",
            )

    except subprocess.TimeoutExpired:
        raise ExportError(
            "unoconv export timed out",
            suggestion="The presentation may be too large",
            code="EXPORT_TIMEOUT",
        )


def is_pdf_export_available() -> dict[str, bool]:
    """Check which PDF export engines are available.

    Returns:
        Dict with engine availability

    Example:
        >>> available = is_pdf_export_available()
        >>> if available["libreoffice"]:
        ...     save_pdf(pres, "output.pdf")
    """
    return {
        "libreoffice": _find_libreoffice() is not None,
        "unoconv": shutil.which("unoconv") is not None,
    }
