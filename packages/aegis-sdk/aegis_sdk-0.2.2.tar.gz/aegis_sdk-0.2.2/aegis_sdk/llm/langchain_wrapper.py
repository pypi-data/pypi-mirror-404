"""LangChain integration with automatic PII masking.

This module provides LangChain components for automatic PII
detection and masking in chains and agents.

Requires: pip install aegis-sdk[langchain]
"""

from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from aegis_sdk.types import AegisBlockedError, Decision
from aegis_sdk.llm.gateway import AegisLLMGateway


class AegisLangChainCallback:
    """LangChain callback handler for PII masking.

    This callback automatically masks PII in prompts before
    they are sent to the LLM.

    Example:
        from langchain.chat_models import ChatOpenAI
        from aegis_sdk.llm import AegisLangChainCallback

        callback = AegisLangChainCallback()

        llm = ChatOpenAI(
            model="gpt-4",
            callbacks=[callback]
        )

        # PII will be automatically masked
        response = llm.invoke("My email is john@example.com")
    """

    def __init__(
        self,
        aegis_config: Optional[dict] = None,
        destination: str = "AI_TOOL",
        raise_on_block: bool = True,
    ):
        """Initialize LangChain callback.

        Args:
            aegis_config: Optional Aegis policy configuration
            destination: Destination for policy evaluation
            raise_on_block: Whether to raise error on blocked content
        """
        self.gateway = AegisLLMGateway(policy_config=aegis_config)
        self.destination = destination
        self.raise_on_block = raise_on_block
        self._last_masked_prompt: Optional[str] = None

    def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Mask prompts before LLM call."""
        masked_prompts = []

        for prompt in prompts:
            result = self.gateway.mask_prompt(prompt, self.destination)

            if result.is_blocked and self.raise_on_block:
                raise AegisBlockedError(
                    result.block_reason or "Content blocked by policy",
                    detected=result.detected,
                )

            masked_prompts.append(result.masked_text or prompt)

        # Store for reference
        self._last_masked_prompt = masked_prompts[0] if masked_prompts else None

        # Replace prompts in-place
        prompts.clear()
        prompts.extend(masked_prompts)

    def on_chat_model_start(
        self,
        serialized: Dict[str, Any],
        messages: List[List[Any]],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Mask messages before chat model call."""
        for message_list in messages:
            for i, message in enumerate(message_list):
                # Handle different message types
                content = self._get_message_content(message)
                if content and self._should_mask_message(message):
                    result = self.gateway.mask_prompt(content, self.destination)

                    if result.is_blocked and self.raise_on_block:
                        raise AegisBlockedError(
                            result.block_reason or "Content blocked by policy",
                            detected=result.detected,
                        )

                    self._set_message_content(message, result.masked_text or content)

    def _get_message_content(self, message: Any) -> Optional[str]:
        """Extract content from LangChain message."""
        if hasattr(message, "content"):
            content = message.content
            if isinstance(content, str):
                return content
        elif isinstance(message, dict):
            return message.get("content")
        return None

    def _set_message_content(self, message: Any, content: str) -> None:
        """Set content on LangChain message."""
        if hasattr(message, "content"):
            message.content = content
        elif isinstance(message, dict):
            message["content"] = content

    def _should_mask_message(self, message: Any) -> bool:
        """Check if message should be masked based on role."""
        role = None
        if hasattr(message, "type"):
            role = message.type
        elif isinstance(message, dict):
            role = message.get("role") or message.get("type")

        # Mask human/user messages
        return role in ("human", "user", "HumanMessage", None)


def create_aegis_chain_wrapper(aegis_config: Optional[dict] = None):
    """Create a wrapper function for LangChain chains.

    This function creates a wrapper that can be used to add
    PII masking to any LangChain chain.

    Example:
        from langchain import LLMChain
        from aegis_sdk.llm import create_aegis_chain_wrapper

        wrap = create_aegis_chain_wrapper()

        chain = LLMChain(llm=llm, prompt=prompt)
        safe_chain = wrap(chain)

        result = safe_chain.run("My email is john@example.com")
    """
    gateway = AegisLLMGateway(policy_config=aegis_config)

    def wrapper(chain):
        """Wrap a chain with PII masking."""
        original_call = chain.__call__

        def masked_call(inputs, *args, **kwargs):
            # Mask string inputs
            if isinstance(inputs, str):
                result = gateway.mask_prompt(inputs)
                if result.is_blocked:
                    raise AegisBlockedError(
                        result.block_reason or "Content blocked",
                        detected=result.detected,
                    )
                inputs = result.masked_text

            # Mask dict inputs
            elif isinstance(inputs, dict):
                masked_inputs = {}
                for key, value in inputs.items():
                    if isinstance(value, str):
                        result = gateway.mask_prompt(value)
                        if result.is_blocked:
                            raise AegisBlockedError(
                                result.block_reason or "Content blocked",
                                detected=result.detected,
                            )
                        masked_inputs[key] = result.masked_text
                    else:
                        masked_inputs[key] = value
                inputs = masked_inputs

            return original_call(inputs, *args, **kwargs)

        chain.__call__ = masked_call
        return chain

    return wrapper


class AegisChatModel:
    """Wrapper for LangChain chat models with PII masking.

    This class wraps any LangChain chat model to add automatic
    PII masking to all messages.

    Example:
        from langchain.chat_models import ChatOpenAI
        from aegis_sdk.llm import AegisChatModel

        base_llm = ChatOpenAI(model="gpt-4")
        safe_llm = AegisChatModel(base_llm)

        response = safe_llm.invoke([
            HumanMessage(content="My SSN is 123-45-6789")
        ])
        # SSN will be masked before sending to OpenAI
    """

    def __init__(
        self,
        llm: Any,
        aegis_config: Optional[dict] = None,
        destination: str = "AI_TOOL",
    ):
        """Initialize Aegis chat model wrapper.

        Args:
            llm: The LangChain chat model to wrap
            aegis_config: Optional Aegis policy configuration
            destination: Destination for policy evaluation
        """
        self._llm = llm
        self.gateway = AegisLLMGateway(policy_config=aegis_config)
        self.destination = destination

    def invoke(self, messages: List[Any], **kwargs) -> Any:
        """Invoke the chat model with masked messages."""
        masked_messages = self._mask_messages(messages)
        return self._llm.invoke(masked_messages, **kwargs)

    async def ainvoke(self, messages: List[Any], **kwargs) -> Any:
        """Async invoke with masked messages."""
        masked_messages = self._mask_messages(messages)
        return await self._llm.ainvoke(masked_messages, **kwargs)

    def _mask_messages(self, messages: List[Any]) -> List[Any]:
        """Mask PII in messages."""
        masked = []

        for msg in messages:
            if hasattr(msg, "content") and isinstance(msg.content, str):
                # Check if this is a user message
                msg_type = getattr(msg, "type", None)
                if msg_type in ("human", "user", None):
                    result = self.gateway.mask_prompt(
                        msg.content,
                        self.destination,
                    )

                    if result.is_blocked:
                        raise AegisBlockedError(
                            result.block_reason or "Content blocked",
                            detected=result.detected,
                        )

                    # Create new message with masked content
                    msg_class = type(msg)
                    masked_msg = msg_class(content=result.masked_text or msg.content)
                    masked.append(masked_msg)
                else:
                    masked.append(msg)
            else:
                masked.append(msg)

        return masked

    def __getattr__(self, name):
        """Forward other attributes to wrapped LLM."""
        return getattr(self._llm, name)
