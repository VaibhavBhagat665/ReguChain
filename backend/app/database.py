"""Enhanced database operations for ReguChain RAG system"""
import sqlite3
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class Database:
    """Enhanced SQLite database for RAG system"""
    
    def __init__(self, db_path: str = "./reguchain.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Enhanced documents table for RAG
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS documents (
                        id TEXT PRIMARY KEY,
                        content TEXT NOT NULL,
                        metadata TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        source TEXT NOT NULL,
                        category TEXT,
                        risk_level TEXT,
                        embedding_stored BOOLEAN DEFAULT FALSE
                    )
                """)
                
                # Transactions table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS transactions (
                        id TEXT PRIMARY KEY,
                        tx_hash TEXT NOT NULL,
                        from_address TEXT NOT NULL,
                        to_address TEXT NOT NULL,
                        amount REAL NOT NULL,
                        timestamp TEXT NOT NULL,
                        risk_score REAL DEFAULT 0,
                        metadata TEXT,
                        chain TEXT DEFAULT 'ethereum'
                    )
                """)
                
                # Ingestion stats table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS ingestion_stats (
                        source TEXT PRIMARY KEY,
                        last_run TEXT,
                        documents_count INTEGER DEFAULT 0,
                        last_error TEXT
                    )
                """)
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
    
    async def store_document(self, doc: Dict[str, Any]):
        """Store a document with enhanced metadata"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                metadata = doc.get('metadata', {})
                
                cursor.execute("""
                    INSERT OR REPLACE INTO documents 
                    (id, content, metadata, timestamp, source, category, risk_level, embedding_stored)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    doc['id'],
                    doc['content'],
                    json.dumps(metadata),
                    metadata.get('timestamp', datetime.now().isoformat()),
                    metadata.get('source', 'unknown'),
                    metadata.get('category', 'general'),
                    metadata.get('risk_level', 'low'),
                    False  # Will be updated when embedding is stored
                ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error storing document {doc.get('id', 'unknown')}: {e}")
    
    async def get_documents_by_metadata(self, key: str, value: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get documents by metadata field"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, content, metadata, timestamp, source, category, risk_level
                    FROM documents
                    WHERE json_extract(metadata, '$.' || ?) = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (key, value, limit))
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        "id": row[0],
                        "content": row[1],
                        "metadata": json.loads(row[2]),
                        "timestamp": row[3],
                        "source": row[4],
                        "category": row[5],
                        "risk_level": row[6]
                    })
                
                return results
                
        except Exception as e:
            logger.error(f"Error getting documents by metadata: {e}")
            return []
    
    def get_recent_documents(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent documents"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, content, metadata, timestamp, source, category, risk_level
                    FROM documents
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (limit,))
                
                results = []
                for row in cursor.fetchall():
                    metadata = json.loads(row[2])
                    results.append({
                        "id": row[0],
                        "text": row[1][:200] + "..." if len(row[1]) > 200 else row[1],
                        "metadata": metadata,
                        "timestamp": row[3],
                        "source": row[4],
                        "category": row[5],
                        "risk_level": row[6],
                        "link": metadata.get("link", "")
                    })
                
                return results
                
        except Exception as e:
            logger.error(f"Error getting recent documents: {e}")
            return []
    
    def get_documents_by_source(self, source: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get documents by source"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, content, metadata, timestamp, source, category, risk_level
                    FROM documents
                    WHERE source = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (source, limit))
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        "id": row[0],
                        "content": row[1],
                        "metadata": json.loads(row[2]),
                        "timestamp": row[3],
                        "source": row[4],
                        "category": row[5],
                        "risk_level": row[6]
                    })
                
                return results
                
        except Exception as e:
            logger.error(f"Error getting documents by source: {e}")
            return []
    
    def update_ingestion_stats(self, source: str, documents_count: int, error: str = None):
        """Update ingestion statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO ingestion_stats 
                    (source, last_run, documents_count, last_error)
                    VALUES (?, ?, ?, ?)
                """, (
                    source,
                    datetime.now().isoformat(),
                    documents_count,
                    error
                ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error updating ingestion stats: {e}")
    
    def get_ingestion_stats(self) -> Dict[str, Any]:
        """Get ingestion statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT source, last_run, documents_count, last_error
                    FROM ingestion_stats
                """)
                
                stats = {}
                for row in cursor.fetchall():
                    stats[row[0]] = {
                        "last_run": row[1],
                        "documents_count": row[2],
                        "last_error": row[3]
                    }
                
                return stats
                
        except Exception as e:
            logger.error(f"Error getting ingestion stats: {e}")
            return {}
    
    def store_transaction(self, tx_data: Dict[str, Any]):
        """Store transaction data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO transactions 
                    (id, tx_hash, from_address, to_address, amount, timestamp, risk_score, metadata, chain)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    tx_data.get("id", ""),
                    tx_data.get("tx", ""),
                    tx_data.get("from", ""),
                    tx_data.get("to", ""),
                    float(tx_data.get("amount", 0)),
                    tx_data.get("timestamp", datetime.now().isoformat()),
                    float(tx_data.get("risk_score", 0)),
                    json.dumps(tx_data.get("metadata", {})),
                    tx_data.get("chain", "ethereum")
                ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error storing transaction: {e}")
    
    def get_total_documents(self) -> int:
        """Get total number of documents"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM documents")
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Error getting total documents: {e}")
            return 0

# Global database instance
database = Database()
