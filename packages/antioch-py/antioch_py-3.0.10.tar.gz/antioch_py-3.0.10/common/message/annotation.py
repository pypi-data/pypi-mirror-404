from __future__ import annotations

from enum import IntEnum

from foxglove.schemas import (
    CircleAnnotation as FoxgloveCircleAnnotation,
    Color as FoxgloveColor,
    ImageAnnotations as FoxgloveImageAnnotations,
    Point2 as FoxglovePoint2,
    PointsAnnotation as FoxglovePointsAnnotation,
    PointsAnnotationType as FoxglovePointsAnnotationType,
    TextAnnotation as FoxgloveTextAnnotation,
)
from pydantic import Field

from common.message.color import Color
from common.message.message import Message
from common.message.point import Point2


class PointsAnnotationType(IntEnum):
    """
    Type of points annotation.

    Example:
        ```python
        from common.message import PointsAnnotationType

        # Use as enum value
        annotation_type = PointsAnnotationType.LINE_STRIP
        ```
    """

    UNKNOWN = 0
    POINTS = 1
    LINE_LOOP = 2
    LINE_STRIP = 3
    LINE_LIST = 4


class CircleAnnotation(Message):
    """
    A circle annotation on a 2D image.

    Coordinates use the top-left corner of the top-left pixel as the origin.

    Example:
        ```python
        from common.message import CircleAnnotation, Point2, Color

        # Create a circle annotation
        circle = CircleAnnotation(
            timestamp_us=1000000,
            position=Point2(x=100.0, y=100.0),
            diameter=50.0,
            thickness=2.0,
            fill_color=Color.transparent(),
            outline_color=Color.red(),
        )
        ```
    """

    timestamp_us: int = Field(description="Timestamp in microseconds")
    position: Point2 = Field(description="Center position of the circle")
    diameter: float = Field(description="Diameter of the circle in pixels")
    thickness: float = Field(description="Line thickness in pixels")
    fill_color: Color = Field(description="Fill color of the circle")
    outline_color: Color = Field(description="Outline color of the circle")


class PointsAnnotation(Message):
    """
    An array of points on a 2D image.

    Coordinates use the top-left corner of the top-left pixel as the origin.

    Example:
        ```python
        from common.message import PointsAnnotation, PointsAnnotationType, Point2, Color

        # Create a line strip annotation
        annotation = PointsAnnotation(
            timestamp_us=1000000,
            type=PointsAnnotationType.LINE_STRIP,
            points=[
                Point2(x=10.0, y=10.0),
                Point2(x=100.0, y=50.0),
                Point2(x=150.0, y=100.0),
            ],
            outline_color=Color.green(),
            thickness=2.0,
        )
        ```
    """

    timestamp_us: int = Field(description="Timestamp in microseconds")
    type: PointsAnnotationType = Field(description="Type of points annotation (points, line_strip, etc.)")
    points: list[Point2] = Field(description="List of 2D points")
    outline_color: Color = Field(description="Primary outline color")
    outline_colors: list[Color] | None = Field(default=None, description="Per-point outline colors")
    fill_color: Color | None = Field(default=None, description="Fill color for closed shapes")
    thickness: float = Field(description="Line thickness in pixels")


class TextAnnotation(Message):
    """
    A text label on a 2D image.

    Position uses the bottom-left origin of the text label.
    Coordinates use the top-left corner of the top-left pixel as the origin.

    Example:
        ```python
        from common.message import TextAnnotation, Point2, Color

        # Create a text annotation
        text = TextAnnotation(
            timestamp_us=1000000,
            position=Point2(x=50.0, y=30.0),
            text="Detection: Person",
            font_size=14.0,
            text_color=Color.white(),
            background_color=Color.rgba(0.0, 0.0, 0.0, 0.5),
        )
        ```
    """

    timestamp_us: int = Field(description="Timestamp in microseconds")
    position: Point2 = Field(description="Bottom-left position of the text label")
    text: str = Field(description="Text content to display")
    font_size: float = Field(description="Font size in pixels")
    text_color: Color = Field(description="Color of the text")
    background_color: Color = Field(description="Background color behind the text")


class ImageAnnotations(Message):
    """
    Array of annotations for a 2D image.

    Used in the Foxglove Image panel for visualization.

    Example:
        ```python
        from common.message import ImageAnnotations, CircleAnnotation, Point2, Color

        # Create an empty annotations container
        annotations = ImageAnnotations.empty()

        # Or create with annotations
        annotations = ImageAnnotations(
            circles=[
                CircleAnnotation(
                    timestamp_us=1000000,
                    position=Point2(x=100.0, y=100.0),
                    diameter=20.0,
                    thickness=2.0,
                    fill_color=Color.transparent(),
                    outline_color=Color.red(),
                ),
            ],
            points=[],
            texts=[],
        )
        ```
    """

    _type = "antioch/image_annotations"
    circles: list[CircleAnnotation] = Field(description="Circle annotations")
    points: list[PointsAnnotation] = Field(description="Points/line annotations")
    texts: list[TextAnnotation] = Field(description="Text annotations")

    @classmethod
    def empty(cls) -> ImageAnnotations:
        """
        Create an empty ImageAnnotations instance.

        :return: ImageAnnotations with no annotations.
        """

        return cls(circles=[], points=[], texts=[])

    def to_foxglove(self) -> FoxgloveImageAnnotations:
        """
        Convert to Foxglove ImageAnnotations for telemetry.

        :return: Foxglove ImageAnnotations schema.
        """

        # Convert PointsAnnotationType to Foxglove type
        type_map = {
            PointsAnnotationType.UNKNOWN: FoxglovePointsAnnotationType.Unknown,
            PointsAnnotationType.POINTS: FoxglovePointsAnnotationType.Points,
            PointsAnnotationType.LINE_LOOP: FoxglovePointsAnnotationType.LineLoop,
            PointsAnnotationType.LINE_STRIP: FoxglovePointsAnnotationType.LineStrip,
            PointsAnnotationType.LINE_LIST: FoxglovePointsAnnotationType.LineList,
        }

        # Convert circles
        circles = [
            FoxgloveCircleAnnotation(
                timestamp=None,
                position=FoxglovePoint2(x=c.position.x, y=c.position.y),
                diameter=c.diameter,
                thickness=c.thickness,
                fill_color=FoxgloveColor(r=c.fill_color.r, g=c.fill_color.g, b=c.fill_color.b, a=c.fill_color.a),
                outline_color=FoxgloveColor(r=c.outline_color.r, g=c.outline_color.g, b=c.outline_color.b, a=c.outline_color.a),
            )
            for c in self.circles
        ]

        # Convert points annotations
        points = [
            FoxglovePointsAnnotation(
                timestamp=None,
                type=type_map[p.type],
                points=[FoxglovePoint2(x=pt.x, y=pt.y) for pt in p.points],
                outline_color=FoxgloveColor(r=p.outline_color.r, g=p.outline_color.g, b=p.outline_color.b, a=p.outline_color.a),
                outline_colors=[FoxgloveColor(r=c.r, g=c.g, b=c.b, a=c.a) for c in p.outline_colors] if p.outline_colors else [],
                fill_color=FoxgloveColor(r=p.fill_color.r, g=p.fill_color.g, b=p.fill_color.b, a=p.fill_color.a) if p.fill_color else None,
                thickness=p.thickness,
            )
            for p in self.points
        ]

        # Convert text annotations
        texts = [
            FoxgloveTextAnnotation(
                timestamp=None,
                position=FoxglovePoint2(x=t.position.x, y=t.position.y),
                text=t.text,
                font_size=t.font_size,
                text_color=FoxgloveColor(r=t.text_color.r, g=t.text_color.g, b=t.text_color.b, a=t.text_color.a),
                background_color=FoxgloveColor(
                    r=t.background_color.r, g=t.background_color.g, b=t.background_color.b, a=t.background_color.a
                ),
            )
            for t in self.texts
        ]

        return FoxgloveImageAnnotations(circles=circles, points=points, texts=texts)
