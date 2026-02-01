from pydantic import Field

from common.message.message import Message


class PirStatus(Message):
    """
    PIR sensor status containing detection state and signal information.

    Passive Infrared (PIR) sensors detect motion by measuring changes in
    infrared radiation in their field of view.

    Example:
        ```python
        from common.message import PirStatus

        # Create a PIR status
        status = PirStatus(
            is_detected=True,
            signal_strength=0.85,
            threshold=0.5,
        )

        # Check for motion
        if status.is_detected:
            print(f"Motion detected! Signal: {status.signal_strength}")
        ```
    """

    _type = "antioch/pir_status"
    is_detected: bool = Field(description="Whether motion is currently detected")
    signal_strength: float = Field(description="Analog signal strength [0.0, 1.0]")
    threshold: float = Field(description="Detection threshold [0.0, 1.0]")
