"""Embeddings module using HuggingFace SentenceTransformer with deterministic fallback"""
import os
import hashlib
import logging
from typing import List
import numpy as np
from .config import EMBEDDINGS_MODEL, EMBEDDINGS_DIMENSION

logger = logging.getLogger(__name__)

# Try to import HuggingFace SentenceTransformer
_hf_model = None
try:
    from sentence_transformers import SentenceTransformer
    def _load_hf_model():
        global _hf_model
        if _hf_model is None:
            model_name = EMBEDDINGS_MODEL or "sentence-transformers/all-MiniLM-L6-v2"
            _hf_model = SentenceTransformer(model_name)
        return _hf_model
except ImportError:
    SentenceTransformer = None
    logger.warning("sentence-transformers not available, using fallback embeddings")

def hash_based_embedding(text: str, dimension: int = EMBEDDINGS_DIMENSION) -> List[float]:
    """Deterministic fallback embedding using hash"""
    # Create a deterministic vector from text hash
    hash_obj = hashlib.sha256(text.encode()).digest()
    # Convert hash to numbers
    numbers = [int.from_bytes(hash_obj[i:i+2], 'big') for i in range(0, min(len(hash_obj), dimension*2), 2)]
    # Pad or truncate to dimension
    if len(numbers) < dimension:
        numbers.extend([0] * (dimension - len(numbers)))
    else:
        numbers = numbers[:dimension]
    # Normalize to unit vector
    vec = np.array(numbers, dtype=np.float32)
    vec = vec / (np.linalg.norm(vec) + 1e-8)
    return vec.tolist()

def get_embeddings(texts: List[str]) -> List[List[float]]:
    """Get embeddings for a list of texts"""
    if not texts:
        return []
    
    # Try to use HuggingFace embeddings if available
    try:
        if SentenceTransformer is not None:
            model = _load_hf_model()
            vecs = model.encode(texts, normalize_embeddings=True, convert_to_numpy=True)
            embeddings = vecs.tolist()
            # Ensure expected dimension
            dim = EMBEDDINGS_DIMENSION or (len(embeddings[0]) if embeddings else 0)
            fixed = []
            for v in embeddings:
                if len(v) > dim:
                    fixed.append(v[:dim])
                elif len(v) < dim:
                    fixed.append(v + [0.0] * (dim - len(v)))
                else:
                    fixed.append(v)
            logger.info(f"Generated {len(fixed)} embeddings using HuggingFace")
            return fixed
    except Exception as e:
        logger.error(f"Error getting HuggingFace embeddings: {e}")
    
    # Fallback to hash-based embeddings
    logger.info(f"Using fallback hash-based embeddings for {len(texts)} texts")
    return [hash_based_embedding(text) for text in texts]

def get_embedding_dimension() -> int:
    """Get the dimension of embeddings"""
    return EMBEDDINGS_DIMENSION

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors"""
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2) + 1e-8)
