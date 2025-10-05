"""Vector store module using FAISS"""
import os
import pickle
import logging
from pathlib import Path
from typing import List, Tuple, Dict, Optional
import numpy as np

try:
    import faiss
except ImportError:
    faiss = None
    logging.warning("FAISS not available, using numpy-based fallback")

from .config import FAISS_INDEX_PATH, EMBEDDINGS_DIMENSION
from .openrouter_embeddings import embeddings_client

logger = logging.getLogger(__name__)

class VectorStore:
    """FAISS-based vector store with fallback"""
    
    def __init__(self):
        self.dimension = EMBEDDINGS_DIMENSION
        self.index = None
        self.documents = []  # Store document metadata
        self.index_path = FAISS_INDEX_PATH
        self.metadata_path = f"{FAISS_INDEX_PATH}.metadata"
        self.load_index()
    
    def load_index(self):
        """Load existing index from disk"""
        try:
            if faiss and os.path.exists(f"{self.index_path}.index"):
                self.index = faiss.read_index(f"{self.index_path}.index")
                logger.info(f"Loaded FAISS index with {self.index.ntotal} vectors")
            elif faiss:
                # Create new FAISS index
                self.index = faiss.IndexFlatL2(self.dimension)
                logger.info(f"Created new FAISS index with dimension {self.dimension}")
            else:
                # Fallback: use numpy arrays
                self.index = {"vectors": [], "use_numpy": True}
                logger.info("Using numpy-based vector store fallback")
            
            # Load metadata
            if os.path.exists(self.metadata_path):
                with open(self.metadata_path, 'rb') as f:
                    self.documents = pickle.load(f)
                logger.info(f"Loaded {len(self.documents)} document metadata")
        except Exception as e:
            logger.error(f"Error loading index: {e}")
            self._create_new_index()
    
    def _create_new_index(self):
        """Create a new index"""
        if faiss:
            self.index = faiss.IndexFlatL2(self.dimension)
        else:
            self.index = {"vectors": [], "use_numpy": True}
        self.documents = []
    
    def save_index(self):
        """Save index to disk"""
        try:
            Path(self.index_path).parent.mkdir(parents=True, exist_ok=True)
            
            if faiss and not isinstance(self.index, dict):
                faiss.write_index(self.index, f"{self.index_path}.index")
                logger.info(f"Saved FAISS index with {self.index.ntotal} vectors")
            elif isinstance(self.index, dict):
                # Save numpy fallback
                with open(f"{self.index_path}.npy", 'wb') as f:
                    pickle.dump(self.index, f)
            
            # Save metadata
            with open(self.metadata_path, 'wb') as f:
                pickle.dump(self.documents, f)
            logger.info(f"Saved {len(self.documents)} document metadata")
        except Exception as e:
            logger.error(f"Error saving index: {e}")
    
    def add_documents(self, texts: List[str], metadata: List[Dict]) -> List[int]:
        """Add documents to the index"""
        if not texts:
            return []
        
        # Get embeddings
        embeddings = get_embeddings(texts)
        
        # Add to index
        ids = []
        start_id = len(self.documents)
        
        if faiss and not isinstance(self.index, dict):
            # Use FAISS
            vectors = np.array(embeddings, dtype=np.float32)
            self.index.add(vectors)
            ids = list(range(start_id, start_id + len(texts)))
        else:
            # Use numpy fallback
            if "vectors" not in self.index:
                self.index["vectors"] = []
            self.index["vectors"].extend(embeddings)
            ids = list(range(start_id, start_id + len(texts)))
        
        # Store metadata
        for i, (text, meta) in enumerate(zip(texts, metadata)):
            doc_meta = meta.copy()
            doc_meta["text"] = text
            doc_meta["embedding_id"] = start_id + i
            self.documents.append(doc_meta)
        
        # Save to disk
        self.save_index()
        
        logger.info(f"Added {len(texts)} documents to index")
        return ids
    
    def add_document(self, doc_id: str, content: str, embedding: List[float], metadata: Dict):
        """Add a single document to the index"""
        try:
            # Create document entry
            doc_entry = {
                'id': doc_id,
                'content': content,
                'metadata': metadata,
                'timestamp': metadata.get('timestamp', '')
            }
            
            # Add to documents list
            self.documents.append(doc_entry)
            
            if faiss and not isinstance(self.index, dict):
                # Add to FAISS index
                embedding_vec = np.array([embedding], dtype=np.float32)
                self.index.add(embedding_vec)
            else:
                # Add to numpy fallback
                if "vectors" not in self.index:
                    self.index["vectors"] = []
                self.index["vectors"].append(embedding)
            
            # Save index
            self.save_index()
            logger.info(f"Added document {doc_id} to vector store")
            
        except Exception as e:
            logger.error(f"Error adding document {doc_id}: {e}")
    
    async def search(self, query: str, k: int = 5) -> List[Tuple[Dict, float]]:
        """Search for similar documents using embeddings"""
        if not self.documents:
            return []
        
        try:
            # Get query embedding
            query_embedding = await embeddings_client.embed_text(query)
            if not query_embedding:
                # Fallback to keyword search
                return self._keyword_search(query, k)
            
            if faiss and not isinstance(self.index, dict) and self.index.ntotal > 0:
                # Use FAISS search
                query_vec = np.array([query_embedding], dtype=np.float32)
                distances, indices = self.index.search(query_vec, min(k, len(self.documents)))
                
                results = []
                for idx, dist in zip(indices[0], distances[0]):
                    if idx < len(self.documents) and idx >= 0:
                        # Convert L2 distance to similarity score (0-1)
                        similarity = 1.0 / (1.0 + dist)
                        results.append((self.documents[idx], similarity))
                return results
            else:
                # Use numpy fallback
                if not self.index.get("vectors"):
                    return self._keyword_search(query, k)
                
                similarities = []
                for i, vec in enumerate(self.index["vectors"]):
                    sim = self._cosine_similarity(query_embedding, vec)
                    similarities.append((i, sim))
                
                # Sort by similarity
                similarities.sort(key=lambda x: x[1], reverse=True)
                
                results = []
                for idx, sim in similarities[:k]:
                    if idx < len(self.documents):
                        results.append((self.documents[idx], sim))
                return results
                
        except Exception as e:
            logger.error(f"Error in vector search: {e}")
            return self._keyword_search(query, k)
    
    def _keyword_search(self, query: str, k: int = 5) -> List[Tuple[Dict, float]]:
        """Fallback keyword-based search"""
        results = []
        query_lower = query.lower()
        
        for doc in self.documents:
            content = doc.get('content', '').lower()
            # Simple keyword matching
            if any(word in content for word in query_lower.split()):
                similarity = 0.8  # Mock similarity score
                results.append((doc, similarity))
        
        return results[:k]
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            vec1 = np.array(vec1)
            vec2 = np.array(vec2)
            
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
        except:
            return 0.0
    
    def clear(self):
        """Clear the index"""
        self._create_new_index()
        self.save_index()
    
    def get_stats(self) -> Dict:
        """Get index statistics"""
        if faiss and not isinstance(self.index, dict):
            return {
                "total_vectors": self.index.ntotal,
                "dimension": self.dimension,
                "documents": len(self.documents),
                "backend": "faiss"
            }
        else:
            return {
                "total_vectors": len(self.index.get("vectors", [])),
                "dimension": self.dimension,
                "documents": len(self.documents),
                "backend": "numpy"
            }
    
    def get_all_documents(self) -> List[Dict]:
        """Get all documents in the vector store"""
        return self.documents.copy()

# Global vector store instance
vector_store = VectorStore()
