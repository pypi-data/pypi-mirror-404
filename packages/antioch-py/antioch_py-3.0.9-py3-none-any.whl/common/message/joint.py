from pydantic import Field

from common.message.message import Message


class JointState(Message):
    """
    State of a single joint.

    Represents the complete physical state of a joint including its position,
    velocity, and measured effort (force/torque).

    Example:
        ```python
        from common.message import JointState

        # Create a joint state
        state = JointState(
            name="shoulder_pan",
            position=1.57,
            velocity=0.1,
            effort=5.0,
        )
        print(f"{state.name}: pos={state.position:.2f} rad")
        ```
    """

    _type = "antioch/joint_state"
    name: str = Field(description="Name of the joint")
    position: float = Field(description="Joint position in radians")
    velocity: float = Field(description="Joint velocity in radians per second")
    effort: float = Field(description="Joint effort (force/torque) in Nm")


class JointTarget(Message):
    """
    Control target for a single joint.

    Specifies desired position, velocity, and/or effort targets for a joint's
    PD controller. The name field is required to identify which joint is being
    targeted. Position, velocity, and effort are optional - omitted values are
    not controlled.

    Example:
        ```python
        from common.message import JointTarget

        # Position control target
        target = JointTarget(name="elbow", position=0.5)

        # Velocity control target
        vel_target = JointTarget(name="wrist", velocity=0.2)

        # Combined position and velocity target
        combined = JointTarget(name="shoulder", position=1.0, velocity=0.1)
        ```
    """

    _type = "antioch/joint_target"
    name: str = Field(description="Name of the joint to control")
    position: float | None = Field(default=None, description="Target position in radians")
    velocity: float | None = Field(default=None, description="Target velocity in radians per second")
    effort: float | None = Field(default=None, description="Target effort (force/torque) in Nm")


class JointStates(Message):
    """
    Collection of joint states for an actuator group.

    Example:
        ```python
        from common.message import JointStates, JointState

        # Create states for a robot arm
        states = JointStates(states=[
            JointState(name="joint1", position=0.0, velocity=0.0, effort=0.0),
            JointState(name="joint2", position=1.57, velocity=0.1, effort=2.5),
        ])

        for state in states.states:
            print(f"{state.name}: {state.position:.2f} rad")
        ```
    """

    _type = "antioch/joint_states"
    states: list[JointState] = Field(description="List of joint states")


class JointTargets(Message):
    """
    Collection of joint targets for an actuator group.

    Example:
        ```python
        from common.message import JointTargets, JointTarget

        # Create targets for multiple joints
        targets = JointTargets(targets=[
            JointTarget(name="joint1", position=0.5),
            JointTarget(name="joint2", position=1.0),
        ])
        ```
    """

    _type = "antioch/joint_targets"
    targets: list[JointTarget] = Field(description="List of joint targets")
