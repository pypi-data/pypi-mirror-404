"""LLM Gateway - Base class for LLM integrations.

This module provides the core gateway functionality for masking
prompts before sending to LLM providers. It handles:
- Prompt masking with reversible option
- Policy evaluation
- Audit logging (optional)
- Metrics collection (optional)
"""

from pathlib import Path
from typing import Callable, Optional, Union
import json
import time
from datetime import datetime, timezone

from aegis_sdk.types import (
    Decision,
    DetectedItem,
    MaskedPrompt,
    AegisBlockedError,
)
from aegis_sdk.core.detector import PatternDetector
from aegis_sdk.core.masker import Masker, mask_text_reversible
from aegis_sdk.core.policy import PolicyEngine


def mask_prompt(
    prompt: str,
    destination: str = "AI_TOOL",
    policy_config: Optional[dict] = None,
    reversible: bool = False,
) -> MaskedPrompt:
    """Mask sensitive data in a prompt.

    This is a convenience function for one-off prompt masking.
    For repeated use, create an AegisLLMGateway instance.

    Args:
        prompt: The prompt text to mask
        destination: Target destination for policy evaluation
        policy_config: Optional custom policy configuration
        reversible: Whether to enable reversible masking

    Returns:
        MaskedPrompt with masked text and decision

    Example:
        result = mask_prompt("Email john@example.com for help")
        if result.is_blocked:
            raise Exception(result.block_reason)
        send_to_llm(result.masked_text)
    """
    gateway = AegisLLMGateway(policy_config=policy_config)
    return gateway.mask_prompt(prompt, destination, reversible)


def mask_messages(
    messages: list[dict],
    destination: str = "AI_TOOL",
    policy_config: Optional[dict] = None,
    roles_to_mask: Optional[list[str]] = None,
) -> tuple[list[dict], list[DetectedItem]]:
    """Mask sensitive data in a list of chat messages.

    This function processes a list of chat messages (OpenAI format)
    and masks user content while preserving system/assistant messages.

    Args:
        messages: List of message dicts with 'role' and 'content'
        destination: Target destination for policy evaluation
        policy_config: Optional custom policy configuration
        roles_to_mask: Roles to mask (default: ["user"])

    Returns:
        Tuple of (masked_messages, all_detected_items)

    Raises:
        AegisBlockedError: If any message contains blocked content

    Example:
        messages = [
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "My email is john@example.com"}
        ]
        masked, detected = mask_messages(messages)
    """
    gateway = AegisLLMGateway(policy_config=policy_config)
    return gateway.mask_messages(messages, destination, roles_to_mask)


class AegisLLMGateway:
    """Gateway for LLM integrations with automatic PII masking.

    This class provides the core functionality for masking prompts
    and messages before sending to LLM providers. It supports:
    - Single prompt masking
    - Chat message list masking
    - Reversible masking for response unmasking
    - Policy-based blocking
    - Optional audit logging

    Example:
        gateway = AegisLLMGateway()

        # Mask a single prompt
        result = gateway.mask_prompt("Contact john@example.com")
        if result.is_blocked:
            print(f"Blocked: {result.block_reason}")
        else:
            response = llm_call(result.masked_text)

        # Mask chat messages
        messages = [{"role": "user", "content": "My SSN is 123-45-6789"}]
        masked_messages, detected = gateway.mask_messages(messages)
    """

    def __init__(
        self,
        policy_config: Optional[dict] = None,
        include_samples: bool = True,
        enable_audit: bool = False,
        audit_path: Optional[Union[str, Path]] = None,
        on_mask: Optional[Callable[[MaskedPrompt], None]] = None,
    ):
        """Initialize LLM Gateway.

        Args:
            policy_config: Optional custom policy configuration
            include_samples: Whether to include masked samples in detections
            enable_audit: Whether to log masking operations
            audit_path: Path for audit log file
            on_mask: Optional callback called after each mask operation
        """
        self.detector = PatternDetector(include_samples=include_samples)
        self.masker = Masker()
        self.policy = PolicyEngine(policy_config)
        self.enable_audit = enable_audit
        self.audit_path = Path(audit_path) if audit_path else None
        self.on_mask = on_mask
        self._mask_map: dict[str, str] = {}
        self._last_detected: list[DetectedItem] = []

    def mask_prompt(
        self,
        prompt: str,
        destination: str = "AI_TOOL",
        reversible: bool = False,
    ) -> MaskedPrompt:
        """Mask sensitive data in a prompt.

        Args:
            prompt: The prompt text to mask
            destination: Target destination for policy evaluation
            reversible: Whether to store mapping for later unmasking

        Returns:
            MaskedPrompt with masked text and decision
        """
        start_time = time.time()

        # Detect sensitive data
        detected = self.detector.detect(prompt)
        self._last_detected = detected

        # Evaluate policy
        decision, summary, suggested_fix = self.policy.evaluate(destination, detected)

        # Handle blocked content
        if decision == Decision.BLOCKED:
            result = MaskedPrompt(
                masked_text=None,
                decision=decision,
                detected=detected,
                block_reason=self.policy.get_block_reason(detected),
            )
            self._log_audit("mask_prompt", prompt, result, time.time() - start_time)
            if self.on_mask:
                self.on_mask(result)
            return result

        # Handle allowed content (no masking needed)
        if decision == Decision.ALLOWED:
            result = MaskedPrompt(
                masked_text=prompt,
                decision=decision,
                detected=[],
            )
            self._log_audit("mask_prompt", prompt, result, time.time() - start_time)
            if self.on_mask:
                self.on_mask(result)
            return result

        # Mask content
        if reversible:
            masked_text, mask_map = mask_text_reversible(prompt)
            self._mask_map = mask_map
        else:
            masked_text = self.masker.mask_text(prompt)

        result = MaskedPrompt(
            masked_text=masked_text,
            decision=decision,
            detected=detected,
        )

        self._log_audit("mask_prompt", prompt, result, time.time() - start_time)
        if self.on_mask:
            self.on_mask(result)

        return result

    def mask_messages(
        self,
        messages: list[dict],
        destination: str = "AI_TOOL",
        roles_to_mask: Optional[list[str]] = None,
    ) -> tuple[list[dict], list[DetectedItem]]:
        """Mask sensitive data in chat messages.

        Args:
            messages: List of message dicts with 'role' and 'content'
            destination: Target destination for policy evaluation
            roles_to_mask: Roles to mask (default: ["user"])

        Returns:
            Tuple of (masked_messages, all_detected_items)

        Raises:
            AegisBlockedError: If any message contains blocked content
        """
        if roles_to_mask is None:
            roles_to_mask = ["user"]

        masked_messages = []
        all_detected: list[DetectedItem] = []

        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")

            # Skip non-string content (e.g., multimodal messages)
            if not isinstance(content, str):
                masked_messages.append(msg.copy())
                continue

            # Only mask specified roles
            if role not in roles_to_mask:
                masked_messages.append(msg.copy())
                continue

            # Mask this message
            result = self.mask_prompt(content, destination)

            if result.is_blocked:
                raise AegisBlockedError(
                    result.block_reason or "Content blocked by policy",
                    detected=result.detected,
                )

            all_detected.extend(result.detected)

            masked_msg = msg.copy()
            masked_msg["content"] = result.masked_text
            masked_messages.append(masked_msg)

        return masked_messages, all_detected

    def unmask_response(self, response: str) -> str:
        """Unmask a response using stored mask map.

        This only works if the previous mask_prompt call used reversible=True.

        Args:
            response: The LLM response text

        Returns:
            Response with original values restored
        """
        if not self._mask_map:
            return response

        result = response
        for masked_val, original_val in self._mask_map.items():
            result = result.replace(masked_val, original_val)

        return result

    def get_last_detected(self) -> list[DetectedItem]:
        """Get detected items from last mask operation."""
        return self._last_detected

    def get_mask_map(self) -> dict[str, str]:
        """Get current mask map for reversible masking."""
        return self._mask_map.copy()

    def clear_mask_map(self):
        """Clear stored mask map."""
        self._mask_map = {}

    def _log_audit(
        self,
        operation: str,
        original: str,
        result: MaskedPrompt,
        duration: float,
    ):
        """Log masking operation to audit file."""
        if not self.enable_audit or not self.audit_path:
            return

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "operation": operation,
            "decision": result.decision,
            "detected_types": [d.type for d in result.detected],
            "detected_counts": {d.type: d.count for d in result.detected},
            "bytes_processed": len(original.encode("utf-8")),
            "duration_ms": round(duration * 1000, 2),
            "blocked": result.is_blocked,
        }

        try:
            with open(self.audit_path, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            pass  # Silently fail audit logging


class StreamingGateway(AegisLLMGateway):
    """Gateway with streaming support for LLM responses.

    This gateway can handle streaming responses from LLMs,
    accumulating content and providing incremental masking.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._stream_buffer = ""
        self._stream_detected: list[DetectedItem] = []

    def process_stream_chunk(
        self,
        chunk: str,
        destination: str = "AI_TOOL",
    ) -> tuple[str, bool]:
        """Process a streaming chunk.

        Args:
            chunk: Text chunk from stream
            destination: Target destination

        Returns:
            Tuple of (processed_chunk, should_block)
        """
        self._stream_buffer += chunk

        # Detect in accumulated buffer
        detected = self.detector.detect(self._stream_buffer)

        # Check if we should block
        decision, _, _ = self.policy.evaluate(destination, detected)
        if decision == Decision.BLOCKED:
            return "", True

        self._stream_detected = detected
        return chunk, False

    def finalize_stream(
        self,
        destination: str = "AI_TOOL",
    ) -> tuple[str, list[DetectedItem]]:
        """Finalize streaming and get masked content.

        Args:
            destination: Target destination

        Returns:
            Tuple of (masked_content, detected_items)
        """
        result = self.mask_prompt(self._stream_buffer, destination)

        # Clear buffer
        buffer = self._stream_buffer
        self._stream_buffer = ""
        detected = self._stream_detected
        self._stream_detected = []

        if result.is_blocked:
            raise AegisBlockedError(
                result.block_reason or "Content blocked",
                detected=result.detected,
            )

        return result.masked_text or buffer, detected

    def reset_stream(self):
        """Reset stream state."""
        self._stream_buffer = ""
        self._stream_detected = []
