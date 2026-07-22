import requests
import json
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from app.core.logger import logger, ai_logger
from app.core.exceptions import AIProviderError, ErrorHandler

class BaseAIProvider(ABC):
    """Abstract base class for all AI service providers."""

    def __init__(self, name: str, api_key: str = "", endpoint_url: str = "", model_name: str = ""):
        self.name = name
        self.api_key = api_key
        self.endpoint_url = endpoint_url
        self.model_name = model_name

    @abstractmethod
    def generate_completion(self, system_prompt: str, user_prompt: str, temperature: float = 0.2, timeout: int = 20) -> str:
        """Generate text completion from provider."""
        pass

    @abstractmethod
    def is_healthy(self) -> bool:
        """Check provider connectivity or status."""
        pass

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for input text (approx 4 chars per token)."""
        if not text:
            return 0
        return max(1, len(text) // 4)

class MockProvider(BaseAIProvider):
    """Offline fallback provider."""
    def __init__(self):
        super().__init__("Mock Mode (Offline)")

    def generate_completion(self, system_prompt: str, user_prompt: str, temperature: float = 0.2, timeout: int = 20) -> str:
        ai_logger.info("MockProvider invoked.")
        return "MOCK_RESPONSE_FALLBACK"

    def is_healthy(self) -> bool:
        return True

class OpenAIProvider(BaseAIProvider):
    """OpenAI API Provider implementation."""
    def __init__(self, api_key: str, model_name: str = "gpt-4o-mini"):
        super().__init__("OpenAI", api_key=api_key, endpoint_url="https://api.openai.com/v1/chat/completions", model_name=model_name)

    def generate_completion(self, system_prompt: str, user_prompt: str, temperature: float = 0.2, timeout: int = 20) -> str:
        if not self.api_key:
            raise AIProviderError("OpenAI API key is missing.")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature
        }

        ai_logger.info(f"Sending completion request to OpenAI ({self.model_name})...")
        response = requests.post(self.endpoint_url, headers=headers, json=payload, timeout=timeout)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        ai_logger.info("Received OpenAI completion response.")
        return content

    def is_healthy(self) -> bool:
        return bool(self.api_key)

class OllamaProvider(BaseAIProvider):
    """Local Ollama Provider implementation."""
    def __init__(self, endpoint_url: str = "http://localhost:11434", model_name: str = "llama3"):
        url = endpoint_url.rstrip("/") + "/v1/chat/completions"
        super().__init__("Ollama (Offline)", endpoint_url=url, model_name=model_name)

    def generate_completion(self, system_prompt: str, user_prompt: str, temperature: float = 0.2, timeout: int = 20) -> str:
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature
        }

        ai_logger.info(f"Sending request to Ollama ({self.model_name}) at {self.endpoint_url}...")
        response = requests.post(self.endpoint_url, headers=headers, json=payload, timeout=timeout)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        ai_logger.info("Received Ollama completion response.")
        return content

    def is_healthy(self) -> bool:
        try:
            health_url = self.endpoint_url.rsplit("/v1/", 1)[0] + "/api/version"
            res = requests.get(health_url, timeout=3)
            return res.status_code == 200
        except Exception:
            return False

class AzureOpenAIProvider(BaseAIProvider):
    """Azure OpenAI Provider implementation."""
    def __init__(self, api_key: str, endpoint_url: str, deployment_name: str):
        super().__init__("Azure OpenAI", api_key=api_key, endpoint_url=endpoint_url, model_name=deployment_name)

    def generate_completion(self, system_prompt: str, user_prompt: str, temperature: float = 0.2, timeout: int = 20) -> str:
        if not self.api_key or not self.endpoint_url:
            raise AIProviderError("Azure OpenAI API key or Endpoint URL missing.")

        headers = {
            "Content-Type": "application/json",
            "api-key": self.api_key
        }
        payload = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature
        }

        ai_logger.info(f"Sending request to Azure OpenAI ({self.model_name})...")
        response = requests.post(self.endpoint_url, headers=headers, json=payload, timeout=timeout)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    def is_healthy(self) -> bool:
        return bool(self.api_key and self.endpoint_url)

class AnthropicProvider(BaseAIProvider):
    """Anthropic Claude Provider implementation."""
    def __init__(self, api_key: str, model_name: str = "claude-3-haiku-20240307"):
        super().__init__("Anthropic", api_key=api_key, endpoint_url="https://api.anthropic.com/v1/messages", model_name=model_name)

    def generate_completion(self, system_prompt: str, user_prompt: str, temperature: float = 0.2, timeout: int = 20) -> str:
        if not self.api_key:
            raise AIProviderError("Anthropic API key missing.")

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": self.model_name,
            "max_tokens": 2048,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
            "temperature": temperature
        }

        ai_logger.info(f"Sending completion request to Anthropic ({self.model_name})...")
        response = requests.post(self.endpoint_url, headers=headers, json=payload, timeout=timeout)
        response.raise_for_status()
        return response.json()["content"][0]["text"]

    def is_healthy(self) -> bool:
        return bool(self.api_key)

class GeminiProvider(BaseAIProvider):
    """Google Gemini Provider implementation."""
    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash"):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        super().__init__("Google Gemini", api_key=api_key, endpoint_url=url, model_name=model_name)

    def generate_completion(self, system_prompt: str, user_prompt: str, temperature: float = 0.2, timeout: int = 20) -> str:
        if not self.api_key:
            raise AIProviderError("Google Gemini API key missing.")

        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": f"{system_prompt}\n\nUser Request: {user_prompt}"}
                    ]
                }
            ],
            "generationConfig": {"temperature": temperature}
        }

        ai_logger.info(f"Sending completion request to Gemini ({self.model_name})...")
        response = requests.post(self.endpoint_url, headers=headers, json=payload, timeout=timeout)
        response.raise_for_status()
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]

    def is_healthy(self) -> bool:
        return bool(self.api_key)
