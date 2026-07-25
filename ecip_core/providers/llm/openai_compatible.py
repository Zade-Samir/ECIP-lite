"""
OpenAI-compatible LLM provider for the Model Gateway.
Works with any OpenAI-compatible REST API: LM Studio, vLLM, Together AI, etc.
Also serves as the base for Ollama gateway integration.
"""
import json
import time
from typing import Iterator, Optional

import httpx

from ecip_core.common.logger import get_logger
from services.model_gateway.gateway import LLMProvider

logger = get_logger(__name__)


class OpenAICompatibleProvider(LLMProvider):
    """
    Generic OpenAI-compatible REST provider.

    Compatible with:
    - LM Studio (http://localhost:1234/v1)
    - vLLM (http://localhost:8000/v1)
    - Ollama OpenAI endpoint (http://localhost:11434/v1)
    - Any other /v1/chat/completions endpoint

    Usage:
        provider = OpenAICompatibleProvider(
            name="lmstudio",
            base_url="http://localhost:1234/v1",
            api_key="lm-studio",  # Dummy for local
        )
    """

    def __init__(
        self,
        name: str,
        base_url: str,
        api_key: str = "local",
        default_model: Optional[str] = None,
        timeout: float = 60.0,
        weight: int = 1,
    ):
        super().__init__(name=name, weight=weight)
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.default_model = default_model
        self.timeout = timeout
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=timeout,
        )

    # ------------------------------------------------------------------
    # LLMProvider interface
    # ------------------------------------------------------------------

    def is_healthy(self) -> bool:
        """Ping /models endpoint to check liveness."""
        try:
            resp = self._client.get("/models", timeout=3.0)
            return resp.status_code == 200
        except Exception:
            return False

    def chat(self, messages: list[dict], model: str, **kwargs) -> str:
        """Blocking chat completion via /chat/completions."""
        model = model or self.default_model
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            **kwargs,
        }
        try:
            resp = self._client.post("/chat/completions", json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as e:
            logger.error("Provider unavailable")
            raise RuntimeError(f"Provider {self.name} HTTP error: {e.response.status_code}") from e
        except Exception as e:
            logger.error("Provider unavailable")
            raise RuntimeError(f"Provider {self.name} failed: {e}") from e

    def stream_chat(self, messages: list[dict], model: str, **kwargs) -> Iterator[str]:
        """Streaming chat via /chat/completions with stream=True."""
        model = model or self.default_model
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            **kwargs,
        }
        try:
            with self._client.stream("POST", "/chat/completions", json=payload) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if not line or line == "data: [DONE]":
                        continue
                    if line.startswith("data: "):
                        data = json.loads(line[6:])
                        delta = data["choices"][0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content
        except Exception as e:
            logger.error("Provider unavailable")
            raise RuntimeError(f"Provider {self.name} streaming failed: {e}") from e


class OllamaGatewayProvider(LLMProvider):
    """
    Ollama provider for the Model Gateway.
    Uses Ollama's native /api/chat endpoint (not OpenAI-compatible).
    """

    def __init__(
        self,
        name: str = "ollama",
        base_url: str = "http://127.0.0.1:11434",
        timeout: float = 120.0,
        weight: int = 1,
    ):
        super().__init__(name=name, weight=weight)
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client = httpx.Client(base_url=self.base_url, timeout=timeout)

    def is_healthy(self) -> bool:
        try:
            resp = self._client.get("/", timeout=2.0)
            return resp.status_code == 200
        except Exception:
            return False

    def chat(self, messages: list[dict], model: str, **kwargs) -> str:
        payload = {"model": model, "messages": messages, "stream": False}
        try:
            resp = self._client.post("/api/chat", json=payload)
            resp.raise_for_status()
            return resp.json()["message"]["content"]
        except Exception as e:
            logger.error("Provider unavailable")
            raise RuntimeError(f"Ollama chat failed: {e}") from e

    def stream_chat(self, messages: list[dict], model: str, **kwargs) -> Iterator[str]:
        payload = {"model": model, "messages": messages, "stream": True}
        try:
            with self._client.stream("POST", "/api/chat", json=payload) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if not line:
                        continue
                    data = json.loads(line)
                    content = data.get("message", {}).get("content", "")
                    if content:
                        yield content
        except Exception as e:
            logger.error("Provider unavailable")
            raise RuntimeError(f"Ollama streaming failed: {e}") from e
