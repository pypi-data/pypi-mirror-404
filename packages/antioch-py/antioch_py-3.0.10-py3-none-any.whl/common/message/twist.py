from pydantic import Field

from common.message.message import Message
from common.message.vector import Vector3


class Twist(Message):
    """
    Linear and angular velocity (twist).

    Represents the velocity of a rigid body in 3D space, combining both
    linear velocity (translation) and angular velocity (rotation).

    Example:
        ```python
        from common.message import Twist, Vector3

        # Create a twist for forward motion with rotation
        twist = Twist(
            linear=Vector3(x=1.0, y=0.0, z=0.0),  # 1 m/s forward
            angular=Vector3(x=0.0, y=0.0, z=0.1),  # 0.1 rad/s yaw
        )

        # Zero velocity
        stationary = Twist(
            linear=Vector3.zeros(),
            angular=Vector3.zeros(),
        )
        ```
    """

    _type = "antioch/twist"
    linear: Vector3 = Field(description="Linear velocity in m/s (x, y, z)")
    angular: Vector3 = Field(description="Angular velocity in rad/s (x, y, z)")
