from __future__ import annotations

from typing import Any

import numpy as np
from foxglove.schemas import Quaternion as FoxgloveQuaternion
from pydantic import Field, model_validator
from scipy.spatial.transform import Rotation

from common.message.message import Message

try:
    from pxr import Gf  # type: ignore

    HAS_PXR = True
except ImportError:
    HAS_PXR = False


class Quaternion(Message):
    """
    A quaternion for 3D rotations (w, x, y, z) where w is the scalar component.

    Supports multiple construction styles:
    - Quaternion(w=1.0, x=0.0, y=0.0, z=0.0) - keyword args
    - Quaternion.from_rpy(roll, pitch, yaw) - from euler angles
    - Quaternion.from_any([1.0, 0.0, 0.0, 0.0]) - from list/tuple

    Example:
        ```python
        from common.message import Quaternion
        import math

        # Create identity quaternion (no rotation)
        identity = Quaternion.identity()

        # Create from roll-pitch-yaw angles
        quat = Quaternion.from_rpy(
            roll=0.0,
            pitch=0.0,
            yaw=math.pi / 2,  # 90 degrees
        )

        # Convert back to RPY
        roll, pitch, yaw = quat.to_rpy()

        # Create from list (w, x, y, z order)
        q = Quaternion.from_any([1.0, 0.0, 0.0, 0.0])
        ```
    """

    _type = "antioch/quaternion"
    w: float = Field(default=1.0, description="Scalar (real) component of the quaternion")
    x: float = Field(default=0.0, description="X component of the quaternion vector part")
    y: float = Field(default=0.0, description="Y component of the quaternion vector part")
    z: float = Field(default=0.0, description="Z component of the quaternion vector part")

    def __len__(self) -> int:
        """
        Get the length of the quaternion (always 4).

        :return: The length of the quaternion.
        """

        return 4

    def __iter__(self):
        """
        Iterate over quaternion components.

        :return: Iterator over [w, x, y, z].
        """

        return iter((self.w, self.x, self.y, self.z))

    def __getitem__(self, index: int) -> float:
        """
        Get quaternion component by index.

        :param index: Index (0=w, 1=x, 2=y, 3=z).
        :return: The component value.
        """

        return (self.w, self.x, self.y, self.z)[index]

    def __eq__(self, other: object) -> bool:
        """
        Check equality with another Quaternion.

        :param other: Another Quaternion.
        :return: True if equal.
        """

        if not isinstance(other, Quaternion):
            return False
        return self.w == other.w and self.x == other.x and self.y == other.y and self.z == other.z

    def __repr__(self) -> str:
        """
        Return a readable string representation.

        :return: String representation.
        """

        return f"Quaternion({self.w}, {self.x}, {self.y}, {self.z})"

    def __str__(self) -> str:
        """
        Return a readable string representation.

        :return: String representation.
        """

        return f"Quaternion({self.w}, {self.x}, {self.y}, {self.z})"

    @classmethod
    def identity(cls) -> Quaternion:
        """
        Create an identity quaternion (no rotation).

        :return: An identity quaternion [1, 0, 0, 0].
        """

        return cls(w=1.0, x=0.0, y=0.0, z=0.0)

    @classmethod
    def from_any(cls, value: Quaternion | tuple | list | dict | np.ndarray | None) -> Quaternion:
        """
        Create Quaternion from any compatible type.

        Accepts:
        - Quaternion instance (returned as-is)
        - Tuple/list of 4 floats: (w, x, y, z)
        - Dict with 'w', 'x', 'y', and 'z' keys
        - Numpy array of shape (4,)
        - None (returns identity quaternion)

        :param value: Any compatible input type.
        :return: A Quaternion instance.
        """

        if value is None:
            return cls.identity()
        if isinstance(value, cls):
            return value
        return cls.model_validate(value)

    @classmethod
    def from_numpy(cls, array: np.ndarray) -> Quaternion:
        """
        Create a quaternion from a numpy array [w, x, y, z].

        :param array: The numpy array (must have 4 elements).
        :return: A quaternion.
        :raises ValueError: If the array does not have exactly 4 elements.
        """

        if array.shape != (4,):
            raise ValueError(f"Quaternion array must have shape (4,), got {array.shape}")
        return cls(w=float(array[0]), x=float(array[1]), y=float(array[2]), z=float(array[3]))

    @classmethod
    def from_rpy(cls, roll: float, pitch: float, yaw: float) -> Quaternion:
        """
        Create a quaternion from roll-pitch-yaw angles (in radians).

        :param roll: Roll angle in radians (rotation around x-axis).
        :param pitch: Pitch angle in radians (rotation around y-axis).
        :param yaw: Yaw angle in radians (rotation around z-axis).
        :return: A quaternion.
        """

        rotation = Rotation.from_euler("XYZ", [roll, pitch, yaw])
        quat_xyzw = rotation.as_quat()
        return cls(w=float(quat_xyzw[3]), x=float(quat_xyzw[0]), y=float(quat_xyzw[1]), z=float(quat_xyzw[2]))

    def to_numpy(self) -> np.ndarray:
        """
        Convert the quaternion to a numpy array.

        :return: The numpy array [w, x, y, z].
        """

        return np.array([self.w, self.x, self.y, self.z], dtype=np.float32)

    def to_list(self) -> list[float]:
        """
        Convert the quaternion to a list.

        :return: The list [w, x, y, z].
        """

        return [self.w, self.x, self.y, self.z]

    def to_tuple(self) -> tuple[float, float, float, float]:
        """
        Convert the quaternion to a tuple.

        :return: The tuple (w, x, y, z).
        """

        return (self.w, self.x, self.y, self.z)

    def to_gf_quatf(self) -> Gf.Quatf:
        """
        Convert the quaternion to a Gf.Quatf.

        Note: Gf.Quatf expects (w, x, y, z) order.

        :return: The Gf.Quatf.
        :raises ImportError: If pxr is not installed.
        """

        from pxr import Gf

        return Gf.Quatf(self.w, self.x, self.y, self.z)

    def to_gf_quatd(self) -> Gf.Quatd:
        """
        Convert the quaternion to a Gf.Quatd (double precision).

        Note: Gf.Quatd expects (w, x, y, z) order.

        :return: The Gf.Quatd.
        :raises ImportError: If pxr is not installed.
        """

        from pxr import Gf

        return Gf.Quatd(self.w, self.x, self.y, self.z)

    def normalize(self) -> Quaternion:
        """
        Return a normalized version of this quaternion.

        :return: A normalized quaternion.
        """

        arr = self.to_numpy()
        norm = np.linalg.norm(arr)
        if norm > 0:
            normalized = arr / norm
            return Quaternion(
                w=float(normalized[0]),
                x=float(normalized[1]),
                y=float(normalized[2]),
                z=float(normalized[3]),
            )
        return self.identity()

    def to_rpy(self) -> tuple[float, float, float]:
        """
        Convert the quaternion to roll-pitch-yaw angles (in radians).

        :return: A tuple of (roll, pitch, yaw) angles in radians.
        """

        rotation = Rotation.from_quat([self.x, self.y, self.z, self.w])
        rpy = rotation.as_euler("xyz")
        return (float(rpy[0]), float(rpy[1]), float(rpy[2]))

    def to_foxglove(self) -> FoxgloveQuaternion:
        """
        Convert to Foxglove Quaternion for telemetry.

        :return: Foxglove Quaternion schema.
        """

        return FoxgloveQuaternion(x=self.x, y=self.y, z=self.z, w=self.w)

    @model_validator(mode="before")
    @classmethod
    def _convert_input(cls, data: Any) -> Any:
        """
        Convert various input types to Quaternion format.
        """

        if isinstance(data, cls):
            return {"w": data.w, "x": data.x, "y": data.y, "z": data.z}
        if isinstance(data, (tuple, list)) and len(data) == 4:
            return {"w": float(data[0]), "x": float(data[1]), "y": float(data[2]), "z": float(data[3])}
        if isinstance(data, np.ndarray) and data.shape == (4,):
            return {"w": float(data[0]), "x": float(data[1]), "y": float(data[2]), "z": float(data[3])}
        if isinstance(data, dict) and all(k in data for k in ("w", "x", "y", "z")):
            return {"w": float(data["w"]), "x": float(data["x"]), "y": float(data["y"]), "z": float(data["z"])}
        return data
