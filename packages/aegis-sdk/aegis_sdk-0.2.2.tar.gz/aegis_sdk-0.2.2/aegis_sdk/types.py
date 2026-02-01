"""Data types for Aegis SDK.

Core types (DetectionType, Decision, Destination, Finding, DetectedItem)
are imported from aegis-core for consistency. SDK-specific types like
ProcessingResult, MaskedPrompt, etc. are defined here.
"""

from dataclasses import dataclass, field
from typing import Optional

# Re-export core types from aegis-core
from aegis_core import (
    Decision,
    Destination,
    DetectedItem,
    DetectionType,
    Finding,
)


@dataclass
class ProcessingResult:
    """Result of processing content through Aegis."""

    decision: Decision
    summary: str
    detected: list[DetectedItem] = field(default_factory=list)
    masked_content: Optional[str] = None
    suggested_fix: Optional[str] = None
    bytes_processed: int = 0

    @property
    def is_allowed(self) -> bool:
        """Check if content is allowed (with or without masking)."""
        return self.decision in (Decision.ALLOWED, Decision.ALLOWED_WITH_MASKING)

    @property
    def is_blocked(self) -> bool:
        """Check if content is blocked."""
        return self.decision == Decision.BLOCKED

    @property
    def requires_masking(self) -> bool:
        """Check if content requires masking."""
        return self.decision == Decision.ALLOWED_WITH_MASKING


@dataclass
class MaskedPrompt:
    """Result of masking a prompt for LLM usage."""

    masked_text: Optional[str]
    decision: Decision
    detected: list[DetectedItem] = field(default_factory=list)
    block_reason: Optional[str] = None

    @property
    def is_blocked(self) -> bool:
        """Check if prompt was blocked."""
        return self.decision == Decision.BLOCKED


@dataclass
class LicenseInfo:
    """License validation information."""

    valid: bool
    expires: str
    org_id: str
    policy_version: str
    policy_config: dict = field(default_factory=dict)
    policy_groups: list[str] = field(default_factory=list)
    default_policy_group: Optional[str] = None
    license_type: str = "standard"
    jwt_token: Optional[str] = None
    cached_at: Optional[str] = None

    @classmethod
    def from_response(cls, data: dict) -> "LicenseInfo":
        """Create LicenseInfo from API response."""
        return cls(
            valid=data.get("valid", False),
            expires=data.get("expires", ""),
            org_id=data.get("org_id", ""),
            policy_version=data.get("policy_version", ""),
            policy_config=data.get("policy_config", {}),
            policy_groups=data.get("policy_groups", []),
            default_policy_group=data.get("default_policy_group"),
            license_type=data.get("license_type", "standard"),
            jwt_token=data.get("jwt_token"),
        )

    def get_policy_for_group(self, group: Optional[str] = None) -> dict:
        """Get policy config for a specific group.

        Args:
            group: Policy group slug. If None, uses default_policy_group.

        Returns:
            Policy configuration dict for the group.
        """
        target_group = group or self.default_policy_group
        if target_group and target_group in self.policy_config:
            return self.policy_config[target_group]
        # Return first available or empty dict
        if self.policy_config:
            first_key = next(iter(self.policy_config))
            return self.policy_config[first_key]
        return {}

    def get_default_group_policy(self) -> Optional[dict]:
        """Get policy config for the default group.

        Returns:
            Default group policy configuration, or None if not available.
        """
        if self.default_policy_group and self.default_policy_group in self.policy_config:
            return self.policy_config[self.default_policy_group]
        return None


class AegisError(Exception):
    """Base exception for Aegis SDK errors."""

    pass


class AegisBlockedError(AegisError):
    """Raised when content is blocked by policy."""

    def __init__(self, reason: str, detected: list[DetectedItem] = None):
        self.reason = reason
        self.detected = detected or []
        super().__init__(reason)


class LicenseValidationError(AegisError):
    """Raised when license validation fails."""

    pass


class PolicyError(AegisError):
    """Raised when policy evaluation fails."""

    pass


@dataclass
class BatchProcessingResult:
    """Result of batch/streaming file processing."""

    decision: Decision
    summary: str
    detected: list[DetectedItem] = field(default_factory=list)
    suggested_fix: Optional[str] = None
    bytes_processed: int = 0
    chunks_processed: int = 0
    blocked_early: bool = False
    input_path: Optional[str] = None
    output_path: Optional[str] = None

    @property
    def is_allowed(self) -> bool:
        """Check if content is allowed (with or without masking)."""
        return self.decision in (Decision.ALLOWED, Decision.ALLOWED_WITH_MASKING)

    @property
    def is_blocked(self) -> bool:
        """Check if content is blocked."""
        return self.decision == Decision.BLOCKED

    @property
    def requires_masking(self) -> bool:
        """Check if content requires masking."""
        return self.decision == Decision.ALLOWED_WITH_MASKING

    @property
    def mb_processed(self) -> float:
        """Get megabytes processed."""
        return self.bytes_processed / (1024 * 1024)
