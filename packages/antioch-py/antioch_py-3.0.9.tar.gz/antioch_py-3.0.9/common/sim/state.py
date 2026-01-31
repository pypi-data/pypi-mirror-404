from enum import Enum


class SimulationState(str, Enum):
    """
    Represents the current state of the simulation.
    """

    PLAYING = "playing"
    PAUSED = "paused"
    STOPPED = "stopped"
