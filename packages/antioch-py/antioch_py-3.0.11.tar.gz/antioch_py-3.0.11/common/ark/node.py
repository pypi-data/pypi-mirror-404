import math
from enum import Enum

from pydantic import Field

from common.ark.token import InputToken
from common.message import Message


class HardwareAccessMode(str, Enum):
    """
    Hardware access mode for a node.
    """

    NONE = "none"
    READ = "read"
    WRITE = "write"
    READ_WRITE = "read_write"


class NodeTimer(Message):
    """
    Timer configuration for periodic node execution.
    """

    frequency: float | None = None
    period: float | None = None

    def to_period_us(self) -> int:
        """
        Convert timer specification to period in microseconds with millisecond rounding.

        :return: Period in microseconds rounded to the nearest millisecond.
        :raises ValueError: If the timer specification is invalid.
        """

        if self.frequency is not None:
            if self.frequency <= 0 or not math.isfinite(self.frequency):
                raise ValueError("Timer frequency must be positive and finite")
            period_ms = 1000.0 / self.frequency
        elif self.period is not None:
            period_ms = self.period
        else:
            raise ValueError("Timer must specify frequency or period")

        period_us = int(period_ms * 1000)
        rounded_us = ((period_us + 500) // 1000) * 1000
        if rounded_us == 0:
            raise ValueError("Timer frequency is too high (sub-millisecond period)")

        return rounded_us


class NodeInput(Message):
    """
    Configuration for a node's input.
    """

    name: str
    description: str | None = None
    type: str
    path: str
    required: bool
    always_run: bool
    last_n: int
    max_age_ms: int | None = None
    consume_inputs: bool


class NodeOutput(Message):
    """
    Configuration for a node's output.
    """

    name: str
    description: str | None = None
    type: str
    path: str


class Node(Message):
    """
    Complete specification for a processing node within a module.
    """

    name: str
    description: str | None = None
    budget_us: int
    timer: NodeTimer | None = None
    inputs: dict[str, NodeInput] = Field(default_factory=dict)
    outputs: dict[str, NodeOutput] = Field(default_factory=dict)
    hardware_access: dict[str, HardwareAccessMode] = Field(default_factory=dict)


class NodeEdge(Message):
    """
    Directed edge representing data flow between nodes.
    """

    _type = "antioch/ark/node_edge"
    source_module: str
    source_node: str
    source_output_name: str
    target_module: str
    target_node: str
    target_input_name: str
    type: str


class SimNodeStart(Message):
    """
    Ark signals node to start execution (sim mode).

    Sent from Ark to node via publisher to trigger node start with hardware reads.
    """

    _type = "antioch/ark/sim_node_start"
    module_name: str
    node_name: str
    start_let_us: int
    start_timestamp_us: int
    input_tokens: list[InputToken]
    hardware_reads: dict[str, bytes]


class SimNodeComplete(Message):
    """
    Node signals completion to Ark (sim mode).

    Sent from node to Ark to indicate completion with optional hardware writes.
    """

    _type = "antioch/ark/sim_node_complete"
    module_name: str
    node_name: str
    completion_let_us: int
    hardware_writes: dict[str, bytes] | None = None
