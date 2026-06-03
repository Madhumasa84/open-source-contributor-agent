from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from app.schemas.provider import ModelRequest, ModelResponse, ProviderDescriptor, ProviderName


class ProviderConfigurationError(RuntimeError):
    pass


class BaseModelProvider(ABC):
    name: ProviderName

    @abstractmethod
    def descriptor(self) -> ProviderDescriptor:
        raise NotImplementedError

    @abstractmethod
    async def complete(self, request: ModelRequest) -> ModelResponse:
        raise NotImplementedError

    @abstractmethod
    async def stream(self, request: ModelRequest) -> AsyncIterator[str]:
        raise NotImplementedError
