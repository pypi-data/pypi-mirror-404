"""Theme helper for easy access to template colors and fonts.

Provides convenient methods for applying theme-consistent
formatting to content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .template import Template


class ThemeHelper:
    """Provides easy access to template theme colors and fonts.

    Accessed via `presentation.theme`. Makes it easy to apply
    consistent theme colors and fonts to rich text content.

    Example:
        >>> pres = template.create_presentation()
        >>> theme = pres.theme
        >>> theme.accent1  # "#41B3FF"
        >>> theme.colored("Important", "accent1")
        {'text': 'Important', 'color': '#41B3FF'}
        >>> theme.bold("Key point")
        {'text': 'Key point', 'bold': True}
    """

    def __init__(self, template: "Template") -> None:
        """Initialize with a template.

        Args:
            template: The Template to get colors/fonts from
        """
        self._template = template
        self._colors = template.colors
        self._fonts = template.fonts

    # --- Color properties ---

    @property
    def accent1(self) -> str:
        """Primary accent color (e.g., brand blue)."""
        return self._colors.get("accent1", "#4472C4")

    @property
    def accent2(self) -> str:
        """Secondary accent color."""
        return self._colors.get("accent2", "#ED7D31")

    @property
    def accent3(self) -> str:
        """Tertiary accent color."""
        return self._colors.get("accent3", "#A5A5A5")

    @property
    def accent4(self) -> str:
        """Fourth accent color."""
        return self._colors.get("accent4", "#FFC000")

    @property
    def accent5(self) -> str:
        """Fifth accent color."""
        return self._colors.get("accent5", "#5B9BD5")

    @property
    def accent6(self) -> str:
        """Sixth accent color."""
        return self._colors.get("accent6", "#70AD47")

    @property
    def dark1(self) -> str:
        """Primary dark color (usually black or near-black)."""
        return self._colors.get("dk1", "#000000")

    @property
    def dark2(self) -> str:
        """Secondary dark color."""
        return self._colors.get("dk2", "#44546A")

    @property
    def light1(self) -> str:
        """Primary light color (usually white)."""
        return self._colors.get("lt1", "#FFFFFF")

    @property
    def light2(self) -> str:
        """Secondary light color."""
        return self._colors.get("lt2", "#E7E6E6")

    @property
    def hyperlink(self) -> str:
        """Hyperlink color."""
        return self._colors.get("hlink", "#0563C1")

    # --- Font properties ---

    @property
    def heading_font(self) -> str:
        """Heading/title font family."""
        return self._fonts.get("heading", "Calibri Light")

    @property
    def body_font(self) -> str:
        """Body text font family."""
        return self._fonts.get("body", "Calibri")

    # --- Color access by index ---

    def accent(self, n: int) -> str:
        """Get accent color by number (1-6).

        Args:
            n: Accent number (1-6)

        Returns:
            Hex color string

        Example:
            >>> theme.accent(1)  # Same as theme.accent1
        """
        colors = [
            self.accent1,
            self.accent2,
            self.accent3,
            self.accent4,
            self.accent5,
            self.accent6,
        ]
        return colors[(n - 1) % 6]

    @property
    def all_colors(self) -> dict[str, str]:
        """Get all theme colors as a dict."""
        return self._colors.copy()

    @property
    def all_fonts(self) -> dict[str, str]:
        """Get all theme fonts as a dict."""
        return self._fonts.copy()

    # --- Formatting helpers ---

    def colored(
        self, text: str, color: str = "accent1", **kwargs: Any
    ) -> dict[str, Any]:
        """Create colored text.

        Args:
            text: The text content
            color: Color name ('accent1'-'accent6', 'dark1', 'dark2',
                   'light1', 'light2', 'hyperlink') or hex string
            **kwargs: Additional formatting (bold, italic, etc.)

        Returns:
            Formatted text dict for use in content lists

        Example:
            >>> theme.colored("Important", "accent1")
            {'text': 'Important', 'color': '#41B3FF'}
        """
        hex_color = self._resolve_color(color)
        return {"text": text, "color": hex_color, **kwargs}

    def bold(self, text: str, **kwargs: Any) -> dict[str, Any]:
        """Create bold text.

        Args:
            text: The text content
            **kwargs: Additional formatting

        Returns:
            Formatted text dict

        Example:
            >>> theme.bold("Key point")
            {'text': 'Key point', 'bold': True}
        """
        return {"text": text, "bold": True, **kwargs}

    def italic(self, text: str, **kwargs: Any) -> dict[str, Any]:
        """Create italic text.

        Args:
            text: The text content
            **kwargs: Additional formatting

        Returns:
            Formatted text dict
        """
        return {"text": text, "italic": True, **kwargs}

    def underline(self, text: str, **kwargs: Any) -> dict[str, Any]:
        """Create underlined text.

        Args:
            text: The text content
            **kwargs: Additional formatting

        Returns:
            Formatted text dict
        """
        return {"text": text, "underline": True, **kwargs}

    def bold_colored(
        self, text: str, color: str = "accent1", **kwargs: Any
    ) -> dict[str, Any]:
        """Create bold colored text.

        Args:
            text: The text content
            color: Color name or hex string
            **kwargs: Additional formatting

        Returns:
            Formatted text dict

        Example:
            >>> theme.bold_colored("Highlight", "accent2")
        """
        hex_color = self._resolve_color(color)
        return {"text": text, "bold": True, "color": hex_color, **kwargs}

    def link(self, text: str, url: str, **kwargs: Any) -> dict[str, Any]:
        """Create a hyperlink.

        Args:
            text: Display text
            url: Link URL
            **kwargs: Additional formatting

        Returns:
            Formatted text dict with hyperlink

        Example:
            >>> theme.link("Click here", "https://example.com")
        """
        return {
            "text": text,
            "hyperlink": url,
            "color": self.hyperlink,
            **kwargs,
        }

    def heading(self, text: str, **kwargs: Any) -> dict[str, Any]:
        """Create text styled as a heading.

        Args:
            text: The text content
            **kwargs: Additional formatting

        Returns:
            Formatted text dict with heading font and bold
        """
        return {
            "text": text,
            "bold": True,
            "font_family": self.heading_font,
            **kwargs,
        }

    def sized(
        self, text: str, size: int, **kwargs: Any
    ) -> dict[str, Any]:
        """Create text with specific font size.

        Args:
            text: The text content
            size: Font size in points
            **kwargs: Additional formatting

        Returns:
            Formatted text dict
        """
        return {"text": text, "font_size": size, **kwargs}

    def label_value(
        self,
        label: str,
        value: str,
        label_bold: bool = True,
        value_color: str | None = None,
    ) -> list[dict[str, Any]]:
        """Create a label: value pair as rich text.

        Args:
            label: The label text (e.g., "Revenue:")
            value: The value text (e.g., "$10M")
            label_bold: Whether to bold the label
            value_color: Optional color for the value

        Returns:
            List of formatted text dicts (for use in a single bullet)

        Example:
            >>> theme.label_value("Status:", "Complete", value_color="accent1")
            [{'text': 'Status: ', 'bold': True}, {'text': 'Complete', 'color': '#41B3FF'}]
        """
        label_fmt: dict[str, Any] = {"text": f"{label} "}
        if label_bold:
            label_fmt["bold"] = True

        value_fmt: dict[str, Any] = {"text": value}
        if value_color:
            value_fmt["color"] = self._resolve_color(value_color)

        return [label_fmt, value_fmt]

    def numbered(
        self, number: int | str, text: str, number_color: str = "accent1"
    ) -> list[dict[str, Any]]:
        """Create numbered text with colored number.

        Args:
            number: The number or step indicator
            text: The text content
            number_color: Color for the number

        Returns:
            List of formatted text dicts

        Example:
            >>> theme.numbered(1, "First step")
            [{'text': '1. ', 'bold': True, 'color': '#41B3FF'}, {'text': 'First step'}]
        """
        return [
            self.bold_colored(f"{number}. ", number_color),
            {"text": text},
        ]

    # --- Private helpers ---

    def _resolve_color(self, color: str) -> str:
        """Resolve a color name or hex string to hex."""
        if color.startswith("#"):
            return color

        color_map = {
            "accent1": self.accent1,
            "accent2": self.accent2,
            "accent3": self.accent3,
            "accent4": self.accent4,
            "accent5": self.accent5,
            "accent6": self.accent6,
            "dark1": self.dark1,
            "dark2": self.dark2,
            "light1": self.light1,
            "light2": self.light2,
            "hyperlink": self.hyperlink,
        }
        return color_map.get(color, self.accent1)

    def __repr__(self) -> str:
        return f"ThemeHelper(accent1={self.accent1}, heading={self.heading_font})"
