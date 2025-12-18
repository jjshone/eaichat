"""
Google Gemini Provider Implementation
======================================

Implements BaseLLMProvider for Google Gemini models.
"""

import os
from typing import Optional, AsyncIterator

from . import BaseLLMProvider, ChatMessage, ChatResponse


class GeminiProvider(BaseLLMProvider):
    """Google Gemini LLM provider."""
    
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.model = os.getenv("GOOGLE_MODEL", "gemini-pro")
        self._client = None
    
    @property
    def provider_name(self) -> str:
        return "gemini"
    
    @property
    def default_model(self) -> str:
        return self.model
    
    def _get_client(self):
        """Lazy load Gemini client."""
        if self._client is None:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self._client = genai
            except ImportError:
                raise ImportError(
                    "google-generativeai package not installed. "
                    "Run: pip install google-generativeai"
                )
        return self._client
    
    def _format_messages(self, messages: list[ChatMessage]) -> tuple[str, list[dict]]:
        """
        Format messages for Gemini API.
        Returns (system_instruction, history).
        """
        system_instruction = ""
        history = []
        
        for m in messages:
            if m.role == "system":
                system_instruction = m.content
            elif m.role == "user":
                history.append({
                    "role": "user",
                    "parts": [m.content],
                })
            elif m.role == "assistant":
                history.append({
                    "role": "model",
                    "parts": [m.content],
                })
        
        return system_instruction, history
    
    async def chat(
        self,
        messages: list[ChatMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        tools: Optional[list[dict]] = None,
    ) -> ChatResponse:
        """Send chat completion to Gemini."""
        genai = self._get_client()
        
        system_instruction, history = self._format_messages(messages)
        
        generation_config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }
        
        # Create model with optional system instruction
        model_kwargs = {
            "model_name": model or self.model,
            "generation_config": generation_config,
        }
        
        if system_instruction:
            model_kwargs["system_instruction"] = system_instruction
        
        gemini_model = genai.GenerativeModel(**model_kwargs)
        
        # Get the last user message
        last_message = ""
        if history:
            for h in reversed(history):
                if h["role"] == "user":
                    last_message = h["parts"][0]
                    break
        
        # Use chat for multi-turn or single generate
        if len(history) > 1:
            chat = gemini_model.start_chat(history=history[:-1])
            response = await chat.send_message_async(last_message)
        else:
            response = await gemini_model.generate_content_async(last_message)
        
        return ChatResponse(
            content=response.text,
            model=model or self.model,
            provider=self.provider_name,
            usage={
                "prompt_tokens": getattr(response.usage_metadata, "prompt_token_count", 0),
                "completion_tokens": getattr(response.usage_metadata, "candidates_token_count", 0),
                "total_tokens": getattr(response.usage_metadata, "total_token_count", 0),
            },
            finish_reason=str(response.candidates[0].finish_reason) if response.candidates else None,
        )
    
    async def chat_stream(
        self,
        messages: list[ChatMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> AsyncIterator[str]:
        """Stream chat completion from Gemini."""
        genai = self._get_client()
        
        system_instruction, history = self._format_messages(messages)
        
        generation_config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }
        
        model_kwargs = {
            "model_name": model or self.model,
            "generation_config": generation_config,
        }
        
        if system_instruction:
            model_kwargs["system_instruction"] = system_instruction
        
        gemini_model = genai.GenerativeModel(**model_kwargs)
        
        last_message = ""
        if history:
            for h in reversed(history):
                if h["role"] == "user":
                    last_message = h["parts"][0]
                    break
        
        response = await gemini_model.generate_content_async(
            last_message,
            stream=True,
        )
        
        async for chunk in response:
            if chunk.text:
                yield chunk.text
    
    async def health_check(self) -> bool:
        """Check if Gemini API is accessible."""
        if not self.api_key:
            return False
        
        try:
            genai = self._get_client()
            # List models to verify API key
            list(genai.list_models())
            return True
        except Exception:
            return False
