from __future__ import annotations

from typing import Any

from pydantic import Field

from common.message.message import Message


class DetectionDistances(Message):
    """
    Detection distances for Foxglove range-time plotting.

    In Foxglove Plot panel, use Y = .distances[:] to see detections over time.

    Example:
        ```python
        from common.message import DetectionDistances

        # Detections at 3.5m and 4.5m
        detections = DetectionDistances(distances=[3.5, 4.5])
        sim.logger.telemetry("radar/detections/combined", detections)
        ```
    """

    _type = "antioch/detection_distances"

    distances: list[float] = Field(
        default_factory=list,
        description="Distances where detections occurred",
    )

    def to_foxglove(self) -> dict[str, Any]:
        """
        Convert to Foxglove-compatible dict.

        :return: Dict with distances array.
        """

        return {"distances": self.distances}
