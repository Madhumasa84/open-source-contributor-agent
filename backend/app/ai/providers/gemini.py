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


class GeminiProvider(BaseModelProvider):
    name = ProviderName.gemini
    default_models = ["gemini-3.1-pro", "gemini-flash"]

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def descriptor(self) -> ProviderDescriptor:
        return ProviderDescriptor(
            name=self.name,
            configured=bool(self.settings.google_api_key),
            default_models=self.default_models,
            capabilities=ModelCapability(streaming=True, tool_calling=True),
        )

    async def complete(self, request: ModelRequest) -> ModelResponse:
        if not self.settings.google_api_key:
            raise ProviderConfigurationError("GOOGLE_API_KEY is not configured")
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{request.model}:generateContent?key={self.settings.google_api_key}"
        )
        payload = {
            "contents": [
                {"role": message.role, "parts": [{"text": message.content}]}
                for message in request.messages
            ],
            "generationConfig": {
                "temperature": request.temperature,
                "maxOutputTokens": request.max_tokens,
            },
        }
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
        content = (
            data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        )
        return ModelResponse(provider=self.name, model=request.model, content=content, raw=data)

    async def stream(self, request: ModelRequest) -> AsyncIterator[str]:
        response = await self.complete(request)
        yield response.content
