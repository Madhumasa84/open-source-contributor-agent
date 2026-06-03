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

from .base import BaseModelProvider, ProviderConfigurationError


class OpenRouterProvider(BaseModelProvider):
    name = ProviderName.openrouter
    default_models = [
        "deepseek/deepseek-chat",
        "qwen/qwen3",
        "moonshotai/kimi",
        "meta-llama/llama-3.1-70b-instruct",
    ]

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def descriptor(self) -> ProviderDescriptor:
        return ProviderDescriptor(
            name=self.name,
            configured=bool(self.settings.openrouter_api_key),
            default_models=self.default_models,
            capabilities=ModelCapability(streaming=True, tool_calling=True),
        )

    async def complete(self, request: ModelRequest) -> ModelResponse:
        if not self.settings.openrouter_api_key:
            raise ProviderConfigurationError("OPENROUTER_API_KEY is not configured")
        payload = {
            "model": request.model,
            "messages": [message.model_dump() for message in request.messages],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "tools": [tool.model_dump() for tool in request.tools] or None,
        }
        headers = {"Authorization": f"Bearer {self.settings.openrouter_api_key}"}
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers
            )
            response.raise_for_status()
            data = response.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        return ModelResponse(provider=self.name, model=request.model, content=content, raw=data)

    async def stream(self, request: ModelRequest) -> AsyncIterator[str]:
        response = await self.complete(request)
        yield response.content
