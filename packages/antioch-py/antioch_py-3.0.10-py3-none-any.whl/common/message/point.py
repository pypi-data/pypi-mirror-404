from __future__ import annotations

from foxglove.schemas import Point2 as FoxglovePoint2, Point3 as FoxglovePoint3
from pydantic import Field

from common.message.message import Message


class Point2(Message):
    """
    A point representing a position in 2D space.

    Used in image annotations and 2D coordinate systems.

    Example:
        ```python
        from common.message import Point2

        # Create a 2D point
        point = Point2(x=100.0, y=200.0)

        # Create using factory method
        origin = Point2.zero()

        # Convert to Foxglove for visualization
        foxglove_point = point.to_foxglove()
        ```
    """

    _type = "antioch/point2"
    x: float = Field(description="X coordinate")
    y: float = Field(description="Y coordinate")

    def __repr__(self) -> str:
        """
        Return a readable string representation.

        :return: String representation.
        """

        return f"Point2(x={self.x}, y={self.y})"

    def __str__(self) -> str:
        """
        Return a readable string representation.

        :return: String representation.
        """

        return f"Point2(x={self.x}, y={self.y})"

    @classmethod
    def new(cls, x: float, y: float) -> Point2:
        """
        Create a new 2D point.

        :param x: The x coordinate.
        :param y: The y coordinate.
        :return: A 2D point.
        """

        return cls(x=x, y=y)

    @classmethod
    def zero(cls) -> Point2:
        """
        Create a point at the origin.

        :return: A point at (0, 0).
        """

        return cls(x=0.0, y=0.0)

    def to_foxglove(self) -> FoxglovePoint2:
        """
        Convert to Foxglove Point2 for telemetry.

        :return: Foxglove Point2 schema.
        """

        return FoxglovePoint2(x=self.x, y=self.y)


class Point3(Message):
    """
    A point representing a position in 3D space.

    Used in 3D graphics and spatial coordinate systems.

    Example:
        ```python
        from common.message import Point3

        # Create a 3D point
        point = Point3(x=1.0, y=2.0, z=3.0)

        # Create at origin
        origin = Point3.zero()

        # Create using factory method
        p = Point3.new(x=0.5, y=1.0, z=0.0)
        ```
    """

    _type = "antioch/point3"
    x: float = Field(description="X coordinate")
    y: float = Field(description="Y coordinate")
    z: float = Field(description="Z coordinate")

    def __repr__(self) -> str:
        """
        Return a readable string representation.

        :return: String representation.
        """

        return f"Point3(x={self.x}, y={self.y}, z={self.z})"

    def __str__(self) -> str:
        """
        Return a readable string representation.

        :return: String representation.
        """

        return f"Point3(x={self.x}, y={self.y}, z={self.z})"

    @classmethod
    def new(cls, x: float, y: float, z: float) -> Point3:
        """
        Create a new 3D point.

        :param x: The x coordinate.
        :param y: The y coordinate.
        :param z: The z coordinate.
        :return: A 3D point.
        """

        return cls(x=x, y=y, z=z)

    @classmethod
    def zero(cls) -> Point3:
        """
        Create a point at the origin.

        :return: A point at (0, 0, 0).
        """

        return cls(x=0.0, y=0.0, z=0.0)

    def to_foxglove(self) -> FoxglovePoint3:
        """
        Convert to Foxglove Point3 for telemetry.

        :return: Foxglove Point3 schema.
        """

        return FoxglovePoint3(x=self.x, y=self.y, z=self.z)
