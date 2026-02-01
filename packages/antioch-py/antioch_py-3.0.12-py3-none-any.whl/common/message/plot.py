from __future__ import annotations

from typing import Any

from pydantic import Field

from common.message.message import Message


class PlotData(Message):
    """
    Simple X/Y plot data for Foxglove visualization.

    Use with Foxglove's Plot panel by selecting:
    - X: .x[:]
    - Y: .y[:]

    Example:
        ```python
        from common.message import PlotData
        import numpy as np

        distances = np.linspace(0, 10, 128)
        values = np.random.rand(128)

        plot = PlotData.from_arrays(distances, values)
        sim.logger.telemetry("radar/mti/radar_left", plot)
        ```
    """

    _type = "antioch/plot_data"

    x: list[float] = Field(default_factory=list, description="X-axis values")
    y: list[float] = Field(default_factory=list, description="Y-axis values")

    @classmethod
    def from_arrays(cls, x: Any, y: Any) -> PlotData:
        """
        Create PlotData from arrays or lists.

        :param x: X values (numpy array or list).
        :param y: Y values (numpy array or list).
        :return: PlotData instance.
        """

        x_list = x.tolist() if hasattr(x, "tolist") else list(x)
        y_list = y.tolist() if hasattr(y, "tolist") else list(y)
        return cls(x=x_list, y=y_list)

    def to_foxglove(self) -> dict[str, Any]:
        """
        Convert to Foxglove-compatible dict.

        :return: Dict with x and y arrays.
        """

        return {"x": self.x, "y": self.y}
