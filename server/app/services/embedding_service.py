"""
Embedding Service
=================

Provides embeddings generation for text and images using SentenceTransformers.
Supports multiple embedding models and caching.
"""

import os
from typing import Optional
from functools import lru_cache

# Lazy imports to avoid loading heavy ML libs if not used
_text_model = None
_image_model = None


def get_text_model():
    """Get or create text embedding model (lazy load)."""
    global _text_model
    if _text_model is None:
        from sentence_transformers import SentenceTransformer
        model_name = os.getenv("TEXT_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        _text_model = SentenceTransformer(model_name)
        print(f"[INFO] Loaded text embedding model: {model_name}")
    return _text_model


def get_image_model():
    """Get or create image embedding model (lazy load)."""
    global _image_model
    if _image_model is None:
        from sentence_transformers import SentenceTransformer
        model_name = os.getenv("IMAGE_EMBEDDING_MODEL", "clip-ViT-B-32")
        _image_model = SentenceTransformer(model_name)
        print(f"[INFO] Loaded image embedding model: {model_name}")
    return _image_model


class EmbeddingService:
    """Service for generating embeddings from text and images."""
    
    def __init__(self):
        self.text_model_name = os.getenv("TEXT_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        self.image_model_name = os.getenv("IMAGE_EMBEDDING_MODEL", "clip-ViT-B-32")
    
    @property
    def text_embedding_size(self) -> int:
        """Get text embedding dimension."""
        # Common model dimensions
        model_dims = {
            "all-MiniLM-L6-v2": 384,
            "all-mpnet-base-v2": 768,
            "paraphrase-MiniLM-L6-v2": 384,
        }
        return model_dims.get(self.text_model_name, 384)
    
    @property
    def image_embedding_size(self) -> int:
        """Get image embedding dimension."""
        model_dims = {
            "clip-ViT-B-32": 512,
            "clip-ViT-L-14": 768,
        }
        return model_dims.get(self.image_model_name, 512)
    
    def embed_text(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        model = get_text_model()
        embedding = model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts (batched)."""
        if not texts:
            return []
        
        model = get_text_model()
        embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        return embeddings.tolist()
    
    def embed_image_from_url(self, url: str) -> Optional[list[float]]:
        """Generate embedding for an image from URL."""
        try:
            import httpx
            from PIL import Image
            from io import BytesIO
            
            # Download image
            response = httpx.get(url, timeout=30.0, follow_redirects=True)
            response.raise_for_status()
            
            # Load and process image
            image = Image.open(BytesIO(response.content))
            
            # Get embedding
            model = get_image_model()
            embedding = model.encode(image, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            print(f"[WARN] Failed to embed image from {url}: {e}")
            return None
    
    def embed_product(
        self,
        title: str,
        description: str,
        category: str = "",
        image_url: Optional[str] = None,
        include_image: bool = False,
    ) -> dict[str, list[float]]:
        """
        Generate embeddings for a product.
        
        Returns dict with 'text' embedding and optionally 'image' embedding.
        """
        # Combine text fields for embedding
        text = f"{title}. {description}"
        if category:
            text += f" Category: {category}"
        
        embeddings = {
            "text": self.embed_text(text),
        }
        
        if include_image and image_url:
            image_embedding = self.embed_image_from_url(image_url)
            if image_embedding:
                embeddings["image"] = image_embedding
        
        return embeddings


# Module-level convenience functions
@lru_cache(maxsize=1)
def get_embedding_service() -> EmbeddingService:
    """Get singleton embedding service."""
    return EmbeddingService()


def embed_text(text: str) -> list[float]:
    """Convenience function to embed text."""
    return get_embedding_service().embed_text(text)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Convenience function to embed multiple texts."""
    return get_embedding_service().embed_texts(texts)
