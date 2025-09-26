"""Embeddings module using Google Gemini"""
import os
import hashlib
import logging
from typing import List
import numpy as np
from .config import GOOGLE_API_KEY, EMBEDDINGS_MODEL, EMBEDDINGS_DIMENSION

logger = logging.getLogger(__name__)

# Try to import Google GenAI SDK with multiple patterns
genai = None
try:
    # Pattern 1: google.generativeai
    import google.generativeai as genai
    genai.configure(api_key=GOOGLE_API_KEY)
    logger.info("Successfully imported google.generativeai")
except ImportError:
    try:
        # Pattern 2: google.ai.generativelanguage
        from google import genai as google_genai
        genai = google_genai
        if hasattr(genai, 'Client'):
            genai = genai.Client(api_key=GOOGLE_API_KEY)
        logger.info("Successfully imported google genai Client")
    except ImportError:
        logger.warning("Google GenAI SDK not available, using fallback embeddings")

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
    
    # Try to use Gemini API if available
    if genai and GOOGLE_API_KEY:
        try:
            embeddings = []
            for text in texts:
                # Try different API patterns
                try:
                    # Pattern 1: embed_content method
                    result = genai.embed_content(
                        model=EMBEDDINGS_MODEL,
                        content=text,
                        task_type="retrieval_document"
                    )
                    if hasattr(result, 'embedding'):
                        embeddings.append(result.embedding)
                    else:
                        embeddings.append(result['embedding'])
                except Exception as e1:
                    try:
                        # Pattern 2: get_embeddings method
                        model = genai.GenerativeModel(EMBEDDINGS_MODEL)
                        result = model.embed_content(text)
                        embeddings.append(result.embedding)
                    except Exception as e2:
                        # Fallback for this text
                        logger.warning(f"Failed to get embedding for text, using fallback: {str(e2)}")
                        embeddings.append(hash_based_embedding(text))
            
            if embeddings:
                logger.info(f"Generated {len(embeddings)} embeddings using Gemini")
                return embeddings
        except Exception as e:
            logger.error(f"Error getting Gemini embeddings: {e}")
    
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
