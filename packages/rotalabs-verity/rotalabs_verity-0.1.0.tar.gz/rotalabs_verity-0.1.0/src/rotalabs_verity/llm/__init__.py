"""LLM integration module.

This module provides LLM clients for synthesis. Each provider is an optional dependency:
- OpenAI: pip install rotalabs-verify[openai]
- Anthropic: pip install rotalabs-verify[anthropic]
- Ollama: pip install rotalabs-verify[ollama]
- All LLMs: pip install rotalabs-verify[llm]
"""

import importlib.util

from rotalabs_verity.llm.client import (
    AnthropicClient,
    LLMClient,
    LLMResponse,
    OllamaClient,
    OpenAIClient,
    get_client,
)
from rotalabs_verity.llm.prompts import PromptBuilder

# Check which providers are available using importlib.util.find_spec
HAS_OPENAI = importlib.util.find_spec("openai") is not None
HAS_ANTHROPIC = importlib.util.find_spec("anthropic") is not None

__all__ = [
    "LLMResponse",
    "LLMClient",
    "OpenAIClient",
    "AnthropicClient",
    "OllamaClient",
    "get_client",
    "PromptBuilder",
    "HAS_OPENAI",
    "HAS_ANTHROPIC",
]
