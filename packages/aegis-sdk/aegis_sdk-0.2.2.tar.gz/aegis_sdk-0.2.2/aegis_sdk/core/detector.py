"""Sensitive data detection module.

This module re-exports detection functionality from aegis-core
for backwards compatibility. All detection logic is now in the
shared aegis-core package.
"""

# Re-export everything from aegis-core
from aegis_core import (
    # Types
    DetectionType,
    Finding,
    DetectedItem,
    PII_TYPES,
    # Pattern data
    PATTERNS,
    PHI_KEYWORDS,
    # Functions
    detect,
    detect_patterns,
    aggregate_findings,
    has_detection_type,
    has_pii,
    luhn_check,
    mask_sample,
    get_pii_types,
    # Class
    PatternDetector,
)

# For backwards compatibility, export all
__all__ = [
    "DetectionType",
    "Finding",
    "DetectedItem",
    "PII_TYPES",
    "PATTERNS",
    "PHI_KEYWORDS",
    "detect",
    "detect_patterns",
    "aggregate_findings",
    "has_detection_type",
    "has_pii",
    "luhn_check",
    "PatternDetector",
    "mask_sample",
    "get_pii_types",
]
