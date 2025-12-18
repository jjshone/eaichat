"""
Anthropic Provider Implementation
=================================

Implements BaseLLMProvider for Anthropic Claude models.
"""

import os
from typing import Optional, AsyncIterator

from . import BaseLLMProvider, ChatMessage, ChatResponse


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude LLM provider."""
    
    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.model = os.getenv("ANTHROPIC_MODEL", "claude-3-opus-20240229")
        self._client = None
    
    @property
    def provider_name(self) -> str:
        return "anthropic"
    
    @property
    def default_model(self) -> str:
        return self.model
    
    def _get_client(self):
        """Lazy load Anthropic client."""
        if self._client is None:
            try:
                from anthropic import AsyncAnthropic
                self._client = AsyncAnthropic(api_key=self.api_key)
            except ImportError:
                raise ImportError("anthropic package not installed. Run: pip install anthropic")
        return self._client
    
    def _format_messages(self, messages: list[ChatMessage]) -> tuple[str, list[dict]]:
        """
        Format messages for Anthropic API.
        Returns (system_prompt, messages_list).
        """
        system_prompt = ""
        formatted = []
        
        for m in messages:
            if m.role == "system":
                system_prompt = m.content
            else:
                formatted.append({
                    "role": m.role,
                    "content": m.content,
                })
        
        return system_prompt, formatted
    
    async def chat(
        self,
        messages: list[ChatMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        tools: Optional[list[dict]] = None,
    ) -> ChatResponse:
        """Send chat completion to Anthropic."""
        client = self._get_client()
        
        system_prompt, formatted_messages = self._format_messages(messages)
        
        kwargs = {
            "model": model or self.model,
            "messages": formatted_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        if system_prompt:
            kwargs["system"] = system_prompt
        
        if tools:
            # Convert OpenAI tool format to Anthropic format
            anthropic_tools = []
            for tool in tools:
                if tool.get("type") == "function":
                    func = tool["function"]
                    anthropic_tools.append({
                        "name": func["name"],
                        "description": func.get("description", ""),
                        "input_schema": func.get("parameters", {}),
                    })
            kwargs["tools"] = anthropic_tools
        
        response = await client.messages.create(**kwargs)
        
        # Extract text content
        content = ""
        for block in response.content:
            if hasattr(block, "text"):
                content += block.text
        
        return ChatResponse(
            content=content,
            model=response.model,
            provider=self.provider_name,
            usage={
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
            },
            finish_reason=response.stop_reason,
        )
    
    async def chat_stream(
        self,
        messages: list[ChatMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> AsyncIterator[str]:
        """Stream chat completion from Anthropic."""
        client = self._get_client()
        
        system_prompt, formatted_messages = self._format_messages(messages)
        
        kwargs = {
            "model": model or self.model,
            "messages": formatted_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        if system_prompt:
            kwargs["system"] = system_prompt
        
        async with client.messages.stream(**kwargs) as stream:
            async for text in stream.text_stream:
                yield text
    
    async def health_check(self) -> bool:
        """Check if Anthropic API is accessible."""
        if not self.api_key:
            return False
        
        try:
            client = self._get_client()
            # Send a minimal request to verify API key
            await client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1,
                messages=[{"role": "user", "content": "Hi"}],
            )
            return True
        except Exception:
            return False
