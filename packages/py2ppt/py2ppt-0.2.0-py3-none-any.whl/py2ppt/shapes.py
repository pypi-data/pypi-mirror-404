"""Shape manipulation utilities for py2ppt.

Provides constants and helpers for adding and styling shapes
in PowerPoint presentations.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor


class ShapeType(str, Enum):
    """Common shape types for easy access.

    Maps friendly names to MSO_SHAPE constants.
    """

    # Basic shapes
    RECTANGLE = "rectangle"
    ROUNDED_RECTANGLE = "rounded_rectangle"
    OVAL = "oval"
    CIRCLE = "circle"
    TRIANGLE = "triangle"
    DIAMOND = "diamond"

    # Arrows
    ARROW_RIGHT = "arrow_right"
    ARROW_LEFT = "arrow_left"
    ARROW_UP = "arrow_up"
    ARROW_DOWN = "arrow_down"
    ARROW_LEFT_RIGHT = "arrow_left_right"
    ARROW_UP_DOWN = "arrow_up_down"

    # Callouts
    CALLOUT_RECTANGLE = "callout_rectangle"
    CALLOUT_ROUNDED_RECTANGLE = "callout_rounded_rectangle"
    CALLOUT_OVAL = "callout_oval"
    CALLOUT_CLOUD = "callout_cloud"

    # Block arrows
    CHEVRON = "chevron"
    PENTAGON = "pentagon"
    HEXAGON = "hexagon"
    HEPTAGON = "heptagon"
    OCTAGON = "octagon"

    # Stars and banners
    STAR_4_POINT = "star_4_point"
    STAR_5_POINT = "star_5_point"
    STAR_6_POINT = "star_6_point"

    # Flowchart
    FLOWCHART_PROCESS = "flowchart_process"
    FLOWCHART_DECISION = "flowchart_decision"
    FLOWCHART_TERMINATOR = "flowchart_terminator"
    FLOWCHART_DATA = "flowchart_data"

    # Other
    HEART = "heart"
    LIGHTNING_BOLT = "lightning_bolt"
    CROSS = "cross"
    PLUS = "plus"


class ConnectorType(str, Enum):
    """Connector types for connecting shapes."""

    STRAIGHT = "straight"
    ELBOW = "elbow"
    CURVED = "curved"


# Mapping from ShapeType to MSO_SHAPE
_SHAPE_TYPE_MAP: dict[ShapeType, int] = {
    ShapeType.RECTANGLE: MSO_SHAPE.RECTANGLE,
    ShapeType.ROUNDED_RECTANGLE: MSO_SHAPE.ROUNDED_RECTANGLE,
    ShapeType.OVAL: MSO_SHAPE.OVAL,
    ShapeType.CIRCLE: MSO_SHAPE.OVAL,  # Circle is just a square oval
    ShapeType.TRIANGLE: MSO_SHAPE.ISOSCELES_TRIANGLE,
    ShapeType.DIAMOND: MSO_SHAPE.DIAMOND,
    ShapeType.ARROW_RIGHT: MSO_SHAPE.RIGHT_ARROW,
    ShapeType.ARROW_LEFT: MSO_SHAPE.LEFT_ARROW,
    ShapeType.ARROW_UP: MSO_SHAPE.UP_ARROW,
    ShapeType.ARROW_DOWN: MSO_SHAPE.DOWN_ARROW,
    ShapeType.ARROW_LEFT_RIGHT: MSO_SHAPE.LEFT_RIGHT_ARROW,
    ShapeType.ARROW_UP_DOWN: MSO_SHAPE.UP_DOWN_ARROW,
    ShapeType.CALLOUT_RECTANGLE: MSO_SHAPE.RECTANGULAR_CALLOUT,
    ShapeType.CALLOUT_ROUNDED_RECTANGLE: MSO_SHAPE.ROUNDED_RECTANGULAR_CALLOUT,
    ShapeType.CALLOUT_OVAL: MSO_SHAPE.OVAL_CALLOUT,
    ShapeType.CALLOUT_CLOUD: MSO_SHAPE.CLOUD_CALLOUT,
    ShapeType.CHEVRON: MSO_SHAPE.CHEVRON,
    ShapeType.PENTAGON: MSO_SHAPE.PENTAGON,
    ShapeType.HEXAGON: MSO_SHAPE.HEXAGON,
    ShapeType.HEPTAGON: MSO_SHAPE.HEPTAGON,
    ShapeType.OCTAGON: MSO_SHAPE.OCTAGON,
    ShapeType.STAR_4_POINT: MSO_SHAPE.STAR_4_POINT,
    ShapeType.STAR_5_POINT: MSO_SHAPE.STAR_5_POINT,
    ShapeType.STAR_6_POINT: MSO_SHAPE.STAR_6_POINT,
    ShapeType.FLOWCHART_PROCESS: MSO_SHAPE.FLOWCHART_PROCESS,
    ShapeType.FLOWCHART_DECISION: MSO_SHAPE.FLOWCHART_DECISION,
    ShapeType.FLOWCHART_TERMINATOR: MSO_SHAPE.FLOWCHART_TERMINATOR,
    ShapeType.FLOWCHART_DATA: MSO_SHAPE.FLOWCHART_DATA,
    ShapeType.HEART: MSO_SHAPE.HEART,
    ShapeType.LIGHTNING_BOLT: MSO_SHAPE.LIGHTNING_BOLT,
    ShapeType.CROSS: MSO_SHAPE.CROSS,
    ShapeType.PLUS: MSO_SHAPE.MATH_PLUS,
}

# Mapping from ConnectorType to MSO_CONNECTOR
_CONNECTOR_TYPE_MAP: dict[ConnectorType, int] = {
    ConnectorType.STRAIGHT: MSO_CONNECTOR.STRAIGHT,
    ConnectorType.ELBOW: MSO_CONNECTOR.ELBOW,
    ConnectorType.CURVED: MSO_CONNECTOR.CURVE,
}


def get_mso_shape(shape_type: ShapeType | str) -> int:
    """Convert ShapeType enum or string to MSO_SHAPE constant.

    Args:
        shape_type: ShapeType enum value or string name

    Returns:
        MSO_SHAPE constant value

    Raises:
        ValueError: If shape type is not recognized
    """
    if isinstance(shape_type, str):
        try:
            shape_type = ShapeType(shape_type.lower())
        except ValueError:
            raise ValueError(
                f"Unknown shape type: {shape_type}. "
                f"Valid types: {', '.join(s.value for s in ShapeType)}"
            )

    if shape_type not in _SHAPE_TYPE_MAP:
        raise ValueError(f"Shape type {shape_type} is not mapped to MSO_SHAPE")

    return _SHAPE_TYPE_MAP[shape_type]


def get_mso_connector(connector_type: ConnectorType | str) -> int:
    """Convert ConnectorType enum or string to MSO_CONNECTOR constant.

    Args:
        connector_type: ConnectorType enum value or string name

    Returns:
        MSO_CONNECTOR constant value

    Raises:
        ValueError: If connector type is not recognized
    """
    if isinstance(connector_type, str):
        try:
            connector_type = ConnectorType(connector_type.lower())
        except ValueError:
            raise ValueError(
                f"Unknown connector type: {connector_type}. "
                f"Valid types: {', '.join(c.value for c in ConnectorType)}"
            )

    if connector_type not in _CONNECTOR_TYPE_MAP:
        raise ValueError(
            f"Connector type {connector_type} is not mapped to MSO_CONNECTOR"
        )

    return _CONNECTOR_TYPE_MAP[connector_type]


def parse_color(color: str | None) -> RGBColor | None:
    """Parse a color string to RGBColor.

    Args:
        color: Hex color string (e.g., "#FF0000") or None

    Returns:
        RGBColor instance or None
    """
    if color is None:
        return None

    color_hex = color.lstrip("#")
    if len(color_hex) != 6:
        return None

    try:
        return RGBColor(
            int(color_hex[:2], 16),
            int(color_hex[2:4], 16),
            int(color_hex[4:6], 16),
        )
    except ValueError:
        return None


def parse_dimension(value: float | int | None, unit: str = "inches") -> int | None:
    """Convert a dimension value to EMUs.

    Args:
        value: Dimension value or None
        unit: Unit type - "inches", "pt", "emu"

    Returns:
        EMU value or None
    """
    if value is None:
        return None

    if unit == "inches":
        return Inches(value)
    elif unit == "pt":
        return Pt(value)
    elif unit == "emu":
        return Emu(value)
    else:
        return Inches(value)
