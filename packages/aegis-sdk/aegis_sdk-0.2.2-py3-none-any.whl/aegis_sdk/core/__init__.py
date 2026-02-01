"""Core detection and masking modules."""

from aegis_sdk.core.detector import (
    PatternDetector,
    detect,
    detect_patterns,
    has_pii,
    has_detection_type,
)
from aegis_sdk.core.masker import Masker, mask_text, mask_content
from aegis_sdk.core.policy import PolicyEngine, evaluate_decision

__all__ = [
    "PatternDetector",
    "detect",
    "detect_patterns",
    "has_pii",
    "has_detection_type",
    "Masker",
    "mask_text",
    "mask_content",
    "PolicyEngine",
    "evaluate_decision",
]
