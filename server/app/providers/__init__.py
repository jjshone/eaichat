"""
LLM Provider Abstraction Layer
==============================

Provides a unified interface for LLM providers (OpenAI, Anthropic, Gemini).
Supports failover, rate limiting, and Langfuse tracing.

Usage:
    from app.providers import get_llm_provider, ChatMessage
    
    provider = get_llm_provider()  # Returns configured default provider
    response = await provider.chat([
        ChatMessage(role="user", content="Hello!")
    ])
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, AsyncIterator
from enum import Enum
import os


class ProviderType(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"


@dataclass
class ChatMessage:
    """A single chat message."""
    role: str  # "system", "user", "assistant"
    content: str
    name: Optional[str] = None


@dataclass
class ChatResponse:
    """Response from LLM."""
    content: str
    model: str
    provider: str
    usage: dict = field(default_factory=dict)
    finish_reason: Optional[str] = None


@dataclass
class ToolCall:
    """Tool call from LLM."""
    id: str
    name: str
    arguments: dict


@dataclass
class ToolResult:
    """Result of tool execution."""
    tool_call_id: str
    content: str


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return provider name."""
        pass
    
    @property
    @abstractmethod
    def default_model(self) -> str:
        """Return default model for this provider."""
        pass
    
    @abstractmethod
    async def chat(
        self,
        messages: list[ChatMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        tools: Optional[list[dict]] = None,
    ) -> ChatResponse:
        """Send chat completion request."""
        pass
    
    @abstractmethod
    async def chat_stream(
        self,
        messages: list[ChatMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> AsyncIterator[str]:
        """Stream chat completion response."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if provider is healthy/available."""
        pass


def get_default_provider() -> ProviderType:
    """Get configured default LLM provider."""
    provider = os.getenv("DEFAULT_LLM_PROVIDER", "openai").lower()
    return ProviderType(provider)


def get_llm_provider(provider: Optional[ProviderType] = None) -> BaseLLMProvider:
    """Get LLM provider instance."""
    if provider is None:
        provider = get_default_provider()
    
    if provider == ProviderType.OPENAI:
        from .openai_provider import OpenAIProvider
        return OpenAIProvider()
    elif provider == ProviderType.ANTHROPIC:
        from .anthropic_provider import AnthropicProvider
        return AnthropicProvider()
    elif provider == ProviderType.GEMINI:
        from .gemini_provider import GeminiProvider
        return GeminiProvider()
    else:
        raise ValueError(f"Unknown provider: {provider}")


async def get_provider_with_failover(
    providers: Optional[list[ProviderType]] = None
) -> BaseLLMProvider:
    """Get first healthy provider from list (failover pattern)."""
    if providers is None:
        providers = [ProviderType.OPENAI, ProviderType.ANTHROPIC, ProviderType.GEMINI]
    
    for provider_type in providers:
        try:
            provider = get_llm_provider(provider_type)
            if await provider.health_check():
                return provider
        except Exception:
            continue
    
    raise RuntimeError("No healthy LLM provider available")
