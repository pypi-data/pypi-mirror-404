import base64
import json
import os
import time
from pathlib import Path

import requests
from pydantic import BaseModel

from common.constants import (
    AUDIENCE,
    AUTH_CLIENT_ID,
    AUTH_GRANT_TYPE,
    AUTH_ORG_ID_CLAIM,
    AUTH_ORG_NAME_CLAIM,
    AUTH_SCOPE,
    AUTH_TIMEOUT_SECONDS,
    AUTH_TOKEN_URL,
    DEVICE_CODE_URL,
    get_auth_dir,
)


class AuthError(Exception):
    """
    Authentication error.
    """


class Organization(BaseModel):
    """
    Organization information extracted from JWT token.
    """

    org_id: str
    org_name: str


class UserInfo(BaseModel):
    """
    User information extracted from JWT token.
    """

    user_id: str
    name: str | None = None
    email: str | None = None


class AuthHandler:
    """
    Client for handling authentication via OAuth2 device code flow.

    Manages authentication tokens and organization context for interacting
    with Antioch services.
    """

    def __init__(self):
        """
        Initialize the auth handler.

        Automatically loads any existing token from disk.
        """

        self._token: str | None = None
        self._org: Organization | None = None
        self._user: UserInfo | None = None
        self._load_local_token()

    def login(self) -> None:
        """
        Authenticate the user via OAuth2 device code flow.

        Initiates the device code flow, prompts the user to authenticate
        in their browser, and saves the token to disk on success.

        :raises AuthError: If authentication fails or times out.
        """

        if self.is_authenticated():
            print("Already authenticated")
            return

        # Request device code
        device_code_payload = {
            "client_id": AUTH_CLIENT_ID,
            "scope": AUTH_SCOPE,
            "audience": AUDIENCE,
        }

        device_code_response = requests.post(DEVICE_CODE_URL, data=device_code_payload)
        device_code_data = device_code_response.json()
        if device_code_response.status_code != 200:
            raise AuthError("Error generating the device code") from Exception(device_code_data)

        print(f"You have {AUTH_TIMEOUT_SECONDS} seconds to complete the following:")
        print(f"  1. Navigate to: {device_code_data['verification_uri_complete']}")
        print(f"  2. Enter the code: {device_code_data['user_code']}")

        # Poll for token
        token_payload = {
            "grant_type": AUTH_GRANT_TYPE,
            "device_code": device_code_data["device_code"],
            "client_id": AUTH_CLIENT_ID,
        }

        start_time = time.time()
        while True:
            token_response = requests.post(AUTH_TOKEN_URL, data=token_payload)
            token_data = token_response.json()
            if token_response.status_code == 200:
                print("Authenticated!")
                self._token = token_data["access_token"]
                break

            if token_data["error"] not in ("authorization_pending", "slow_down"):
                print(token_data["error_description"])
                raise AuthError("Error authenticating the user") from Exception(token_data)

            if time.time() - start_time > AUTH_TIMEOUT_SECONDS:
                raise AuthError("Timeout waiting for authentication")

            time.sleep(device_code_data["interval"])

        if self._token is None:
            raise AuthError("No token received")

        self._validate_token_claims(self._token)
        self.save_token()

    def is_authenticated(self) -> bool:
        """
        Check if the user is authenticated.

        :return: True if authenticated with a valid token, False otherwise.
        """

        return self._org is not None

    def get_org(self) -> Organization:
        """
        Get the current organization.

        :return: The current organization.
        :raises AuthError: If the user is not authenticated.
        """

        if not self.is_authenticated() or self._org is None:
            raise AuthError("Not authenticated. Please login first")
        return self._org

    def get_user_info(self) -> UserInfo | None:
        """
        Get the current user information.

        :return: The current user info, or None if not available.
        :raises AuthError: If the user is not authenticated.
        """

        if not self.is_authenticated():
            raise AuthError("Not authenticated. Please login first")
        return self._user

    def get_token(self) -> str:
        """
        Get the current authentication token.

        :return: The JWT access token.
        :raises AuthError: If the user is not authenticated.
        """

        if not self.is_authenticated() or self._token is None:
            raise AuthError("Not authenticated. Please login first")
        return self._token

    def save_token(self) -> None:
        """
        Save the authentication token and organization data to disk.

        Creates the token file with restrictive permissions (0600).

        :raises AuthError: If not authenticated.
        """

        if not self.is_authenticated():
            raise AuthError("Not authenticated. Please login first")

        stored_data = {"token": self._token, "org": self._org.model_dump() if self._org else None}
        token_path = self._get_token_path()
        fd = os.open(token_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as f:
            json.dump(stored_data, f, indent=2)

    def clear_token(self) -> None:
        """
        Clear the stored authentication token from disk.
        """

        token_path = self._get_token_path()
        if token_path.exists():
            token_path.unlink()

    def _load_local_token(self) -> None:
        """
        Load the authentication token from disk.

        Silently returns if no token exists. Clears invalid or expired tokens.
        """

        token_path = self._get_token_path()
        if not token_path.exists():
            return

        try:
            with open(token_path, "r") as f:
                stored_data = json.load(f)

            self._token = stored_data.get("token")
            if not self._token:
                return

            # Validate and extract all claims from token
            self._validate_token_claims(self._token)
            if stored_data.get("org"):
                self._org = Organization(**stored_data["org"])
        except Exception as e:
            print(f"Error loading local token: {e}")
            self._token = None
            self.clear_token()

    def _validate_token_claims(self, token: str) -> None:
        """
        Validate the token and extract organization and user information.

        :param token: The JWT token to validate.
        :raises AuthError: If the token is invalid, expired, or missing required claims.
        """

        parts = token.split(".")
        if len(parts) != 3:
            raise AuthError("Invalid token format")

        # Decode the payload
        payload_encoded = parts[1]
        padding = len(payload_encoded) % 4
        if padding:
            payload_encoded += "=" * (4 - padding)
        payload_bytes = base64.urlsafe_b64decode(payload_encoded)
        payload = json.loads(payload_bytes)

        # Check expiration
        exp = payload.get("exp")
        if exp and time.time() > exp:
            raise AuthError("Token has expired")

        # Extract organization
        org_id = payload.get(AUTH_ORG_ID_CLAIM)
        org_name = payload.get(AUTH_ORG_NAME_CLAIM)
        if not org_id or not org_name:
            raise AuthError("Organization information not found in token claims")
        self._org = Organization(org_id=org_id, org_name=org_name)

        # Extract user info (optional claims)
        user_id = payload.get("sub")
        if user_id:
            self._user = UserInfo(
                user_id=user_id,
                name=payload.get("name") or payload.get("nickname"),
                email=payload.get("email"),
            )

    def _get_token_path(self) -> Path:
        """
        Get the token file path.

        :return: Path to the token.json file.
        """

        return get_auth_dir() / "token.json"
