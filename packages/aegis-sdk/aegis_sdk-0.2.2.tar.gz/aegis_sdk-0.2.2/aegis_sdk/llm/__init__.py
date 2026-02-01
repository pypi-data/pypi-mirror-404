"""LLM integration module.

This module provides wrappers for popular LLM providers with
automatic PII masking and policy enforcement.

Supported integrations:
- OpenAI (ChatGPT, GPT-4)
- Anthropic (Claude)
- LangChain
"""

from aegis_sdk.llm.gateway import (
    AegisLLMGateway,
    mask_prompt,
    mask_messages,
)

__all__ = [
    "AegisLLMGateway",
    "mask_prompt",
    "mask_messages",
]

# Optional imports based on installed packages
try:
    from aegis_sdk.llm.openai_wrapper import (
        AegisOpenAI,
        aegis_openai_client,
    )
    __all__.extend(["AegisOpenAI", "aegis_openai_client"])
except ImportError:
    pass

try:
    from aegis_sdk.llm.langchain_wrapper import (
        AegisLangChainCallback,
        AegisChatModel,
    )
    __all__.extend(["AegisLangChainCallback", "AegisChatModel"])
except ImportError:
    pass

try:
    from aegis_sdk.llm.anthropic_wrapper import (
        AegisAnthropic,
    )
    __all__.extend(["AegisAnthropic"])
except ImportError:
    pass
