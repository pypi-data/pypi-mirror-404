from __future__ import annotations

from typing import Any

import numpy as np
from foxglove.schemas import Pose as FoxglovePose, Quaternion as FoxgloveQuaternion, Vector3 as FoxgloveVector3
from pydantic import Field, field_validator, model_validator

from common.message.message import Message
from common.message.vector import Vector3


class Pose(Message):
    """
    A pose representing position and orientation in 3D space.

    Serializes position as [x, y, z] and orientation as [roll, pitch, yaw] in radians.
    Orientation is stored as RPY (Roll-Pitch-Yaw) Euler angles.

    Automatically converts from common Python types:
    - Lists/tuples: Pose(position=[1.0, 2.0, 3.0], orientation=[0.0, 0.0, 1.57])
    - Dicts: Pose(position={"x": 1.0, "y": 2.0, "z": 3.0}, orientation={"x": 0.0, "y": 0.0, "z": 1.57})

    Example:
        ```python
        from common.message import Pose, Vector3

        # Create a pose with position and orientation
        pose = Pose(
            position=[1.0, 2.0, 0.5],
            orientation=[0.0, 0.0, 1.57],  # 90 degrees yaw
        )

        # Create from identity
        identity = Pose.identity()

        # Translate a pose
        translated = pose.translate(Vector3(x=1.0, y=0.0, z=0.0))

        # Access position components
        print(f"Position: ({pose.position.x}, {pose.position.y}, {pose.position.z})")
        ```
    """

    _type = "antioch/pose"
    position: Vector3 = Field(default_factory=lambda: Vector3.zeros(), description="Position in 3D space as (x, y, z)")
    orientation: Vector3 = Field(default_factory=lambda: Vector3.zeros(), description="Orientation as (roll, pitch, yaw) in radians")

    def __add__(self, other: Vector3) -> Pose:
        """
        Translate the pose by a vector (adds to position).

        :param other: A Vector3 representing the translation.
        :return: The translated pose.
        """

        return Pose(position=self.position + other, orientation=self.orientation)

    def __sub__(self, other: Vector3) -> Pose:
        """
        Translate the pose by a negative vector (subtracts from position).

        :param other: A Vector3 representing the translation.
        :return: The translated pose.
        """

        return Pose(position=self.position - other, orientation=self.orientation)

    @model_validator(mode="before")
    @classmethod
    def convert_nested_types(cls, data: Any) -> Any:
        """
        Allow passing position and orientation as lists/tuples that auto-convert to Vector3/Quaternion.
        Orientation can be 3 values (RPY) or 4 values (quaternion) - always stored as quaternion.
        """

        # Already a Pose instance
        if isinstance(data, cls):
            return data.model_dump()

        # Dict format - let Pydantic and nested validators handle it
        if isinstance(data, dict):
            return data

        return data

    @field_validator("position", mode="before")
    @classmethod
    def validate_position(cls, v: Any) -> Any:
        """
        Convert position from list/tuple/array to Vector3 format before type validation.
        """

        if isinstance(v, (list, tuple, np.ndarray)):
            return Vector3._convert_input.__func__(Vector3, v)
        return v

    @field_validator("orientation", mode="before")
    @classmethod
    def validate_orientation(cls, v: Any) -> Any:
        """
        Convert orientation from list/tuple/array to Vector3 format before type validation.
        """

        if isinstance(v, (list, tuple, np.ndarray)):
            return Vector3._convert_input.__func__(Vector3, v)
        return v

    @classmethod
    def from_any(cls, value: Pose | dict | tuple | list | None) -> Pose:
        """
        Create Pose from any compatible type.

        Accepts:
        - Pose instance (returned as-is)
        - Dict with 'position' and/or 'orientation' keys
        - Tuple/list of 3 floats (treated as position only)
        - None (returns identity pose)

        :param value: Any compatible input type.
        :return: A Pose instance.
        """

        if value is None:
            return cls.identity()
        if isinstance(value, cls):
            return value
        if isinstance(value, dict):
            return cls.model_validate(value)
        if isinstance(value, (tuple, list)):
            # Treat as position only
            return cls(position=Vector3.from_any(value))
        raise ValueError(f"Cannot convert {type(value).__name__} to Pose")

    @classmethod
    def identity(cls) -> Pose:
        """
        Create an identity pose at origin with zero rotation.

        :return: Identity pose.
        """

        return cls(position=Vector3.zeros(), orientation=Vector3.zeros())

    @classmethod
    def from_position(cls, position: Vector3) -> Pose:
        """
        Create a pose from a position with zero rotation.

        :param position: The position.
        :return: The pose.
        """

        return cls(position=position, orientation=Vector3.zeros())

    def translate(self, offset: Vector3) -> Pose:
        """
        Create a new pose with the position translated by an offset.

        :param offset: The translation offset.
        :return: The translated pose.
        """

        return Pose(position=self.position + offset, orientation=self.orientation)

    def rotate(self, rotation: Vector3) -> Pose:
        """
        Create a new pose with additional rotation (in RPY).

        :param rotation: Additional rotation in Roll-Pitch-Yaw.
        :return: The rotated pose.
        """

        return Pose(position=self.position, orientation=self.orientation + rotation)

    def to_foxglove(self) -> FoxglovePose:
        """
        Convert to Foxglove Pose for telemetry.

        :return: Foxglove Pose schema.
        """

        # Convert RPY orientation to quaternion for Foxglove
        quat = self.orientation.to_quat()
        return FoxglovePose(
            position=FoxgloveVector3(x=self.position.x, y=self.position.y, z=self.position.z),
            orientation=FoxgloveQuaternion(x=quat.x, y=quat.y, z=quat.z, w=quat.w),
        )
