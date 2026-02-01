"""Policy evaluation module.

This module provides decision logic for determining how to handle
detected sensitive data based on destination and policy rules.
Extracted from api/app/services/rules.py for standalone SDK usage.
"""

from typing import Optional

from aegis_sdk.types import Decision, Destination, DetectedItem, DetectionType
from aegis_sdk.core.detector import has_detection_type, has_pii


# Default policy configuration
DEFAULT_POLICY = {
    "destinations": {
        Destination.AI_TOOL: {
            "mask": [
                DetectionType.EMAIL,
                DetectionType.PHONE,
                DetectionType.CREDIT_CARD,
                DetectionType.SSN,
                DetectionType.IBAN,
            ],
            "block_with_phi": [
                DetectionType.EMAIL,
                DetectionType.PHONE,
                DetectionType.SSN,
            ],
        },
        Destination.VENDOR: {
            "mask": [
                DetectionType.EMAIL,
                DetectionType.PHONE,
                DetectionType.CREDIT_CARD,
                DetectionType.SSN,
                DetectionType.IBAN,
            ],
            "block": [DetectionType.PHI_KEYWORD],
        },
        Destination.CUSTOMER: {
            "block": [DetectionType.API_SECRET],
        },
    }
}


def evaluate_decision(
    destination: str,
    detected: list[DetectedItem],
    policy: Optional[dict] = None,
) -> tuple[Decision, str, Optional[str]]:
    """Evaluate the decision based on destination and detected items.

    Args:
        destination: Target destination (AI_TOOL, VENDOR, CUSTOMER)
        detected: List of detected items
        policy: Optional policy configuration (reserved for future use;
                currently uses hardcoded rules per V1 spec)

    Returns:
        Tuple of (decision, summary, suggested_fix)

    Note:
        V1 uses hardcoded rules. Custom policy configurations will be
        supported in a future version with a policy DSL.
    """
    # Note: policy parameter is reserved for future use
    _ = policy
    # Normalize destination
    if isinstance(destination, str):
        destination = destination.upper()

    has_phi = has_detection_type(detected, DetectionType.PHI_KEYWORD)
    has_pii_data = has_pii(detected)
    has_secrets = has_detection_type(detected, DetectionType.API_SECRET)
    has_pii_with_phi = has_phi and has_detection_type(
        detected,
        DetectionType.EMAIL,
        DetectionType.PHONE,
        DetectionType.SSN,
    )

    if destination == Destination.AI_TOOL or destination == "AI_TOOL":
        return _evaluate_ai_tool(has_phi, has_pii_with_phi, has_pii_data)

    elif destination == Destination.VENDOR or destination == "VENDOR":
        return _evaluate_vendor(has_phi, has_pii_data)

    elif destination == Destination.CUSTOMER or destination == "CUSTOMER":
        return _evaluate_customer(has_secrets)

    # Default fallback
    return Decision.ALLOWED, "Safe to share.", None


def _evaluate_ai_tool(
    has_phi: bool, has_pii_with_phi: bool, has_pii_data: bool
) -> tuple[Decision, str, Optional[str]]:
    """AI Tool destination rules.

    Rules:
    - PHI + (EMAIL/PHONE/SSN) -> BLOCKED
    - PII present -> ALLOWED_WITH_MASKING
    - Clean -> ALLOWED
    """
    if has_pii_with_phi:
        return (
            Decision.BLOCKED,
            "Not safe to share — PHI with identifying information detected.",
            "Remove PHI fields or send de-identified data.",
        )

    if has_pii_data:
        return (
            Decision.ALLOWED_WITH_MASKING,
            "Sensitive data detected — masked automatically.",
            None,
        )

    return Decision.ALLOWED, "Safe to share.", None


def _evaluate_vendor(
    has_phi: bool, has_pii_data: bool
) -> tuple[Decision, str, Optional[str]]:
    """Vendor destination rules.

    Rules:
    - PHI present -> BLOCKED
    - PII present -> ALLOWED_WITH_MASKING
    - Clean -> ALLOWED
    """
    if has_phi:
        return (
            Decision.BLOCKED,
            "Not safe to share — PHI detected.",
            "Remove PHI or share aggregated/de-identified data.",
        )

    if has_pii_data:
        return (
            Decision.ALLOWED_WITH_MASKING,
            "Sensitive data detected — masked automatically.",
            None,
        )

    return Decision.ALLOWED, "Safe to share.", None


def _evaluate_customer(has_secrets: bool) -> tuple[Decision, str, Optional[str]]:
    """Customer destination rules.

    Rules:
    - API secrets -> BLOCKED
    - Otherwise -> ALLOWED
    """
    if has_secrets:
        return (
            Decision.BLOCKED,
            "Not safe to share — API secrets detected.",
            "Remove secrets/keys before sharing.",
        )

    return Decision.ALLOWED, "Safe to share.", None


class PolicyEngine:
    """Policy evaluation engine for object-oriented usage.

    This class wraps the module-level functions and provides
    additional configuration options.
    """

    def __init__(self, policy_config: Optional[dict] = None):
        """Initialize policy engine.

        Args:
            policy_config: Optional custom policy configuration
        """
        self.policy = policy_config or DEFAULT_POLICY

    def evaluate(
        self, destination: str, detected: list[DetectedItem]
    ) -> tuple[Decision, str, Optional[str]]:
        """Evaluate decision for given destination and detections.

        Args:
            destination: Target destination
            detected: List of detected items

        Returns:
            Tuple of (decision, summary, suggested_fix)
        """
        return evaluate_decision(destination, detected, self.policy)

    def get_decision(self, destination: str, detected: list[DetectedItem]) -> Decision:
        """Get just the decision enum.

        Args:
            destination: Target destination
            detected: List of detected items

        Returns:
            Decision enum value
        """
        decision, _, _ = self.evaluate(destination, detected)
        return decision

    def get_block_reason(self, detected: list[DetectedItem]) -> str:
        """Get a human-readable reason for blocking.

        Args:
            detected: List of detected items

        Returns:
            Block reason string
        """
        has_phi = has_detection_type(detected, DetectionType.PHI_KEYWORD)
        has_secrets = has_detection_type(detected, DetectionType.API_SECRET)

        if has_phi:
            return "Protected Health Information (PHI) detected"
        if has_secrets:
            return "API secrets/credentials detected"

        types = [item.type for item in detected]
        if types:
            return f"Sensitive data detected: {', '.join(types)}"

        return "Content blocked by policy"

    def is_pii_allowed(self, destination: str) -> bool:
        """Check if PII is allowed for destination (with masking).

        Args:
            destination: Target destination

        Returns:
            True if PII can be shared with masking
        """
        dest_upper = destination.upper()
        return dest_upper in (Destination.AI_TOOL, "AI_TOOL", Destination.VENDOR, "VENDOR")

    def is_phi_blocked(self, destination: str) -> bool:
        """Check if PHI is blocked for destination.

        Args:
            destination: Target destination

        Returns:
            True if PHI is blocked
        """
        dest_upper = destination.upper()
        # PHI is blocked for VENDOR, and blocked with PII for AI_TOOL
        return dest_upper in (Destination.VENDOR, "VENDOR")
