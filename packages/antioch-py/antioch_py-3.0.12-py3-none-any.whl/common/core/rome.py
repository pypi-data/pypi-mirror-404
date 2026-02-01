from typing import overload

import requests
from requests import Response

from common.core.types import ArkReference, AssetReference, TaskRun


class RomeError(Exception):
    """
    Base error for Rome API operations.
    """


class RomeAuthError(RomeError):
    """
    Authentication error when interacting with Rome API.
    """


class RomeNetworkError(RomeError):
    """
    Network error when interacting with Rome API.
    """


class RomeClient:
    """
    Client for interacting with Rome (Antioch's cloud API).

    Handles task runs, artifact uploads/downloads, and registry operations for Arks and Assets.
    """

    def __init__(self, api_url: str, token: str):
        """
        Initialize the Rome client.

        :param api_url: Base URL for Rome API.
        :param token: Authentication token.
        """

        self._api_url = api_url
        self._token = token

    def create_task_run(
        self,
        task_run: TaskRun,
        upload_mcap: bool = False,
        upload_bundle: bool = False,
    ) -> tuple[str | None, str | None]:
        """
        Create a task run and optionally get signed URLs for artifact uploads.

        :param task_run: TaskRun model with run data.
        :param upload_mcap: Whether client will upload an MCAP file.
        :param upload_bundle: Whether client will upload a bundle file.
        :return: Tuple of (mcap_upload_url, bundle_upload_url).
        """

        response = self._send_request(
            "POST",
            "/tasks/runs",
            json={
                "task_run": task_run.model_dump(mode="json"),
                "upload_mcap": upload_mcap,
                "upload_bundle": upload_bundle,
            },
        )

        return response.get("mcap_upload_url"), response.get("bundle_upload_url")

    def list_arks(self) -> list[ArkReference]:
        """
        List all Arks from Rome registry.

        :return: List of ArkReference objects from remote registry.
        """

        response = self._send_request("GET", "/ark/list")
        return [ArkReference(**ark) for ark in response.get("data", [])]

    def pull_ark(self, name: str, version: str, config_output_path: str, asset_output_path: str | None = None) -> bool:
        """
        Pull Ark config and optionally asset from Rome via signed URLs.

        :param name: Name of the Ark.
        :param version: Version of the Ark.
        :param config_output_path: Path where ark.json should be saved.
        :param asset_output_path: Path where asset.usdz should be saved (if present).
        :return: True if an asset was downloaded, False otherwise.
        """

        if not self._token:
            raise RomeAuthError("User not authenticated")

        try:
            # Get ark data with download URLs
            response = self._send_request("GET", "/ark/get", json={"name": name, "version": version})

            # Download config
            config_response = requests.get(response["config_download_url"], timeout=60)
            config_response.raise_for_status()
            with open(config_output_path, "wb") as f:
                f.write(config_response.content)

            # Download asset if present and output path provided
            has_asset = response.get("asset_download_url") is not None
            if has_asset and asset_output_path:
                asset_response = requests.get(response["asset_download_url"], timeout=None)
                asset_response.raise_for_status()
                with open(asset_output_path, "wb") as f:
                    f.write(asset_response.content)
                return True

            return False
        except requests.exceptions.RequestException as e:
            raise RomeNetworkError(f"Network error: {e}") from e

    def list_assets(self) -> list[AssetReference]:
        """
        List all assets from Rome registry.

        :return: List of AssetReference objects from remote registry.
        """

        response = self._send_request("GET", "/asset/list")
        return [AssetReference(**asset) for asset in response.get("data", [])]

    def pull_asset(self, name: str, version: str, output_path: str) -> dict[str, str]:
        """
        Pull asset file from Rome registry via signed URL.

        :param name: Name of the asset.
        :param version: Version of the asset.
        :param output_path: Path where the file should be saved.
        :return: Metadata dictionary containing extension, file_size, and modified_time.
        """

        if not self._token:
            raise RomeAuthError("User not authenticated")

        try:
            response = self._send_request("GET", "/asset/pull", params={"name": name, "version": version})
            print(f"Downloading {name}:{version}...")
            download_response = requests.get(response["download_url"], timeout=None)
            download_response.raise_for_status()
            with open(output_path, "wb") as f:
                f.write(download_response.content)
            return {
                "extension": response.get("extension", ""),
                "file_size": response.get("file_size", ""),
                "modified_time": response.get("modified_time", ""),
            }
        except requests.exceptions.RequestException as e:
            raise RomeNetworkError(f"Network error: {e}") from e

    def get_gar_token(self) -> dict:
        """
        Get a GAR (Google Artifact Registry) access token for Docker operations.

        :return: Dictionary with registry_host, repository, access_token, and expires_at.
        """

        response = self._send_request("GET", "/token/gar")
        return response["data"]

    @overload
    def _send_request(
        self,
        method: str,
        endpoint: str,
        json: dict | None = None,
        params: dict | None = None,
        return_content: bool = False,
    ) -> dict: ...

    @overload
    def _send_request(
        self,
        method: str,
        endpoint: str,
        json: dict | None = None,
        params: dict | None = None,
        return_content: bool = True,
    ) -> bytes: ...

    def _send_request(
        self,
        method: str,
        endpoint: str,
        json: dict | None = None,
        params: dict | None = None,
        return_content: bool = False,
    ) -> dict | bytes:
        """
        Send a request to Rome API with standardized error handling.

        :param method: HTTP method (GET, POST, etc.).
        :param endpoint: API endpoint path.
        :param json: Optional JSON payload.
        :param params: Optional query parameters.
        :param return_content: If True, return raw bytes content instead of JSON.
        :return: Response JSON data or raw content bytes.
        """

        if not self._token:
            raise RomeAuthError("User not authenticated")

        try:
            url = f"{self._api_url}{endpoint}"
            headers = {"Authorization": f"Bearer {self._token}", "Content-Type": "application/json"}
            response = requests.request(method, url, json=json, params=params, headers=headers, timeout=30)
            self._check_response_errors(response)
            if return_content:
                return response.content

            try:
                return response.json()
            except requests.exceptions.JSONDecodeError as e:
                raise RomeError(f"Invalid JSON response: {e}") from e
        except requests.exceptions.RequestException as e:
            raise RomeNetworkError(f"Network error: {e}") from e

    def _check_response_errors(self, response: Response) -> None:
        """
        Check response for HTTP errors and raise appropriate exceptions.

        :param response: HTTP response object.
        """

        if response.status_code >= 400:
            error_message = self._extract_error_message(response)
            if response.status_code < 500:
                raise RomeError(error_message)
            raise RomeNetworkError(f"Server error: {error_message}")

    def _extract_error_message(self, response: Response) -> str:
        """
        Extract error message from response JSON or return generic message.

        :param response: HTTP response object.
        :return: Error message string from response or generic HTTP status message.
        """

        try:
            data = response.json()
            if isinstance(data, dict) and "message" in data:
                return data["message"]
        except Exception:
            pass
        return f"HTTP {response.status_code}"
