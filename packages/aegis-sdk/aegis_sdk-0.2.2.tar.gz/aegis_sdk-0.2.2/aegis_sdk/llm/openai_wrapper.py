"""OpenAI integration with automatic PII masking.

This module provides drop-in replacements for OpenAI client
with automatic PII detection and masking.

Requires: pip install aegis-sdk[openai]
"""

from typing import Any, Optional, Union, Iterator
import os

from aegis_sdk.types import Decision, AegisBlockedError
from aegis_sdk.llm.gateway import AegisLLMGateway


def aegis_openai_client(
    api_key: Optional[str] = None,
    aegis_config: Optional[dict] = None,
    **openai_kwargs,
) -> "AegisOpenAI":
    """Create an Aegis-wrapped OpenAI client.

    Convenience function for creating an AegisOpenAI instance.

    Args:
        api_key: OpenAI API key (or use OPENAI_API_KEY env var)
        aegis_config: Optional Aegis configuration
        **openai_kwargs: Additional OpenAI client kwargs

    Returns:
        AegisOpenAI client instance
    """
    return AegisOpenAI(
        api_key=api_key,
        aegis_config=aegis_config,
        **openai_kwargs,
    )


class AegisOpenAI:
    """OpenAI client wrapper with automatic PII masking.

    This class wraps the OpenAI client to automatically detect
    and mask PII in user messages before sending to OpenAI.

    Example:
        from aegis_sdk.llm import AegisOpenAI

        client = AegisOpenAI(api_key="sk-...")

        # Regular chat completion - PII is automatically masked
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": "My email is john@example.com"}
            ]
        )

        # The message sent to OpenAI will have masked email
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        aegis_config: Optional[dict] = None,
        destination: str = "AI_TOOL",
        block_on_detection: bool = False,
        **openai_kwargs,
    ):
        """Initialize Aegis OpenAI wrapper.

        Args:
            api_key: OpenAI API key (or use OPENAI_API_KEY env var)
            aegis_config: Optional Aegis policy configuration
            destination: Destination for policy evaluation
            block_on_detection: If True, raise error on any PII detection
            **openai_kwargs: Additional OpenAI client configuration
        """
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self._openai_kwargs = openai_kwargs
        self._client = None
        self.destination = destination
        self.block_on_detection = block_on_detection

        # Initialize Aegis gateway
        self.gateway = AegisLLMGateway(
            policy_config=aegis_config,
            include_samples=True,
        )

        # Create chat completions wrapper
        self.chat = _ChatCompletions(self)

    def _get_client(self):
        """Lazily initialize OpenAI client."""
        if self._client is None:
            try:
                import openai
            except ImportError:
                raise ImportError(
                    "OpenAI package not installed. "
                    "Install with: pip install aegis-sdk[openai]"
                )

            self._client = openai.OpenAI(
                api_key=self._api_key,
                **self._openai_kwargs,
            )
        return self._client

    def _mask_messages(
        self,
        messages: list[dict],
    ) -> list[dict]:
        """Mask PII in messages.

        Args:
            messages: List of chat messages

        Returns:
            Messages with user content masked

        Raises:
            AegisBlockedError: If content is blocked by policy
        """
        masked_messages, detected = self.gateway.mask_messages(
            messages,
            destination=self.destination,
        )

        # Optionally block on any detection
        if self.block_on_detection and detected:
            raise AegisBlockedError(
                "PII detected in message",
                detected=detected,
            )

        return masked_messages


class _ChatCompletions:
    """Wrapper for OpenAI chat.completions."""

    def __init__(self, client: AegisOpenAI):
        self._client = client
        self.completions = _Completions(client)


class _Completions:
    """Wrapper for OpenAI chat.completions.create."""

    def __init__(self, client: AegisOpenAI):
        self._client = client

    def create(
        self,
        messages: list[dict],
        model: str = "gpt-4",
        stream: bool = False,
        **kwargs,
    ) -> Any:
        """Create a chat completion with automatic PII masking.

        Args:
            messages: List of chat messages
            model: Model to use
            stream: Whether to stream the response
            **kwargs: Additional OpenAI parameters

        Returns:
            OpenAI ChatCompletion response

        Raises:
            AegisBlockedError: If content is blocked by policy
        """
        # Mask messages
        masked_messages = self._client._mask_messages(messages)

        # Get OpenAI client
        openai_client = self._client._get_client()

        # Make the API call
        if stream:
            return self._stream_create(
                openai_client,
                masked_messages,
                model,
                **kwargs,
            )
        else:
            return openai_client.chat.completions.create(
                model=model,
                messages=masked_messages,
                **kwargs,
            )

    def _stream_create(
        self,
        openai_client,
        messages: list[dict],
        model: str,
        **kwargs,
    ) -> Iterator:
        """Handle streaming completions."""
        stream = openai_client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
            **kwargs,
        )

        for chunk in stream:
            yield chunk


class AegisAsyncOpenAI:
    """Async OpenAI client wrapper with automatic PII masking.

    This class wraps the async OpenAI client for use with asyncio.

    Example:
        from aegis_sdk.llm import AegisAsyncOpenAI

        client = AegisAsyncOpenAI(api_key="sk-...")

        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": "My email is john@example.com"}]
        )
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        aegis_config: Optional[dict] = None,
        destination: str = "AI_TOOL",
        **openai_kwargs,
    ):
        """Initialize Aegis Async OpenAI wrapper."""
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self._openai_kwargs = openai_kwargs
        self._client = None
        self.destination = destination

        self.gateway = AegisLLMGateway(
            policy_config=aegis_config,
            include_samples=True,
        )

        self.chat = _AsyncChatCompletions(self)

    def _get_client(self):
        """Lazily initialize async OpenAI client."""
        if self._client is None:
            try:
                import openai
            except ImportError:
                raise ImportError(
                    "OpenAI package not installed. "
                    "Install with: pip install aegis-sdk[openai]"
                )

            self._client = openai.AsyncOpenAI(
                api_key=self._api_key,
                **self._openai_kwargs,
            )
        return self._client

    def _mask_messages(self, messages: list[dict]) -> list[dict]:
        """Mask PII in messages."""
        masked_messages, _ = self.gateway.mask_messages(
            messages,
            destination=self.destination,
        )
        return masked_messages


class _AsyncChatCompletions:
    """Wrapper for async OpenAI chat.completions."""

    def __init__(self, client: AegisAsyncOpenAI):
        self._client = client
        self.completions = _AsyncCompletions(client)


class _AsyncCompletions:
    """Wrapper for async OpenAI chat.completions.create."""

    def __init__(self, client: AegisAsyncOpenAI):
        self._client = client

    async def create(
        self,
        messages: list[dict],
        model: str = "gpt-4",
        **kwargs,
    ) -> Any:
        """Create an async chat completion with automatic PII masking."""
        masked_messages = self._client._mask_messages(messages)
        openai_client = self._client._get_client()

        return await openai_client.chat.completions.create(
            model=model,
            messages=masked_messages,
            **kwargs,
        )
