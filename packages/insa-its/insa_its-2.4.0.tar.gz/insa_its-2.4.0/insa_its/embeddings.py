import numpy as np
import hashlib
import os
import sys
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Optional retry support
try:
    from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
    TENACITY_AVAILABLE = True
except ImportError:
    TENACITY_AVAILABLE = False
    logger.debug("tenacity not installed - retry logic disabled. Install with: pip install tenacity")


class EmbeddingCache:
    """Simple LRU cache for embeddings"""
    def __init__(self, max_size: int = 2000):
        self.max_size = max_size
        self.cache = {}
        self.order = []

    def get(self, text: str) -> Optional[np.ndarray]:
        key = hashlib.md5(text.encode()).hexdigest()
        if key in self.cache:
            self.order.remove(key)
            self.order.append(key)
            return self.cache[key]
        return None

    def set(self, text: str, embedding: np.ndarray):
        key = hashlib.md5(text.encode()).hexdigest()
        if key in self.cache:
            self.order.remove(key)
        elif len(self.cache) >= self.max_size:
            old_key = self.order.pop(0)
            del self.cache[old_key]
        self.cache[key] = embedding
        self.order.append(key)

    def clear(self):
        """Clear all cached embeddings."""
        self.cache.clear()
        self.order.clear()

    def stats(self) -> dict:
        """Return cache statistics."""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hit_rate": "N/A"  # Would need tracking for actual rate
        }


# Global cache
cache = EmbeddingCache()


def get_synthetic_embedding(text: str, dim: int = 384) -> np.ndarray:
    """
    Fallback embedding function using deterministic hashing.

    WARNING: This provides very weak semantic similarity and should only
    be used when sentence-transformers is unavailable.
    """
    cached = cache.get(text)
    if cached is not None:
        return cached

    # Deterministic but weak embedding
    words = text.lower().split()
    emb = np.zeros(dim)
    for i in range(dim):
        emb[i] = (np.sin(i * len(text) * 0.01) + np.cos(i * len(words) * 0.02)) / 2

    # Boost certain terms for slightly better domain relevance
    boosts = {
        'quantum': [0.8, 0.3, -0.4],
        'code': [0.7, -0.2, 0.5],
        'machine learning': [-0.3, 0.8, 0.4],
        'api': [0.5, 0.5, 0.1],
        'error': [-0.4, 0.6, 0.3],
    }
    for term, vec in boosts.items():
        if term in text.lower():
            emb[:len(vec)] += np.array(vec) * 2.5

    norm = np.linalg.norm(emb) or 1
    emb = emb / norm
    cache.set(text, emb)
    return emb


LOCAL_MODEL_AVAILABLE = False
local_model = None

# HuggingFace download warnings
HF_WARNINGS = {
    "slow_download": (
        "HuggingFace download is slow. Tips:\n"
        "  1. Set HF_HUB_ENABLE_HF_TRANSFER=1 for faster downloads\n"
        "  2. Use a mirror: HF_ENDPOINT=https://hf-mirror.com\n"
        "  3. Pre-download: huggingface-cli download BAAI/bge-small-en-v1.5"
    ),
    "offline_mode": (
        "Running in offline mode. Model must be pre-cached.\n"
        "  To cache: python -c \"from sentence_transformers import SentenceTransformer; "
        "SentenceTransformer('BAAI/bge-small-en-v1.5')\""
    ),
    "connection_error": (
        "Cannot connect to HuggingFace. Suggestions:\n"
        "  1. Check internet connection\n"
        "  2. Try setting HF_ENDPOINT=https://hf-mirror.com\n"
        "  3. Pre-download the model when online"
    )
}


def _create_retry_decorator():
    """Create a retry decorator if tenacity is available."""
    if not TENACITY_AVAILABLE:
        # Return a no-op decorator
        def no_retry(func):
            return func
        return no_retry

    # Retry on connection-related errors
    return retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError, OSError)),
        before_sleep=lambda retry_state: logger.warning(
            f"Retry attempt {retry_state.attempt_number} for model download..."
        ),
        reraise=True
    )


@_create_retry_decorator()
def _download_model_with_retry():
    """Download the embedding model with retry logic."""
    from sentence_transformers import SentenceTransformer
    import time

    start_time = time.time()
    logger.info("Downloading embedding model BAAI/bge-small-en-v1.5 (~100MB)...")
    logger.info("This is a one-time download. Model will be cached locally.")

    # Check for slow download warning
    def check_download_speed():
        elapsed = time.time() - start_time
        if elapsed > 30:
            logger.warning(HF_WARNINGS["slow_download"])

    model = SentenceTransformer("BAAI/bge-small-en-v1.5")

    elapsed = time.time() - start_time
    logger.info(f"Model downloaded successfully in {elapsed:.1f}s")

    return model


def _try_load_model():
    """
    Try to load sentence-transformers model with proper error handling.

    Load order:
    1. Try local cache first (fast, offline-capable)
    2. Try online download with retries
    3. Fall back to synthetic embeddings
    """
    global LOCAL_MODEL_AVAILABLE, local_model

    # Check if sentence-transformers is installed
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        logger.warning(
            "sentence-transformers not installed. Using synthetic embeddings.\n"
            "For better quality, install: pip install sentence-transformers"
        )
        LOCAL_MODEL_AVAILABLE = False
        return

    # Step 1: Try loading from local cache (offline mode)
    try:
        local_model = SentenceTransformer("BAAI/bge-small-en-v1.5", local_files_only=True)
        LOCAL_MODEL_AVAILABLE = True
        logger.info("Loaded embedding model from local cache")
        return
    except Exception as cache_error:
        logger.debug(f"Model not in cache: {cache_error}")

    # Check if we're in offline mode
    if os.environ.get("TRANSFORMERS_OFFLINE") == "1" or os.environ.get("HF_HUB_OFFLINE") == "1":
        logger.warning(HF_WARNINGS["offline_mode"])
        logger.warning("Using synthetic embeddings (lower quality)")
        LOCAL_MODEL_AVAILABLE = False
        return

    # Step 2: Try online download with retries
    try:
        local_model = _download_model_with_retry()
        LOCAL_MODEL_AVAILABLE = True
        return
    except ConnectionError as e:
        logger.error(f"Connection error downloading model: {e}", exc_info=True)
        logger.warning(HF_WARNINGS["connection_error"])
    except TimeoutError as e:
        logger.error(f"Timeout downloading model: {e}", exc_info=True)
        logger.warning(HF_WARNINGS["slow_download"])
    except Exception as e:
        logger.error(f"Failed to load embedding model: {e}", exc_info=True)

    # Step 3: Fall back to synthetic
    logger.warning(
        "Using synthetic embeddings. Quality will be lower.\n"
        "To fix: ensure internet access and run:\n"
        "  pip install sentence-transformers\n"
        "  python -c \"from sentence_transformers import SentenceTransformer; "
        "SentenceTransformer('BAAI/bge-small-en-v1.5')\""
    )
    LOCAL_MODEL_AVAILABLE = False


# Try to load on import
_try_load_model()


def get_local_embedding(text: str) -> np.ndarray:
    """
    Get embedding using local model or synthetic fallback.

    Priority:
    1. Check cache
    2. Use sentence-transformers if available
    3. Fall back to synthetic embeddings

    Args:
        text: The text to embed

    Returns:
        numpy array of shape (384,) - normalized embedding vector
    """
    cached = cache.get(text)
    if cached is not None:
        return cached

    if LOCAL_MODEL_AVAILABLE and local_model is not None:
        try:
            # Use high-quality sentence-transformers
            emb = local_model.encode(
                text,
                normalize_embeddings=True,
                convert_to_numpy=True,
                show_progress_bar=False
            )
        except Exception as e:
            logger.error(f"Error encoding text: {e}", exc_info=True)
            emb = get_synthetic_embedding(text)
    else:
        # Fallback to synthetic (works offline, lower quality)
        emb = get_synthetic_embedding(text)

    cache.set(text, emb)
    return emb


def get_embedding_info() -> dict:
    """
    Get information about the current embedding configuration.

    Returns:
        Dict with embedding backend info
    """
    return {
        "backend": "sentence-transformers" if LOCAL_MODEL_AVAILABLE else "synthetic",
        "model": "BAAI/bge-small-en-v1.5" if LOCAL_MODEL_AVAILABLE else None,
        "dimension": 384,
        "quality": "high" if LOCAL_MODEL_AVAILABLE else "low",
        "cache_stats": cache.stats(),
        "tenacity_available": TENACITY_AVAILABLE
    }


def reload_model() -> bool:
    """
    Attempt to reload the embedding model.

    Useful if network conditions have changed since initial load.

    Returns:
        True if model loaded successfully, False otherwise
    """
    global LOCAL_MODEL_AVAILABLE, local_model

    # Reset state
    LOCAL_MODEL_AVAILABLE = False
    local_model = None

    # Try loading again
    _try_load_model()

    return LOCAL_MODEL_AVAILABLE
