import time
from enum import Enum

from foxglove.schemas import Log as FoxgloveLog, LogLevel as FoxgloveLogLevel
from pydantic import Field

from common.message.message import Message


class LogLevel(str, Enum):
    """
    Log level.

    Example:
        ```python
        from common.message import LogLevel

        level = LogLevel.INFO
        if level == LogLevel.ERROR:
            print("Error occurred")
        ```
    """

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class Log(Message):
    """
    Log entry structure.

    Example:
        ```python
        from common.message import Log, LogLevel

        # Create a log entry
        log = Log(
            let_us=1000000,
            level=LogLevel.INFO,
            message="Robot initialized successfully",
            channel="robot.init",
        )
        ```
    """

    _type = "antioch/log"
    timestamp_us: int = Field(default_factory=lambda: int(time.time_ns() // 1000), description="Wall clock timestamp in microseconds")
    let_us: int = Field(description="Logical event time in microseconds")
    level: LogLevel = Field(description="Log severity level")
    message: str | None = Field(default=None, description="Log message text")
    channel: str | None = Field(default=None, description="Log channel/category")
    telemetry: bytes | None = Field(default=None, description="Optional serialized telemetry data")

    def to_foxglove(self) -> FoxgloveLog:
        """
        Convert to Foxglove Log for telemetry.

        :return: Foxglove Log schema.
        """

        level_map = {
            LogLevel.DEBUG: FoxgloveLogLevel.Debug,
            LogLevel.INFO: FoxgloveLogLevel.Info,
            LogLevel.WARNING: FoxgloveLogLevel.Warning,
            LogLevel.ERROR: FoxgloveLogLevel.Error,
        }
        return FoxgloveLog(
            timestamp=None,
            level=level_map[self.level],
            message=self.message or "",
            name=self.channel or "",
            file="",
            line=0,
        )
