"""Data masking module.

This module re-exports masking functionality from aegis-core
and provides additional format-specific masking (CSV, JSON).
"""

import csv
import io
import json
from typing import Optional

# Re-export core masking from aegis-core
from aegis_core import (
    DetectionType,
    Finding,
    Masker as CoreMasker,
    detect_patterns,
    mask_api_secret,
    mask_email,
    mask_phone,
    mask_credit_card,
    mask_ssn,
    mask_iban,
    mask_text,
    mask_text_reversible,
    mask_value,
    unmask_text,
)


# Mapping of detection types to masking functions
MASKERS: dict[str, callable] = {
    DetectionType.EMAIL: mask_email,
    DetectionType.PHONE: mask_phone,
    DetectionType.CREDIT_CARD: mask_credit_card,
    DetectionType.SSN: mask_ssn,
    DetectionType.API_SECRET: mask_api_secret,
    DetectionType.IBAN: mask_iban,
}


def get_masker(detection_type: str) -> Optional[callable]:
    """Get the appropriate masking function for a detection type.

    Args:
        detection_type: The type of detection

    Returns:
        Masking function or None if not found
    """
    return MASKERS.get(detection_type)


def mask_csv_content(content: str) -> str:
    """Mask sensitive data in CSV content.

    Args:
        content: CSV content to mask

    Returns:
        CSV content with sensitive data masked
    """
    try:
        reader = csv.reader(io.StringIO(content))
        rows = list(reader)
    except csv.Error:
        # If CSV parsing fails, fall back to text masking
        return mask_text(content)

    masked_rows = []
    for row in rows:
        masked_row = [mask_text(cell) for cell in row]
        masked_rows.append(masked_row)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerows(masked_rows)
    return output.getvalue()


def mask_json_content(content: str) -> str:
    """Mask sensitive data in JSON content.

    Args:
        content: JSON content to mask

    Returns:
        JSON content with sensitive data masked
    """
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        # If JSON parsing fails, fall back to text masking
        return mask_text(content)

    def mask_json_value(value):
        if isinstance(value, str):
            return mask_text(value)
        elif isinstance(value, dict):
            return {k: mask_json_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [mask_json_value(item) for item in value]
        return value

    masked_data = mask_json_value(data)
    return json.dumps(masked_data, indent=2)


def mask_content(content: str, file_extension: Optional[str] = None) -> str:
    """Mask content based on file type.

    Args:
        content: Content to mask
        file_extension: File extension (e.g., ".csv", ".json")

    Returns:
        Masked content
    """
    if file_extension:
        ext = file_extension.lower()
        if ext == ".csv":
            return mask_csv_content(content)
        elif ext == ".json":
            return mask_json_content(content)

    # Default to text masking
    return mask_text(content)


class Masker:
    """Masker class for object-oriented usage.

    This class wraps the module-level functions for use in contexts
    where an instantiated object is preferred.
    """

    def __init__(self):
        """Initialize masker."""
        pass

    def mask(self, content: str, file_extension: Optional[str] = None) -> str:
        """Mask sensitive data in content.

        Args:
            content: Content to mask
            file_extension: Optional file extension for format-specific masking

        Returns:
            Masked content
        """
        return mask_content(content, file_extension)

    def mask_text(self, content: str) -> str:
        """Mask sensitive data in plain text.

        Args:
            content: Text content to mask

        Returns:
            Masked text
        """
        return mask_text(content)

    def mask_reversible(self, content: str) -> tuple[str, dict[str, str]]:
        """Mask text with reversible mapping.

        Args:
            content: Text content to mask

        Returns:
            Tuple of (masked_content, mapping_dict)
        """
        return mask_text_reversible(content)

    def unmask(self, content: str, mask_map: dict[str, str]) -> str:
        """Restore masked values using a mask map.

        Args:
            content: Masked content
            mask_map: Mapping from masked values to originals

        Returns:
            Content with original values restored
        """
        return unmask_text(content, mask_map)

    def mask_csv(self, content: str) -> str:
        """Mask sensitive data in CSV content."""
        return mask_csv_content(content)

    def mask_json(self, content: str) -> str:
        """Mask sensitive data in JSON content."""
        return mask_json_content(content)


# Export all
__all__ = [
    # From aegis-core
    "mask_email",
    "mask_phone",
    "mask_credit_card",
    "mask_ssn",
    "mask_iban",
    "mask_text",
    "mask_text_reversible",
    "mask_value",
    "unmask_text",
    # Local additions
    "mask_api_secret",
    "mask_csv_content",
    "mask_json_content",
    "mask_content",
    "get_masker",
    "Masker",
    "MASKERS",
]
