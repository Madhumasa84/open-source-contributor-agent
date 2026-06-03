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


class AnthropicProvider(BaseModelProvider):
    name = ProviderName.anthropic
    default_models = ["claude-sonnet", "claude-opus"]

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def descriptor(self) -> ProviderDescriptor:
        return ProviderDescriptor(
            name=self.name,
            configured=bool(self.settings.anthropic_api_key),
            default_models=self.default_models,
            capabilities=ModelCapability(streaming=True, tool_calling=True),
        )

    async def complete(self, request: ModelRequest) -> ModelResponse:
        if not self.settings.anthropic_api_key:
            raise ProviderConfigurationError("ANTHROPIC_API_KEY is not configured")
        payload = {
            "model": request.model,
            "messages": [message.model_dump() for message in request.messages],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "tools": [tool.model_dump() for tool in request.tools] or None,
        }
        headers = {
            "x-api-key": self.settings.anthropic_api_key,
            "anthropic-version": "2023-06-01",
        }
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages", json=payload, headers=headers
            )
            response.raise_for_status()
            data = response.json()
        content = "".join(
            part.get("text", "") for part in data.get("content", []) if part.get("type") == "text"
        )
        return ModelResponse(provider=self.name, model=request.model, content=content, raw=data)

    async def stream(self, request: ModelRequest) -> AsyncIterator[str]:
        response = await self.complete(request)
        yield response.content
