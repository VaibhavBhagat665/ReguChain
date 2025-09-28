"""Tests for retrieval and vector store"""
import pytest
from app.vector_store import VectorStore
from app.embeddings import get_embeddings, hash_based_embedding

def test_hash_based_embedding():
    """Test deterministic hash-based embeddings"""
    text = "Test document"
    embedding1 = hash_based_embedding(text)
    embedding2 = hash_based_embedding(text)
    
    assert embedding1 == embedding2  # Should be deterministic
    assert len(embedding1) == 768  # Default dimension
    assert all(isinstance(x, float) for x in embedding1)

def test_get_embeddings_fallback():
    """Test embedding generation with fallback"""
    texts = ["Document 1", "Document 2"]
    embeddings = get_embeddings(texts)
    
    assert len(embeddings) == 2
    assert all(len(emb) == 768 for emb in embeddings)

def test_vector_store_add_and_search():
    """Test adding documents and searching"""
    store = VectorStore()
    store.clear()  # Start fresh
    
    # Add documents
    texts = [
        "OFAC sanction on wallet 0xABC",
        "SEC investigation into crypto exchange",
        "Normal transaction recorded"
    ]
    metadata = [
        {"source": "OFAC", "id": 1},
        {"source": "SEC", "id": 2},
        {"source": "Blockchain", "id": 3}
    ]
    
    ids = store.add_documents(texts, metadata)
    assert len(ids) == 3
    
    # Search
    results = store.search("OFAC sanction", k=2)
    assert len(results) <= 2
    assert results[0][0]["source"] == "OFAC"  # Most relevant should be first

def test_vector_store_persistence():
    """Test vector store save and load"""
    store = VectorStore()
    store.clear()
    
    # Add document
    texts = ["Test document for persistence"]
    metadata = [{"source": "Test"}]
    store.add_documents(texts, metadata)
    
    # Save
    store.save_index()
    
    # Create new store and check if loaded
    new_store = VectorStore()
    stats = new_store.get_stats()
    assert stats["documents"] >= 1
