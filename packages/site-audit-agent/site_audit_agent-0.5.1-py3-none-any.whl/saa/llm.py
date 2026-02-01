"""LLM dispatcher for SAA - supports xAI (Grok) and Anthropic."""

import json
from abc import ABC, abstractmethod
from typing import Optional

import requests

from saa.config import Config


class LLMClient(ABC):
    """Abstract base class for LLM clients."""

    @abstractmethod
    def complete(self, prompt: str, system: Optional[str] = None) -> str:
        """Generate a completion for the given prompt."""
        pass

    @abstractmethod
    def complete_json(self, prompt: str, system: Optional[str] = None) -> dict:
        """Generate a completion and parse as JSON."""
        pass


class XAIClient(LLMClient):
    """xAI/Grok API client."""

    def __init__(self, api_key: str, model: str = "grok-2-latest"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.x.ai/v1"

    def complete(self, prompt: str, system: Optional[str] = None) -> str:
        """Generate completion using xAI API."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": messages,
                "temperature": 0.7,
            },
            timeout=180,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

    def complete_json(self, prompt: str, system: Optional[str] = None) -> dict:
        """Generate completion and parse as JSON."""
        # Add JSON instruction to system prompt
        json_system = (system or "") + "\n\nRespond with valid JSON only. No markdown, no explanation."
        result = self.complete(prompt, json_system)

        # Clean up response (remove markdown code blocks if present)
        result = result.strip()
        if result.startswith("```json"):
            result = result[7:]
        if result.startswith("```"):
            result = result[3:]
        if result.endswith("```"):
            result = result[:-3]
        result = result.strip()

        return json.loads(result)


class AnthropicClient(LLMClient):
    """Anthropic/Claude API client."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.anthropic.com/v1"

    def complete(self, prompt: str, system: Optional[str] = None) -> str:
        """Generate completion using Anthropic API."""
        body = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            body["system"] = system

        response = requests.post(
            f"{self.base_url}/messages",
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json=body,
            timeout=180,
        )
        response.raise_for_status()
        data = response.json()
        return data["content"][0]["text"]

    def complete_json(self, prompt: str, system: Optional[str] = None) -> dict:
        """Generate completion and parse as JSON."""
        json_system = (system or "") + "\n\nRespond with valid JSON only. No markdown, no explanation."
        result = self.complete(prompt, json_system)

        # Clean up response
        result = result.strip()
        if result.startswith("```json"):
            result = result[7:]
        if result.startswith("```"):
            result = result[3:]
        if result.endswith("```"):
            result = result[:-3]
        result = result.strip()

        return json.loads(result)


# Model aliases for convenience
MODEL_ALIASES = {
    # xAI models (grok-2 deprecated Sep 2025, use grok-3)
    "grok": "grok-3",
    "grok-2": "grok-3",  # Redirected since grok-2 deprecated
    "grok-3": "grok-3",
    # Anthropic models
    "claude": "claude-sonnet-4-20250514",
    "sonnet": "claude-sonnet-4-20250514",
    "opus": "claude-opus-4-20250514",
    "haiku": "claude-3-5-haiku-20241022",
}


def get_llm_client(provider_model: str, config: Config) -> LLMClient:
    """Factory to create LLM client from provider:model string.

    Examples:
        get_llm_client("xai:grok-2", config)
        get_llm_client("anthropic:sonnet", config)
    """
    if ":" not in provider_model:
        raise ValueError(f"Invalid LLM format: {provider_model}. Use provider:model (e.g., xai:grok)")

    provider, model = provider_model.split(":", 1)
    provider = provider.lower()

    # Resolve model alias
    model = MODEL_ALIASES.get(model.lower(), model)

    if provider == "xai":
        if not config.xai_api_key:
            raise ValueError("XAI_API_KEY not set. Add it to ~/.saa/.keys or environment.")
        return XAIClient(config.xai_api_key, model)

    elif provider == "anthropic":
        if not config.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY not set. Add it to ~/.saa/.keys or environment.")
        return AnthropicClient(config.anthropic_api_key, model)

    else:
        raise ValueError(f"Unknown LLM provider: {provider}. Supported: xai, anthropic")


def test_llm_connection(config: Config, provider_model: str) -> bool:
    """Test if LLM connection works."""
    try:
        client = get_llm_client(provider_model, config)
        response = client.complete("Say 'OK' if you can read this.")
        return "OK" in response.upper()
    except Exception as e:
        print(f"LLM connection test failed: {e}")
        return False
