"""
Chat API Router
================

Provides chat endpoints with RAG integration and LLM provider support.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional
import json

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    session_id: Optional[str] = None
    use_rag: bool = True
    stream: bool = False
    provider: Optional[str] = None  # openai, anthropic, gemini


class ChatResponse(BaseModel):
    response: str
    session_id: str
    products: list[dict] = []
    provider: str
    model: str


@router.post("/send", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """
    Send a chat message and get AI response.
    
    Optionally uses RAG to include relevant products in context.
    """
    try:
        from app.providers import get_llm_provider, ChatMessage, ProviderType
        from app.services.indexing_service import get_indexing_service
        import uuid
        
        # Get or create session
        session_id = request.session_id or str(uuid.uuid4())
        
        # Get LLM provider
        provider_type = None
        if request.provider:
            provider_type = ProviderType(request.provider.lower())
        
        provider = get_llm_provider(provider_type)
        
        # Build messages
        messages = []
        
        # System prompt
        system_prompt = """You are a helpful e-commerce assistant for an online store. 
You help customers find products, answer questions about them, and assist with their shopping needs.
Be friendly, concise, and helpful. If you don't know something, say so.
When recommending products, mention their key features and prices."""
        
        messages.append(ChatMessage(role="system", content=system_prompt))
        
        # RAG: Get relevant products
        products = []
        if request.use_rag:
            try:
                service = get_indexing_service()
                products = await service.search_products(
                    query=request.message,
                    limit=3,
                )
                
                if products:
                    # Add product context to system message
                    product_context = "\n\nRelevant products from our catalog:\n"
                    for i, p in enumerate(products, 1):
                        product_context += (
                            f"{i}. {p.get('title', 'Product')} - ${p.get('price', 0):.2f}\n"
                            f"   {p.get('description', '')[:100]}...\n"
                        )
                    messages[0] = ChatMessage(
                        role="system",
                        content=system_prompt + product_context
                    )
            except Exception as e:
                print(f"[WARN] RAG search failed: {e}")
        
        # Add user message
        messages.append(ChatMessage(role="user", content=request.message))
        
        # Get response
        response = await provider.chat(messages)
        
        return ChatResponse(
            response=response.content,
            session_id=session_id,
            products=products[:3],  # Return top 3 products
            provider=response.provider,
            model=response.model,
        )
    
    except ImportError as e:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def stream_message(request: ChatRequest):
    """
    Stream a chat response using Server-Sent Events.
    """
    try:
        from app.providers import get_llm_provider, ChatMessage, ProviderType
        
        # Get LLM provider
        provider_type = None
        if request.provider:
            provider_type = ProviderType(request.provider.lower())
        
        provider = get_llm_provider(provider_type)
        
        # Build messages
        messages = [
            ChatMessage(role="system", content="You are a helpful e-commerce assistant."),
            ChatMessage(role="user", content=request.message),
        ]
        
        async def generate():
            try:
                async for chunk in provider.chat_stream(messages):
                    yield f"data: {json.dumps({'content': chunk})}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
    
    except ImportError as e:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {e}")


@router.get("/providers")
async def list_providers():
    """List available LLM providers and their status."""
    from app.providers import ProviderType, get_llm_provider
    
    providers = []
    for provider_type in ProviderType:
        try:
            provider = get_llm_provider(provider_type)
            healthy = await provider.health_check()
            providers.append({
                "name": provider_type.value,
                "model": provider.default_model,
                "healthy": healthy,
            })
        except Exception:
            providers.append({
                "name": provider_type.value,
                "model": "unknown",
                "healthy": False,
            })
    
    return {"providers": providers}
