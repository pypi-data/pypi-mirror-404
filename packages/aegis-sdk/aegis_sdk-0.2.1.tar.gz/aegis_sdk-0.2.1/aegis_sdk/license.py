"""License validation and caching module.

This module handles license key validation with the Aegis Cloud API,
including local caching for offline operation and grace period support.

Key features:
- License validation against Aegis Cloud API
- JWT token verification for secure license validation
- Local caching (24 hours by default)
- Offline grace period (7 days)
- Policy configuration fetching
- Multi-department policy group support
"""

import hashlib
import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import threading

from aegis_sdk.types import LicenseInfo, LicenseValidationError

# Try to import jwt for verification (optional dependency)
try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False


# Default configuration
DEFAULT_CACHE_DIR = Path.home() / ".aegis"
DEFAULT_CACHE_TTL = 86400  # 24 hours
DEFAULT_GRACE_PERIOD_DAYS = 7
DEFAULT_API_ENDPOINT = "https://api.aegispreflight.com/v1"

# Bundled public key for JWT verification (fetched from /v1/license/public-key)
# This is updated periodically and can be overridden via constructor
AEGIS_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAx4Z+qVKXVPkNjZ8C8O6g
/1HlXk5fCl7S2wP4UZhJ3lQHYEfKpI7NtKjQkWJNSO7r/NcKJPAMFv7XqI5O9OPy
/0NM4gNxPM+qLO5XwLH6QPFA3J7KZQN+P1PJ4YXKI8I7hJvKCqYVZ3IG+5pI7O6R
DGBZcJ/t6XMDPJ1pDZJQB5eFQ3FqGwHZP8pJ6Uk7V5P1qVMW3Yt4BNKLQLP4kJ5J
JvMN9pN4ZH5OKZPBJJ5M8Q9P1QJXPZJQ9PJXP1QJX9PZJ5MQ9PJXP1QJXP9ZJ5MQ
9PJX1PQJXP9ZJ5MQ9PJXP1QJXP9ZJ5MQ9PJXP1QJXP9ZJ5MQ9PJXP1QJXP9ZJ5MQ
9QIDAQAB
-----END PUBLIC KEY-----"""


@dataclass
class CachedLicense:
    """Cached license information."""

    license_info: LicenseInfo
    cached_at: float
    policy_hash: str = ""
    jwt_token: Optional[str] = None

    def is_expired(self, ttl: int = DEFAULT_CACHE_TTL) -> bool:
        """Check if cache has expired."""
        return time.time() - self.cached_at > ttl

    def is_within_grace_period(self, grace_days: int = DEFAULT_GRACE_PERIOD_DAYS) -> bool:
        """Check if still within offline grace period."""
        grace_seconds = grace_days * 24 * 60 * 60
        return time.time() - self.cached_at < grace_seconds

    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            "license_info": {
                "valid": self.license_info.valid,
                "expires": self.license_info.expires,
                "org_id": self.license_info.org_id,
                "policy_version": self.license_info.policy_version,
                "policy_config": self.license_info.policy_config,
                "policy_groups": self.license_info.policy_groups,
                "default_policy_group": self.license_info.default_policy_group,
                "license_type": self.license_info.license_type,
            },
            "cached_at": self.cached_at,
            "policy_hash": self.policy_hash,
            "jwt_token": self.jwt_token,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CachedLicense":
        """Create from dictionary."""
        license_data = data["license_info"]
        license_info = LicenseInfo(
            valid=license_data["valid"],
            expires=license_data["expires"],
            org_id=license_data["org_id"],
            policy_version=license_data["policy_version"],
            policy_config=license_data.get("policy_config", {}),
            policy_groups=license_data.get("policy_groups", []),
            default_policy_group=license_data.get("default_policy_group"),
            license_type=license_data.get("license_type", "standard"),
            jwt_token=data.get("jwt_token"),
            cached_at=datetime.fromtimestamp(data["cached_at"]).isoformat(),
        )
        return cls(
            license_info=license_info,
            cached_at=data["cached_at"],
            policy_hash=data.get("policy_hash", ""),
            jwt_token=data.get("jwt_token"),
        )


class LicenseManager:
    """Manages license validation and caching.

    This class handles:
    - License key validation against Aegis Cloud API
    - JWT token verification for secure validation
    - Local caching for performance and offline operation
    - Offline grace period for temporary connectivity issues
    - Policy configuration fetching and caching
    - Multi-department policy group support

    Example:
        manager = LicenseManager("aegis_lic_xxxxx")

        # Validate license (uses cache if available)
        info = manager.validate()
        print(f"Organization: {info.org_id}")
        print(f"Expires: {info.expires}")

        # Get policy for a specific department
        policy = manager.get_policy_for_group("engineering")

        # List available policy groups
        print(f"Groups: {info.policy_groups}")
    """

    def __init__(
        self,
        license_key: str,
        cache_dir: Optional[Path] = None,
        cache_ttl: int = DEFAULT_CACHE_TTL,
        grace_period_days: int = DEFAULT_GRACE_PERIOD_DAYS,
        api_endpoint: str = DEFAULT_API_ENDPOINT,
        offline_mode: bool = False,
        verify_jwt: bool = True,
        public_key: Optional[str] = None,
        policy_group: Optional[str] = None,
    ):
        """Initialize license manager.

        Args:
            license_key: Aegis license key
            cache_dir: Directory for cache files (default: ~/.aegis)
            cache_ttl: Cache time-to-live in seconds (default: 24 hours)
            grace_period_days: Offline grace period in days (default: 7)
            api_endpoint: Aegis API endpoint
            offline_mode: If True, skip API validation and use cache only
            verify_jwt: If True, verify JWT signature (requires pyjwt)
            public_key: Custom public key for JWT verification
            policy_group: Default policy group/department to use
        """
        self.license_key = license_key
        self.cache_dir = cache_dir or DEFAULT_CACHE_DIR
        self.cache_ttl = cache_ttl
        self.grace_period_days = grace_period_days
        self.api_endpoint = api_endpoint
        self.offline_mode = offline_mode
        self.verify_jwt = verify_jwt and JWT_AVAILABLE
        self.public_key = public_key or AEGIS_PUBLIC_KEY
        self.policy_group = policy_group

        self._cached_license: Optional[CachedLicense] = None
        self._lock = threading.Lock()
        self._public_key_fetched = False

        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    @property
    def cache_file(self) -> Path:
        """Get path to cache file for this license key."""
        # Hash the license key for the filename
        key_hash = hashlib.sha256(self.license_key.encode()).hexdigest()[:16]
        return self.cache_dir / f"license_{key_hash}.json"

    @property
    def public_key_file(self) -> Path:
        """Get path to cached public key file."""
        return self.cache_dir / "aegis_public_key.pem"

    def validate(self, force_refresh: bool = False) -> LicenseInfo:
        """Validate license, using cache if available.

        Args:
            force_refresh: If True, skip cache and fetch from API

        Returns:
            LicenseInfo with validation details

        Raises:
            LicenseValidationError: If license cannot be validated
        """
        with self._lock:
            # Try to use cached license
            if not force_refresh and not self.offline_mode:
                cached = self._load_cache()
                if cached and not cached.is_expired(self.cache_ttl):
                    # Verify JWT if available and enabled
                    if self.verify_jwt and cached.jwt_token:
                        try:
                            self._verify_jwt_token(cached.jwt_token)
                        except LicenseValidationError:
                            # JWT invalid, force refresh
                            pass
                        else:
                            self._cached_license = cached
                            return cached.license_info
                    else:
                        self._cached_license = cached
                        return cached.license_info

            # In offline mode, always use cache
            if self.offline_mode:
                cached = self._load_cache()
                if cached and cached.is_within_grace_period(self.grace_period_days):
                    self._cached_license = cached
                    return cached.license_info
                raise LicenseValidationError(
                    "License validation failed: offline mode with no valid cache"
                )

            # Fetch from API
            try:
                license_info = self._fetch_license()
                self._save_cache(license_info)
                return license_info
            except Exception as e:
                # Try to use cached license within grace period
                cached = self._load_cache()
                if cached and cached.is_within_grace_period(self.grace_period_days):
                    self._cached_license = cached
                    return cached.license_info

                raise LicenseValidationError(f"License validation failed: {e}")

    def get_policy(self) -> dict:
        """Get policy configuration.

        Returns:
            Policy configuration dictionary
        """
        if self._cached_license:
            return self._cached_license.license_info.policy_config

        # Validate to populate cache
        info = self.validate()
        return info.policy_config

    def get_policy_for_group(self, group: Optional[str] = None) -> dict:
        """Get policy configuration for a specific group.

        Args:
            group: Policy group slug. If None, uses default_policy_group or
                   the policy_group set at initialization.

        Returns:
            Policy configuration dictionary for the group
        """
        info = self.validate()
        target_group = group or self.policy_group or info.default_policy_group
        return info.get_policy_for_group(target_group)

    def get_policy_groups(self) -> list[str]:
        """Get list of available policy groups.

        Returns:
            List of policy group slugs
        """
        info = self.validate()
        return info.policy_groups

    def is_valid(self) -> bool:
        """Check if license is currently valid.

        Returns:
            True if license is valid
        """
        try:
            info = self.validate()
            return info.valid
        except LicenseValidationError:
            return False

    def get_org_id(self) -> Optional[str]:
        """Get organization ID from license.

        Returns:
            Organization ID or None if not available
        """
        try:
            info = self.validate()
            return info.org_id
        except LicenseValidationError:
            return None

    def invalidate_cache(self):
        """Invalidate the cached license."""
        with self._lock:
            self._cached_license = None
            if self.cache_file.exists():
                self.cache_file.unlink()

    def _verify_jwt_token(self, token: str) -> dict:
        """Verify JWT token signature and return payload.

        Args:
            token: JWT token string

        Returns:
            Decoded JWT payload

        Raises:
            LicenseValidationError: If verification fails
        """
        if not JWT_AVAILABLE:
            raise LicenseValidationError("pyjwt not installed, cannot verify JWT")

        try:
            # Fetch public key if not already done
            if not self._public_key_fetched:
                self._fetch_public_key()

            payload = jwt.decode(
                token,
                self.public_key,
                algorithms=["RS256"],
                issuer="aegis-cloud",
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise LicenseValidationError("JWT token has expired")
        except jwt.InvalidTokenError as e:
            raise LicenseValidationError(f"Invalid JWT token: {e}")

    def _fetch_public_key(self):
        """Fetch public key from API for JWT verification."""
        try:
            import urllib.request
            import urllib.error

            url = f"{self.api_endpoint}/v1/license/public-key"
            # Avoid circular import
            try:
                from importlib.metadata import version
                sdk_version = version("aegis-sdk")
            except:
                sdk_version = "unknown"
            headers = {"User-Agent": f"aegis-sdk/{sdk_version}"}

            request = urllib.request.Request(url, headers=headers, method="GET")

            try:
                with urllib.request.urlopen(request, timeout=10) as response:
                    data = json.loads(response.read().decode())
                    if "public_key" in data:
                        self.public_key = data["public_key"]
                        # Cache the public key
                        try:
                            with open(self.public_key_file, "w") as f:
                                f.write(self.public_key)
                        except OSError:
                            pass
            except (urllib.error.HTTPError, urllib.error.URLError):
                # Try to load from cache
                if self.public_key_file.exists():
                    with open(self.public_key_file, "r") as f:
                        self.public_key = f.read()

            self._public_key_fetched = True

        except ImportError:
            pass  # No urllib, use default key

    def _fetch_license(self) -> LicenseInfo:
        """Fetch license from API.

        Returns:
            LicenseInfo from API response

        Raises:
            LicenseValidationError: If API call fails
        """
        try:
            import urllib.request
            import urllib.error

            url = f"{self.api_endpoint}/v1/license/validate"
            # Avoid circular import
            try:
                from importlib.metadata import version
                sdk_version = version("aegis-sdk")
            except:
                sdk_version = "unknown"

            headers = {
                "Authorization": f"Bearer {self.license_key}",
                "Content-Type": "application/json",
                "User-Agent": f"aegis-sdk/{sdk_version}",
            }

            request = urllib.request.Request(url, headers=headers, method="GET")

            try:
                with urllib.request.urlopen(request, timeout=10) as response:
                    data = json.loads(response.read().decode())

                    # Verify JWT if present and enabled
                    if self.verify_jwt and data.get("jwt_token"):
                        self._verify_jwt_token(data["jwt_token"])

                    return LicenseInfo.from_response(data)
            except urllib.error.HTTPError as e:
                if e.code == 401:
                    raise LicenseValidationError("Invalid license key")
                elif e.code == 403:
                    raise LicenseValidationError("License expired or suspended")
                else:
                    raise LicenseValidationError(f"API error: {e.code}")
            except urllib.error.URLError as e:
                raise LicenseValidationError(f"Connection error: {e.reason}")

        except ImportError:
            # Fallback for environments without urllib
            raise LicenseValidationError("HTTP client not available")

    def _load_cache(self) -> Optional[CachedLicense]:
        """Load cached license from file."""
        try:
            if not self.cache_file.exists():
                return None

            with open(self.cache_file, "r") as f:
                data = json.load(f)
                return CachedLicense.from_dict(data)
        except (json.JSONDecodeError, KeyError, FileNotFoundError):
            return None

    def _save_cache(self, license_info: LicenseInfo):
        """Save license to cache file."""
        cached = CachedLicense(
            license_info=license_info,
            cached_at=time.time(),
            policy_hash=hashlib.sha256(
                json.dumps(license_info.policy_config, sort_keys=True).encode()
            ).hexdigest()[:16],
            jwt_token=license_info.jwt_token,
        )
        self._cached_license = cached

        try:
            with open(self.cache_file, "w") as f:
                json.dump(cached.to_dict(), f, indent=2)
        except OSError:
            pass  # Silently fail cache writes


class OfflineLicenseManager(LicenseManager):
    """License manager for completely offline/air-gapped environments.

    This manager reads license information from a local file
    instead of connecting to Aegis Cloud API.

    Example:
        manager = OfflineLicenseManager(
            license_file="/path/to/aegis_license.json"
        )
        info = manager.validate()
    """

    def __init__(
        self,
        license_file: Path,
        cache_dir: Optional[Path] = None,
        verify_jwt: bool = False,
        public_key: Optional[str] = None,
    ):
        """Initialize offline license manager.

        Args:
            license_file: Path to offline license file
            cache_dir: Directory for cache files
            verify_jwt: If True, verify JWT signature in license file
            public_key: Custom public key for JWT verification
        """
        self.license_file = Path(license_file)

        # Extract license key from file for parent class
        license_data = self._load_license_file()
        license_key = license_data.get("license_key", "offline")

        super().__init__(
            license_key=license_key,
            cache_dir=cache_dir,
            offline_mode=True,
            verify_jwt=verify_jwt,
            public_key=public_key,
        )

        self._license_data = license_data

    def _load_license_file(self) -> dict:
        """Load license data from file."""
        if not self.license_file.exists():
            raise LicenseValidationError(
                f"License file not found: {self.license_file}"
            )

        try:
            with open(self.license_file, "r") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise LicenseValidationError(f"Invalid license file: {e}")

    def validate(self, force_refresh: bool = False) -> LicenseInfo:
        """Validate offline license.

        Args:
            force_refresh: If True, reload license file

        Returns:
            LicenseInfo from license file
        """
        if force_refresh:
            self._license_data = self._load_license_file()

        # Verify JWT if present and enabled
        jwt_token = self._license_data.get("jwt_token")
        if self.verify_jwt and jwt_token:
            self._verify_jwt_token(jwt_token)

        # Check expiration
        expires = self._license_data.get("expires", "")
        if expires:
            try:
                exp_date = datetime.fromisoformat(expires.replace("Z", "+00:00"))
                if datetime.now(exp_date.tzinfo) > exp_date:
                    raise LicenseValidationError("Offline license has expired")
            except ValueError:
                pass  # Invalid date format, skip check

        return LicenseInfo(
            valid=self._license_data.get("valid", True),
            expires=expires,
            org_id=self._license_data.get("org_id", "offline"),
            policy_version=self._license_data.get("policy_version", "v1"),
            policy_config=self._license_data.get("policy_config", {}),
            policy_groups=self._license_data.get("policy_groups", []),
            default_policy_group=self._license_data.get("default_policy_group"),
            license_type=self._license_data.get("license_type", "standard"),
            jwt_token=jwt_token,
        )


def validate_license_key(license_key: str) -> LicenseInfo:
    """Convenience function to validate a license key.

    Args:
        license_key: Aegis license key

    Returns:
        LicenseInfo with validation details

    Raises:
        LicenseValidationError: If validation fails
    """
    manager = LicenseManager(license_key)
    return manager.validate()


def create_offline_license(
    output_path: Path,
    org_id: str,
    expires: str,
    policy_config: Optional[dict] = None,
    policy_groups: Optional[list[str]] = None,
    default_policy_group: Optional[str] = None,
) -> None:
    """Create an offline license file.

    This is typically used by Aegis to generate license files
    for air-gapped customers.

    Args:
        output_path: Path for output license file
        org_id: Organization ID
        expires: Expiration date (ISO format)
        policy_config: Optional policy configuration
        policy_groups: Optional list of policy group slugs
        default_policy_group: Optional default policy group
    """
    license_data = {
        "valid": True,
        "org_id": org_id,
        "expires": expires,
        "policy_version": "v1",
        "policy_config": policy_config or {},
        "policy_groups": policy_groups or [],
        "default_policy_group": default_policy_group,
        "license_type": "standard",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    with open(output_path, "w") as f:
        json.dump(license_data, f, indent=2)
