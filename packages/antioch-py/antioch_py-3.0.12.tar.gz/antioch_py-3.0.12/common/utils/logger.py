import re

from common.message import Log, LogLevel, Message
from common.utils.comms import CommsSession

# Valid channel pattern: alphanumeric, underscore, hyphen, period, slash
# Must start with alphanumeric, cannot have consecutive slashes or end with slash
CHANNEL_PATTERN = re.compile(r"^[a-zA-Z0-9](?:[a-zA-Z0-9_.\-]*(?:/[a-zA-Z0-9][a-zA-Z0-9_.\-]*)*)?$")


class Logger:
    """
    Logger that publishes structured logs to the communication system.

    Creates its own Zenoh session for publishing logs.
    """

    def __init__(
        self,
        base_channel: str | None = None,
        debug: bool = False,
        print_logs: bool = True,
    ) -> None:
        """
        Initialize the logger.

        :param base_channel: Optional base channel for logs and telemetry.
        :param debug: Whether to run in debug mode.
        :param print_logs: Whether to print logs to stdout.
        """

        self._comms = CommsSession()
        self._log_publisher = self._comms.declare_publisher("_logs")
        self._base_channel = base_channel
        self._debug = debug
        self._print_logs = print_logs
        self._let_us: int = 0

    def set_let(self, let_us: int) -> None:
        """
        Set the logical execution time.

        :param let_us: Logical execution time in microseconds.
        """

        self._let_us = let_us

    def debug(self, message: str) -> None:
        """
        Log a debug message.

        :param message: Log message.
        """

        if self._debug:
            self._log(LogLevel.DEBUG, message)

    def info(self, message: str) -> None:
        """
        Log an info message.

        :param message: Log message.
        """

        self._log(LogLevel.INFO, message)

    def warning(self, message: str) -> None:
        """
        Log a warning message.

        :param message: Log message.
        """

        self._log(LogLevel.WARNING, message)

    def error(self, message: str) -> None:
        """
        Log an error message.

        :param message: Log message.
        """

        self._log(LogLevel.ERROR, message)

    def telemetry(self, channel: str, telemetry: Message | dict) -> None:
        """
        Record telemetry data from a Message or a JSON-serializable dictionary.

        :param channel: Telemetry channel (alphanumeric with underscore/hyphen/period/slash).
        :param telemetry: The message or dict to record.
        :raises ValueError: If channel format is invalid.
        """

        if not CHANNEL_PATTERN.match(channel):
            raise ValueError(
                f"Invalid channel '{channel}': must be alphanumeric with underscore/hyphen/period/slash, "
                "start and end with alphanumeric, no consecutive slashes"
            )

        # Pack telemetry data based on type
        if isinstance(telemetry, Message):
            packed_data = telemetry.pack()
        elif isinstance(telemetry, dict):
            packed_data = Message.pack_json(telemetry)

        self._log_publisher.publish(
            Log(
                level=LogLevel.INFO,
                message=None,
                channel=f"{self._base_channel}/{channel}" if self._base_channel else channel,
                let_us=self._let_us,
                telemetry=packed_data,
            )
        )

    def close(self) -> None:
        """
        Close the logger and release resources.
        """

        self._log_publisher.close()
        self._comms.close()

    def _log(self, level: LogLevel, message: str) -> None:
        """
        Send a log message through Zenoh.

        :param level: The log level.
        :param message: The log message.
        """

        self._log_publisher.publish(
            Log(
                level=level,
                message=message,
                channel=f"{self._base_channel}/logs" if self._base_channel else None,
                let_us=self._let_us,
            )
        )

        if self._print_logs:
            print(f"[{level.value.upper()}] {message}")
