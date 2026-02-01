import time
from pathlib import Path

import foxglove
import zenoh
from foxglove import Capability, MCAPWriter  # type: ignore[attr-defined]

from common.constants import FOXGLOVE_WEBSOCKET_PORT
from common.message import (
    DetectionDistances,
    FrameTransforms,
    Image,
    ImageAnnotations,
    Log,
    Message,
    PlotData,
    PointCloud,
    Pose,
    RadarScan,
    RangeMap,
    Vector2,
    Vector3,
)
from common.utils.comms import CommsSession

TYPE_MAP: dict[str, type] = {
    "antioch/vector2": Vector2,
    "antioch/vector3": Vector3,
    "antioch/pose": Pose,
    "antioch/image": Image,
    "antioch/image_annotations": ImageAnnotations,
    "antioch/point_cloud": PointCloud,
    "antioch/frame_transforms": FrameTransforms,
    "antioch/log": Log,
    "antioch/radar_scan": RadarScan,
    "antioch/range_map": RangeMap,
    "antioch/plot_data": PlotData,
    "antioch/detection_distances": DetectionDistances,
}


class TelemetryManager:
    """
    Manages Foxglove WebSocket server and MCAP recording.

    The WebSocket server persists across tasks. MCAP recording is per-task.
    Uses a callback subscriber to process logs from Zenoh and forward to Foxglove.
    """

    def __init__(self, run_websocket: bool = True) -> None:
        """
        Create a new telemetry manager.

        Initializes the Foxglove WebSocket server (if enabled) and starts listening for logs.

        :param run_websocket: Whether to start the WebSocket server. Set to False for
            headless non-streaming mode to avoid port conflicts.
        """

        self._comms = CommsSession()
        self._mcap_writer: MCAPWriter | None = None
        self._start_timestamp_ns: int = time.time_ns()
        self._time_offset_ns: int = 0
        self._last_let_us: int = 0
        self._run_websocket = run_websocket

        if run_websocket:
            try:
                self._server = foxglove.start_server(
                    name="antioch-telemetry",
                    host="0.0.0.0",
                    port=FOXGLOVE_WEBSOCKET_PORT,
                    capabilities=[Capability.Time],
                )
            except RuntimeError as e:
                if "Address already in use" in str(e):
                    raise RuntimeError(
                        f"Foxglove server port {FOXGLOVE_WEBSOCKET_PORT} is already in use. "
                        f"Another simulation may be running. Stop it first with sim.stop(), "
                        f"or kill the process: lsof -ti :{FOXGLOVE_WEBSOCKET_PORT} | xargs -r kill"
                    ) from None
                raise
        else:
            self._server = None

        self._subscriber = self._comms.declare_callback_subscriber("_logs", self._on_log)

    def stop(self) -> None:
        """
        Stop the telemetry manager and clean up resources.

        Stops the log subscriber, MCAP recording, and WebSocket server.
        """

        self._subscriber.undeclare()
        self.stop_recording()
        if self._server is not None:
            self._server.stop()
        self._comms.close()

    def start_recording(self, mcap_path: str) -> None:
        """
        Start recording telemetry to an MCAP file.

        :param mcap_path: Path to save the MCAP file.
        """

        self.stop_recording()
        path = Path(mcap_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self._mcap_writer = foxglove.open_mcap(str(path), allow_overwrite=True)

    def stop_recording(self) -> None:
        """
        Stop MCAP recording and finalize the file.
        """

        if self._mcap_writer:
            self._mcap_writer.close()
            self._mcap_writer = None

    def reset_time(self) -> None:
        """
        Accumulate the current time offset for monotonic timestamps.

        Call this when the simulation is cleared or stopped. This ensures that
        timestamps continue monotonically increasing across multiple episodes
        in the same MCAP file.
        """

        self._time_offset_ns += self._last_let_us * 1000
        self._last_let_us = 0

    def _on_log(self, sample: zenoh.Sample) -> None:
        """
        Callback for incoming log samples.
        """

        log = Log.unpack(bytes(sample.payload))
        if log.channel is None:
            return

        self._last_let_us = log.let_us

        # Calculate monotonically increasing timestamp
        log_time_ns = self._start_timestamp_ns + self._time_offset_ns + (log.let_us * 1000)

        # Broadcast time if websocket server is running
        if self._server is not None:
            self._server.broadcast_time(log_time_ns)

        if log.telemetry is not None:
            msg_type = Message.extract_type(log.telemetry)
            self._log_payload(log.channel, log.telemetry, msg_type, log_time_ns)
            return

        foxglove_log = log.to_foxglove()
        if foxglove_log is not None:
            foxglove.log(log.channel, foxglove_log, log_time=log_time_ns)

    def _log_payload(self, channel: str, data: bytes, msg_type: str | None, log_time_ns: int) -> None:
        """
        Extract and log a telemetry payload.
        """

        msg_class = TYPE_MAP.get(msg_type) if msg_type else None
        if msg_class is None:
            # Unknown type - log as JSON directly
            json_data = Message.extract_data_as_json(data)
            foxglove.log(channel, json_data, log_time=log_time_ns)
            return

        msg = msg_class.unpack(data)
        foxglove_msg = msg.to_foxglove()
        if foxglove_msg is not None:
            foxglove.log(channel, foxglove_msg, log_time=log_time_ns)
