from __future__ import annotations

from foxglove.schemas import (
    FrameTransform as FoxgloveFrameTransform,
    FrameTransforms as FoxgloveFrameTransforms,
    Quaternion as FoxgloveQuaternion,
    Vector3 as FoxgloveVector3,
)
from pydantic import Field

from common.message.message import Message
from common.message.quaternion import Quaternion
from common.message.vector import Vector3


class FrameTransform(Message):
    """
    A transform between two reference frames in 3D space.

    Example:
        ```python
        from common.message import FrameTransform, Vector3, Quaternion

        # Create a transform from world to robot base
        transform = FrameTransform(
            parent_frame_id="world",
            child_frame_id="robot_base",
            translation=Vector3(x=1.0, y=0.0, z=0.0),
            rotation=Quaternion.identity(),
        )

        # Create an identity transform
        identity = FrameTransform.identity("parent", "child")
        ```
    """

    _type = "antioch/frame_transform"
    parent_frame_id: str = Field(description="Name of the parent frame")
    child_frame_id: str = Field(description="Name of the child frame")
    translation: Vector3 = Field(description="Translation component of the transform")
    rotation: Quaternion = Field(description="Rotation component of the transform")

    @classmethod
    def identity(cls, parent_frame_id: str, child_frame_id: str) -> FrameTransform:
        """
        Create an identity transform between two frames.

        :param parent_frame_id: Name of the parent frame.
        :param child_frame_id: Name of the child frame.
        :return: Identity frame transform.
        """

        return cls(
            parent_frame_id=parent_frame_id,
            child_frame_id=child_frame_id,
            translation=Vector3.zeros(),
            rotation=Quaternion.identity(),
        )

    def to_foxglove(self) -> FoxgloveFrameTransform:
        """
        Convert to Foxglove FrameTransform for telemetry.

        :return: Foxglove FrameTransform schema.
        """

        return FoxgloveFrameTransform(
            timestamp=None,
            parent_frame_id=self.parent_frame_id,
            child_frame_id=self.child_frame_id,
            translation=FoxgloveVector3(x=self.translation.x, y=self.translation.y, z=self.translation.z),
            rotation=FoxgloveQuaternion(x=self.rotation.x, y=self.rotation.y, z=self.rotation.z, w=self.rotation.w),
        )


class FrameTransforms(Message):
    """
    An array of FrameTransform messages.

    Example:
        ```python
        from common.message import FrameTransforms, FrameTransform, Vector3, Quaternion

        # Create a collection of transforms for a robot
        transforms = FrameTransforms(transforms=[
            FrameTransform(
                parent_frame_id="world",
                child_frame_id="base_link",
                translation=Vector3(x=0.0, y=0.0, z=0.1),
                rotation=Quaternion.identity(),
            ),
            FrameTransform(
                parent_frame_id="base_link",
                child_frame_id="camera",
                translation=Vector3(x=0.5, y=0.0, z=0.3),
                rotation=Quaternion.identity(),
            ),
        ])
        ```
    """

    _type = "antioch/frame_transforms"
    transforms: list[FrameTransform] = Field(default_factory=list, description="Array of transforms")

    def to_foxglove(self) -> FoxgloveFrameTransforms:
        """
        Convert to Foxglove FrameTransforms for telemetry.

        :return: Foxglove FrameTransforms schema.
        """

        return FoxgloveFrameTransforms(
            transforms=[t.to_foxglove() for t in self.transforms],
        )
