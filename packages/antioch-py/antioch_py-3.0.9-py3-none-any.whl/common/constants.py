import os
from pathlib import Path

# =============================================================================
# Environment
# =============================================================================

ANTIOCH_ENV = os.environ.get("ANTIOCH_ENV", "prod").lower()
if ANTIOCH_ENV not in ("prod", "staging", "local"):
    raise ValueError(f"Invalid ANTIOCH_ENV: {ANTIOCH_ENV}")

# =============================================================================
# API URLs
# =============================================================================

# Local dev uses staging APIs
if ANTIOCH_ENV in ("staging", "local"):
    ANTIOCH_API_URL = "https://staging.api.antioch.com"
    AUTH_DOMAIN = "https://staging.auth.antioch.com"
    AUTH_CLIENT_ID = "x0aOquV43Xe76ehqAm6Zir80O0MWpqTV"
else:
    ANTIOCH_API_URL = "https://api.antioch.com"
    AUTH_DOMAIN = "https://auth.antioch.com"
    AUTH_CLIENT_ID = "8RLoPEgMP3ih10sfJsGPkwbUWGilsoyX"

# Allow environment variable overrides
ANTIOCH_API_URL = os.environ.get("ANTIOCH_API_URL", ANTIOCH_API_URL)
AUTH_DOMAIN = os.environ.get("AUTH_DOMAIN", AUTH_DOMAIN)

# =============================================================================
# Local Storage Directories
# =============================================================================

ANTIOCH_DIR = os.environ.get("ANTIOCH_DIR", f"{os.environ.get('HOME', '.')}/.antioch/{ANTIOCH_ENV}")
ANTIOCH_ARKS_DIR = os.environ.get("ANTIOCH_ARKS_DIR", f"{ANTIOCH_DIR}/arks")
ANTIOCH_ASSETS_DIR = os.environ.get("ANTIOCH_ASSETS_DIR", f"{ANTIOCH_DIR}/assets")

# =============================================================================
# Auth0 Configuration
# =============================================================================

AUTH_TOKEN_URL = f"{AUTH_DOMAIN}/oauth/token"
DEVICE_CODE_URL = f"{AUTH_DOMAIN}/oauth/device/code"

AUTH_SCOPE = "openid profile email"
AUDIENCE = "https://sessions.antioch.com"
AUTH_GRANT_TYPE = "urn:ietf:params:oauth:grant-type:device_code"
AUTH_TIMEOUT_SECONDS = 120

# JWT claim names (namespaced for Auth0)
AUTH_ORG_ID_CLAIM = "https://antioch.com/org_id"
AUTH_ORG_NAME_CLAIM = "https://antioch.com/org_name"
AUTH_ORG_ROLE_CLAIM = "https://antioch.com/org_role"

# Organization roles (mutually exclusive within an org)
ORG_ROLE_ADMIN = "team_admin"
ORG_ROLE_MEMBER = "team_member"
ORG_ROLE_SUPPORT = "support_staff"
ORG_ROLES = (ORG_ROLE_ADMIN, ORG_ROLE_MEMBER, ORG_ROLE_SUPPORT)

# =============================================================================
# Telemetry Configuration
# =============================================================================

FOXGLOVE_WEBSOCKET_PORT = 8765

# =============================================================================
# Zenoh Shared Memory Configuration
# =============================================================================

# Enable shared memory transport for high-performance IPC between processes
# When enabled, large messages use shared memory instead of TCP, providing
# 4-8x latency improvement for messages > 64 KB. Falls back to TCP when SHM
# is unavailable (cross-machine, pool exhausted, etc.)
SHM_ENABLED = True

# Shared memory pool size in bytes (256 MB)
# This is the total amount of shared memory allocated for message transport
SHM_POOL_SIZE_BYTES = 256 * 1024 * 1024

# Message size threshold in bytes for SHM transport (64 KB)
# Messages larger than this use SHM; smaller messages use TCP
# Based on benchmarks showing SHM wins for messages >= 64 KB
SHM_MESSAGE_SIZE_THRESHOLD_BYTES = 64 * 1024


def get_auth_dir() -> Path:
    """
    Get the auth storage directory path.

    Creates the auth directory if it doesn't exist.

    :return: Path to the auth directory.
    """

    auth_dir = Path(ANTIOCH_DIR) / "auth"
    auth_dir.mkdir(parents=True, exist_ok=True)
    return auth_dir


def get_ark_dir() -> Path:
    """
    Get the arks storage directory path.

    Creates the arks directory if it doesn't exist.

    :return: Path to the arks directory.
    """

    ark_dir = Path(ANTIOCH_ARKS_DIR)
    ark_dir.mkdir(parents=True, exist_ok=True)
    return ark_dir


def get_asset_dir() -> Path:
    """
    Get the assets storage directory path.

    Creates the assets directory if it doesn't exist.

    :return: Path to the assets directory.
    """

    asset_dir = Path(ANTIOCH_ASSETS_DIR)
    asset_dir.mkdir(parents=True, exist_ok=True)
    return asset_dir
