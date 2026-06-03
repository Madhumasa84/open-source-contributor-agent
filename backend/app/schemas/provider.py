from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ProviderName(StrEnum):
    gemini = "gemini"
    anthropic = "anthropic"
    openrouter = "openrouter"
    ollama = "ollama"


class ModelCapability(BaseModel):
    streaming: bool = True
    tool_calling: bool = True
    local: bool = False


class ProviderDescriptor(BaseModel):
    name: ProviderName
    configured: bool
    default_models: list[str]
    capabilities: ModelCapability


class ProviderSelection(BaseModel):
    provider: ProviderName
    model: str
    role: str = Field(default="general", examples=["fix_proposal", "risk_analysis"])


class ChatMessage(BaseModel):
    role: str
    content: str


class ToolSpec(BaseModel):
    name: str
    description: str
    input_schema: dict[str, Any]


class ModelRequest(BaseModel):
    model: str
    messages: list[ChatMessage]
    tools: list[ToolSpec] = Field(default_factory=list)
    temperature: float = 0.2
    max_tokens: int = 2048


class ModelResponse(BaseModel):
    provider: ProviderName
    model: str
    content: str
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)
