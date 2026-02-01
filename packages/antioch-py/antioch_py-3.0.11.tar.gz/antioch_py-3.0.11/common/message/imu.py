from pydantic import Field

from common.message.message import Message
from common.message.quaternion import Quaternion
from common.message.vector import Vector3


class ImuSample(Message):
    """
    IMU sensor sample data.

    Contains linear acceleration, angular velocity, and orientation from an
    inertial measurement unit sensor.

    Example:
        ```python
        from common.message import ImuSample, Vector3, Quaternion

        # Create an IMU sample
        sample = ImuSample(
            linear_acceleration=Vector3(x=0.0, y=0.0, z=9.81),  # Gravity
            angular_velocity=Vector3(x=0.01, y=0.0, z=0.0),
            orientation=Quaternion.identity(),
        )

        # Access acceleration components
        accel_z = sample.linear_acceleration.z
        ```
    """

    _type = "antioch/imu_sample"
    linear_acceleration: Vector3 = Field(description="Linear acceleration in m/s² (x, y, z)")
    angular_velocity: Vector3 = Field(description="Angular velocity in rad/s (x, y, z)")
    orientation: Quaternion = Field(description="Orientation as quaternion (w, x, y, z)")
