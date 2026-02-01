from __future__ import annotations

from typing import Any

import numpy as np
from foxglove.schemas import Vector2 as FoxgloveVector2, Vector3 as FoxgloveVector3
from pydantic import Field, model_validator

from common.message.message import Message
from common.message.point import Point2, Point3
from common.message.quaternion import Quaternion

try:
    from pxr import Gf  # type: ignore

    HAS_PXR = True
except ImportError:
    HAS_PXR = False


class Vector2(Message):
    """
    A 2D vector (x, y).

    Supports multiple construction styles:
    - Vector2(x=1.0, y=2.0) - keyword args
    - Vector2.from_any([1.0, 2.0]) - from list/tuple
    - Vector2.from_any((1.0, 2.0)) - from tuple

    Example:
        ```python
        from common.message import Vector2

        # Create a 2D vector
        v = Vector2(x=3.0, y=4.0)

        # Vector operations
        magnitude = v.magnitude()  # 5.0
        normalized = v.normalize()

        # Arithmetic operations
        v2 = Vector2(x=1.0, y=2.0)
        sum_v = v + v2
        scaled = v * 2.0
        ```
    """

    _type = "antioch/vector2"
    x: float = Field(default=0.0, description="X component")
    y: float = Field(default=0.0, description="Y component")

    def __len__(self) -> int:
        """
        Get the length of the vector (always 2).

        :return: The length of the vector.
        """

        return 2

    def __iter__(self):
        """
        Iterate over vector components.

        :return: Iterator over [x, y].
        """

        return iter((self.x, self.y))

    def __getitem__(self, index: int) -> float:
        """
        Get vector component by index.

        :param index: Index (0=x, 1=y).
        :return: The component value.
        """

        return (self.x, self.y)[index]

    def __eq__(self, other: object) -> bool:
        """
        Check equality with another Vector2.

        :param other: Another Vector2.
        :return: True if equal.
        """

        if not isinstance(other, Vector2):
            return False
        return self.x == other.x and self.y == other.y

    def __repr__(self) -> str:
        """
        Return a readable string representation.

        :return: String representation.
        """

        return f"Vector2({self.x}, {self.y})"

    def __str__(self) -> str:
        """
        Return a readable string representation.

        :return: String representation.
        """

        return f"Vector2({self.x}, {self.y})"

    def __add__(self, other: Vector2) -> Vector2:
        """
        Add two vectors component-wise.

        :param other: Another Vector2.
        :return: The sum vector.
        """

        return Vector2(x=self.x + other.x, y=self.y + other.y)

    def __sub__(self, other: Vector2) -> Vector2:
        """
        Subtract two vectors component-wise.

        :param other: Another Vector2.
        :return: The difference vector.
        """

        return Vector2(x=self.x - other.x, y=self.y - other.y)

    def __mul__(self, scalar: float) -> Vector2:
        """
        Multiply vector by a scalar.

        :param scalar: The scalar value.
        :return: The scaled vector.
        """

        return Vector2(x=self.x * scalar, y=self.y * scalar)

    def __rmul__(self, scalar: float) -> Vector2:
        """
        Multiply vector by a scalar (reversed operands).

        :param scalar: The scalar value.
        :return: The scaled vector.
        """

        return self.__mul__(scalar)

    def __truediv__(self, scalar: float) -> Vector2:
        """
        Divide vector by a scalar.

        :param scalar: The scalar value.
        :return: The scaled vector.
        :raises ZeroDivisionError: If scalar is zero.
        """

        if scalar == 0:
            raise ZeroDivisionError("Cannot divide vector by zero")
        return Vector2(x=self.x / scalar, y=self.y / scalar)

    def __neg__(self) -> Vector2:
        """
        Negate the vector.

        :return: The negated vector.
        """

        return Vector2(x=-self.x, y=-self.y)

    @classmethod
    def zeros(cls) -> Vector2:
        """
        Create a zero vector.

        :return: A zero vector.
        """

        return cls(x=0.0, y=0.0)

    @classmethod
    def ones(cls) -> Vector2:
        """
        Create a ones vector.

        :return: A ones vector.
        """

        return cls(x=1.0, y=1.0)

    @classmethod
    def from_any(cls, value: Vector2 | tuple | list | dict | np.ndarray | None) -> Vector2:
        """
        Create Vector2 from any compatible type.

        Accepts:
        - Vector2 instance (returned as-is)
        - Tuple/list of 2 floats: (x, y)
        - Dict with 'x' and 'y' keys
        - Numpy array of shape (2,)
        - None (returns zero vector)

        :param value: Any compatible input type.
        :return: A Vector2 instance.
        """

        if value is None:
            return cls(x=0.0, y=0.0)
        if isinstance(value, cls):
            return value
        return cls.model_validate(value)

    @classmethod
    def from_numpy(cls, array: np.ndarray) -> Vector2:
        """
        Create from a numpy array.

        :param array: The numpy array (must have shape (2,)).
        :return: A Vector2.
        :raises ValueError: If array shape is not (2,).
        """

        if array.shape != (2,):
            raise ValueError(f"Vector2 array must have shape (2,), got {array.shape}")
        return cls(x=float(array[0]), y=float(array[1]))

    @classmethod
    def from_list(cls, values: list[float]) -> Vector2:
        """
        Create from a list of 2 values.

        :param values: List of 2 float values.
        :return: A Vector2.
        :raises ValueError: If list does not have exactly 2 values.
        """

        if len(values) != 2:
            raise ValueError(f"Vector2 requires 2 values, got {len(values)}")
        return cls(x=values[0], y=values[1])

    def dot(self, other: Vector2) -> float:
        """
        Compute dot product with another vector.

        :param other: Another Vector2.
        :return: The dot product.
        """

        return self.x * other.x + self.y * other.y

    def magnitude(self) -> float:
        """
        Compute the magnitude (length) of the vector.

        :return: The magnitude.
        """

        return (self.x**2 + self.y**2) ** 0.5

    def magnitude_squared(self) -> float:
        """
        Compute the squared magnitude of the vector.

        :return: The squared magnitude.
        """

        return self.x**2 + self.y**2

    def normalize(self) -> Vector2:
        """
        Return a normalized (unit length) version of this vector.

        :return: The normalized vector.
        :raises ValueError: If the vector has zero magnitude.
        """

        mag = self.magnitude()
        if mag == 0:
            raise ValueError("Cannot normalize zero vector")
        return self / mag

    def to_numpy(self) -> np.ndarray:
        """
        Convert to a numpy array.

        :return: The numpy array.
        """

        return np.array([self.x, self.y], dtype=np.float32)

    def to_list(self) -> list[float]:
        """
        Convert to a list.

        :return: The list of values.
        """

        return [self.x, self.y]

    def to_tuple(self) -> tuple[float, float]:
        """
        Convert to a tuple.

        :return: The tuple of values.
        """

        return (self.x, self.y)

    def to_point(self) -> Point2:
        """
        Convert to a Point2.

        :return: A Point2 with the same x, y coordinates.
        """

        return Point2(x=self.x, y=self.y)

    def to_foxglove(self) -> FoxgloveVector2:
        """
        Convert to Foxglove Vector2 for telemetry.

        :return: Foxglove Vector2 schema.
        """

        return FoxgloveVector2(x=self.x, y=self.y)

    @model_validator(mode="before")
    @classmethod
    def _convert_input(cls, data: Any) -> Any:
        """
        Convert various input types to Vector2 format.
        """

        if isinstance(data, cls):
            return {"x": data.x, "y": data.y}
        if isinstance(data, (tuple, list)) and len(data) == 2:
            return {"x": float(data[0]), "y": float(data[1])}
        if isinstance(data, np.ndarray) and data.shape == (2,):
            return {"x": float(data[0]), "y": float(data[1])}
        if isinstance(data, dict) and "x" in data and "y" in data:
            return {"x": float(data["x"]), "y": float(data["y"])}
        return data


class Vector3(Message):
    """
    A 3D vector (x, y, z).

    Supports multiple construction styles:
    - Vector3(x=1.0, y=2.0, z=3.0) - keyword args
    - Vector3.from_any([1.0, 2.0, 3.0]) - from list
    - Vector3.from_any((1.0, 2.0, 3.0)) - from tuple

    Example:
        ```python
        from common.message import Vector3

        # Create a 3D vector
        v = Vector3(x=1.0, y=2.0, z=3.0)

        # Vector operations
        magnitude = v.magnitude()
        normalized = v.normalize()

        # Cross and dot products
        v2 = Vector3(x=0.0, y=1.0, z=0.0)
        cross = v.cross(v2)
        dot = v.dot(v2)

        # Convert to numpy
        arr = v.to_numpy()
        ```
    """

    _type = "antioch/vector3"
    x: float = Field(default=0.0, description="X component")
    y: float = Field(default=0.0, description="Y component")
    z: float = Field(default=0.0, description="Z component")

    def __len__(self) -> int:
        """
        Get the length of the vector (always 3).

        :return: The length of the vector.
        """

        return 3

    def __iter__(self):
        """
        Iterate over vector components.

        :return: Iterator over [x, y, z].
        """

        return iter((self.x, self.y, self.z))

    def __getitem__(self, index: int) -> float:
        """
        Get vector component by index.

        :param index: Index (0=x, 1=y, 2=z).
        :return: The component value.
        """

        return (self.x, self.y, self.z)[index]

    def __eq__(self, other: object) -> bool:
        """
        Check equality with another Vector3.

        :param other: Another Vector3.
        :return: True if equal.
        """

        if not isinstance(other, Vector3):
            return False
        return self.x == other.x and self.y == other.y and self.z == other.z

    def __repr__(self) -> str:
        """
        Return a readable string representation.

        :return: String representation.
        """

        return f"Vector3({self.x}, {self.y}, {self.z})"

    def __str__(self) -> str:
        """
        Return a readable string representation.

        :return: String representation.
        """

        return f"Vector3({self.x}, {self.y}, {self.z})"

    def __add__(self, other: Vector3) -> Vector3:
        """
        Add two vectors component-wise.

        :param other: Another Vector3.
        :return: The sum vector.
        """

        return Vector3(x=self.x + other.x, y=self.y + other.y, z=self.z + other.z)

    def __sub__(self, other: Vector3) -> Vector3:
        """
        Subtract two vectors component-wise.

        :param other: Another Vector3.
        :return: The difference vector.
        """

        return Vector3(x=self.x - other.x, y=self.y - other.y, z=self.z - other.z)

    def __mul__(self, scalar: float) -> Vector3:
        """
        Multiply vector by a scalar.

        :param scalar: The scalar value.
        :return: The scaled vector.
        """

        return Vector3(x=self.x * scalar, y=self.y * scalar, z=self.z * scalar)

    def __rmul__(self, scalar: float) -> Vector3:
        """
        Multiply vector by a scalar (reversed operands).

        :param scalar: The scalar value.
        :return: The scaled vector.
        """

        return self.__mul__(scalar)

    def __truediv__(self, scalar: float) -> Vector3:
        """
        Divide vector by a scalar.

        :param scalar: The scalar value.
        :return: The scaled vector.
        :raises ZeroDivisionError: If scalar is zero.
        """

        if scalar == 0:
            raise ZeroDivisionError("Cannot divide vector by zero")
        return Vector3(x=self.x / scalar, y=self.y / scalar, z=self.z / scalar)

    def __neg__(self) -> Vector3:
        """
        Negate the vector.

        :return: The negated vector.
        """

        return Vector3(x=-self.x, y=-self.y, z=-self.z)

    @classmethod
    def zeros(cls) -> Vector3:
        """
        Create a zero vector.

        :return: A zero vector.
        """

        return cls(x=0.0, y=0.0, z=0.0)

    @classmethod
    def ones(cls) -> Vector3:
        """
        Create a ones vector.

        :return: A ones vector.
        """

        return cls(x=1.0, y=1.0, z=1.0)

    @classmethod
    def from_any(cls, value: Vector3 | tuple | list | dict | np.ndarray | None) -> Vector3:
        """
        Create Vector3 from any compatible type.

        Accepts:
        - Vector3 instance (returned as-is)
        - Tuple/list of 3 floats: (x, y, z)
        - Dict with 'x', 'y', and 'z' keys
        - Numpy array of shape (3,)
        - None (returns zero vector)

        :param value: Any compatible input type.
        :return: A Vector3 instance.
        """

        if value is None:
            return cls(x=0.0, y=0.0, z=0.0)
        if isinstance(value, cls):
            return value
        return cls.model_validate(value)

    @classmethod
    def from_numpy(cls, array: np.ndarray) -> Vector3:
        """
        Create from a numpy array.

        :param array: The numpy array (must have shape (3,)).
        :return: A Vector3.
        :raises ValueError: If array shape is not (3,).
        """

        if array.shape != (3,):
            raise ValueError(f"Vector3 array must have shape (3,), got {array.shape}")
        return cls(x=float(array[0]), y=float(array[1]), z=float(array[2]))

    @classmethod
    def from_list(cls, values: list[float]) -> Vector3:
        """
        Create from a list of 3 values.

        :param values: List of 3 float values.
        :return: A Vector3.
        :raises ValueError: If list does not have exactly 3 values.
        """

        if len(values) != 3:
            raise ValueError(f"Vector3 requires 3 values, got {len(values)}")
        return cls(x=values[0], y=values[1], z=values[2])

    def dot(self, other: Vector3) -> float:
        """
        Compute dot product with another vector.

        :param other: Another Vector3.
        :return: The dot product.
        """

        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other: Vector3) -> Vector3:
        """
        Compute cross product with another vector.

        :param other: Another Vector3.
        :return: The cross product vector.
        """

        return Vector3(
            x=self.y * other.z - self.z * other.y,
            y=self.z * other.x - self.x * other.z,
            z=self.x * other.y - self.y * other.x,
        )

    def magnitude(self) -> float:
        """
        Compute the magnitude (length) of the vector.

        :return: The magnitude.
        """

        return (self.x**2 + self.y**2 + self.z**2) ** 0.5

    def magnitude_squared(self) -> float:
        """
        Compute the squared magnitude of the vector.

        :return: The squared magnitude.
        """

        return self.x**2 + self.y**2 + self.z**2

    def normalize(self) -> Vector3:
        """
        Return a normalized (unit length) version of this vector.

        :return: The normalized vector.
        :raises ValueError: If the vector has zero magnitude.
        """

        mag = self.magnitude()
        if mag == 0:
            raise ValueError("Cannot normalize zero vector")
        return self / mag

    def to_numpy(self) -> np.ndarray:
        """
        Convert to a numpy array.

        :return: The numpy array.
        """

        return np.array([self.x, self.y, self.z], dtype=np.float32)

    def to_list(self) -> list[float]:
        """
        Convert to a list.

        :return: The list of values.
        """

        return [self.x, self.y, self.z]

    def to_tuple(self) -> tuple[float, float, float]:
        """
        Convert to a tuple.

        :return: The tuple of values.
        """

        return (self.x, self.y, self.z)

    def to_gf_vec3f(self) -> Gf.Vec3f:
        """
        Convert to a Gf.Vec3f.

        :return: The Gf.Vec3f.
        :raises ImportError: If pxr is not installed.
        """

        from pxr import Gf

        return Gf.Vec3f(self.x, self.y, self.z)

    def to_gf_vec3d(self) -> Gf.Vec3d:
        """
        Convert to a Gf.Vec3d (double precision).

        :return: The Gf.Vec3d.
        :raises ImportError: If pxr is not installed.
        """

        from pxr import Gf

        return Gf.Vec3d(self.x, self.y, self.z)

    def to_quat(self) -> Quaternion:
        """
        Convert RPY angles to quaternion.

        Assumes this Vector3 contains roll-pitch-yaw angles in radians.

        :return: Quaternion representation.
        """

        return Quaternion.from_rpy(self.x, self.y, self.z)

    def to_point(self) -> Point3:
        """
        Convert to a Point3.

        :return: A Point3 with the same x, y, z coordinates.
        """

        return Point3(x=self.x, y=self.y, z=self.z)

    def to_foxglove(self) -> FoxgloveVector3:
        """
        Convert to Foxglove Vector3 for telemetry.

        :return: Foxglove Vector3 schema.
        """

        return FoxgloveVector3(x=self.x, y=self.y, z=self.z)

    @model_validator(mode="before")
    @classmethod
    def _convert_input(cls, data: Any) -> Any:
        """
        Convert various input types to Vector3 format.
        """

        if isinstance(data, cls):
            return {"x": data.x, "y": data.y, "z": data.z}
        if isinstance(data, (tuple, list)) and len(data) == 3:
            return {"x": float(data[0]), "y": float(data[1]), "z": float(data[2])}
        if isinstance(data, np.ndarray) and data.shape == (3,):
            return {"x": float(data[0]), "y": float(data[1]), "z": float(data[2])}
        if isinstance(data, dict) and "x" in data and "y" in data and "z" in data:
            return {"x": float(data["x"]), "y": float(data["y"]), "z": float(data["z"])}
        return data
