"""
Duplicate Content Detector for WordPress
Uses semantic similarity via embeddings to detect duplicate/similar content.
Includes persistent caching to avoid re-indexing on every search.
"""
import asyncio
import hashlib
import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# Profiling utilities
_PROFILING_ENABLED = False
_PROFILE_DATA: Dict[str, List[float]] = {}


def enable_profiling(enabled: bool = True):
    """Enable or disable profiling."""
    global _PROFILING_ENABLED
    _PROFILING_ENABLED = enabled


def get_profile_data() -> Dict[str, Dict[str, float]]:
    """Get profiling statistics."""
    stats = {}
    for name, times in _PROFILE_DATA.items():
        if times:
            stats[name] = {
                "count": len(times),
                "total": sum(times),
                "avg": sum(times) / len(times),
                "min": min(times),
                "max": max(times),
            }
    return stats


def clear_profile_data():
    """Clear profiling data."""
    global _PROFILE_DATA
    _PROFILE_DATA = {}


def profile(name: str = None):
    """Decorator to profile function execution time."""
    def decorator(func: Callable):
        func_name = name or func.__name__
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not _PROFILING_ENABLED:
                return func(*args, **kwargs)
            
            start = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                elapsed = time.perf_counter() - start
                if func_name not in _PROFILE_DATA:
                    _PROFILE_DATA[func_name] = []
                _PROFILE_DATA[func_name].append(elapsed)
                logger.debug(f"[PROFILE] {func_name}: {elapsed:.4f}s")
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not _PROFILING_ENABLED:
                return await func(*args, **kwargs)
            
            start = time.perf_counter()
            try:
                return await func(*args, **kwargs)
            finally:
                elapsed = time.perf_counter() - start
                if func_name not in _PROFILE_DATA:
                    _PROFILE_DATA[func_name] = []
                _PROFILE_DATA[func_name].append(elapsed)
                logger.debug(f"[PROFILE] {func_name}: {elapsed:.4f}s")
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return wrapper
    return decorator

# Cache directory
CACHE_DIR = Path.home() / ".praisonaiwp" / "cache"
CACHE_DB = CACHE_DIR / "embeddings.db"


@dataclass
class DuplicateResult:
    """Result of a duplicate check."""
    is_duplicate: bool
    similarity_score: float
    post_id: Optional[int] = None
    title: Optional[str] = None
    url: Optional[str] = None
    status: str = "unique"  # unique, similar, duplicate
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_duplicate": self.is_duplicate,
            "similarity_score": self.similarity_score,
            "post_id": self.post_id,
            "title": self.title,
            "url": self.url,
            "status": self.status
        }


@dataclass
class DuplicateCheckResponse:
    """Response from duplicate check."""
    query: str
    threshold: float
    matches: List[DuplicateResult] = field(default_factory=list)
    total_posts_checked: int = 0
    has_duplicates: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "threshold": self.threshold,
            "matches": [m.to_dict() for m in self.matches],
            "total_posts_checked": self.total_posts_checked,
            "has_duplicates": self.has_duplicates,
            "duplicate_count": sum(1 for m in self.matches if m.is_duplicate)
        }


# Singleton vector tool instance
_VECTOR_TOOL_INSTANCE = None
_QDRANT_CLIENT = None

def _get_vector_tool():
    """Lazy import SQLiteVectorTool from praisonai_tools (singleton)."""
    global _VECTOR_TOOL_INSTANCE
    if _VECTOR_TOOL_INSTANCE is not None:
        return _VECTOR_TOOL_INSTANCE
    try:
        from praisonai_tools import SQLiteVectorTool
        _VECTOR_TOOL_INSTANCE = SQLiteVectorTool(path=str(CACHE_DB))
        return _VECTOR_TOOL_INSTANCE
    except ImportError:
        logger.warning("praisonai_tools not installed, falling back to local cache")
        return None


def _get_qdrant_client(url: str = "http://localhost:6333"):
    """Get Qdrant client (singleton, lazy import)."""
    global _QDRANT_CLIENT
    if _QDRANT_CLIENT is not None:
        return _QDRANT_CLIENT
    try:
        from qdrant_client import QdrantClient
        _QDRANT_CLIENT = QdrantClient(url=url)
        # Test connection
        _QDRANT_CLIENT.get_collections()
        logger.info(f"Connected to Qdrant at {url}")
        return _QDRANT_CLIENT
    except ImportError:
        logger.debug("qdrant-client not installed")
        return None
    except Exception as e:
        logger.debug(f"Qdrant not available: {e}")
        return None


class QdrantVectorStore:
    """
    Qdrant vector store for high-performance similarity search.
    Optional - falls back to SQLite if Qdrant is not available.
    """
    
    COLLECTION_NAME = "wp_posts"
    VECTOR_SIZE = 1536  # OpenAI text-embedding-3-small
    
    def __init__(self, url: str = "http://localhost:6333"):
        self.url = url
        self.client = _get_qdrant_client(url)
        if self.client:
            self._ensure_collection()
    
    def _ensure_collection(self):
        """Create collection if it doesn't exist."""
        try:
            from qdrant_client.models import Distance, VectorParams
            collections = [c.name for c in self.client.get_collections().collections]
            if self.COLLECTION_NAME not in collections:
                self.client.create_collection(
                    collection_name=self.COLLECTION_NAME,
                    vectors_config=VectorParams(size=self.VECTOR_SIZE, distance=Distance.COSINE)
                )
                logger.info(f"Created Qdrant collection: {self.COLLECTION_NAME}")
        except Exception as e:
            logger.error(f"Failed to create Qdrant collection: {e}")
    
    @property
    def available(self) -> bool:
        return self.client is not None
    
    def add(self, post_id: int, title: str, url: str, content_hash: str, embedding: List[float]):
        """Add a single embedding to Qdrant."""
        if not self.client:
            return
        try:
            from qdrant_client.models import PointStruct
            self.client.upsert(
                collection_name=self.COLLECTION_NAME,
                points=[PointStruct(
                    id=post_id,
                    vector=embedding,
                    payload={"title": title, "url": url, "content_hash": content_hash}
                )]
            )
        except Exception as e:
            logger.error(f"Qdrant add error: {e}")
    
    def add_batch(self, items: List[Tuple[int, str, str, str, List[float]]]):
        """Add multiple embeddings to Qdrant in batch."""
        if not self.client or not items:
            return
        try:
            from qdrant_client.models import PointStruct
            points = [
                PointStruct(
                    id=post_id,
                    vector=embedding,
                    payload={"title": title, "url": url, "content_hash": content_hash}
                )
                for post_id, title, url, content_hash, embedding in items
            ]
            self.client.upsert(collection_name=self.COLLECTION_NAME, points=points)
            logger.debug(f"Qdrant batch upsert: {len(points)} points")
        except Exception as e:
            logger.error(f"Qdrant batch add error: {e}")
    
    def get_all(self) -> List[Tuple[int, str, str, List[float]]]:
        """Get all embeddings from Qdrant."""
        if not self.client:
            return []
        try:
            results = []
            offset = None
            while True:
                response = self.client.scroll(
                    collection_name=self.COLLECTION_NAME,
                    limit=1000,
                    offset=offset,
                    with_vectors=True,
                    with_payload=True
                )
                points, offset = response
                if not points:
                    break
                for point in points:
                    results.append((
                        point.id,
                        point.payload.get("title", ""),
                        point.payload.get("url", ""),
                        point.vector
                    ))
                if offset is None:
                    break
            return results
        except Exception as e:
            logger.error(f"Qdrant get_all error: {e}")
            return []
    
    def count(self) -> int:
        """Get count of embeddings in Qdrant."""
        if not self.client:
            return 0
        try:
            info = self.client.get_collection(self.COLLECTION_NAME)
            return info.points_count
        except Exception as e:
            logger.debug(f"Qdrant count error: {e}")
            return 0
    
    def clear(self):
        """Clear all embeddings from Qdrant."""
        if not self.client:
            return
        try:
            self.client.delete_collection(self.COLLECTION_NAME)
            self._ensure_collection()
            logger.info("Qdrant collection cleared")
        except Exception as e:
            logger.error(f"Qdrant clear error: {e}")
    
    def search(self, embedding: List[float], limit: int = 10) -> List[Tuple[int, str, str, float]]:
        """Search for similar embeddings."""
        if not self.client:
            return []
        try:
            results = self.client.search(
                collection_name=self.COLLECTION_NAME,
                query_vector=embedding,
                limit=limit,
                with_payload=True
            )
            return [
                (r.id, r.payload.get("title", ""), r.payload.get("url", ""), r.score)
                for r in results
            ]
        except Exception as e:
            logger.error(f"Qdrant search error: {e}")
            return []


class EmbeddingCache:
    """
    Embedding cache using SQLiteVectorTool from praisonai_tools.
    Falls back to local SQLite implementation if not available.
    """
    
    def __init__(self, db_path: Path = CACHE_DB):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._tool = _get_vector_tool()
        if not self._tool:
            self._init_local_db()
    
    def _init_local_db(self):
        """Initialize local SQLite database (fallback)."""
        import sqlite3
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS embeddings (
                    post_id INTEGER PRIMARY KEY,
                    title TEXT,
                    url TEXT,
                    content_hash TEXT,
                    embedding TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_content_hash ON embeddings(content_hash)")
    
    def get(self, post_id: int) -> Optional[Tuple[str, List[float], Dict]]:
        """Get cached embedding for a post."""
        if self._tool:
            results = self._tool.get(collection="wp_posts", ids=[str(post_id)], include=["embeddings", "metadatas"])
            if results and not any("error" in r for r in results):
                for r in results:
                    if r.get("id") == str(post_id):
                        meta = r.get("metadata") or {}
                        emb = r.get("embedding", [])
                        return meta.get("title", ""), emb, meta
        else:
            import sqlite3
            with sqlite3.connect(self.db_path) as conn:
                row = conn.execute(
                    "SELECT title, url, embedding FROM embeddings WHERE post_id = ?",
                    (post_id,)
                ).fetchone()
                if row:
                    return row[0], json.loads(row[2]), {"title": row[0], "url": row[1]}
        return None
    
    def set(self, post_id: int, title: str, url: str, content_hash: str, embedding: List[float]):
        """Cache embedding for a post."""
        if self._tool:
            self._tool.add(
                collection="wp_posts",
                documents=[f"{title}"],
                embeddings=[embedding],
                ids=[str(post_id)],
                metadatas=[{"title": title, "url": url, "content_hash": content_hash}]
            )
        else:
            import sqlite3
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO embeddings (post_id, title, url, content_hash, embedding)
                    VALUES (?, ?, ?, ?, ?)
                """, (post_id, title, url, content_hash, json.dumps(embedding)))
    
    def set_batch(self, items: List[Tuple[int, str, str, str, List[float]]]):
        """
        Batch insert embeddings for multiple posts.
        
        Args:
            items: List of (post_id, title, url, content_hash, embedding) tuples
        """
        if not items:
            return
        
        if self._tool:
            # Batch add to vector tool
            ids = [str(item[0]) for item in items]
            documents = [item[1] for item in items]
            embeddings = [item[4] for item in items]
            metadatas = [{"title": item[1], "url": item[2], "content_hash": item[3]} for item in items]
            self._tool.add(
                collection="wp_posts",
                documents=documents,
                embeddings=embeddings,
                ids=ids,
                metadatas=metadatas
            )
        else:
            import sqlite3
            with sqlite3.connect(self.db_path) as conn:
                conn.executemany("""
                    INSERT OR REPLACE INTO embeddings (post_id, title, url, content_hash, embedding)
                    VALUES (?, ?, ?, ?, ?)
                """, [(item[0], item[1], item[2], item[3], json.dumps(item[4])) for item in items])
    
    def get_all(self) -> List[Tuple[int, str, str, List[float]]]:
        """Get all cached embeddings."""
        if self._tool:
            results = self._tool.get(collection="wp_posts", include=["embeddings", "metadatas"])
            items = []
            for r in results:
                if "error" not in r:
                    meta = r.get("metadata") or {}
                    emb = r.get("embedding", [])
                    items.append((
                        int(r["id"]),
                        meta.get("title", ""),
                        meta.get("url", ""),
                        emb
                    ))
            return items
        else:
            import sqlite3
            with sqlite3.connect(self.db_path) as conn:
                rows = conn.execute(
                    "SELECT post_id, title, url, embedding FROM embeddings"
                ).fetchall()
                return [(r[0], r[1], r[2], json.loads(r[3])) for r in rows]
    
    def query(self, embedding: List[float], n_results: int = 10) -> List[Dict]:
        """Query similar embeddings using vector store."""
        if self._tool:
            return self._tool.query(
                collection="wp_posts",
                query_embeddings=[embedding],
                n_results=n_results
            )
        return []
    
    def count(self) -> int:
        """Count cached embeddings."""
        if self._tool:
            result = self._tool.count(collection="wp_posts")
            return result.get("count", 0)
        else:
            import sqlite3
            with sqlite3.connect(self.db_path) as conn:
                return conn.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0]
    
    def clear(self):
        """Clear all cached embeddings."""
        if self._tool:
            self._tool.clear(collection="wp_posts")
        else:
            import sqlite3
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM embeddings")
        logger.info("Embedding cache cleared")


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    try:
        import numpy as np
        a_arr = np.array(a)
        b_arr = np.array(b)
        dot = np.dot(a_arr, b_arr)
        norm_a = np.linalg.norm(a_arr)
        norm_b = np.linalg.norm(b_arr)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(dot / (norm_a * norm_b))
    except ImportError:
        # Fallback to pure Python
        import math
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)


def cosine_similarity_batch(query: List[float], embeddings: List[List[float]]) -> List[float]:
    """
    Compute cosine similarity between query and multiple embeddings using numpy.
    
    This is MUCH faster than computing one-by-one for large datasets.
    
    Args:
        query: Query embedding vector
        embeddings: List of embedding vectors to compare against
        
    Returns:
        List of similarity scores
    """
    if not embeddings:
        return []
    
    try:
        import numpy as np
        query_arr = np.array(query)
        emb_arr = np.array(embeddings)
        
        # Normalize query
        query_norm = np.linalg.norm(query_arr)
        if query_norm == 0:
            return [0.0] * len(embeddings)
        query_normalized = query_arr / query_norm
        
        # Normalize all embeddings at once
        emb_norms = np.linalg.norm(emb_arr, axis=1, keepdims=True)
        # Avoid division by zero
        emb_norms = np.where(emb_norms == 0, 1, emb_norms)
        emb_normalized = emb_arr / emb_norms
        
        # Compute all similarities at once via matrix multiplication
        similarities = np.dot(emb_normalized, query_normalized)
        return similarities.tolist()
    except ImportError:
        # Fallback to sequential computation
        return [cosine_similarity(query, emb) for emb in embeddings]


class DuplicateDetector:
    """
    Detects duplicate content in WordPress using embedding-based semantic similarity.
    
    Uses persistent SQLite cache to avoid re-indexing on every search.
    """
    
    def __init__(
        self,
        wp_client,
        threshold: float = 0.7,
        duplicate_threshold: float = 0.95,
        embedding_model: str = "text-embedding-3-small",
        use_cache: bool = True,
        use_qdrant: bool = False,
        qdrant_url: str = "http://localhost:6333",
        verbose: int = 0
    ):
        """
        Initialize the duplicate detector.
        
        Args:
            wp_client: WordPress client instance
            threshold: Minimum similarity to flag as similar (0-1)
            duplicate_threshold: Similarity threshold to flag as duplicate (0-1)
            embedding_model: Model to use for embeddings
            use_cache: Whether to use persistent cache
            use_qdrant: Use Qdrant vector store (optional, falls back to SQLite)
            qdrant_url: Qdrant server URL
            verbose: Verbosity level
        """
        self.wp_client = wp_client
        self.threshold = threshold
        self.duplicate_threshold = duplicate_threshold
        self.embedding_model = embedding_model
        self.use_cache = use_cache
        self.use_qdrant = use_qdrant
        self.verbose = verbose
        
        # Qdrant vector store (optional, for high-performance search)
        self.qdrant = None
        if use_qdrant:
            self.qdrant = QdrantVectorStore(url=qdrant_url)
            if self.qdrant.available:
                logger.info("Using Qdrant vector store")
            else:
                logger.warning("Qdrant not available, falling back to SQLite cache")
                self.qdrant = None
        
        # Persistent cache (SQLite fallback)
        self.cache = EmbeddingCache() if use_cache else None
        
        # In-memory embeddings for current session
        self._embeddings: Dict[int, Tuple[str, str, List[float]]] = {}
        self._indexed = False
    
    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for text using praisonai.embedding().
        
        Handles both old API (returns List[float]) and new API (returns EmbeddingResult).
        """
        try:
            from praisonai import embedding
            result = embedding(text, model=self.embedding_model)
            # Handle EmbeddingResult (new API returns object with .embeddings)
            if hasattr(result, 'embeddings'):
                return result.embeddings[0]  # Extract first embedding vector
            # Fallback for raw list (old API or direct litellm)
            return result
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            raise
    
    @profile("embeddings_batch")
    def _get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Get embeddings for multiple texts in a single API call (batch).
        
        OpenAI supports up to 2048 inputs per batch request.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        try:
            from praisonai import embedding
            # OpenAI embedding API supports batch input
            result = embedding(texts, model=self.embedding_model)
            # Handle EmbeddingResult (new API returns object with .embeddings)
            if hasattr(result, 'embeddings'):
                return result.embeddings
            # Fallback for raw list
            return result
        except Exception as e:
            logger.error(f"Batch embedding error: {e}")
            raise
    
    async def _get_embeddings_batch_async(self, texts: List[str]) -> List[List[float]]:
        """
        Get embeddings for multiple texts asynchronously using litellm.aembedding().
        
        This is faster than sync batch for large datasets as it doesn't block.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        try:
            # Try litellm async embedding first (preferred)
            from litellm import aembedding
            result = await aembedding(model=self.embedding_model, input=texts)
            # litellm returns EmbeddingResponse with .data list
            if hasattr(result, 'data'):
                return [item.embedding for item in result.data]
            return result
        except ImportError:
            # Fallback to sync in thread pool
            logger.debug("litellm not available, falling back to sync embedding")
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._get_embeddings_batch, texts)
        except Exception as e:
            logger.error(f"Async batch embedding error: {e}")
            raise
    
    async def _index_posts_async(
        self, 
        posts: List[Dict], 
        batch_size: int = 50,
        max_concurrent: int = 10
    ) -> int:
        """
        Index posts using async embeddings for maximum throughput.
        
        Args:
            posts: List of post dicts with post_id, title, url, text
            batch_size: Posts per batch for embedding API
            max_concurrent: Maximum concurrent API calls
            
        Returns:
            Number of posts indexed
        """
        start_time = time.perf_counter()
        
        # Split into batches
        batches = [posts[i:i + batch_size] for i in range(0, len(posts), batch_size)]
        logger.info(f"[ASYNC] Processing {len(posts)} posts in {len(batches)} batches...")
        
        if self.verbose:
            print(f"[ASYNC] Processing {len(posts)} posts in {len(batches)} batches...")
        
        results = []
        errors = 0
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_batch(batch_idx: int, batch: List[Dict]) -> List[Tuple]:
            async with semaphore:
                texts = [p["text"] for p in batch]
                try:
                    embeddings = await self._get_embeddings_batch_async(texts)
                    batch_results = []
                    for i, post in enumerate(batch):
                        if i < len(embeddings):
                            content_hash = self._content_hash(post["text"])
                            batch_results.append((
                                post["post_id"],
                                post["title"],
                                post["url"],
                                content_hash,
                                embeddings[i]
                            ))
                    return batch_results
                except Exception as e:
                    logger.error(f"Async batch {batch_idx} failed: {e}")
                    return []
        
        # Process all batches concurrently
        tasks = [process_batch(i, batch) for i, batch in enumerate(batches)]
        batch_results_list = await asyncio.gather(*tasks, return_exceptions=True)
        
        completed = 0
        for batch_result in batch_results_list:
            if isinstance(batch_result, Exception):
                errors += 1
                logger.error(f"Batch failed with exception: {batch_result}")
            else:
                results.extend(batch_result)
                completed += 1
                if self.verbose and completed % 5 == 0:
                    print(f"[ASYNC] Completed {completed}/{len(batches)} batches | Indexed: {len(results)}")
        
        # Store results in memory
        for post_id, title, url, content_hash, embedding in results:
            self._embeddings[post_id] = (title, url, embedding)
        
        # Batch write to Qdrant (if available) and SQLite cache
        if self.qdrant and self.qdrant.available and results:
            self.qdrant.add_batch(results)
        if self.cache and results:
            self.cache.set_batch(results)
        
        elapsed = time.perf_counter() - start_time
        logger.info(f"[ASYNC] Indexing completed: {len(results)} posts in {elapsed:.1f}s ({errors} errors)")
        if self.verbose:
            print(f"[ASYNC] Indexed {len(results)} posts in {elapsed:.1f}s")
        
        return len(results)
    
    def _content_hash(self, text: str) -> str:
        """Generate hash for content."""
        return hashlib.md5(text.encode()).hexdigest()
    
    def _get_post_text(self, post: Dict) -> str:
        """Extract searchable text from a post."""
        title = post.get("post_title", post.get("title", ""))
        content = ""
        
        if "post_content" in post:
            content = post["post_content"]
        elif "content" in post:
            content = post["content"]
        elif "ID" in post:
            try:
                content = self.wp_client.get_post(post["ID"], field="post_content")
            except Exception as e:
                logger.warning(f"Failed to get content for post {post['ID']}: {e}")
        
        content = str(content)[:1000] if content else ""
        return f"{title}\n\n{content}"
    
    @profile("index_posts")
    def index_posts(
        self,
        post_type: str = "post",
        post_status: str = "publish",
        category: Optional[str] = None,
        force: bool = False,
        parallel: bool = True,
        max_workers: int = 25,
        batch_size: int = 50,
        use_async: bool = False
    ) -> int:
        """
        Index all posts for similarity search.
        Uses persistent cache - only indexes new/changed posts.
        
        Args:
            post_type: Type of posts to index
            post_status: Status filter
            category: Category filter (optional)
            force: Force re-indexing even if cached
            parallel: Use parallel processing for faster indexing (default: True)
            max_workers: Number of parallel workers (default: 25)
            batch_size: Number of posts per batch for embedding API (default: 50)
            use_async: Use async embeddings via litellm.aembedding() (default: False)
            
        Returns:
            Number of posts indexed (new + from cache)
        """
        # Load from Qdrant first (if available), then SQLite cache
        if self.qdrant and self.qdrant.available and not force:
            qdrant_count = self.qdrant.count()
            if qdrant_count > 0:
                logger.info(f"Loading {qdrant_count} embeddings from Qdrant...")
                for post_id, title, url, embedding in self.qdrant.get_all():
                    self._embeddings[post_id] = (title, url, embedding)
                self._indexed = True
                if self.verbose:
                    print(f"Loaded {qdrant_count} embeddings from Qdrant")
        elif self.cache and not force:
            cached_count = self.cache.count()
            if cached_count > 0:
                logger.info(f"Loading {cached_count} embeddings from SQLite cache...")
                for post_id, title, url, embedding in self.cache.get_all():
                    self._embeddings[post_id] = (title, url, embedding)
                self._indexed = True
                if self.verbose:
                    print(f"Loaded {cached_count} cached embeddings")
        
        logger.info(f"Fetching {post_type}s with status={post_status}...")
        
        filters = {"post_status": post_status, "posts_per_page": 2000}
        if category:
            filters["category_name"] = category
        
        posts = self.wp_client.list_posts(post_type=post_type, **filters)
        
        if not posts:
            logger.warning("No posts found")
            return len(self._embeddings)
        
        # Filter to only new posts
        new_posts = []
        for post in posts:
            post_id = post.get("ID")
            if not post_id or post_id in self._embeddings:
                continue
            text = self._get_post_text(post)
            if not text.strip():
                continue
            new_posts.append({
                "post_id": post_id,
                "title": post.get("post_title", ""),
                "url": post.get("guid", ""),
                "text": text
            })
        
        if not new_posts:
            self._indexed = True
            return len(self._embeddings)
        
        logger.info(f"Indexing {len(new_posts)} new posts (parallel={parallel}, async={use_async}, workers={max_workers}, batch={batch_size})...")
        
        if use_async:
            # Use async embeddings for maximum throughput
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If already in async context, create task
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        future = pool.submit(asyncio.run, self._index_posts_async(new_posts, batch_size, max_workers))
                        new_indexed = future.result()
                else:
                    new_indexed = loop.run_until_complete(self._index_posts_async(new_posts, batch_size, max_workers))
            except RuntimeError:
                # No event loop, create one
                new_indexed = asyncio.run(self._index_posts_async(new_posts, batch_size, max_workers))
        elif parallel:
            new_indexed = self._index_posts_parallel(new_posts, max_workers, batch_size)
        else:
            new_indexed = self._index_posts_sequential(new_posts)
        
        self._indexed = True
        total = len(self._embeddings)
        logger.info(f"Indexed {new_indexed} new posts (total: {total})")
        if self.verbose:
            print(f"Indexed {new_indexed} new posts (total: {total} in cache)")
        
        return total
    
    def _index_posts_sequential(self, posts: List[Dict]) -> int:
        """Index posts sequentially (fallback method)."""
        new_indexed = 0
        for post in posts:
            post_id = post["post_id"]
            title = post["title"]
            url = post["url"]
            text = post["text"]
            
            try:
                embedding = self._get_embedding(text)
            except Exception as e:
                logger.error(f"Failed to embed post {post_id}: {e}")
                continue
            
            self._embeddings[post_id] = (title, url, embedding)
            if self.cache:
                content_hash = self._content_hash(text)
                self.cache.set(post_id, title, url, content_hash, embedding)
            
            new_indexed += 1
            if self.verbose and new_indexed % 50 == 0:
                print(f"Indexed {new_indexed} new posts...")
        
        return new_indexed
    
    def _index_posts_parallel(self, posts: List[Dict], max_workers: int = 25, batch_size: int = 50) -> int:
        """
        Index posts in parallel using batch embeddings and ThreadPoolExecutor.
        
        Strategy:
        1. Split posts into batches of batch_size
        2. Process batches in parallel using ThreadPoolExecutor
        3. Each batch uses batch embedding API for efficiency
        4. Batch write results to cache
        
        Args:
            posts: List of post dicts with post_id, title, url, text
            max_workers: Number of parallel workers
            batch_size: Posts per batch for embedding API
            
        Returns:
            Number of posts indexed
        """
        import time
        start_time = time.time()
        
        # Split into batches
        batches = [posts[i:i + batch_size] for i in range(0, len(posts), batch_size)]
        logger.info(f"Processing {len(posts)} posts in {len(batches)} batches with {max_workers} workers...")
        
        if self.verbose:
            print(f"Processing {len(posts)} posts in {len(batches)} batches...")
        
        results = []
        errors = 0
        
        def process_batch(batch: List[Dict]) -> List[Tuple[int, str, str, str, List[float]]]:
            """Process a single batch of posts."""
            texts = [p["text"] for p in batch]
            try:
                embeddings = self._get_embeddings_batch(texts)
                batch_results = []
                for i, post in enumerate(batch):
                    if i < len(embeddings):
                        content_hash = self._content_hash(post["text"])
                        batch_results.append((
                            post["post_id"],
                            post["title"],
                            post["url"],
                            content_hash,
                            embeddings[i]
                        ))
                return batch_results
            except Exception as e:
                logger.error(f"Batch embedding failed: {e}")
                return []
        
        # Process batches in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(process_batch, batch): i for i, batch in enumerate(batches)}
            
            completed = 0
            total_indexed = 0
            for future in as_completed(futures):
                batch_idx = futures[future]
                try:
                    batch_results = future.result()
                    results.extend(batch_results)
                    completed += 1
                    total_indexed += len(batch_results)
                    pending = len(posts) - total_indexed
                    # Always log progress
                    logger.info(f"[INDEXING] Batch {completed}/{len(batches)} done | Indexed: {total_indexed} | Pending: {pending}")
                    if self.verbose:
                        print(f"[INDEXING] Batch {completed}/{len(batches)} | Indexed: {total_indexed}/{len(posts)} | Pending: {pending}")
                except Exception as e:
                    logger.error(f"Batch {batch_idx} failed: {e}")
                    errors += 1
        
        # Store results in memory
        for post_id, title, url, content_hash, embedding in results:
            self._embeddings[post_id] = (title, url, embedding)
        
        # Batch write to Qdrant (if available) and SQLite cache
        if self.qdrant and self.qdrant.available and results:
            self.qdrant.add_batch(results)
        if self.cache and results:
            self.cache.set_batch(results)
        
        elapsed = time.time() - start_time
        logger.info(f"Parallel indexing completed: {len(results)} posts in {elapsed:.1f}s ({errors} errors)")
        if self.verbose:
            print(f"Indexed {len(results)} posts in {elapsed:.1f}s")
        
        return len(results)
    
    @profile("check_duplicate")
    def check_duplicate(
        self,
        content: str,
        title: Optional[str] = None,
        exclude_post_id: Optional[int] = None,
        top_k: int = 5
    ) -> DuplicateCheckResponse:
        """
        Check if content is a duplicate of existing posts.
        
        Uses numpy-optimized batch cosine similarity for fast comparison.
        """
        start_time = time.perf_counter()
        
        if not self._indexed:
            logger.info("Auto-indexing posts for duplicate check...")
            self.index_posts()
        
        query = f"{title}\n\n{content}" if title else content
        
        # Get query embedding
        embed_start = time.perf_counter()
        query_embedding = self._get_embedding(query)
        embed_time = time.perf_counter() - embed_start
        logger.debug(f"[TIMING] Query embedding: {embed_time:.3f}s")
        
        # Prepare data for batch similarity computation
        post_ids = []
        post_titles = []
        post_urls = []
        embeddings = []
        
        for post_id, (post_title, url, embedding) in self._embeddings.items():
            if exclude_post_id and post_id == exclude_post_id:
                continue
            post_ids.append(post_id)
            post_titles.append(post_title)
            post_urls.append(url)
            embeddings.append(embedding)
        
        # Compute all similarities at once using numpy (FAST!)
        sim_start = time.perf_counter()
        scores = cosine_similarity_batch(query_embedding, embeddings)
        sim_time = time.perf_counter() - sim_start
        logger.debug(f"[TIMING] Batch similarity ({len(embeddings)} posts): {sim_time:.4f}s")
        
        # Combine results
        similarities = list(zip(post_ids, post_titles, post_urls, scores))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[3], reverse=True)
        
        # Build response
        matches = []
        has_duplicates = False
        
        for post_id, post_title, url, score in similarities[:top_k]:
            if score < self.threshold:
                continue
            
            is_duplicate = score >= self.duplicate_threshold
            if is_duplicate:
                status = "duplicate"
                has_duplicates = True
            else:
                status = "similar"
            
            matches.append(DuplicateResult(
                is_duplicate=is_duplicate,
                similarity_score=score,
                post_id=post_id,
                title=post_title,
                url=url,
                status=status
            ))
        
        total_time = time.perf_counter() - start_time
        logger.debug(f"[TIMING] Total check_duplicate: {total_time:.3f}s")
        
        return DuplicateCheckResponse(
            query=query[:100] + "..." if len(query) > 100 else query,
            threshold=self.threshold,
            matches=matches,
            total_posts_checked=len(self._embeddings),
            has_duplicates=has_duplicates
        )
    
    def check_duplicates_batch(
        self,
        items: List[str],
        exclude_post_id: Optional[int] = None,
        top_k: int = 5,
        any_match: bool = True
    ) -> DuplicateCheckResponse:
        """
        Check multiple items (sentences, paragraphs, titles) for duplicates.
        
        This is more robust than single-string checking because it checks
        each item independently and aggregates results.
        
        Args:
            items: List of strings to check (sentences, paragraphs, titles)
            exclude_post_id: Post ID to exclude from results
            top_k: Number of top matches to return per item
            any_match: If True, return has_duplicates=True if ANY item matches.
                      If False, require ALL items to match.
        
        Returns:
            DuplicateCheckResponse with aggregated results
        
        Example:
            # Check multiple sentences
            result = detector.check_duplicates_batch([
                "OpenAI launches new model",
                "GPT-5 announced at conference",
                "AI breakthrough in 2026"
            ])
        """
        if not self._indexed:
            self.index_posts()
        
        if not items:
            return DuplicateCheckResponse(
                query="(empty batch)",
                threshold=self.threshold,
                matches=[],
                total_posts_checked=len(self._embeddings),
                has_duplicates=False
            )
        
        # Track all matches across items
        all_matches: Dict[int, DuplicateResult] = {}
        items_with_duplicates = 0
        
        for item in items:
            if not item or not item.strip():
                continue
            
            query_embedding = self._get_embedding(item.strip())
            
            for post_id, (post_title, url, embedding) in self._embeddings.items():
                if exclude_post_id and post_id == exclude_post_id:
                    continue
                
                score = cosine_similarity(query_embedding, embedding)
                
                if score < self.threshold:
                    continue
                
                is_duplicate = score >= self.duplicate_threshold
                
                # Update if this is a higher score for this post
                if post_id not in all_matches or score > all_matches[post_id].similarity_score:
                    status = "duplicate" if is_duplicate else "similar"
                    all_matches[post_id] = DuplicateResult(
                        is_duplicate=is_duplicate,
                        similarity_score=score,
                        post_id=post_id,
                        title=post_title,
                        url=url,
                        status=status
                    )
            
            # Check if this item found duplicates
            item_result = self.check_duplicate(content=item, exclude_post_id=exclude_post_id, top_k=1)
            if item_result.has_duplicates:
                items_with_duplicates += 1
        
        # Sort by similarity score
        sorted_matches = sorted(all_matches.values(), key=lambda x: x.similarity_score, reverse=True)
        top_matches = sorted_matches[:top_k]
        
        # Determine if has duplicates based on any_match flag
        if any_match:
            has_duplicates = any(m.is_duplicate for m in top_matches)
        else:
            has_duplicates = items_with_duplicates == len([i for i in items if i and i.strip()])
        
        query_summary = f"Batch check: {len(items)} items"
        
        return DuplicateCheckResponse(
            query=query_summary,
            threshold=self.threshold,
            matches=top_matches,
            total_posts_checked=len(self._embeddings),
            has_duplicates=has_duplicates
        )
    
    def find_related_posts(
        self,
        post: Dict,
        count: int = 5,
        similarity_threshold: Optional[float] = None,
        exclude_same_category: bool = False
    ) -> Dict[str, Any]:
        """Find posts related to the given post."""
        threshold = similarity_threshold or self.threshold
        
        if not self._indexed:
            self.index_posts()
        
        query = self._get_post_text(post)
        post_id = post.get("ID")
        query_embedding = self._get_embedding(query)
        
        # Compute similarities
        similarities = []
        for pid, (title, url, embedding) in self._embeddings.items():
            if pid == post_id:
                continue
            
            score = cosine_similarity(query_embedding, embedding)
            if score >= threshold:
                similarities.append((pid, title, url, score))
        
        similarities.sort(key=lambda x: x[3], reverse=True)
        
        related = []
        for pid, title, url, score in similarities[:count]:
            related.append({
                "id": pid,
                "title": title,
                "url": url,
                "similarity_score": score,
                "is_duplicate": score >= self.duplicate_threshold
            })
        
        return {
            "posts": related,
            "count": len(related),
            "query_post_id": post_id,
            "threshold": threshold
        }
    
    def clear_cache(self):
        """Clear the embedding cache."""
        if self.cache:
            self.cache.clear()
        self._embeddings.clear()
        self._indexed = False
        logger.info("Cache cleared")
