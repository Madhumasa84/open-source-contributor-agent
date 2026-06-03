from __future__ import annotations

from collections.abc import AsyncIterator

import httpx

from app.core.config import Settings, get_settings
from app.schemas.provider import (
    ModelCapability,
    ModelRequest,
    ModelResponse,
    ProviderDescriptor,
    ProviderName,
)

from .base import BaseModelProvider


class OllamaProvider(BaseModelProvider):
    name = ProviderName.ollama
    default_models = ["llama3.1", "gemma2", "qwen2.5", "deepseek-r1"]

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def descriptor(self) -> ProviderDescriptor:
        return ProviderDescriptor(
            name=self.name,
            configured=bool(self.settings.ollama_base_url),
            default_models=self.default_models,
            capabilities=ModelCapability(streaming=True, tool_calling=False, local=True),
        )

    async def complete(self, request: ModelRequest) -> ModelResponse:
        payload = {
            "model": request.model,
            "messages": [message.model_dump() for message in request.messages],
            "stream": False,
            "options": {"temperature": request.temperature, "num_predict": request.max_tokens},
        }
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(f"{self.settings.ollama_base_url}/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()
        return ModelResponse(
            provider=self.name,
            model=request.model,
            content=data.get("message", {}).get("content", ""),
            raw=data,
        )

    async def stream(self, request: ModelRequest) -> AsyncIterator[str]:
        payload = {
            "model": request.model,
            "messages": [message.model_dump() for message in request.messages],
            "stream": True,
            "options": {"temperature": request.temperature, "num_predict": request.max_tokens},
        }
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                "POST", f"{self.settings.ollama_base_url}/api/chat", json=payload
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        yield line
