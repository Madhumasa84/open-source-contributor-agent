from app.core.config import Settings, get_settings
from app.schemas.provider import ProviderDescriptor, ProviderName

from .anthropic import AnthropicProvider
from .base import BaseModelProvider
from .gemini import GeminiProvider
from .ollama import OllamaProvider
from .openrouter import OpenRouterProvider


class ProviderRegistry:
    def __init__(self, settings: Settings | None = None) -> None:
        settings = settings or get_settings()
        self._providers: dict[ProviderName, BaseModelProvider] = {
            ProviderName.gemini: GeminiProvider(settings),
            ProviderName.anthropic: AnthropicProvider(settings),
            ProviderName.openrouter: OpenRouterProvider(settings),
            ProviderName.ollama: OllamaProvider(settings),
        }

    def get(self, name: ProviderName) -> BaseModelProvider:
        return self._providers[name]

    def descriptors(self) -> list[ProviderDescriptor]:
        return [provider.descriptor() for provider in self._providers.values()]
