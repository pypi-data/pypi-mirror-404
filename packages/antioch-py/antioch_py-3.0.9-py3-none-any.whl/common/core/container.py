import contextlib
import time
from enum import Enum

import docker
from docker.errors import APIError
from docker.models.containers import Container

from common.ark import Ark as ArkDefinition, Environment
from common.ark.module import ModuleImage, ModuleReady, ModuleStart
from common.constants import ANTIOCH_API_URL
from common.core.auth import AuthHandler
from common.core.rome import RomeClient
from common.utils.comms import CommsSession
from common.utils.time import now_us

# Container naming prefix for all Antioch module containers
CONTAINER_PREFIX = "antioch-module-"

# Synchronization paths for module coordination
ARK_MODULE_READY_PATH = "_ark/module_ready"
ARK_MODULE_START_PATH = "_ark/module_start"


class ContainerSource(str, Enum):
    """
    Source location for container images.
    """

    LOCAL = "Local"
    REMOTE = "Remote"


class ContainerManagerError(Exception):
    """
    Raised when container management operations fail.
    """

    pass


class ContainerManager:
    """
    Manages Docker containers for Ark modules.

    Handles launching, coordination, and cleanup of module containers.
    Uses host networking for Zenoh communication.
    """

    def __init__(self) -> None:
        """
        Create a new container manager.

        Initializes Docker client and Zenoh communication session.
        """

        self._comms = CommsSession()
        self._client = docker.from_env()
        self._containers: dict[str, Container] = {}

    def launch_ark(
        self,
        ark: ArkDefinition,
        source: ContainerSource = ContainerSource.LOCAL,
        environment: Environment = Environment.SIM,
        debug: bool = False,
        timeout: float = 30.0,
    ) -> int:
        """
        Launch all module containers for an Ark.

        Stops any existing module containers first to ensure idempotent behavior.

        :param ark: Ark definition to launch.
        :param source: Container image source (local or remote).
        :param environment: Environment to run in (sim or real).
        :param debug: Enable debug mode.
        :param timeout: Timeout in seconds for modules to become ready.
        :return: Global start time in microseconds.
        :raises ContainerManagerError: If environment is incompatible or launch fails.
        """

        # Validate environment compatibility
        if ark.capability == Environment.SIM and environment == Environment.REAL:
            raise ContainerManagerError(f"Ark '{ark.name}' has sim capability but requested for real")
        if ark.capability == Environment.REAL and environment == Environment.SIM:
            raise ContainerManagerError(f"Ark '{ark.name}' has real capability but requested for sim")

        # Stop all existing module containers (idempotent)
        self._stop_all()

        # Get GAR credentials if pulling from remote
        gar_auth = self._get_gar_auth() if source == ContainerSource.REMOTE else None

        # Build container configs
        configs: list[tuple[str, str, str]] = []
        for module in ark.modules:
            image = self._get_image(module.image, environment)
            if image is None:
                raise ContainerManagerError(f"No image for module '{module.name}' in {environment}")
            if gar_auth is not None:
                image = f"{gar_auth['registry_host']}/{gar_auth['repository']}/{image}"
            container_name = f"{CONTAINER_PREFIX}{ark.name.replace('_', '-')}-{module.name.replace('_', '-')}"
            configs.append((module.name, container_name, image))

        # Pull images if remote
        if gar_auth is not None:
            self._pull_images([c[2] for c in configs], gar_auth)

        # Set up ready subscriber before launching
        ready_sub = self._comms.declare_async_subscriber(ARK_MODULE_READY_PATH)

        # Launch containers
        ark_json = ark.model_dump_json()
        for module_name, container_name, image in configs:
            self._launch(module_name, container_name, image, ark_json, environment, debug)

        # Wait for all modules to be ready
        pending = {m.name for m in ark.modules}
        start = time.time()
        while pending:
            if time.time() - start > timeout:
                raise ContainerManagerError(f"Timeout waiting for modules: {', '.join(sorted(pending))}")
            msg = ready_sub.recv_timeout(ModuleReady, timeout=0.1)
            if msg is not None:
                print(f"Module ready: {msg.module_name}")
                pending.discard(msg.module_name)

        # Broadcast global start time (2s in future for sync)
        global_start_us = ((now_us() // 1_000_000) + 2) * 1_000_000
        self._comms.declare_publisher(ARK_MODULE_START_PATH).publish(ModuleStart(global_start_time_us=global_start_us))
        return global_start_us

    def stop(self, timeout: float = 10.0) -> None:
        """
        Stop all module containers.

        :param timeout: Timeout in seconds for container stop operation.
        """

        self._stop_all(timeout)

    def close(self, timeout: float = 10.0) -> None:
        """
        Close the container manager and clean up resources.

        Stops all module containers and closes the Zenoh session.

        :param timeout: Timeout in seconds for container stop operation.
        """

        self._stop_all(timeout)
        self._comms.close()

    def _launch(
        self,
        module_name: str,
        container_name: str,
        image: str,
        ark_json: str,
        environment: Environment,
        debug: bool,
    ) -> None:
        """
        Launch a single module container.

        :param module_name: Name of the module.
        :param container_name: Docker container name.
        :param image: Docker image to use.
        :param ark_json: Serialized Ark definition.
        :param environment: Environment (sim or real).
        :param debug: Enable debug mode.
        :raises ContainerManagerError: If container launch fails.
        """

        try:
            container = self._client.containers.run(
                image=image,
                name=container_name,
                environment={
                    "_MODULE_NAME": module_name,
                    "_ARK": ark_json,
                    "_ENVIRONMENT": str(environment.value),
                    "_DEBUG": str(debug).lower(),
                },
                network_mode="host",
                ipc_mode="host",
                detach=True,
                remove=False,
            )
            self._containers[container_name] = container
            print(f"Launched container: {container_name}")
        except APIError as e:
            raise ContainerManagerError(f"Failed to launch '{container_name}': {e}") from e

    def _stop_all(self, timeout: float = 10.0) -> None:
        """
        Stop all Antioch module containers.

        Finds all containers with the antioch-module- prefix and stops them.

        :param timeout: Timeout in seconds for stop operation.
        """

        with contextlib.suppress(APIError):
            for container in self._client.containers.list(all=True):
                if container.name and container.name.startswith(CONTAINER_PREFIX):
                    print(f"Stopping container: {container.name}")
                    self._stop_container(container, timeout)

        self._containers.clear()

    def _stop_container(self, container: Container, timeout: float) -> None:
        """
        Stop and remove a single container.

        :param container: Docker container to stop.
        :param timeout: Timeout in seconds for stop operation.
        """

        with contextlib.suppress(APIError):
            container.stop(timeout=int(timeout))
        with contextlib.suppress(APIError):
            container.remove(force=True)

    def _get_image(self, image: str | ModuleImage, environment: Environment) -> str | None:
        """
        Get the image name for the given environment.

        :param image: Image specification (string or ModuleImage).
        :param environment: Environment to get image for.
        :return: Image name or None if not available.
        """

        if isinstance(image, str):
            return image
        return image.sim if environment == Environment.SIM else image.real

    def _get_gar_auth(self) -> dict:
        """
        Get Google Artifact Registry authentication credentials.

        :return: Dictionary containing registry host, repository, and access token.
        """

        auth = AuthHandler()
        rome = RomeClient(ANTIOCH_API_URL, auth.get_token())
        return rome.get_gar_token()

    def _pull_images(self, images: list[str], gar_auth: dict) -> None:
        """
        Pull container images from the registry.

        :param images: List of image names to pull.
        :param gar_auth: GAR authentication credentials.
        """

        auth_config = {"username": "oauth2accesstoken", "password": gar_auth["access_token"]}
        for image in set(images):
            print(f"Pulling image: {image}")
            self._client.images.pull(image, auth_config=auth_config)
