from datetime import datetime
from enum import Enum

from common.message import Message

# =============================================================================
# Task Types
# =============================================================================


class TaskOutcome(str, Enum):
    """
    Task outcome status.
    """

    SUCCESS = "success"
    FAILURE = "failure"
    ERROR = "error"
    TIMEOUT = "timeout"
    SKIPPED = "skipped"


class TaskTriggerSource(str, Enum):
    """
    How the task was triggered.
    """

    MANUAL = "manual"
    CI = "ci"
    SCHEDULED = "scheduled"
    API = "api"


class TaskRunner(Message):
    """
    Runner/execution environment metadata for a task run.
    """

    runner_id: str | None = None
    runner_name: str | None = None
    environment: dict | None = None


class TaskRun(Message):
    """
    A single execution of a task with timing, outcome, and results.

    Task runs are grouped by task_name for display.
    """

    # Identity - run_id is generated server-side, org_id/user_id set from context
    run_id: str | None = None
    org_id: str | None = None
    user_id: str | None = None

    # Timing
    started_at: datetime
    completed_at: datetime
    duration_ms: int | None = None

    # Task identity
    task_name: str
    description: str | None = None

    # Outcome and results
    outcome: TaskOutcome
    result: dict | None = None

    # User info (display names for search/filtering)
    user_name: str | None = None
    user_email: str | None = None

    # Filtering
    tags: list[str] | None = None
    parameters: dict | None = None

    # Execution context
    runner: TaskRunner | None = None
    trigger_source: TaskTriggerSource | None = None


# =============================================================================
# Registry Types
# =============================================================================


class ArkRegistryMetadata(Message):
    """
    Metadata stored in GCS for a published Ark version.

    This is the canonical schema for Ark registry metadata. All fields are
    populated by Rome during push and validated against this schema.
    """

    module_count: int
    image_count: int
    capability: str
    has_assets: bool
    description: str
    timestamp: str
    digest: str

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> "ArkRegistryMetadata":
        """
        Parse metadata from GCS blob metadata (all values are strings).

        :param data: Raw metadata dict from GCS.
        :return: Parsed ArkRegistryMetadata.
        """

        return cls(
            module_count=int(data.get("module_count", "0")),
            image_count=int(data.get("image_count", "0")),
            capability=data.get("capability", ""),
            has_assets=data.get("has_assets", "false").lower() == "true",
            description=data.get("description", ""),
            timestamp=data.get("timestamp", ""),
            digest=data.get("digest", ""),
        )

    def to_gcs_metadata(self) -> dict[str, str]:
        """
        Convert to GCS metadata format (all values as strings).

        :return: Dict suitable for GCS blob metadata.
        """

        return {
            "module_count": str(self.module_count),
            "image_count": str(self.image_count),
            "capability": self.capability,
            "has_assets": str(self.has_assets).lower(),
            "description": self.description,
            "timestamp": self.timestamp,
            "digest": self.digest,
        }


class ArkVersionReference(Message):
    """
    Reference to an Ark version in the remote Ark registry.
    """

    version: str
    created_at: str
    updated_at: str
    full_path: str
    size_bytes: int
    asset_path: str | None = None
    asset_size_bytes: int | None = None
    metadata: ArkRegistryMetadata | None = None


class ArkReference(Message):
    """
    Reference to an Ark in the remote Ark registry.
    """

    name: str
    versions: list[ArkVersionReference]
    created_at: str
    updated_at: str

    def __str__(self) -> str:
        """
        Return a string representation of the ArkReference.
        """

        versions_str = ", ".join(v.version for v in self.versions)
        return f"{self.name} [{versions_str}]"

    def __repr__(self) -> str:
        """
        Return a detailed representation of the ArkReference.
        """

        versions_list = [v.version for v in self.versions]
        return f"ArkReference(name='{self.name}', versions={versions_list})"


class AssetVersionReference(Message):
    """
    Reference to a specific asset version.
    """

    version: str
    full_path: str
    size_bytes: int
    created_at: str
    updated_at: str
    metadata: dict[str, str] = {}


class AssetReference(Message):
    """
    Reference to an asset with all its versions.
    """

    name: str
    versions: list[AssetVersionReference]
    created_at: str
    updated_at: str

    def __str__(self) -> str:
        """
        Return a string representation of the AssetReference.
        """

        versions_str = ", ".join(v.version for v in self.versions)
        return f"{self.name} [{versions_str}]"

    def __repr__(self) -> str:
        """
        Return a detailed representation of the AssetReference.
        """

        versions_list = [v.version for v in self.versions]
        return f"AssetReference(name='{self.name}', versions={versions_list})"
