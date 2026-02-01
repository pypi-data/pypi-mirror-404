from enum import Enum

from common.ark.hardware import Hardware
from common.ark.kinematics import Joint, Link
from common.ark.module import Module, ModuleImage
from common.ark.scheduler import NodeEdge
from common.message import Message


class Environment(str, Enum):
    """
    The environment of the Ark.

    :cvar SIM: The simulation environment.
    :cvar REAL: The real environment.
    :cvar ALL: All environments.
    """

    SIM = "sim"
    REAL = "real"
    ALL = "all"

    def __str__(self) -> str:
        return self.value


class ArkMetadata(Message):
    """
    Metadata about the Ark.
    """

    digest: str
    version: str
    timestamp: str
    asset_hash: str | None = None


class ArkInfo(Message):
    """
    Information about the Ark.
    """

    description: str
    version: str


class Kinematics(Message):
    """
    The kinematics of the Ark.
    """

    links: list[Link]
    joints: list[Joint]


class Ark(Message):
    """
    Antioch Ark specification.
    """

    metadata: ArkMetadata
    name: str
    capability: Environment
    info: ArkInfo
    modules: list[Module]
    edges: list[NodeEdge]
    kinematics: Kinematics
    hardware: list[Hardware]

    def collect_image_names(self, environment: Environment | None = None) -> list[str]:
        """
        Collect all Docker image names used by modules in this Ark.

        :param environment: Filter images by environment (SIM or REAL). If None, collects all images.
        :return: List of unique image names sorted alphabetically.
        """

        images: set[str] = set()
        for module in self.modules:
            if isinstance(module.image, str):
                # Simple string image
                if module.image:
                    images.add(module.image)
            elif isinstance(module.image, ModuleImage):
                # Hardware module with sim/real images
                if environment in (None, Environment.SIM) and module.image.sim:
                    images.add(module.image.sim)
                if environment in (None, Environment.REAL) and module.image.real:
                    images.add(module.image.real)

        return sorted(images)
