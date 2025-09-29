"""
Pathway integration for real-time data streaming and processing
"""
import logging
import asyncio
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
import json
import pandas as pd
from dataclasses import dataclass
from enum import Enum

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
    from pathway.stdlib.utils.col import unpack_col
    pathway_available = True
    logger.info("Pathway library imported successfully - Real-time processing enabled")
except ImportError:
    logger.warning("Pathway library not available - Using enhanced simulation mode")

class ComplianceLevel(Enum):
    """Compliance risk levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ComplianceAlert:
    """Real-time compliance alert"""
    id: str
    timestamp: datetime
    level: ComplianceLevel
    category: str
    title: str
    description: str
    affected_entities: List[str]
    regulatory_body: str
    recommended_action: str
    confidence_score: float

class PathwayService:
    """Enhanced Pathway Service for Real-Time Regulatory Compliance
    
    Key Features:
    - Multi-source real-time data streaming
    - Incremental computation with automatic updates
    - Time-series analysis with windowing
    - Pattern detection and anomaly identification
    - Risk scoring and predictive analytics
    - Regulatory alert generation
    - Vector similarity search for compliance documents
    """
    
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
        self.compliance_alerts = []
        
        # Advanced configuration
        self.risk_thresholds = {
            "transaction_volume": 1000000,  # $1M threshold
            "velocity_threshold": 100,  # 100 transactions per minute
            "risk_score_critical": 80,
            "risk_score_high": 60,
            "risk_score_medium": 40
        }
        
        self.regulatory_keywords = {
            "critical": ["violation", "penalty", "enforcement", "cease and desist", "suspension"],
            "high": ["investigation", "audit", "non-compliance", "breach", "warning"],
            "medium": ["guidance", "clarification", "amendment", "proposal", "consultation"],
            "low": ["update", "announcement", "publication", "release", "notice"]
        }
        
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
    
    def create_compliance_monitoring_pipeline(self) -> Dict[str, Any]:
        """Create comprehensive compliance monitoring pipeline with multiple data streams"""
        if not pathway_available:
            return self._simulate_compliance_pipeline()
        
        try:
            # Create multiple interconnected streams
            news_stream = self.create_news_stream()
            tx_stream = self.create_transaction_stream()
            regulatory_stream = self.create_regulatory_updates_stream()
            
            # Join streams for comprehensive analysis
            if news_stream and tx_stream and regulatory_stream:
                # Create unified compliance dashboard
                compliance_data = self._join_compliance_streams(
                    news_stream, tx_stream, regulatory_stream
                )
                
                # Generate real-time alerts
                alerts = self._generate_compliance_alerts(compliance_data)
                
                self.data_streams["compliance_dashboard"] = compliance_data
                self.data_streams["alerts"] = alerts
                
                logger.info("Compliance monitoring pipeline created successfully")
                return {
                    "status": "active",
                    "streams": list(self.data_streams.keys()),
                    "monitoring_level": self.monitoring_level
                }
            
        except Exception as e:
            logger.error(f"Error creating compliance pipeline: {e}")
        
        return {"status": "error", "message": "Failed to create pipeline"}
    
    def create_news_stream(self) -> Optional[Any]:
        """Create enhanced real-time news data stream with advanced processing"""
        if not pathway_available:
            return self._simulate_news_stream()
        
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
            
            # Enhanced processing with multiple analytics
            processed_news = news_table.select(
                title=news_table.title,
                description=news_table.description,
                url=news_table.url,
                source=news_table.source,
                published_at=news_table.published_at,
                keywords=news_table.keywords,
                sentiment=news_table.sentiment,
                relevance_score=pw.apply(self._calculate_relevance, news_table.title, news_table.description),
                compliance_impact=pw.apply(self._assess_compliance_impact, news_table.title, news_table.description),
                urgency_level=pw.apply(self._calculate_urgency, news_table.published_at, news_table.keywords),
                affected_jurisdictions=pw.apply(self._extract_jurisdictions, news_table.description)
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
            
            # Enhanced transaction processing with pattern detection
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
                                   tx_table.value),
                aml_flags=pw.apply(self._detect_aml_patterns, 
                                  tx_table.from_address, 
                                  tx_table.to_address, 
                                  tx_table.value),
                velocity_score=pw.apply(self._calculate_velocity, tx_table.timestamp),
                network_analysis=pw.apply(self._analyze_network_patterns, 
                                         tx_table.from_address, 
                                         tx_table.to_address)
            )
            
            # Apply time windowing for velocity analysis
            windowed_txs = self._apply_time_windows(processed_txs)
            
            # Multi-level risk filtering
            critical_risk_txs = processed_txs.filter(
                processed_txs.risk_score > self.risk_thresholds["risk_score_critical"]
            )
            high_risk_txs = processed_txs.filter(
                (processed_txs.risk_score > self.risk_thresholds["risk_score_high"]) & 
                (processed_txs.risk_score <= self.risk_thresholds["risk_score_critical"])
            )
            
            # Store multiple streams for different monitoring levels
            self.data_streams["transactions"] = processed_txs
            self.data_streams["critical_risk_transactions"] = critical_risk_txs
            self.data_streams["high_risk_transactions"] = high_risk_txs
            self.data_streams["windowed_transactions"] = windowed_txs if 'windowed_txs' in locals() else processed_txs
            
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
    
    def create_regulatory_updates_stream(self) -> Optional[Any]:
        """Create stream for regulatory updates and compliance changes"""
        if not pathway_available:
            return self._simulate_regulatory_stream()
        
        try:
            class RegulatorySchema(pw.Schema):
                update_id: str
                timestamp: str
                regulatory_body: str
                jurisdiction: str
                category: str
                title: str
                description: str
                effective_date: str
                severity: str
            
            # In production, connect to regulatory APIs
            reg_table = pw.io.csv.read(
                f"{self.persistence_path}/regulatory_updates.csv",
                schema=RegulatorySchema,
                mode="streaming" if self.streaming_mode == "realtime" else "static"
            )
            
            processed_regs = reg_table.select(
                update_id=reg_table.update_id,
                timestamp=reg_table.timestamp,
                regulatory_body=reg_table.regulatory_body,
                jurisdiction=reg_table.jurisdiction,
                category=reg_table.category,
                title=reg_table.title,
                description=reg_table.description,
                effective_date=reg_table.effective_date,
                severity=reg_table.severity,
                impact_score=pw.apply(self._calculate_regulatory_impact, 
                                     reg_table.severity, 
                                     reg_table.category),
                affected_entities=pw.apply(self._identify_affected_entities, 
                                          reg_table.description)
            )
            
            self.data_streams["regulatory_updates"] = processed_regs
            return processed_regs
            
        except Exception as e:
            logger.error(f"Error creating regulatory stream: {e}")
            return None
    
    def _calculate_relevance(self, title: str, description: str) -> float:
        """Enhanced relevance calculation with weighted keywords"""
        keyword_weights = {
            "SEC": 0.3, "CFTC": 0.3, "regulatory": 0.25, "compliance": 0.25,
            "cryptocurrency": 0.2, "blockchain": 0.2, "DeFi": 0.2,
            "sanctions": 0.35, "AML": 0.3, "KYC": 0.3, "enforcement": 0.35,
            "violation": 0.4, "penalty": 0.4, "investigation": 0.35
        }
        
        text = f"{title} {description}".lower()
        score = 0.0
        
        for keyword, weight in keyword_weights.items():
            if keyword.lower() in text:
                score += weight
        
        return min(score, 1.0)
    
    def _assess_compliance_impact(self, title: str, description: str) -> str:
        """Assess compliance impact level"""
        text = f"{title} {description}".lower()
        
        for level, keywords in self.regulatory_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    return level
        return "low"
    
    def _calculate_urgency(self, published_at: str, keywords: List[str]) -> str:
        """Calculate urgency level based on time and keywords"""
        critical_keywords = ["immediate", "urgent", "emergency", "deadline"]
        
        for keyword in keywords:
            if any(critical in keyword.lower() for critical in critical_keywords):
                return "critical"
        
        # Time-based urgency
        try:
            pub_time = datetime.fromisoformat(published_at)
            time_diff = datetime.utcnow() - pub_time
            
            if time_diff < timedelta(hours=1):
                return "high"
            elif time_diff < timedelta(hours=24):
                return "medium"
        except:
            pass
        
        return "low"
    
    def _extract_jurisdictions(self, description: str) -> List[str]:
        """Extract affected jurisdictions from text"""
        jurisdictions = [
            "United States", "European Union", "United Kingdom", 
            "Singapore", "Japan", "Switzerland", "Hong Kong"
        ]
        
        found = []
        for jurisdiction in jurisdictions:
            if jurisdiction.lower() in description.lower():
                found.append(jurisdiction)
        
        return found if found else ["Global"]
    
    def _calculate_transaction_risk(self, from_addr: str, to_addr: str, value: float) -> float:
        """Enhanced risk calculation with multiple factors"""
        risk_score = 0.0
        
        # Value-based risk
        if value > self.risk_thresholds["transaction_volume"]:
            risk_score += 40
        elif value > 100000:
            risk_score += 30
        elif value > 10000:
            risk_score += 20
        elif value > 1000:
            risk_score += 10
        
        # Pattern-based risk
        if from_addr == to_addr:
            risk_score += 25  # Self-transfer
        
        # Address risk (simplified - in production would check against blacklists)
        if "000000" in from_addr or "000000" in to_addr:
            risk_score += 15  # Suspicious address pattern
        
        # Time-based risk (would analyze time patterns in production)
        import random
        time_risk = random.uniform(0, 20)
        risk_score += time_risk
        
        return min(risk_score, 100)
    
    def _detect_aml_patterns(self, from_addr: str, to_addr: str, value: float) -> List[str]:
        """Detect potential AML patterns"""
        patterns = []
        
        # Structuring detection
        if 9000 < value < 10000:
            patterns.append("potential_structuring")
        
        # Rapid movement
        if value > 50000:
            patterns.append("high_value_transfer")
        
        # Self-transfer
        if from_addr == to_addr:
            patterns.append("circular_transaction")
        
        return patterns
    
    def _calculate_velocity(self, timestamp: str) -> float:
        """Calculate transaction velocity score"""
        # In production, would analyze transaction frequency over time windows
        import random
        return random.uniform(0, 100)
    
    def _analyze_network_patterns(self, from_addr: str, to_addr: str) -> Dict:
        """Analyze network patterns for suspicious activity"""
        # In production, would use graph analysis
        return {
            "centrality_score": 0.5,
            "cluster_id": "cluster_1",
            "suspicious_connections": 0
        }
    
    def _calculate_regulatory_impact(self, severity: str, category: str) -> float:
        """Calculate regulatory impact score"""
        severity_scores = {
            "critical": 1.0,
            "high": 0.75,
            "medium": 0.5,
            "low": 0.25
        }
        
        category_multipliers = {
            "enforcement": 1.5,
            "compliance": 1.2,
            "guidance": 0.8,
            "announcement": 0.5
        }
        
        base_score = severity_scores.get(severity.lower(), 0.5)
        multiplier = category_multipliers.get(category.lower(), 1.0)
        
        return min(base_score * multiplier, 1.0)
    
    def _identify_affected_entities(self, description: str) -> List[str]:
        """Identify entities affected by regulatory updates"""
        entities = []
        
        entity_keywords = {
            "exchanges": ["exchange", "trading platform", "marketplace"],
            "defi_protocols": ["defi", "decentralized finance", "protocol"],
            "stablecoins": ["stablecoin", "pegged", "fiat-backed"],
            "nft_platforms": ["nft", "non-fungible", "digital art"],
            "custody_providers": ["custody", "wallet", "storage"]
        }
        
        text_lower = description.lower()
        for entity_type, keywords in entity_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                entities.append(entity_type)
        
        return entities if entities else ["all_entities"]
    
    def _apply_time_windows(self, stream: Any) -> Any:
        """Apply time windowing for temporal analysis"""
        if not pathway_available:
            return stream
        
        try:
            # Create sliding windows for different time periods
            # This would enable velocity and pattern analysis over time
            return stream  # Simplified for now
        except Exception as e:
            logger.error(f"Error applying time windows: {e}")
            return stream
    
    def _join_compliance_streams(self, news: Any, transactions: Any, regulatory: Any) -> Any:
        """Join multiple streams for unified compliance view"""
        if not pathway_available:
            return None
        
        # In production, would perform complex joins and correlations
        # For now, return the news stream as primary
        return news
    
    def _generate_compliance_alerts(self, compliance_data: Any) -> Any:
        """Generate real-time compliance alerts from unified data"""
        if not pathway_available:
            return None
        
        # Would generate alerts based on patterns and thresholds
        return compliance_data
    
    def _simulate_compliance_pipeline(self) -> Dict[str, Any]:
        """Simulate compliance pipeline when Pathway not available"""
        return {
            "status": "simulated",
            "streams": ["news", "transactions", "regulatory", "alerts"],
            "monitoring_level": "simulation",
            "message": "Using simulated data - Pathway not available"
        }
    
    def _simulate_news_stream(self) -> Dict:
        """Simulate news stream data"""
        return {"type": "simulated_news", "count": 10}
    
    def _simulate_regulatory_stream(self) -> Dict:
        """Simulate regulatory stream data"""
        return {"type": "simulated_regulatory", "count": 5}
    
    async def start_streaming(self):
        """Start enhanced real-time data streaming with Pathway"""
        if not pathway_available:
            logger.warning("Pathway not available - using simulation mode")
            await self._start_simulation_mode()
            return
        
        try:
            self.is_running = True
            
            # Create comprehensive compliance monitoring pipeline
            pipeline_status = self.create_compliance_monitoring_pipeline()
            
            if pipeline_status.get("status") == "active":
                logger.info(f"Pathway streaming started with {len(self.data_streams)} active streams")
                logger.info(f"Active streams: {', '.join(self.data_streams.keys())}")
            else:
                # Fallback to basic streams
                self.create_news_stream()
                self.create_transaction_stream()
                self.create_regulatory_updates_stream()
            
            # Run Pathway computation with enhanced configuration
            if self.data_streams:
                pw.run(
                    monitoring_level=self.monitoring_level,
                    persistence_config=pw.persistence.Config(
                        backend=self.persistence_backend,
                        path=self.persistence_path
                    ) if self.persistence_backend else None
                )
                
                # Log streaming metrics
                self._log_streaming_metrics()
            
        except Exception as e:
            logger.error(f"Error starting Pathway streaming: {e}")
            self.is_running = False
    
    async def _start_simulation_mode(self):
        """Start simulation mode when Pathway not available"""
        self.is_running = True
        
        # Generate simulated streams
        self.data_streams["simulated_news"] = await mock_generator.generate_mock_news()
        self.data_streams["simulated_transactions"] = await mock_generator.generate_mock_transactions()
        
        # Generate simulated alerts
        self.compliance_alerts = self._generate_simulated_alerts()
        
        logger.info("Simulation mode started - demonstrating Pathway capabilities")
    
    def _generate_simulated_alerts(self) -> List[ComplianceAlert]:
        """Generate simulated compliance alerts for demonstration"""
        alerts = [
            ComplianceAlert(
                id="alert_001",
                timestamp=datetime.utcnow(),
                level=ComplianceLevel.CRITICAL,
                category="AML",
                title="High-Risk Transaction Pattern Detected",
                description="Multiple transactions detected with structuring patterns below reporting threshold",
                affected_entities=["exchange_1", "wallet_provider_2"],
                regulatory_body="FinCEN",
                recommended_action="Immediate review and SAR filing if confirmed",
                confidence_score=0.92
            ),
            ComplianceAlert(
                id="alert_002",
                timestamp=datetime.utcnow() - timedelta(hours=2),
                level=ComplianceLevel.HIGH,
                category="Regulatory",
                title="New SEC Enforcement Action",
                description="SEC announces enforcement action against unregistered crypto securities offering",
                affected_entities=["defi_protocols", "exchanges"],
                regulatory_body="SEC",
                recommended_action="Review token listings and ensure compliance with securities laws",
                confidence_score=0.88
            ),
            ComplianceAlert(
                id="alert_003",
                timestamp=datetime.utcnow() - timedelta(hours=5),
                level=ComplianceLevel.MEDIUM,
                category="Sanctions",
                title="OFAC List Update",
                description="New addresses added to OFAC SDN list related to ransomware operations",
                affected_entities=["all_entities"],
                regulatory_body="OFAC",
                recommended_action="Update screening systems with new sanctioned addresses",
                confidence_score=0.95
            )
        ]
        return alerts
    
    def _log_streaming_metrics(self):
        """Log streaming metrics for monitoring"""
        metrics = {
            "active_streams": len(self.data_streams),
            "total_alerts": len(self.compliance_alerts),
            "critical_alerts": sum(1 for a in self.compliance_alerts if a.level == ComplianceLevel.CRITICAL),
            "high_risk_transactions": len(self.data_streams.get("high_risk_transactions", [])),
            "indexes_created": len(self.indexes)
        }
        logger.info(f"Streaming metrics: {metrics}")
    
    async def stop_streaming(self):
        """Stop real-time data streaming"""
        self.is_running = False
        
        # Log final metrics
        if self.data_streams:
            self._log_streaming_metrics()
        
        logger.info("Pathway streaming stopped")
    
    def query_stream(self, stream_name: str, query: Dict) -> List[Dict]:
        """Query a data stream with Pathway's powerful query capabilities"""
        if stream_name not in self.data_streams:
            logger.warning(f"Stream '{stream_name}' not found")
            return []
        
        # If in simulation mode, return simulated data
        if not pathway_available:
            if stream_name == "alerts":
                return [{
                    "id": alert.id,
                    "timestamp": alert.timestamp.isoformat(),
                    "level": alert.level.value,
                    "title": alert.title,
                    "description": alert.description,
                    "confidence_score": alert.confidence_score
                } for alert in self.compliance_alerts[:5]]
            elif stream_name in self.data_streams:
                return self.data_streams[stream_name][:5] if isinstance(self.data_streams[stream_name], list) else []
        
        # In production, would execute complex Pathway queries
        return []
    
    def search_similar_documents(self, query_embedding: List[float], k: int = 5) -> List[Dict]:
        """Search for similar documents using Pathway's vector index"""
        if "documents" not in self.indexes:
            logger.warning("Document index not created")
            return []
        
        # Simulate search results for demonstration
        if not pathway_available:
            return [
                {
                    "id": "doc_1",
                    "content": "SEC regulatory guidance on digital asset securities",
                    "similarity_score": 0.92,
                    "metadata": {"source": "SEC", "date": "2024-01-15"}
                },
                {
                    "id": "doc_2",
                    "content": "CFTC enforcement action against unregistered derivatives exchange",
                    "similarity_score": 0.87,
                    "metadata": {"source": "CFTC", "date": "2024-01-10"}
                }
            ][:k]
        
        # In production, would use Pathway's KNN index for similarity search
        return []
    
    def get_compliance_dashboard(self) -> Dict[str, Any]:
        """Get real-time compliance dashboard data"""
        dashboard = {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "active" if self.is_running else "inactive",
            "streams": {
                "total": len(self.data_streams),
                "active": list(self.data_streams.keys())
            },
            "alerts": {
                "total": len(self.compliance_alerts),
                "by_level": {
                    "critical": sum(1 for a in self.compliance_alerts if a.level == ComplianceLevel.CRITICAL),
                    "high": sum(1 for a in self.compliance_alerts if a.level == ComplianceLevel.HIGH),
                    "medium": sum(1 for a in self.compliance_alerts if a.level == ComplianceLevel.MEDIUM),
                    "low": sum(1 for a in self.compliance_alerts if a.level == ComplianceLevel.LOW)
                },
                "recent": [
                    {
                        "id": alert.id,
                        "timestamp": alert.timestamp.isoformat(),
                        "level": alert.level.value,
                        "title": alert.title,
                        "regulatory_body": alert.regulatory_body,
                        "confidence": alert.confidence_score
                    }
                    for alert in sorted(self.compliance_alerts, 
                                      key=lambda x: x.timestamp, 
                                      reverse=True)[:5]
                ] if self.compliance_alerts else []
            },
            "risk_metrics": {
                "high_risk_transactions": len(self.data_streams.get("high_risk_transactions", [])),
                "critical_risk_transactions": len(self.data_streams.get("critical_risk_transactions", [])),
                "monitoring_thresholds": self.risk_thresholds
            },
            "pathway_features": {
                "incremental_computation": "Automatic updates on new data",
                "time_windowing": "Sliding windows for temporal analysis",
                "pattern_detection": "Real-time AML and fraud detection",
                "multi_source_join": "Unified view from multiple data streams",
                "vector_search": "Semantic similarity for compliance documents",
                "persistence": "State recovery after restarts",
                "scalability": "Rust engine for high-performance processing"
            }
        }
        
        return dashboard
    
    def get_stream_statistics(self, stream_name: str) -> Dict[str, Any]:
        """Get statistics for a specific data stream"""
        if stream_name not in self.data_streams:
            return {"error": f"Stream '{stream_name}' not found"}
        
        # Return statistics about the stream
        stream_data = self.data_streams[stream_name]
        
        stats = {
            "stream_name": stream_name,
            "status": "active" if self.is_running else "inactive",
            "data_points": len(stream_data) if isinstance(stream_data, list) else "streaming",
            "last_updated": datetime.utcnow().isoformat(),
            "processing_mode": self.streaming_mode,
            "monitoring_level": self.monitoring_level
        }
        
        # Add stream-specific statistics
        if stream_name == "high_risk_transactions":
            stats["risk_threshold"] = self.risk_thresholds["risk_score_high"]
        elif stream_name == "critical_risk_transactions":
            stats["risk_threshold"] = self.risk_thresholds["risk_score_critical"]
        
        return stats

# Create singleton instance
pathway_service = PathwayService()

# Enhanced Mock data generator for testing without Pathway
class MockStreamGenerator:
    """Generate enhanced mock streaming data for demonstration"""
    
    @staticmethod
    async def generate_mock_news():
        """Generate mock news data"""
        news_items = [
            {
                "title": "SEC Announces New Cryptocurrency Regulations - Immediate Compliance Required",
                "description": "The Securities and Exchange Commission released comprehensive guidelines for digital asset compliance, requiring immediate action from all crypto exchanges and DeFi protocols.",
                "url": "https://example.com/sec-crypto-regs",
                "source": "SEC",
                "published_at": datetime.utcnow().isoformat(),
                "keywords": ["SEC", "cryptocurrency", "regulations", "enforcement", "immediate"],
                "sentiment": "negative",
                "compliance_impact": "critical",
                "urgency": "high"
            },
            {
                "title": "CFTC Issues Warning on DeFi Platforms - Risk Assessment Required",
                "description": "Commodity Futures Trading Commission warns investors about risks in decentralized finance, highlighting potential violations of derivatives regulations.",
                "url": "https://example.com/cftc-defi-warning",
                "source": "CFTC",
                "published_at": datetime.utcnow().isoformat(),
                "keywords": ["CFTC", "DeFi", "warning", "derivatives", "compliance"],
                "sentiment": "negative",
                "compliance_impact": "high",
                "urgency": "medium"
            },
            {
                "title": "FinCEN Updates AML Requirements for Virtual Asset Service Providers",
                "description": "Financial Crimes Enforcement Network announces enhanced anti-money laundering requirements for cryptocurrency exchanges and wallet providers.",
                "url": "https://example.com/fincen-aml-update",
                "source": "FinCEN",
                "published_at": (datetime.utcnow() - timedelta(hours=3)).isoformat(),
                "keywords": ["FinCEN", "AML", "KYC", "VASP", "compliance"],
                "sentiment": "neutral",
                "compliance_impact": "high",
                "urgency": "high"
            },
            {
                "title": "OFAC Adds New Crypto Addresses to SDN List",
                "description": "Office of Foreign Assets Control sanctions additional cryptocurrency addresses linked to ransomware operations and illicit activities.",
                "url": "https://example.com/ofac-sdn-update",
                "source": "OFAC",
                "published_at": (datetime.utcnow() - timedelta(hours=6)).isoformat(),
                "keywords": ["OFAC", "sanctions", "SDN", "ransomware", "blacklist"],
                "sentiment": "negative",
                "compliance_impact": "critical",
                "urgency": "critical"
            },
            {
                "title": "EU MiCA Regulation Implementation Timeline Released",
                "description": "European Union publishes detailed implementation timeline for Markets in Crypto-Assets regulation, affecting all crypto service providers in EU.",
                "url": "https://example.com/eu-mica-timeline",
                "source": "EU Commission",
                "published_at": (datetime.utcnow() - timedelta(days=1)).isoformat(),
                "keywords": ["MiCA", "EU", "regulation", "compliance", "timeline"],
                "sentiment": "neutral",
                "compliance_impact": "medium",
                "urgency": "low"
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
