import json
import os
import tempfile
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from common.ark import Ark as ArkDefinition
from common.constants import ANTIOCH_API_URL, get_ark_dir, get_asset_dir
from common.core.auth import AuthHandler
from common.core.rome import RomeClient
from common.core.types import ArkReference, ArkVersionReference, AssetReference, AssetVersionReference


def list_local_arks() -> list[ArkReference]:
    """
    List all locally available Arks.

    :return: List of ArkReference objects from local storage.
    """

    arks_dir = get_ark_dir()

    # Group files by ark name and version
    # File format: {name}:{version}:ark.json or {name}:{version}:asset.usdz
    files_by_name_version: dict[str, dict[str, dict[str, Path]]] = defaultdict(lambda: defaultdict(dict))
    for file_path in arks_dir.iterdir():
        if not file_path.is_file():
            continue
        if file_path.name.endswith(":ark.json"):
            name, version, _ = file_path.name.rsplit(":", 2)
            files_by_name_version[name][version]["ark"] = file_path
        elif file_path.name.endswith(":asset.usdz"):
            name, version, _ = file_path.name.rsplit(":", 2)
            files_by_name_version[name][version]["asset"] = file_path

    # Build references for each ark
    results = []
    for name, versions in files_by_name_version.items():
        version_refs = []
        for version, files in versions.items():
            ark_file = files.get("ark")
            if ark_file is None:
                continue
            asset_file = files.get("asset")
            ark_stat = ark_file.stat()
            version_refs.append(
                ArkVersionReference(
                    version=version,
                    full_path=str(ark_file),
                    asset_path=str(asset_file) if asset_file else None,
                    size_bytes=ark_stat.st_size,
                    created_at=datetime.fromtimestamp(ark_stat.st_ctime).isoformat(),
                    updated_at=datetime.fromtimestamp(ark_stat.st_mtime).isoformat(),
                    asset_size_bytes=asset_file.stat().st_size if asset_file else None,
                )
            )
        if version_refs:
            results.append(build_ark_reference_from_versions(name, version_refs))

    return results


def load_local_ark(name: str, version: str) -> ArkDefinition:
    """
    Load Ark definition from local storage.

    :param name: Name of the Ark.
    :param version: Version of the Ark.
    :return: The loaded Ark definition.
    """

    with open(get_ark_version_reference(name, version).full_path) as f:
        return ArkDefinition(**json.load(f))


def get_ark_version_reference(name: str, version: str) -> ArkVersionReference:
    """
    Get version reference for an Ark.

    :param name: Name of the Ark.
    :param version: Version of the Ark.
    :return: Version reference for the Ark.
    """

    available_arks = list_local_arks()
    for ark_ref in available_arks:
        if ark_ref.name == name:
            for version_ref in ark_ref.versions:
                if version_ref.version == version:
                    return version_ref
            raise FileNotFoundError(f"Version {version} of Ark {name} not found locally. Please pull the Ark first.")
    raise FileNotFoundError(f"No versions of Ark {name} found locally. Please pull the Ark first.")


def get_asset_path(name: str, version: str, extension: str = "usdz", assert_exists: bool = True) -> Path:
    """
    Get the local file path for a specific asset version.

    :param name: Name of the asset.
    :param version: Version of the asset.
    :param extension: File extension (without dot), defaults to 'usdz'.
    :param assert_exists: If True, raises error if asset file doesn't exist.
    :return: Path to the asset file.
    """

    assets_dir = get_asset_dir()
    asset_file = assets_dir / f"{name}:{version}:file.{extension}"
    if assert_exists and not asset_file.exists():
        raise FileNotFoundError(f"Asset {name}:{version} with extension .{extension} does not exist")

    return asset_file


def list_local_assets() -> list[AssetReference]:
    """
    List all locally cached assets.

    :return: List of AssetReference objects from local storage.
    """

    assets_dir = get_asset_dir()
    if not assets_dir.exists():
        return []

    # Group files by asset name and version
    # File format: {name}:{version}:file.{extension}
    files_by_name_version: dict[str, dict[str, Path]] = defaultdict(dict)
    for file_path in assets_dir.iterdir():
        if not file_path.is_file():
            continue
        parts = file_path.stem.split(":")
        if len(parts) == 3 and parts[-1] == "file":
            name, version = parts[0], parts[1]
            files_by_name_version[name][version] = file_path

    # Build references for each asset
    results = []
    for name, versions in files_by_name_version.items():
        version_refs = []
        for version, asset_file in versions.items():
            asset_stat = asset_file.stat()
            version_refs.append(
                AssetVersionReference(
                    version=version,
                    full_path=str(asset_file),
                    size_bytes=asset_stat.st_size,
                    created_at=datetime.fromtimestamp(asset_stat.st_ctime).isoformat(),
                    updated_at=datetime.fromtimestamp(asset_stat.st_mtime).isoformat(),
                )
            )
        if version_refs:
            results.append(build_asset_reference_from_versions(name, version_refs))

    return results


def list_remote_arks() -> list[ArkReference]:
    """
    List all Arks from remote registry.

    Requires authentication.

    :return: List of ArkReference objects from remote registry.
    :raises AuthError: If not authenticated.
    """

    auth = AuthHandler()
    token = auth.get_token()
    rome_client = RomeClient(api_url=ANTIOCH_API_URL, token=token)
    return rome_client.list_arks()


def pull_remote_ark(name: str, version: str, overwrite: bool = False) -> ArkDefinition:
    """
    Pull an Ark from remote registry to local storage.

    Downloads the Ark config (ark.json) and asset (asset.usdz) if present.

    Requires authentication.

    :param name: Name of the Ark.
    :param version: Version of the Ark.
    :param overwrite: Overwrite local Ark if it already exists.
    :return: The loaded Ark definition.
    :raises AuthError: If not authenticated.
    """

    # Check if Ark already exists locally
    arks_dir = get_ark_dir()
    ark_json_path = arks_dir / f"{name}:{version}:ark.json"
    ark_asset_path = arks_dir / f"{name}:{version}:asset.usdz"
    if ark_json_path.exists() and not overwrite:
        return load_local_ark(name, version)

    auth = AuthHandler()
    token = auth.get_token()
    rome_client = RomeClient(api_url=ANTIOCH_API_URL, token=token)

    print(f"Pulling {name} v{version}")
    downloaded_asset = rome_client.pull_ark(
        name=name,
        version=version,
        config_output_path=str(ark_json_path),
        asset_output_path=str(ark_asset_path),
    )
    print("  ✓ Config downloaded")
    if downloaded_asset:
        print("  ✓ Asset downloaded")
    print(f"✓ Ark {name} v{version} pulled successfully")
    return load_local_ark(name, version)


def list_remote_assets() -> list[AssetReference]:
    """
    List all assets from remote registry.

    Requires authentication.

    :return: List of AssetReference objects from remote registry.
    :raises AuthError: If not authenticated.
    """

    token = AuthHandler().get_token()
    rome_client = RomeClient(api_url=ANTIOCH_API_URL, token=token)
    return rome_client.list_assets()


def pull_remote_asset(name: str, version: str, overwrite: bool = False) -> Path:
    """
    Pull an asset from remote registry to local storage.

    Requires authentication.

    :param name: Name of the asset.
    :param version: Version of the asset.
    :param overwrite: Overwrite local asset if it already exists.
    :return: Path to the downloaded asset file.
    :raises AuthError: If not authenticated.
    """

    # Check if asset already exists locally
    # NOTE: Only checks USDZ assets for now
    asset_file_path = get_asset_path(name=name, version=version, extension="usdz", assert_exists=False)
    if asset_file_path.exists() and not overwrite:
        return asset_file_path

    token = AuthHandler().get_token()
    rome_client = RomeClient(api_url=ANTIOCH_API_URL, token=token)
    temp_path: str | None = None

    try:
        # Download to a temp file in the destination directory so publishing can be atomic
        # This avoids EXDEV when the asset directory is a separate mount (common in Kubernetes)
        asset_file_path.parent.mkdir(parents=True, exist_ok=True)
        safe_prefix = f".{name.replace(':', '_')}.{version.replace(':', '_')}."
        fd, temp_path = tempfile.mkstemp(prefix=safe_prefix, dir=str(asset_file_path.parent))
        os.close(fd)

        # Pull asset - metadata comes back from response body
        metadata = rome_client.pull_asset(name=name, version=version, output_path=temp_path)
        extension = metadata.get("extension", "usdz")

        # Get final path with correct extension
        asset_file_path = get_asset_path(name=name, version=version, extension=extension, assert_exists=False)
        asset_file_path.parent.mkdir(parents=True, exist_ok=True)

        # Publish atomically on the same filesystem
        Path(temp_path).replace(asset_file_path)
        return asset_file_path
    finally:
        # Clean up if download fails or publish raises
        if temp_path is not None:
            Path(temp_path).unlink(missing_ok=True)


def build_ark_reference_from_versions(name: str, version_refs: list[ArkVersionReference]) -> ArkReference | None:
    """
    Build an ArkReference from version references.

    :param name: The Ark name.
    :param version_refs: List of ArkVersionReference instances.
    :return: ArkReference or None if no versions exist.
    """

    if not version_refs:
        return None

    # Aggregate timestamps from versions, fallback to empty string if all are missing
    created_at = min((v.created_at for v in version_refs if v.created_at), default="")
    updated_at = max((v.updated_at for v in version_refs if v.updated_at), default="")
    return ArkReference(name=name, versions=version_refs, created_at=created_at, updated_at=updated_at)


def build_asset_reference_from_versions(name: str, version_refs: list[AssetVersionReference]) -> AssetReference | None:
    """
    Build an AssetReference from version references.

    :param name: The Asset name.
    :param version_refs: List of AssetVersionReference instances.
    :return: AssetReference or None if no versions exist.
    """

    if not version_refs:
        return None

    # Aggregate timestamps from versions, fallback to empty string if all are missing
    created_at = min((v.created_at for v in version_refs if v.created_at), default="")
    updated_at = max((v.updated_at for v in version_refs if v.updated_at), default="")
    return AssetReference(name=name, versions=version_refs, created_at=created_at, updated_at=updated_at)
