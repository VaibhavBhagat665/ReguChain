"""
Pathway integration for real-time data streaming and processing
"""
import logging
import asyncio
from typing import List, Dict, Optional, Any
from datetime import datetime
import json

from .config import (
    PATHWAY_KEY, PATHWAY_MODE, PATHWAY_STREAMING_MODE,
    PATHWAY_PERSISTENCE_BACKEND, PATHWAY_PERSISTENCE_PATH,
    PATHWAY_MONITORING_LEVEL
)

logger = logging.getLogger(__name__)

# Try to import Pathway
pathway_available = False
try:
    import pathway as pw
    from pathway.stdlib.ml.index import KNNIndex
    pathway_available = True
    logger.info("Pathway library imported successfully")
except ImportError:
    logger.warning("Pathway library not available - real-time streaming disabled")

class PathwayService:
    """Service for real-time data streaming with Pathway"""
    
    def __init__(self):
        self.pathway_key = PATHWAY_KEY
        self.mode = PATHWAY_MODE
        self.streaming_mode = PATHWAY_STREAMING_MODE
        self.persistence_backend = PATHWAY_PERSISTENCE_BACKEND
        self.persistence_path = PATHWAY_PERSISTENCE_PATH
        self.monitoring_level = PATHWAY_MONITORING_LEVEL
        
        self.data_streams = {}
        self.indexes = {}
        self.is_running = False
        
        if pathway_available and self.pathway_key:
            self._initialize_pathway()
    
    def _initialize_pathway(self):
        """Initialize Pathway configuration"""
        try:
            # Set up Pathway configuration
            pw.set_license_key(self.pathway_key)
            
            # Configure monitoring
            if self.monitoring_level == "debug":
                pw.set_monitoring_level(pw.MonitoringLevel.ALL)
            elif self.monitoring_level == "info":
                pw.set_monitoring_level(pw.MonitoringLevel.REGULAR)
            else:
                pw.set_monitoring_level(pw.MonitoringLevel.NONE)
            
            logger.info("Pathway initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing Pathway: {e}")
    
    def create_news_stream(self) -> Optional[Any]:
        """Create a real-time news data stream"""
        if not pathway_available:
            return None
        
        try:
            # Define schema for news data
            class NewsSchema(pw.Schema):
                title: str
                description: str
                url: str
                source: str
                published_at: str
                keywords: List[str]
                sentiment: str
            
            # Create input connector (could be Kafka, HTTP, etc.)
            # For now, we'll use a simple CSV connector for demonstration
            news_table = pw.io.csv.read(
                f"{self.persistence_path}/news_stream.csv",
                schema=NewsSchema,
                mode="streaming" if self.streaming_mode == "realtime" else "static"
            )
            
            # Process the stream - extract keywords, analyze sentiment
            processed_news = news_table.select(
                title=news_table.title,
                description=news_table.description,
                url=news_table.url,
                source=news_table.source,
                published_at=news_table.published_at,
                keywords=news_table.keywords,
                sentiment=news_table.sentiment,
                relevance_score=pw.apply(self._calculate_relevance, news_table.title, news_table.description)
            )
            
            # Filter for high-relevance news
            relevant_news = processed_news.filter(processed_news.relevance_score > 0.5)
            
            # Store in data streams
            self.data_streams["news"] = relevant_news
            
            logger.info("News stream created successfully")
            return relevant_news
            
        except Exception as e:
            logger.error(f"Error creating news stream: {e}")
            return None
    
    def create_transaction_stream(self) -> Optional[Any]:
        """Create a real-time blockchain transaction stream"""
        if not pathway_available:
            return None
        
        try:
            # Define schema for transaction data
            class TransactionSchema(pw.Schema):
                hash: str
                from_address: str
                to_address: str
                value: float
                timestamp: str
                block_number: int
                gas_used: float
            
            # Create input connector
            tx_table = pw.io.csv.read(
                f"{self.persistence_path}/transaction_stream.csv",
                schema=TransactionSchema,
                mode="streaming" if self.streaming_mode == "realtime" else "static"
            )
            
            # Process transactions - calculate risk scores
            processed_txs = tx_table.select(
                hash=tx_table.hash,
                from_address=tx_table.from_address,
                to_address=tx_table.to_address,
                value=tx_table.value,
                timestamp=tx_table.timestamp,
                block_number=tx_table.block_number,
                risk_score=pw.apply(self._calculate_transaction_risk, 
                                   tx_table.from_address, 
                                   tx_table.to_address, 
                                   tx_table.value)
            )
            
            # Filter high-risk transactions
            high_risk_txs = processed_txs.filter(processed_txs.risk_score > 70)
            
            # Store in data streams
            self.data_streams["transactions"] = processed_txs
            self.data_streams["high_risk_transactions"] = high_risk_txs
            
            logger.info("Transaction stream created successfully")
            return processed_txs
            
        except Exception as e:
            logger.error(f"Error creating transaction stream: {e}")
            return None
    
    def create_vector_index(self, documents: List[Dict]) -> Optional[Any]:
        """Create a vector index for similarity search"""
        if not pathway_available:
            return None
        
        try:
            # Convert documents to Pathway table
            class DocumentSchema(pw.Schema):
                id: str
                content: str
                embedding: List[float]
                metadata: Dict
            
            # Create table from documents
            doc_data = []
            for doc in documents:
                doc_data.append({
                    "id": doc.get("id", ""),
                    "content": doc.get("content", ""),
                    "embedding": doc.get("embedding", []),
                    "metadata": doc.get("metadata", {})
                })
            
            doc_table = pw.debug.table_from_pandas(
                pd.DataFrame(doc_data),
                schema=DocumentSchema
            )
            
            # Create KNN index
            index = KNNIndex(
                doc_table.embedding,
                doc_table,
                n_dimensions=768,  # Embedding dimension
                n_neighbors=10,
                metric="cosine"
            )
            
            self.indexes["documents"] = index
            
            logger.info("Vector index created successfully")
            return index
            
        except Exception as e:
            logger.error(f"Error creating vector index: {e}")
            return None
    
    def _calculate_relevance(self, title: str, description: str) -> float:
        """Calculate relevance score for news articles"""
        keywords = ["SEC", "CFTC", "regulatory", "compliance", "cryptocurrency", 
                   "blockchain", "DeFi", "sanctions", "AML", "KYC"]
        
        text = f"{title} {description}".lower()
        score = 0.0
        
        for keyword in keywords:
            if keyword.lower() in text:
                score += 0.2
        
        return min(score, 1.0)
    
    def _calculate_transaction_risk(self, from_addr: str, to_addr: str, value: float) -> float:
        """Calculate risk score for transactions"""
        # Simple risk calculation based on value and addresses
        risk_score = 0.0
        
        # High value transactions
        if value > 100000:
            risk_score += 30
        elif value > 10000:
            risk_score += 20
        elif value > 1000:
            risk_score += 10
        
        # Check for known risky patterns (simplified)
        if from_addr == to_addr:
            risk_score += 20  # Self-transfer
        
        # Add random factor for demonstration
        import random
        risk_score += random.uniform(0, 30)
        
        return min(risk_score, 100)
    
    async def start_streaming(self):
        """Start real-time data streaming"""
        if not pathway_available:
            logger.warning("Pathway not available - streaming disabled")
            return
        
        try:
            self.is_running = True
            
            # Create streams
            self.create_news_stream()
            self.create_transaction_stream()
            
            # Run Pathway computation
            if self.data_streams:
                pw.run(
                    monitoring_level=self.monitoring_level,
                    persistence_config=pw.persistence.Config(
                        backend=self.persistence_backend,
                        path=self.persistence_path
                    ) if self.persistence_backend else None
                )
            
            logger.info("Pathway streaming started")
            
        except Exception as e:
            logger.error(f"Error starting Pathway streaming: {e}")
            self.is_running = False
    
    async def stop_streaming(self):
        """Stop real-time data streaming"""
        self.is_running = False
        logger.info("Pathway streaming stopped")
    
    def query_stream(self, stream_name: str, query: Dict) -> List[Dict]:
        """Query a data stream"""
        if stream_name not in self.data_streams:
            return []
        
        # For now, return empty list as Pathway queries are complex
        # In production, this would execute Pathway queries
        return []
    
    def search_similar_documents(self, query_embedding: List[float], k: int = 5) -> List[Dict]:
        """Search for similar documents using vector index"""
        if "documents" not in self.indexes:
            return []
        
        # For now, return empty list as Pathway search is complex
        # In production, this would use the KNN index
        return []

# Create singleton instance
pathway_service = PathwayService()

# Mock data generator for testing without Pathway
class MockStreamGenerator:
    """Generate mock streaming data for testing"""
    
    @staticmethod
    async def generate_mock_news():
        """Generate mock news data"""
        news_items = [
            {
                "title": "SEC Announces New Cryptocurrency Regulations",
                "description": "The Securities and Exchange Commission released new guidelines for digital asset compliance.",
                "url": "https://example.com/sec-crypto-regs",
                "source": "SEC",
                "published_at": datetime.utcnow().isoformat(),
                "keywords": ["SEC", "cryptocurrency", "regulations"],
                "sentiment": "neutral"
            },
            {
                "title": "CFTC Issues Warning on DeFi Platforms",
                "description": "Commodity Futures Trading Commission warns investors about risks in decentralized finance.",
                "url": "https://example.com/cftc-defi-warning",
                "source": "CFTC",
                "published_at": datetime.utcnow().isoformat(),
                "keywords": ["CFTC", "DeFi", "warning"],
                "sentiment": "negative"
            }
        ]
        return news_items
    
    @staticmethod
    async def generate_mock_transactions():
        """Generate mock transaction data"""
        import random
        
        transactions = []
        for i in range(5):
            transactions.append({
                "hash": f"0x{''.join(random.choices('0123456789abcdef', k=64))}",
                "from_address": f"0x{''.join(random.choices('0123456789abcdef', k=40))}",
                "to_address": f"0x{''.join(random.choices('0123456789abcdef', k=40))}",
                "value": random.uniform(0.1, 10000),
                "timestamp": datetime.utcnow().isoformat(),
                "block_number": random.randint(15000000, 16000000),
                "gas_used": random.uniform(21000, 100000)
            })
        
        return transactions

mock_generator = MockStreamGenerator()
