"""Anthropic (Claude) integration with automatic PII masking.

This module provides drop-in replacements for Anthropic client
with automatic PII detection and masking.

Requires: pip install aegis-sdk[anthropic]
"""

from typing import Any, Optional, Union
import os

from aegis_sdk.types import AegisBlockedError
from aegis_sdk.llm.gateway import AegisLLMGateway


class AegisAnthropic:
    """Anthropic client wrapper with automatic PII masking.

    This class wraps the Anthropic client to automatically detect
    and mask PII in user messages before sending to Claude.

    Example:
        from aegis_sdk.llm import AegisAnthropic

        client = AegisAnthropic(api_key="sk-ant-...")

        response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": "My email is john@example.com"}
            ]
        )
        # The message sent to Claude will have masked email
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        aegis_config: Optional[dict] = None,
        destination: str = "AI_TOOL",
        **anthropic_kwargs,
    ):
        """Initialize Aegis Anthropic wrapper.

        Args:
            api_key: Anthropic API key (or use ANTHROPIC_API_KEY env var)
            aegis_config: Optional Aegis policy configuration
            destination: Destination for policy evaluation
            **anthropic_kwargs: Additional Anthropic client configuration
        """
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self._anthropic_kwargs = anthropic_kwargs
        self._client = None
        self.destination = destination

        self.gateway = AegisLLMGateway(
            policy_config=aegis_config,
            include_samples=True,
        )

        self.messages = _Messages(self)

    def _get_client(self):
        """Lazily initialize Anthropic client."""
        if self._client is None:
            try:
                import anthropic
            except ImportError:
                raise ImportError(
                    "Anthropic package not installed. "
                    "Install with: pip install aegis-sdk[anthropic]"
                )

            self._client = anthropic.Anthropic(
                api_key=self._api_key,
                **self._anthropic_kwargs,
            )
        return self._client

    def _mask_messages(
        self,
        messages: list[dict],
    ) -> list[dict]:
        """Mask PII in messages.

        Anthropic uses the same message format as OpenAI.
        """
        masked_messages, _ = self.gateway.mask_messages(
            messages,
            destination=self.destination,
        )
        return masked_messages

    def _mask_system(self, system: Optional[str]) -> Optional[str]:
        """Optionally mask system prompt."""
        if system is None:
            return None

        result = self.gateway.mask_prompt(system, self.destination)
        if result.is_blocked:
            raise AegisBlockedError(
                result.block_reason or "System prompt blocked",
                detected=result.detected,
            )
        return result.masked_text


class _Messages:
    """Wrapper for Anthropic messages."""

    def __init__(self, client: AegisAnthropic):
        self._client = client

    def create(
        self,
        model: str,
        max_tokens: int,
        messages: list[dict],
        system: Optional[str] = None,
        stream: bool = False,
        **kwargs,
    ) -> Any:
        """Create a message with automatic PII masking.

        Args:
            model: Model to use (e.g., "claude-3-opus-20240229")
            max_tokens: Maximum tokens in response
            messages: List of chat messages
            system: Optional system prompt
            stream: Whether to stream the response
            **kwargs: Additional Anthropic parameters

        Returns:
            Anthropic Message response

        Raises:
            AegisBlockedError: If content is blocked by policy
        """
        # Mask messages and system prompt
        masked_messages = self._client._mask_messages(messages)
        masked_system = self._client._mask_system(system)

        # Get Anthropic client
        anthropic_client = self._client._get_client()

        # Build kwargs
        create_kwargs = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": masked_messages,
            **kwargs,
        }

        if masked_system:
            create_kwargs["system"] = masked_system

        if stream:
            create_kwargs["stream"] = True
            return anthropic_client.messages.create(**create_kwargs)
        else:
            return anthropic_client.messages.create(**create_kwargs)


class AegisAsyncAnthropic:
    """Async Anthropic client wrapper with automatic PII masking.

    Example:
        from aegis_sdk.llm import AegisAsyncAnthropic

        client = AegisAsyncAnthropic(api_key="sk-ant-...")

        response = await client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1024,
            messages=[{"role": "user", "content": "My email is john@example.com"}]
        )
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        aegis_config: Optional[dict] = None,
        destination: str = "AI_TOOL",
        **anthropic_kwargs,
    ):
        """Initialize Aegis Async Anthropic wrapper."""
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self._anthropic_kwargs = anthropic_kwargs
        self._client = None
        self.destination = destination

        self.gateway = AegisLLMGateway(
            policy_config=aegis_config,
            include_samples=True,
        )

        self.messages = _AsyncMessages(self)

    def _get_client(self):
        """Lazily initialize async Anthropic client."""
        if self._client is None:
            try:
                import anthropic
            except ImportError:
                raise ImportError(
                    "Anthropic package not installed. "
                    "Install with: pip install aegis-sdk[anthropic]"
                )

            self._client = anthropic.AsyncAnthropic(
                api_key=self._api_key,
                **self._anthropic_kwargs,
            )
        return self._client

    def _mask_messages(self, messages: list[dict]) -> list[dict]:
        """Mask PII in messages."""
        masked_messages, _ = self.gateway.mask_messages(
            messages,
            destination=self.destination,
        )
        return masked_messages

    def _mask_system(self, system: Optional[str]) -> Optional[str]:
        """Optionally mask system prompt."""
        if system is None:
            return None

        result = self.gateway.mask_prompt(system, self.destination)
        if result.is_blocked:
            raise AegisBlockedError(
                result.block_reason or "System prompt blocked",
                detected=result.detected,
            )
        return result.masked_text


class _AsyncMessages:
    """Wrapper for async Anthropic messages."""

    def __init__(self, client: AegisAsyncAnthropic):
        self._client = client

    async def create(
        self,
        model: str,
        max_tokens: int,
        messages: list[dict],
        system: Optional[str] = None,
        **kwargs,
    ) -> Any:
        """Create an async message with automatic PII masking."""
        masked_messages = self._client._mask_messages(messages)
        masked_system = self._client._mask_system(system)

        anthropic_client = self._client._get_client()

        create_kwargs = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": masked_messages,
            **kwargs,
        }

        if masked_system:
            create_kwargs["system"] = masked_system

        return await anthropic_client.messages.create(**create_kwargs)
