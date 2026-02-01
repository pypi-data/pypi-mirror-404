"""Aegis SDK - On-premise PII detection and masking for AI applications.

This SDK provides:
- Pattern-based detection of PII, PHI, and other sensitive data
- Format-preserving masking
- Policy-based decision engine
- LLM integration wrappers (OpenAI, LangChain)
- Streaming file processing for large files

Example usage:

    # Simple text processing
    from aegis_sdk import Aegis

    aegis = Aegis()
    result = aegis.process(
        text="Contact john@example.com",
        destination="AI_TOOL"
    )
    print(result.decision)      # ALLOWED_WITH_MASKING
    print(result.masked_content) # Contact j***@example.com

    # With OpenAI integration (requires: pip install aegis-sdk[openai])
    from aegis_sdk import AegisOpenAI

    client = AegisOpenAI(api_key="sk-...")
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": user_input}]
    )
    # PII automatically masked before sending to OpenAI
"""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("aegis-sdk")
except PackageNotFoundError:
    __version__ = "0.0.0-dev"  # Fallback for development

# Core types
from aegis_sdk.types import (
    Decision,
    Destination,
    DetectedItem,
    DetectionType,
    Finding,
    MaskedPrompt,
    ProcessingResult,
    AegisError,
    AegisBlockedError,
    LicenseValidationError,
    PolicyError,
)

# Core modules
from aegis_sdk.core.detector import (
    PatternDetector,
    detect,
    detect_patterns,
    has_pii,
    has_detection_type,
)
from aegis_sdk.core.masker import (
    Masker,
    mask_text,
    mask_content,
)
from aegis_sdk.core.policy import (
    PolicyEngine,
    evaluate_decision,
)

# Batch processing
from aegis_sdk.types import BatchProcessingResult
from aegis_sdk.batch.processor import (
    StreamingProcessor,
    process_file,
)
from aegis_sdk.batch.csv_processor import (
    CSVStreamProcessor,
    process_csv_file,
)

# LLM Gateway
from aegis_sdk.llm.gateway import (
    AegisLLMGateway,
    StreamingGateway,
    mask_prompt,
    mask_messages,
)

# Optional LLM provider wrappers (require optional dependencies)
try:
    from aegis_sdk.llm.openai_wrapper import AegisOpenAI
except ImportError:
    AegisOpenAI = None  # type: ignore

try:
    from aegis_sdk.llm.anthropic_wrapper import AegisAnthropic
except ImportError:
    AegisAnthropic = None  # type: ignore

# License, Metrics, Audit
from aegis_sdk.license import (
    LicenseManager,
    OfflineLicenseManager,
    validate_license_key,
    create_offline_license,
)
from aegis_sdk.metrics import (
    MetricsReporter,
    LocalMetricsCollector,
)
from aegis_sdk.audit import (
    AuditLog,
    GDPRAuditLog,
)


class Aegis:
    """Main Aegis SDK class for simple text processing.

    This class provides a high-level interface for detecting and masking
    sensitive data in text content.

    Example:
        # Basic usage with license (uses org's default policy)
        aegis = Aegis(license_key="aegis_lic_xxx")
        result = aegis.process("Contact john@example.com", destination="AI_TOOL")
        print(result.masked_content)  # Contact j***@example.com

        # With specific policy group (department)
        aegis = Aegis(license_key="aegis_lic_xxx", policy_group="marketing")
        result = aegis.process("Call 555-1234", destination="VENDOR")

        # Switch department without re-initializing
        engineering = aegis.with_policy_group("engineering")
    """

    def __init__(
        self,
        license_key: str,
        include_samples: bool = True,
        policy_config: dict = None,
        policy_group: str = None,
        auto_fetch_policy: bool = True,
        api_endpoint: str = None,
    ):
        """Initialize Aegis SDK.

        Args:
            license_key: Required license key for cloud features
            include_samples: Whether to include masked samples in detection results
            policy_config: Optional custom policy configuration (overrides cloud policy)
            policy_group: Policy group/department to use (e.g., "marketing", "engineering")
            auto_fetch_policy: If True and license_key provided, fetch policy from cloud
            api_endpoint: Optional API endpoint override for license validation
        """
        self.license_key = license_key
        self._include_samples = include_samples
        self._policy_group = policy_group
        self._license_manager = None
        self._license_info = None

        self.detector = PatternDetector(include_samples=include_samples)
        self.masker = Masker()

        # License key is now required - validate it
        manager_kwargs = {"policy_group": policy_group}
        if api_endpoint:
            manager_kwargs["api_endpoint"] = api_endpoint

        self._license_manager = LicenseManager(license_key, **manager_kwargs)
        self._license_info = self._license_manager.validate()

        # Enhanced policy resolution hierarchy
        effective_policy = policy_config
        if auto_fetch_policy and not policy_config:
            if policy_group:
                # 1. Use specific policy group if requested
                effective_policy = self._license_info.get_policy_for_group(policy_group)
            else:
                # 2. Use org's default policy group
                default_group_policy = self._license_info.get_default_group_policy()
                if default_group_policy:
                    effective_policy = default_group_policy
                # 3. Fallback will be handled by PolicyEngine (uses DEFAULT_POLICY)

        self.policy = PolicyEngine(effective_policy)

    @property
    def policy_group(self) -> str:
        """Get current policy group."""
        # Return explicitly set policy group, or license default
        if self._policy_group is not None:
            return self._policy_group
        if self._license_info and self._license_info.default_policy_group:
            return self._license_info.default_policy_group
        return None

    @property
    def policy_groups(self) -> list[str]:
        """Get available policy groups from license.

        Returns:
            List of policy group slugs, or empty list if not using license.
        """
        if self._license_info:
            return self._license_info.policy_groups
        return []

    @property
    def license_info(self):
        """Get license info if available."""
        return self._license_info

    def with_policy_group(self, group: str) -> "Aegis":
        """Create a new Aegis instance with a different policy group.

        This allows using different department policies with the same license.

        Args:
            group: Policy group slug (e.g., "marketing", "engineering")

        Returns:
            New Aegis instance configured for the specified policy group

        Example:
            aegis = Aegis(license_key="aegis_lic_xxx")
            marketing = aegis.with_policy_group("marketing")
            engineering = aegis.with_policy_group("engineering")
        """
        if not self.license_key:
            raise ValueError("with_policy_group requires a license_key")

        # Get policy config for the group
        policy_config = None
        if self._license_info:
            policy_config = self._license_info.get_policy_for_group(group)

        return Aegis(
            license_key=self.license_key,
            include_samples=self._include_samples,
            policy_config=policy_config,
            policy_group=group,
            auto_fetch_policy=False,  # Already have the policy
        )

    def process(
        self,
        text: str,
        destination: str = "AI_TOOL",
    ) -> ProcessingResult:
        """Process text content and return decision with masked content.

        Args:
            text: Text content to process
            destination: Target destination (AI_TOOL, VENDOR, CUSTOMER)

        Returns:
            ProcessingResult with decision, detected items, and masked content
        """
        # Detect sensitive data
        detected = self.detector.detect(text)

        # Evaluate policy
        decision, summary, suggested_fix = self.policy.evaluate(destination, detected)

        # Mask content if needed
        masked_content = None
        if decision == Decision.ALLOWED_WITH_MASKING:
            masked_content = self.masker.mask_text(text)
        elif decision == Decision.ALLOWED:
            masked_content = text

        return ProcessingResult(
            decision=decision,
            summary=summary,
            detected=detected,
            masked_content=masked_content,
            suggested_fix=suggested_fix,
            bytes_processed=len(text.encode("utf-8")),
        )

    def detect(self, text: str) -> list[DetectedItem]:
        """Detect sensitive data in text.

        Args:
            text: Text content to scan

        Returns:
            List of DetectedItem with detection results
        """
        return self.detector.detect(text)

    def mask(self, text: str) -> str:
        """Mask sensitive data in text.

        Args:
            text: Text content to mask

        Returns:
            Masked text
        """
        return self.masker.mask_text(text)

    def evaluate(
        self, destination: str, detected: list[DetectedItem]
    ) -> Decision:
        """Evaluate policy for detected items.

        Args:
            destination: Target destination
            detected: List of detected items

        Returns:
            Decision enum value
        """
        return self.policy.get_decision(destination, detected)


# Export all public symbols
__all__ = [
    # Version
    "__version__",
    # Main class
    "Aegis",
    # Types
    "Decision",
    "Destination",
    "DetectedItem",
    "DetectionType",
    "Finding",
    "MaskedPrompt",
    "ProcessingResult",
    "BatchProcessingResult",
    # Errors
    "AegisError",
    "AegisBlockedError",
    "LicenseValidationError",
    "PolicyError",
    # Core classes
    "PatternDetector",
    "Masker",
    "PolicyEngine",
    # Batch processing
    "StreamingProcessor",
    "CSVStreamProcessor",
    # LLM Gateway
    "AegisLLMGateway",
    "StreamingGateway",
    # LLM Wrappers (optional dependencies)
    "AegisOpenAI",
    "AegisAnthropic",
    # License & Metrics
    "LicenseManager",
    "OfflineLicenseManager",
    "MetricsReporter",
    "LocalMetricsCollector",
    # Audit
    "AuditLog",
    "GDPRAuditLog",
    # Functions
    "detect",
    "detect_patterns",
    "has_pii",
    "has_detection_type",
    "mask_text",
    "mask_content",
    "evaluate_decision",
    "process_file",
    "process_csv_file",
    "mask_prompt",
    "mask_messages",
    "validate_license_key",
    "create_offline_license",
]
