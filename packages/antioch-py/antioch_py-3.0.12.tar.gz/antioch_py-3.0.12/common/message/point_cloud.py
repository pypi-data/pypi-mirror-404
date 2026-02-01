import struct

from foxglove.schemas import (
    PackedElementField,
    PackedElementFieldNumericType as NumericType,
    PointCloud as FoxglovePointCloud,
    Pose as FoxglovePose,
    Quaternion as FoxgloveQuaternion,
    Vector3 as FoxgloveVector3,
)
from pydantic import Field, model_validator

from common.message.message import Message


class PointCloud(Message):
    """
    A collection of 3D points.

    Point clouds are used for representing 3D sensor data such as LiDAR
    scans or depth camera point clouds.

    Example:
        ```python
        from common.message import PointCloud

        # Create a point cloud
        cloud = PointCloud(
            frame_id="lidar_link",
            x=[1.0, 2.0, 3.0],
            y=[0.5, 1.0, 1.5],
            z=[0.1, 0.2, 0.3],
        )

        # Convert to Foxglove for visualization
        foxglove_cloud = cloud.to_foxglove()

        # Get packed bytes for transmission
        data = cloud.to_bytes()
        ```
    """

    _type = "antioch/point_cloud"
    frame_id: str = Field(default="", description="Frame of reference for the point cloud")
    x: list[float] = Field(description="X coordinates of points in meters")
    y: list[float] = Field(description="Y coordinates of points in meters")
    z: list[float] = Field(description="Z coordinates of points in meters")

    @model_validator(mode="after")
    def validate_array_lengths(self) -> "PointCloud":
        """
        Validate that all coordinate arrays have the same length.
        """

        lengths = [len(self.x), len(self.y), len(self.z)]

        if len(set(lengths)) > 1:
            raise ValueError(f"All coordinate arrays must have the same length: x={len(self.x)}, y={len(self.y)}, z={len(self.z)}")

        return self

    def to_bytes(self) -> bytes:
        """
        Pack point cloud data into bytes for Foxglove.

        :return: Packed data with x, y, z for each point.
        """

        data = bytearray()
        for i in range(len(self.x)):
            data.extend(struct.pack("<fff", self.x[i], self.y[i], self.z[i]))

        return bytes(data)

    def to_foxglove(self) -> FoxglovePointCloud:
        """
        Convert to Foxglove PointCloud for telemetry.

        :return: Foxglove PointCloud schema.
        """

        # Pack point data as interleaved x, y, z floats
        data = self.to_bytes()

        return FoxglovePointCloud(
            timestamp=None,
            frame_id=self.frame_id,
            pose=FoxglovePose(
                position=FoxgloveVector3(x=0, y=0, z=0),
                orientation=FoxgloveQuaternion(x=0, y=0, z=0, w=1),
            ),
            point_stride=12,  # 3 floats * 4 bytes
            fields=[
                PackedElementField(name="x", offset=0, type=NumericType.Float32),
                PackedElementField(name="y", offset=4, type=NumericType.Float32),
                PackedElementField(name="z", offset=8, type=NumericType.Float32),
            ],
            data=data,
        )
