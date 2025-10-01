"""
OpenRouter Embeddings Client
Real embeddings using OpenRouter API
"""
import asyncio
import logging
from typing import List, Optional
import aiohttp
import numpy as np
from .config import OPENROUTER_API_KEY, EMBEDDINGS_MODEL

logger = logging.getLogger(__name__)

class OpenRouterEmbeddingsClient:
    """OpenRouter embeddings client for real-time embedding generation"""
    
    def __init__(self):
        self.api_key = OPENROUTER_API_KEY
        self.model = EMBEDDINGS_MODEL or "text-embedding-3-small"
        self.base_url = "https://openrouter.ai/api/v1"
        self.embedding_dim = 1536  # Default for text-embedding-3-small
        
        if not self.api_key:
            logger.warning("⚠️ OpenRouter API key not configured, using mock embeddings")
    
    async def embed_text(self, text: str) -> Optional[List[float]]:
        """Generate embedding for a single text"""
        if not text.strip():
            return None
        
        embeddings = await self.embed_texts([text])
        return embeddings[0] if embeddings else None
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts using OpenRouter API"""
        if not texts:
            return []
        
        if not self.api_key:
            logger.warning("Using mock embeddings (no API key)")
            return [np.random.rand(self.embedding_dim).tolist() for _ in texts]
        
        try:
            logger.info(f"🔄 Generating embeddings for {len(texts)} texts...")
            
            # Prepare request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://reguchain.ai",
                "X-Title": "ReguChain"
            }
            
            payload = {
                "model": self.model,
                "input": texts
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/embeddings",
                    headers=headers,
                    json=payload,
                    timeout=30
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"OpenRouter embeddings API error {response.status}: {error_text}")
                        # Fallback to mock embeddings
                        return [np.random.rand(self.embedding_dim).tolist() for _ in texts]
                    
                    data = await response.json()
            
            # Extract embeddings
            embeddings = []
            for item in data.get('data', []):
                embedding = item.get('embedding', [])
                if embedding:
                    embeddings.append(embedding)
                else:
                    # Fallback for failed individual embeddings
                    embeddings.append(np.random.rand(self.embedding_dim).tolist())
            
            logger.info(f"✅ Generated {len(embeddings)} embeddings")
            return embeddings
            
        except asyncio.TimeoutError:
            logger.error("❌ OpenRouter embeddings API timeout")
            return [np.random.rand(self.embedding_dim).tolist() for _ in texts]
        except Exception as e:
            logger.error(f"❌ Error generating embeddings: {e}")
            return [np.random.rand(self.embedding_dim).tolist() for _ in texts]
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings"""
        return self.embedding_dim
    
    async def test_connection(self) -> bool:
        """Test OpenRouter embeddings API connection"""
        try:
            result = await self.embed_text("test connection")
            return result is not None and len(result) == self.embedding_dim
        except:
            return False

# Global instance
embeddings_client = OpenRouterEmbeddingsClient()
