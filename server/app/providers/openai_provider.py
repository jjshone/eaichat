"""
OpenAI Provider Implementation
==============================

Implements BaseLLMProvider for OpenAI GPT models.
"""

import os
from typing import Optional, AsyncIterator

from . import BaseLLMProvider, ChatMessage, ChatResponse


class OpenAIProvider(BaseLLMProvider):
    """OpenAI LLM provider."""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
        self._client = None
    
    @property
    def provider_name(self) -> str:
        return "openai"
    
    @property
    def default_model(self) -> str:
        return self.model
    
    def _get_client(self):
        """Lazy load OpenAI client."""
        if self._client is None:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError("openai package not installed. Run: pip install openai")
        return self._client
    
    async def chat(
        self,
        messages: list[ChatMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        tools: Optional[list[dict]] = None,
    ) -> ChatResponse:
        """Send chat completion to OpenAI."""
        client = self._get_client()
        
        # Format messages for OpenAI
        formatted_messages = [
            {"role": m.role, "content": m.content}
            for m in messages
        ]
        
        kwargs = {
            "model": model or self.model,
            "messages": formatted_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        
        response = await client.chat.completions.create(**kwargs)
        
        choice = response.choices[0]
        
        return ChatResponse(
            content=choice.message.content or "",
            model=response.model,
            provider=self.provider_name,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            },
            finish_reason=choice.finish_reason,
        )
    
    async def chat_stream(
        self,
        messages: list[ChatMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> AsyncIterator[str]:
        """Stream chat completion from OpenAI."""
        client = self._get_client()
        
        formatted_messages = [
            {"role": m.role, "content": m.content}
            for m in messages
        ]
        
        stream = await client.chat.completions.create(
            model=model or self.model,
            messages=formatted_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    async def health_check(self) -> bool:
        """Check if OpenAI API is accessible."""
        if not self.api_key:
            return False
        
        try:
            client = self._get_client()
            # Simple models list call to verify API key
            await client.models.list()
            return True
        except Exception:
            return False
