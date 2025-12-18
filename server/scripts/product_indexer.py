"""
Product Indexing Service for eaichat
=====================================

This module provides helper functions for:
- Fetching products from Fake Store API
- Creating Qdrant collection schema
- Generating embeddings with SentenceTransformers
- Batch upserting vectors to Qdrant
- RAG pipeline query functions
- Temporal workflow integration hooks

Usage:
    python -m server.scripts.product_indexer --fetch --index
    python -m server.scripts.product_indexer --reindex
"""

import argparse
import json
import os
from dataclasses import dataclass
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# Configuration
# ============================================================================

FAKE_STORE_API = "https://fakestoreapi.com/products"
QDRANT_HOST = os.getenv("QDRANT__HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT__PORT", "6333"))
COLLECTION_NAME = "products"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384
BATCH_SIZE = 32

# Database config
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "eaichat")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "secret")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "eaichat")


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class Product:
    id: int
    title: str
    description: str
    price: float
    category: str
    image: str
    rating_rate: float = 0.0
    rating_count: int = 0


# ============================================================================
# Fake Store API Integration
# ============================================================================

def fetch_products_from_fake_store() -> list[Product]:
    """Fetch all products from Fake Store API."""
    print(f"[INFO] Fetching products from {FAKE_STORE_API}")
    try:
        response = requests.get(FAKE_STORE_API, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        products = []
        for item in data:
            products.append(Product(
                id=item["id"],
                title=item["title"],
                description=item["description"],
                price=item["price"],
                category=item["category"],
                image=item["image"],
                rating_rate=item.get("rating", {}).get("rate", 0.0),
                rating_count=item.get("rating", {}).get("count", 0),
            ))
        
        print(f"[INFO] Fetched {len(products)} products")
        return products
    except Exception as e:
        print(f"[ERROR] Failed to fetch products: {e}")
        return []


def download_product_image(image_url: str, save_dir: str = "") -> Optional[str]:
    """Download product image and return local path."""
    import tempfile
    if not save_dir:
        save_dir = os.path.join(tempfile.gettempdir(), "product_images")
    os.makedirs(save_dir, exist_ok=True)
    filename = os.path.basename(image_url.split("?")[0])
    filepath = os.path.join(save_dir, filename)
    
    if os.path.exists(filepath):
        return filepath
    
    try:
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        with open(filepath, "wb") as f:
            f.write(response.content)
        return filepath
    except Exception as e:
        print(f"[WARN] Failed to download image {image_url}: {e}")
        return None


# ============================================================================
# MySQL Integration
# ============================================================================

def get_mysql_connection():
    """Get MySQL database connection."""
    try:
        import pymysql
        return pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
        )
    except ImportError:
        print("[ERROR] pymysql not installed. Run: pip install PyMySQL")
        return None


def save_products_to_mysql(products: list[Product]) -> int:
    """Save products to MySQL database."""
    conn = get_mysql_connection()
    if not conn:
        return 0
    
    try:
        with conn.cursor() as cursor:
            for p in products:
                cursor.execute("""
                    INSERT INTO products (id, title, description, price, category, created_at)
                    VALUES (%s, %s, %s, %s, %s, NOW())
                    ON DUPLICATE KEY UPDATE
                        title = VALUES(title),
                        description = VALUES(description),
                        price = VALUES(price),
                        category = VALUES(category)
                """, (p.id, p.title, p.description, p.price, p.category))
        conn.commit()
        print(f"[INFO] Saved {len(products)} products to MySQL")
        return len(products)
    except Exception as e:
        print(f"[ERROR] Failed to save products to MySQL: {e}")
        return 0
    finally:
        conn.close()


def get_products_from_mysql(limit: int = 1000, offset: int = 0) -> list[Product]:
    """Fetch products from MySQL for indexing."""
    conn = get_mysql_connection()
    if not conn:
        return []
    
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, title, description, price, category FROM products ORDER BY id LIMIT %s OFFSET %s",
                (limit, offset)
            )
            rows = cursor.fetchall()
            return [
                Product(
                    id=row["id"],
                    title=row["title"],
                    description=row["description"] or "",
                    price=row["price"],
                    category=row["category"] or "",
                    image="",
                )
                for row in rows
            ]
    except Exception as e:
        print(f"[ERROR] Failed to fetch products from MySQL: {e}")
        return []
    finally:
        conn.close()


def update_reindex_checkpoint(collection: str, last_id: int):
    """Update reindex checkpoint in MySQL."""
    conn = get_mysql_connection()
    if not conn:
        return
    
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO reindex_checkpoints (collection, last_processed_id, updated_at)
                VALUES (%s, %s, NOW())
                ON DUPLICATE KEY UPDATE
                    last_processed_id = VALUES(last_processed_id),
                    updated_at = NOW()
            """, (collection, last_id))
        conn.commit()
    except Exception as e:
        print(f"[ERROR] Failed to update checkpoint: {e}")
    finally:
        conn.close()


def get_reindex_checkpoint(collection: str) -> int:
    """Get last processed ID for resumable reindexing."""
    conn = get_mysql_connection()
    if not conn:
        return 0
    
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT last_processed_id FROM reindex_checkpoints WHERE collection = %s",
                (collection,)
            )
            row = cursor.fetchone()
            return row["last_processed_id"] if row else 0
    except Exception as e:
        print(f"[ERROR] Failed to get checkpoint: {e}")
        return 0
    finally:
        conn.close()


# ============================================================================
# Embedding Generation
# ============================================================================

_embedding_model = None

def get_embedding_model():
    """Lazy load SentenceTransformer model."""
    global _embedding_model
    if _embedding_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _embedding_model = SentenceTransformer(EMBEDDING_MODEL)
            print(f"[INFO] Loaded embedding model: {EMBEDDING_MODEL}")
        except ImportError:
            print("[ERROR] sentence-transformers not installed. Run: pip install sentence-transformers")
            return None
    return _embedding_model


def generate_embedding(text: str) -> Optional[list[float]]:
    """Generate embedding for a single text."""
    model = get_embedding_model()
    if model is None:
        return None
    return model.encode(text).tolist()


def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for multiple texts."""
    model = get_embedding_model()
    if model is None:
        return []
    return model.encode(texts).tolist()


def get_product_search_text(product: Product) -> str:
    """Create searchable text from product for embedding."""
    return f"{product.title}. {product.description}. Category: {product.category}"


# ============================================================================
# Qdrant Vector Database Integration
# ============================================================================

def get_qdrant_client():
    """Get Qdrant client."""
    try:
        from qdrant_client import QdrantClient
        return QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    except ImportError:
        print("[ERROR] qdrant-client not installed. Run: pip install qdrant-client")
        return None


def create_collection_schema(collection_name: str = COLLECTION_NAME, recreate: bool = False):
    """Create Qdrant collection with proper schema."""
    client = get_qdrant_client()
    if client is None:
        return False
    
    try:
        from qdrant_client.models import Distance, VectorParams
        
        # Check if collection exists
        collections = client.get_collections().collections
        exists = any(c.name == collection_name for c in collections)
        
        if exists and not recreate:
            print(f"[INFO] Collection '{collection_name}' already exists")
            return True
        
        if exists and recreate:
            print(f"[INFO] Recreating collection '{collection_name}'")
            client.delete_collection(collection_name)
        
        # Create collection with vector config
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=EMBEDDING_DIM,
                distance=Distance.COSINE,
            ),
        )
        print(f"[INFO] Created collection '{collection_name}' with {EMBEDDING_DIM} dimensions")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to create collection: {e}")
        return False


def upsert_product_vectors(products: list[Product], collection_name: str = COLLECTION_NAME) -> int:
    """Batch upsert product vectors to Qdrant."""
    client = get_qdrant_client()
    if client is None:
        return 0
    
    try:
        from qdrant_client.models import PointStruct
        
        # Generate embeddings
        texts = [get_product_search_text(p) for p in products]
        embeddings = generate_embeddings_batch(texts)
        
        if not embeddings:
            print("[ERROR] Failed to generate embeddings")
            return 0
        
        # Create points
        points = []
        for i, product in enumerate(products):
            points.append(PointStruct(
                id=product.id,
                vector=embeddings[i],
                payload={
                    "title": product.title,
                    "description": product.description[:500],  # Truncate for storage
                    "price": product.price,
                    "category": product.category,
                    "image": product.image,
                    "rating_rate": product.rating_rate,
                    "rating_count": product.rating_count,
                },
            ))
        
        # Upsert to Qdrant
        client.upsert(collection_name=collection_name, points=points)
        print(f"[INFO] Upserted {len(points)} vectors to '{collection_name}'")
        return len(points)
    except Exception as e:
        print(f"[ERROR] Failed to upsert vectors: {e}")
        return 0


def delete_product_vector(product_id: int, collection_name: str = COLLECTION_NAME) -> bool:
    """Delete a single product vector from Qdrant."""
    client = get_qdrant_client()
    if client is None:
        return False
    
    try:
        client.delete(collection_name=collection_name, points_selector=[product_id])
        return True
    except Exception as e:
        print(f"[ERROR] Failed to delete vector {product_id}: {e}")
        return False


def get_collection_stats(collection_name: str = COLLECTION_NAME) -> dict:
    """Get collection statistics."""
    client = get_qdrant_client()
    if client is None:
        return {}
    
    try:
        info = client.get_collection(collection_name)
        return {
            "name": collection_name,
            "vectors_count": info.vectors_count,
            "points_count": info.points_count,
            "status": info.status.value,
        }
    except Exception as e:
        print(f"[ERROR] Failed to get collection stats: {e}")
        return {}


# ============================================================================
# RAG Pipeline Functions
# ============================================================================

def search_similar_products(
    query: str,
    top_k: int = 5,
    category_filter: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    collection_name: str = COLLECTION_NAME,
) -> list[dict]:
    """
    Search for similar products using vector similarity.
    This is the main function for RAG retrieval.
    """
    client = get_qdrant_client()
    if client is None:
        return []
    
    try:
        from qdrant_client.models import Filter, FieldCondition, MatchValue, Range
        
        # Generate query embedding
        query_vector = generate_embedding(query)
        if query_vector is None:
            return []
        
        # Build filter conditions
        must_conditions = []
        if category_filter:
            must_conditions.append(
                FieldCondition(key="category", match=MatchValue(value=category_filter))
            )
        if min_price is not None or max_price is not None:
            must_conditions.append(
                FieldCondition(
                    key="price",
                    range=Range(gte=min_price, lte=max_price),
                )
            )
        
        query_filter = Filter(must=must_conditions) if must_conditions else None
        
        # Search
        results = client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=top_k,
            query_filter=query_filter,
        )
        
        return [
            {
                "id": hit.id,
                "score": hit.score,
                **hit.payload,
            }
            for hit in results
        ]
    except Exception as e:
        print(f"[ERROR] Search failed: {e}")
        return []


def get_product_context_for_llm(query: str, top_k: int = 3) -> str:
    """
    Get formatted product context for LLM prompt injection.
    Used in RAG pipeline to provide relevant product information to LLM.
    """
    products = search_similar_products(query, top_k=top_k)
    if not products:
        return "No relevant products found."
    
    context_parts = []
    for i, p in enumerate(products, 1):
        context_parts.append(
            f"{i}. **{p['title']}** (${p['price']:.2f})\n"
            f"   Category: {p['category']}\n"
            f"   {p['description'][:200]}..."
        )
    
    return "\n\n".join(context_parts)


# ============================================================================
# Reindexing Pipeline (Temporal Integration Hooks)
# ============================================================================

def reindex_all_products(batch_size: int = BATCH_SIZE, resume: bool = True):
    """
    Full reindex pipeline - can be called from Temporal workflow.
    Supports resumable checkpointing.
    """
    print(f"[INFO] Starting full reindex (batch_size={batch_size}, resume={resume})")
    
    # Ensure collection exists
    if not create_collection_schema():
        print("[ERROR] Failed to create collection schema")
        return False
    
    # Get checkpoint
    offset = get_reindex_checkpoint(COLLECTION_NAME) if resume else 0
    total_indexed = 0
    
    while True:
        # Fetch batch from MySQL
        products = get_products_from_mysql(limit=batch_size, offset=offset)
        if not products:
            break
        
        # Index batch
        indexed = upsert_product_vectors(products)
        total_indexed += indexed
        
        # Update checkpoint
        last_id = max(p.id for p in products)
        update_reindex_checkpoint(COLLECTION_NAME, last_id)
        
        offset += batch_size
        print(f"[INFO] Progress: indexed {total_indexed} products")
    
    print(f"[INFO] Reindex complete: {total_indexed} products indexed")
    return True


def fetch_and_index_from_fake_store():
    """Fetch from Fake Store API, save to MySQL, and index to Qdrant."""
    print("[INFO] Starting Fake Store API fetch and index pipeline")
    
    # Fetch products
    products = fetch_products_from_fake_store()
    if not products:
        print("[ERROR] No products fetched")
        return False
    
    # Save to MySQL
    saved = save_products_to_mysql(products)
    print(f"[INFO] Saved {saved} products to MySQL")
    
    # Create collection if needed
    if not create_collection_schema():
        print("[ERROR] Failed to create collection")
        return False
    
    # Index to Qdrant
    indexed = upsert_product_vectors(products)
    print(f"[INFO] Indexed {indexed} products to Qdrant")
    
    return indexed > 0


# ============================================================================
# Temporal Workflow Hooks (for temporal worker integration)
# ============================================================================

def temporal_reindex_activity():
    """
    Activity function for Temporal reindex workflow.
    Called by the Temporal worker.
    """
    return reindex_all_products(resume=True)


def temporal_fetch_and_index_activity():
    """
    Activity function for Temporal sync workflow.
    Fetches from Fake Store API and indexes.
    """
    return fetch_and_index_from_fake_store()


# ============================================================================
# CLI Entry Point
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Product Indexing Service")
    parser.add_argument("--fetch", action="store_true", help="Fetch products from Fake Store API")
    parser.add_argument("--index", action="store_true", help="Index products to Qdrant")
    parser.add_argument("--reindex", action="store_true", help="Full reindex from MySQL")
    parser.add_argument("--stats", action="store_true", help="Show collection statistics")
    parser.add_argument("--search", type=str, help="Test search query")
    parser.add_argument("--create-schema", action="store_true", help="Create Qdrant collection schema")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE, help="Batch size for indexing")
    parser.add_argument("--no-resume", action="store_true", help="Don't resume from checkpoint")
    
    args = parser.parse_args()
    
    if args.create_schema:
        create_collection_schema(recreate=True)
    
    if args.fetch and args.index:
        fetch_and_index_from_fake_store()
    elif args.fetch:
        products = fetch_products_from_fake_store()
        save_products_to_mysql(products)
    elif args.index:
        reindex_all_products(batch_size=args.batch_size, resume=not args.no_resume)
    
    if args.reindex:
        reindex_all_products(batch_size=args.batch_size, resume=not args.no_resume)
    
    if args.stats:
        stats = get_collection_stats()
        print(json.dumps(stats, indent=2))
    
    if args.search:
        results = search_similar_products(args.search)
        print(json.dumps(results, indent=2, default=str))


if __name__ == "__main__":
    main()
