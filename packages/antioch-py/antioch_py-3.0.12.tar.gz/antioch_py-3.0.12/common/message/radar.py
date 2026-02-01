from __future__ import annotations

from typing import Any

import numpy as np
from pydantic import Field

from common.message.array import Array
from common.message.image import Image, ImageEncoding
from common.message.message import Message
from common.message.point_cloud import PointCloud


class RadarScan(Message):
    """
    Radar scan data containing all detections from a single scan.

    Data is stored as numpy arrays (via Array) for efficient processing.

    Example:
        ```python
        from common.message import RadarScan

        # Access detection data efficiently via arrays
        scan = radar.get_scan()
        ranges = scan.ranges.to_numpy()
        rcs = scan.rcs.to_numpy()

        # Filter detections by range
        close_mask = ranges < 10.0
        close_rcs = rcs[close_mask]

        # Convert to point cloud for visualization
        point_cloud = scan.to_point_cloud(frame_id="radar_link")
        ```
    """

    _type = "antioch/radar_scan"

    # Raw spherical coordinates (stored as Arrays for serialization)
    ranges: Array = Field(default_factory=lambda: Array.zeros(0), description="Range to targets in meters")
    azimuths: Array = Field(default_factory=lambda: Array.zeros(0), description="Azimuth angles in radians")
    elevations: Array = Field(default_factory=lambda: Array.zeros(0), description="Elevation angles in radians")
    rcs: Array = Field(default_factory=lambda: Array.zeros(0), description="Radar cross section in dBsm")
    velocities: Array = Field(default_factory=lambda: Array.zeros(0), description="Radial velocities in m/s")

    # Cartesian positions (computed from spherical, stored for efficiency)
    x: Array = Field(default_factory=lambda: Array.zeros(0), description="X positions in sensor frame")
    y: Array = Field(default_factory=lambda: Array.zeros(0), description="Y positions in sensor frame")
    z: Array = Field(default_factory=lambda: Array.zeros(0), description="Z positions in sensor frame")

    @property
    def num_detections(self) -> int:
        """
        Number of detections in this scan.
        """

        return len(self.ranges)

    @classmethod
    def from_arrays(
        cls,
        ranges: np.ndarray,
        azimuths: np.ndarray,
        elevations: np.ndarray,
        rcs: np.ndarray,
        velocities: np.ndarray,
        x: np.ndarray,
        y: np.ndarray,
        z: np.ndarray,
    ) -> RadarScan:
        """
        Create RadarScan directly from numpy arrays.

        This is the most efficient way to create a RadarScan as it avoids
        creating any intermediate Python objects.

        :param ranges: Range values in meters.
        :param azimuths: Azimuth angles in radians.
        :param elevations: Elevation angles in radians.
        :param rcs: RCS values in dBsm.
        :param velocities: Radial velocities in m/s.
        :param x: X positions in sensor frame.
        :param y: Y positions in sensor frame.
        :param z: Z positions in sensor frame.
        :return: RadarScan instance.
        :raises ValueError: If arrays have mismatched lengths.
        """

        n = len(ranges)
        if not all(len(arr) == n for arr in [azimuths, elevations, rcs, velocities, x, y, z]):
            raise ValueError("All arrays must have the same length")

        return cls(
            ranges=Array.from_numpy(ranges.astype(np.float32)),
            azimuths=Array.from_numpy(azimuths.astype(np.float32)),
            elevations=Array.from_numpy(elevations.astype(np.float32)),
            rcs=Array.from_numpy(rcs.astype(np.float32)),
            velocities=Array.from_numpy(velocities.astype(np.float32)),
            x=Array.from_numpy(x.astype(np.float32)),
            y=Array.from_numpy(y.astype(np.float32)),
            z=Array.from_numpy(z.astype(np.float32)),
        )

    def to_point_cloud(self, frame_id: str = "radar") -> PointCloud:
        """
        Convert radar scan to a point cloud.

        :param frame_id: Frame of reference for the point cloud.
        :return: PointCloud with detection positions.
        """

        return PointCloud(
            frame_id=frame_id,
            x=self.x.to_list(),
            y=self.y.to_list(),
            z=self.z.to_list(),
        )

    def to_foxglove(self) -> dict[str, Any]:
        """
        Convert to a JSON-serializable dict for Foxglove visualization.

        :return: Dictionary with all scan data as lists.
        """

        return {
            "num_detections": self.num_detections,
            "ranges": self.ranges.to_list(),
            "azimuths": self.azimuths.to_list(),
            "elevations": self.elevations.to_list(),
            "rcs": self.rcs.to_list(),
            "velocities": self.velocities.to_list(),
            "x": self.x.to_list(),
            "y": self.y.to_list(),
            "z": self.z.to_list(),
        }


class RangeMap(Message):
    """
    1D range bin map for radar processing.

    Represents radar signal strength across range bins, commonly used for
    MTI (Moving Target Indication) processing and detection.
    """

    _type = "antioch/range_map"

    r_bins: int = Field(description="Number of range bins")
    r_min_m: float = Field(description="Minimum range in meters (inclusive)")
    r_max_m: float = Field(description="Maximum range in meters (inclusive)")
    dr_m: float = Field(description="Range bin size in meters")
    data: Array = Field(description="Float32 array of shape (r_bins,)")

    def to_numpy(self) -> np.ndarray:
        """
        Convert the range map to a 1D numpy array.

        :return: float32 array with shape (r_bins,).
        """

        return self.data.to_numpy().reshape(self.r_bins)

    def to_image(
        self,
        *,
        transform: str = "log1p",
        encoding: ImageEncoding = ImageEncoding.MONO8,
        clip_percentile: float = 99.5,
        height: int = 32,
    ) -> Image:
        """
        Convert this range map into an Image for visualization.

        The image is a horizontal bar where x-axis is range bins.

        :param transform: "linear" or "log1p".
        :param encoding: Image encoding to use (default MONO8).
        :param clip_percentile: When encoding is MONO8, clip values to this percentile.
        :param height: Height of the output image in pixels.
        :return: Image representing the range map.
        """

        data = self.to_numpy()
        if transform == "log1p":
            values = np.log1p(data).astype(np.float32)
        elif transform == "linear":
            values = data.astype(np.float32, copy=False)
        else:
            raise ValueError(f"Unsupported transform '{transform}'")

        if encoding == ImageEncoding.DEPTH_F32:
            tiled = np.tile(values.reshape(1, -1), (height, 1))
            return Image.from_numpy(tiled.astype(np.float32, copy=False), encoding=encoding)

        if encoding != ImageEncoding.MONO8:
            raise ValueError(f"Unsupported encoding '{encoding.value}' for range map image")

        # Normalize to 8-bit
        vmax = float(np.percentile(values, clip_percentile)) if values.size else 0.0
        if vmax <= 0.0 or not np.isfinite(vmax):
            mono = np.zeros((height, self.r_bins), dtype=np.uint8)
        else:
            scaled = np.clip(values / np.float32(vmax), 0.0, 1.0)
            mono_row = (scaled * np.float32(255.0)).astype(np.uint8, copy=False)
            mono = np.tile(mono_row.reshape(1, -1), (height, 1))

        return Image.from_numpy(mono, encoding=encoding)

    def to_foxglove(self) -> dict[str, Any]:
        """
        Convert to a JSON-serializable dict for Foxglove visualization.

        :return: Dictionary with range map metadata and data as list.
        """

        return {
            "r_bins": self.r_bins,
            "r_min_m": self.r_min_m,
            "r_max_m": self.r_max_m,
            "dr_m": self.dr_m,
            "data": self.data.to_list(),
        }
