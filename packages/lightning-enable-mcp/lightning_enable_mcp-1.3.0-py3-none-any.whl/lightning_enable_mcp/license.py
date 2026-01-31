"""
License Service

Handles MCP L402 license management - one-time 6,000 sats payment for L402 features.
License is bound to wallet pubkey (for NWC) or device ID (fallback).
"""

import hashlib
import json
import logging
import os
import platform
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import aiohttp

logger = logging.getLogger("lightning-enable-mcp.license")

# License API endpoint
LICENSE_API_URL = "https://api.lightningenable.com/api/mcp-license"

# Default license fee (can be overridden by API)
DEFAULT_LICENSE_FEE_SATS = 6000


@dataclass
class LocalLicense:
    """Local storage model for MCP L402 license."""

    license_key: str
    bound_identifier: str
    identifier_type: str
    wallet_type: str | None
    activated_at: datetime
    last_validated_at: datetime
    is_valid: bool

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "licenseKey": self.license_key,
            "boundIdentifier": self.bound_identifier,
            "identifierType": self.identifier_type,
            "walletType": self.wallet_type,
            "activatedAt": self.activated_at.isoformat(),
            "lastValidatedAt": self.last_validated_at.isoformat(),
            "isValid": self.is_valid,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LocalLicense":
        """Create from dictionary."""
        return cls(
            license_key=data.get("licenseKey", ""),
            bound_identifier=data.get("boundIdentifier", ""),
            identifier_type=data.get("identifierType", ""),
            wallet_type=data.get("walletType"),
            activated_at=datetime.fromisoformat(data["activatedAt"]) if data.get("activatedAt") else datetime.now(timezone.utc),
            last_validated_at=datetime.fromisoformat(data["lastValidatedAt"]) if data.get("lastValidatedAt") else datetime.now(timezone.utc),
            is_valid=data.get("isValid", False),
        )


def get_config_dir() -> Path:
    """Get the configuration directory (~/.lightning-enable/)."""
    home = Path.home()
    config_dir = home / ".lightning-enable"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_license_path() -> Path:
    """Get the license file path."""
    return get_config_dir() / "license.json"


def get_device_id_path() -> Path:
    """Get the device ID file path."""
    return get_config_dir() / "device_id"


class LicenseService:
    """
    Service for managing MCP L402 license.

    L402 features require a one-time payment of 6,000 sats.
    License is bound to wallet pubkey (NWC) or device ID (fallback).
    """

    def __init__(self) -> None:
        self._local_license: LocalLicense | None = None
        self._wallet_pubkey: str | None = None
        self._wallet_type: str | None = None
        self._identifier_type: str | None = None
        self._load_local_license()

    def _load_local_license(self) -> None:
        """Load license from local storage."""
        license_path = get_license_path()
        if license_path.exists():
            try:
                with open(license_path) as f:
                    data = json.load(f)
                    self._local_license = LocalLicense.from_dict(data)
                    logger.info(f"Loaded local license: {self._local_license.license_key[:8]}...")
            except Exception as e:
                logger.warning(f"Failed to load local license: {e}")

    def save_local_license(self, license: LocalLicense) -> None:
        """Save license to local storage."""
        license_path = get_license_path()
        try:
            with open(license_path, "w") as f:
                json.dump(license.to_dict(), f, indent=2)
            self._local_license = license
            logger.info(f"Saved local license: {license.license_key[:8]}...")
        except Exception as e:
            logger.error(f"Failed to save local license: {e}")

    def set_wallet_pubkey(self, pubkey: str, wallet_type: str | None = None) -> None:
        """Set the wallet pubkey for license binding."""
        self._wallet_pubkey = pubkey
        self._wallet_type = wallet_type
        self._identifier_type = "nwc_pubkey"
        logger.info(f"Set wallet pubkey for license: {pubkey[:16]}...")

    @property
    def bound_identifier(self) -> str | None:
        """Get the bound identifier (wallet pubkey or device ID)."""
        if self._wallet_pubkey:
            return self._wallet_pubkey
        return self._get_device_id()

    @property
    def identifier_type(self) -> str | None:
        """Get the type of identifier being used."""
        if self._wallet_pubkey:
            return "nwc_pubkey"
        return "device_id"

    def _get_device_id(self) -> str:
        """Get or generate a stable device ID."""
        device_id_path = get_device_id_path()

        if device_id_path.exists():
            try:
                return device_id_path.read_text().strip()
            except Exception:
                pass

        # Generate new device ID based on machine characteristics
        machine_info = f"{platform.node()}-{platform.machine()}-{platform.system()}"
        device_id = hashlib.sha256(machine_info.encode()).hexdigest()

        try:
            device_id_path.write_text(device_id)
        except Exception as e:
            logger.warning(f"Failed to save device ID: {e}")

        return device_id

    @property
    def is_licensed(self) -> bool:
        """Check if L402 features are licensed."""
        if self._local_license and self._local_license.is_valid:
            # Check if license matches current identifier
            current_id = self.bound_identifier
            if current_id and self._local_license.bound_identifier == current_id:
                return True
        return False

    @property
    def license_key(self) -> str | None:
        """Get the current license key if licensed."""
        if self._local_license and self._local_license.is_valid:
            return self._local_license.license_key
        return None

    def get_local_license(self) -> LocalLicense | None:
        """Get the local license if one exists."""
        return self._local_license

    def validate_l402_access(self) -> str | None:
        """
        Validate that L402 features are licensed.

        Returns:
            None if licensed, error message if not.
        """
        if not self.is_licensed:
            return (
                "L402 features require a license. "
                "Use unlock_l402_features to purchase one for 6,000 sats (one-time, valid forever)."
            )
        return None

    async def check_license_async(self, identifier: str) -> dict[str, Any] | None:
        """Check license status from API."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{LICENSE_API_URL}/check/{identifier}",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    logger.warning(f"License check failed: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"License check error: {e}")
            return None

    async def purchase_license_async(
        self,
        identifier: str,
        identifier_type: str | None = None,
        wallet_type: str | None = None,
    ) -> dict[str, Any] | None:
        """Initiate license purchase from API."""
        try:
            request_data = {
                "identifier": identifier,
                "identifierType": identifier_type,
                "walletType": wallet_type,
                "mcpVersion": "1.1.0",
                "platform": "python",
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{LICENSE_API_URL}/purchase",
                    json=request_data,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    return await response.json()
        except Exception as e:
            logger.error(f"License purchase error: {e}")
            return None

    async def activate_license_async(
        self,
        preimage: str,
        identifier: str,
    ) -> dict[str, Any] | None:
        """Activate license with payment preimage."""
        try:
            request_data = {
                "preimage": preimage,
                "identifier": identifier,
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{LICENSE_API_URL}/activate",
                    json=request_data,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    return await response.json()
        except Exception as e:
            logger.error(f"License activation error: {e}")
            return None

    async def get_compatible_wallets_async(self) -> dict[str, Any] | None:
        """Get list of L402-compatible wallets from API."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{LICENSE_API_URL}/compatible-wallets",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    return None
        except Exception as e:
            logger.error(f"Compatible wallets error: {e}")
            return None


def detect_wallet_type(relay_url: str | None) -> str | None:
    """Detect wallet type from NWC relay URL."""
    if not relay_url:
        return None

    relay_lower = relay_url.lower()

    if "getalby.com" in relay_lower:
        return "alby"
    if "coinos.io" in relay_lower:
        return "coinos"
    if "mutinywallet.com" in relay_lower:
        return "mutiny"
    if "zeus" in relay_lower:
        return "zeus"
    if "bluewallet" in relay_lower:
        return "bluewallet"

    return "unknown"
