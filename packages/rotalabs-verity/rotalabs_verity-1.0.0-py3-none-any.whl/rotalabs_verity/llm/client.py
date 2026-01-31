"""
LLM API client supporting multiple providers.
"""

import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal


@dataclass
class LLMResponse:
    """Response from LLM."""
    content: str
    model: str
    tokens_used: int
    latency_ms: float


class LLMClient(ABC):
    """Abstract LLM client."""

    @abstractmethod
    def generate(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.0) -> LLMResponse:
        """Generate response from prompt."""
        pass


class OpenAIClient(LLMClient):
    """OpenAI API client."""

    def __init__(self, model: str = "gpt-4", api_key: str | None = None):
        self.model = model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")

        if not self.api_key:
            raise ValueError("OpenAI API key required")

        import openai
        self.client = openai.OpenAI(api_key=self.api_key)

    def generate(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.0) -> LLMResponse:
        start = time.time()

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature
        )

        latency = (time.time() - start) * 1000

        return LLMResponse(
            content=response.choices[0].message.content,
            model=self.model,
            tokens_used=response.usage.total_tokens,
            latency_ms=latency
        )


class AnthropicClient(LLMClient):
    """Anthropic API client."""

    def __init__(self, model: str = "claude-sonnet-4-20250514", api_key: str | None = None):
        self.model = model
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")

        if not self.api_key:
            raise ValueError("Anthropic API key required")

        import anthropic
        self.client = anthropic.Anthropic(api_key=self.api_key)

    def generate(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.0) -> LLMResponse:
        start = time.time()

        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )

        latency = (time.time() - start) * 1000

        return LLMResponse(
            content=response.content[0].text,
            model=self.model,
            tokens_used=response.usage.input_tokens + response.usage.output_tokens,
            latency_ms=latency
        )


class OllamaClient(LLMClient):
    """Ollama local client."""

    def __init__(self, model: str = "codellama:13b", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url

    def generate(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.0) -> LLMResponse:
        import requests

        start = time.time()

        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": temperature
                }
            }
        )

        latency = (time.time() - start) * 1000
        data = response.json()

        return LLMResponse(
            content=data["response"],
            model=self.model,
            tokens_used=data.get("eval_count", 0),
            latency_ms=latency
        )


def get_client(provider: Literal["openai", "anthropic", "ollama"], model: str | None = None) -> LLMClient:
    """Factory function to get LLM client."""
    if provider == "openai":
        return OpenAIClient(model=model or "gpt-4")
    elif provider == "anthropic":
        return AnthropicClient(model=model or "claude-sonnet-4-20250514")
    elif provider == "ollama":
        return OllamaClient(model=model or "codellama:13b")
    else:
        raise ValueError(f"Unknown provider: {provider}")
