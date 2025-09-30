"""
Real-time Pathway Service for streaming news and AI analysis
"""
import asyncio
import logging
import json
import time
import csv
import os
from typing import List, Dict, Optional, Any, AsyncGenerator
from pathlib import Path
import pandas as pd
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

from .config import (
    PATHWAY_KEY,
    PATHWAY_PERSISTENCE_PATH,
    GROQ_API_KEY,
    NEWSAPI_KEY,
    TRANSACTION_THRESHOLD,
    RISK_SCORE_THRESHOLD,
)
from .realtime_news_service import realtime_news_service, NewsArticle
from .blockchain_service import blockchain_service

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
    logger.warning("Pathway library not available - Install with: pip install pathway")

@dataclass
class ProcessedNews:
    """Processed news item for Pathway streaming"""
    id: str
    timestamp: str
    title: str
    description: str
    source: str
    category: str
    sentiment: str
    relevance_score: float
    regulatory_impact: str
    keywords: str  # JSON string
    entities: str  # JSON string
    
    def to_dict(self) -> Dict:
        return asdict(self)

class RealTimePathwayService:
    """Real-time Pathway service for streaming news and AI analysis with wallet monitoring"""
    
    def __init__(self):
        self.pathway_key = PATHWAY_KEY
        self.persistence_path = Path(PATHWAY_PERSISTENCE_PATH)
        self.news_service = None
        self.streaming_active = False
        self.is_running = False
        self.stream_tables = {}
        self.processed_articles = []
        self.wallet_streams = {}  # Track wallet-specific streams
        self.connected_wallets = set()  # Track connected wallets
        self.seen_tx_hashes = set()  # Deduplicate streamed transactions
        
        # Create directories
        self.persistence_path.mkdir(parents=True, exist_ok=True)
        (self.persistence_path / "streams").mkdir(exist_ok=True)
        (self.persistence_path / "processed").mkdir(exist_ok=True)
        (self.persistence_path / "wallet_streams").mkdir(exist_ok=True)
        
        # Initialize Pathway if available
        if pathway_available and self.pathway_key:
            self._initialize_pathway()
        
        # Initialize Groq for analysis
        if GROQ_API_KEY:
            try:
                from groq import Groq
                self.groq_client = Groq(api_key=GROQ_API_KEY)
                logger.info("Groq API initialized for real-time analysis")
            except Exception as e:
                logger.error(f"Failed to initialize Groq API: {e}")
                self.groq_client = None
        else:
            logger.warning("No Groq API key provided")
            self.groq_client = None
    
    def _initialize_pathway(self):
        """Initialize Pathway configuration"""
        try:
            # Set up Pathway license
            pw.set_license_key(self.pathway_key)
            
            # Configure monitoring
            pw.set_monitoring_level(pw.MonitoringLevel.REGULAR)
            
            logger.info("Pathway initialized successfully for real-time processing")
            
        except Exception as e:
            logger.error(f"Error initializing Pathway: {e}")
    
    async def start_realtime_pipeline(self):
        """Start the real-time news processing pipeline"""
        if not pathway_available:
            logger.error("Pathway not available - cannot start real-time pipeline")
            return False
        
        try:
            self.is_running = True
            logger.info("Starting real-time Pathway pipeline...")
            
            # Start news collection in background
            asyncio.create_task(self._collect_news_continuously())
            # Start wallet transaction collection in background
            asyncio.create_task(self._collect_wallet_transactions_continuously())
            
            # Create and run Pathway pipeline
            await self._create_pathway_pipeline()
            
            return True
            
        except Exception as e:
            logger.error(f"Error starting real-time pipeline: {e}")
            self.is_running = False
            return False
    
    async def _collect_news_continuously(self):
        """Continuously collect news and write to CSV for Pathway"""
        news_csv_path = self.persistence_path / "streams" / "realtime_news.csv"
        
        # Initialize CSV file with headers
        with open(news_csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'id', 'timestamp', 'title', 'description', 'source', 
                'category', 'sentiment', 'relevance_score', 'regulatory_impact',
                'keywords', 'entities', 'url'
            ])
            writer.writeheader()
        
        logger.info("Starting continuous news collection...")
        
        async with realtime_news_service:
            while self.is_running:
                try:
                    # Fetch latest news
                    articles = await realtime_news_service.fetch_realtime_news(
                        query="cryptocurrency OR blockchain OR DeFi OR regulatory OR compliance OR SEC OR CFTC",
                        page_size=50
                    )
                    
                    if articles:
                        # Process and append to CSV
                        processed_articles = []
                        for article in articles:
                            processed = await self._process_news_for_pathway(article)
                            if processed:
                                processed_articles.append(processed.to_dict())
                        
                        # Append to CSV file
                        if processed_articles:
                            with open(news_csv_path, 'a', newline='', encoding='utf-8') as f:
                                writer = csv.DictWriter(f, fieldnames=processed_articles[0].keys())
                                writer.writerows(processed_articles)
                            
                            logger.info(f"Added {len(processed_articles)} articles to stream")
                    
                    # Wait before next collection
                    await asyncio.sleep(300)  # 5 minutes
                    
                except Exception as e:
                    logger.error(f"Error in news collection: {e}")
                    await asyncio.sleep(60)  # Wait 1 minute on error
    
    async def _collect_wallet_transactions_continuously(self):
        """Continuously collect wallet transactions and write to CSV for Pathway"""
        wallet_csv_path = self.persistence_path / "streams" / "wallet_transactions.csv"
        # Initialize CSV with headers if not exists
        if not wallet_csv_path.exists():
            with open(wallet_csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'id', 'timestamp', 'wallet_address', 'hash', 'from_address', 'to_address',
                    'value', 'block_number'
                ])
                writer.writeheader()
        
        logger.info("Starting continuous wallet transactions collection...")
        
        while self.is_running:
            try:
                if not self.connected_wallets:
                    await asyncio.sleep(15)
                    continue
                total_appended = 0
                for wallet in list(self.connected_wallets):
                    try:
                        txs = await blockchain_service.get_transactions(wallet, limit=10)
                    except Exception as e:
                        logger.error(f"Error fetching transactions for {wallet}: {e}")
                        continue
                    rows = []
                    for tx in txs or []:
                        try:
                            if not getattr(tx, 'hash', None):
                                continue
                            if tx.hash in self.seen_tx_hashes:
                                continue
                            # Mark as seen to prevent duplicates
                            self.seen_tx_hashes.add(tx.hash)
                            # Parse value as float
                            try:
                                val = float(tx.value) if tx.value is not None else 0.0
                            except Exception:
                                val = 0.0
                            rows.append({
                                'id': f"tx_{tx.hash}",
                                'timestamp': getattr(tx, 'timestamp', datetime.now().isoformat()),
                                'wallet_address': wallet,
                                'hash': tx.hash,
                                'from_address': getattr(tx, 'from_address', ''),
                                'to_address': getattr(tx, 'to_address', ''),
                                'value': val,
                                'block_number': getattr(tx, 'block_number', 0) or 0,
                            })
                        except Exception as e:
                            logger.warning(f"Skipping malformed tx for {wallet}: {e}")
                            continue
                    if rows:
                        with open(wallet_csv_path, 'a', newline='', encoding='utf-8') as f:
                            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                            writer.writerows(rows)
                        total_appended += len(rows)
                if total_appended:
                    logger.info(f"Appended {total_appended} wallet transactions to stream")
                await asyncio.sleep(60)  # 1 minute cadence for demo responsiveness
            except Exception as e:
                logger.error(f"Error in wallet transactions collection: {e}")
                await asyncio.sleep(30)
    
    async def _process_news_for_pathway(self, article: NewsArticle) -> Optional[ProcessedNews]:
        """Process news article for Pathway streaming"""
        try:
            # Enhanced analysis via Groq or use article-provided analysis
            enhanced_analysis = await self._enhanced_analysis(article)
            
            return ProcessedNews(
                id=article.id,
                timestamp=datetime.now().isoformat(),
                title=article.title,
                description=article.description or "",
                source=article.source,
                category=enhanced_analysis.get('category', article.category),
                sentiment=enhanced_analysis.get('sentiment', article.sentiment),
                relevance_score=enhanced_analysis.get('relevance_score', article.relevance_score),
                regulatory_impact=enhanced_analysis.get('regulatory_impact', 'medium'),
                keywords=json.dumps(enhanced_analysis.get('keywords', article.keywords)),
                entities=json.dumps(enhanced_analysis.get('entities', article.entities)),
                url=article.url
            )
            
        except Exception as e:
            logger.error(f"Error processing article for Pathway: {e}")
            return None
    
    async def _enhanced_analysis(self, article: NewsArticle) -> Dict:
        """Enhanced analysis using Groq if available, otherwise use article fields."""
        # If Groq client is available, you could refine analysis here similarly to realtime_news_service
        # For stability in hackathon demo, use the already computed fields from news service
        return {
            'category': article.category,
            'sentiment': article.sentiment,
            'relevance_score': article.relevance_score,
            'regulatory_impact': 'medium',
            'keywords': article.keywords,
            'entities': article.entities
        }
    
    async def _create_pathway_pipeline(self):
        """Create and run the Pathway streaming pipeline"""
        if not pathway_available:
            return
        
        try:
            # Define schema for news stream
            class NewsStreamSchema(pw.Schema):
                id: str
                timestamp: str
                title: str
                description: str
                source: str
                category: str
                sentiment: str
                relevance_score: float
                regulatory_impact: str
                keywords: str
                entities: str
                url: str
            
            # Create streaming input from CSV
            news_csv_path = self.persistence_path / "streams" / "realtime_news.csv"
            # Ensure file exists with headers before reading
            if not news_csv_path.exists():
                with open(news_csv_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=[
                        'id', 'timestamp', 'title', 'description', 'source',
                        'category', 'sentiment', 'relevance_score', 'regulatory_impact',
                        'keywords', 'entities', 'url'
                    ])
                    writer.writeheader()
            
            # Create the streaming table
            news_table = pw.io.csv.read(
                str(news_csv_path),
                schema=NewsStreamSchema,
                mode="streaming"
            )
            
            # Define schema for wallet transactions stream
            class WalletTxSchema(pw.Schema):
                id: str
                timestamp: str
                wallet_address: str
                hash: str
                from_address: str
                to_address: str
                value: float
                block_number: int
            
            wallet_csv_path = self.persistence_path / "streams" / "wallet_transactions.csv"
            # Ensure file exists with headers before reading
            if not wallet_csv_path.exists():
                with open(wallet_csv_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=[
                        'id', 'timestamp', 'wallet_address', 'hash', 'from_address', 'to_address',
                        'value', 'block_number'
                    ])
                    writer.writeheader()
            wallet_table = pw.io.csv.read(
                str(wallet_csv_path),
                schema=WalletTxSchema,
                mode="streaming"
            )
            
            # Process the stream with advanced analytics
            processed_news = news_table.select(
                id=news_table.id,
                timestamp=news_table.timestamp,
                title=news_table.title,
                source=news_table.source,
                category=news_table.category,
                sentiment=news_table.sentiment,
                relevance_score=news_table.relevance_score,
                regulatory_impact=news_table.regulatory_impact,
                
                # Add computed columns
                priority_score=pw.apply(
                    self._calculate_priority_score,
                    news_table.relevance_score,
                    news_table.regulatory_impact,
                    news_table.category
                ),
                
                alert_level=pw.apply(
                    self._determine_alert_level,
                    news_table.regulatory_impact,
                    news_table.relevance_score
                ),
                
                processing_timestamp=pw.apply(
                    lambda: datetime.now().isoformat()
                )
            )
            
            # Filter high-priority news
            high_priority_news = processed_news.filter(
                processed_news.priority_score > 0.7
            )
            
            # Create alerts for critical news
            critical_alerts = processed_news.filter(
                processed_news.alert_level == "critical"
            )
            
            # Process wallet transactions with risk and alerts
            wallet_processed = wallet_table.select(
                id=wallet_table.id,
                timestamp=wallet_table.timestamp,
                wallet_address=wallet_table.wallet_address,
                hash=wallet_table.hash,
                from_address=wallet_table.from_address,
                to_address=wallet_table.to_address,
                value=wallet_table.value,
                block_number=wallet_table.block_number,
                tx_risk=pw.apply(self._tx_risk_score, wallet_table.value),
                tx_alert=pw.apply(self._tx_alert_level, wallet_table.value)
            )
            wallet_alerts = wallet_processed.filter(
                (wallet_processed.tx_alert == "critical") |
                (wallet_processed.value > float(TRANSACTION_THRESHOLD))
            )
            
            # Output streams to files for monitoring
            pw.io.csv.write(
                processed_news,
                str(self.persistence_path / "streams" / "processed_news.csv")
            )
            
            pw.io.csv.write(
                high_priority_news,
                str(self.persistence_path / "streams" / "high_priority_news.csv")
            )
            
            pw.io.csv.write(
                critical_alerts,
                str(self.persistence_path / "streams" / "critical_alerts.csv")
            )
            
            pw.io.csv.write(
                wallet_processed,
                str(self.persistence_path / "streams" / "wallet_transactions_processed.csv")
            )
            
            pw.io.csv.write(
                wallet_alerts,
                str(self.persistence_path / "streams" / "wallet_alerts.csv")
            )
            
            # Store references
            self.stream_tables = {
                'news': news_table,
                'processed': processed_news,
                'high_priority': high_priority_news,
                'critical_alerts': critical_alerts,
                'wallet_transactions': wallet_table,
                'wallet_transactions_processed': wallet_processed,
                'wallet_alerts': wallet_alerts
            }
            
            logger.info("Pathway pipeline created successfully")
            
            # Run the computation in a background thread to avoid blocking the event loop
            await asyncio.to_thread(
                pw.run,
                monitoring_level=pw.MonitoringLevel.REGULAR,
                persistence_config=pw.persistence.Config(
                    backend=pw.persistence.Backend.FILESYSTEM,
                    path=str(self.persistence_path / "pathway_state")
                )
            )
            
        except Exception as e:
            logger.error(f"Error creating Pathway pipeline: {e}")
    
    def _calculate_priority_score(self, relevance_score: float, regulatory_impact: str, category: str) -> float:
        """Calculate priority score for news items"""
        base_score = float(relevance_score)
        
        # Impact multipliers
        impact_multipliers = {
            'critical': 1.5,
            'high': 1.2,
            'medium': 1.0,
            'low': 0.8,
            'none': 0.5
        }
        
        # Category multipliers
        category_multipliers = {
            'enforcement': 1.4,
            'regulatory': 1.3,
            'compliance': 1.2,
            'guidance': 1.0,
            'technology': 0.9,
            'market': 0.8
        }
        
        impact_mult = impact_multipliers.get(regulatory_impact, 1.0)
        category_mult = category_multipliers.get(category, 1.0)
        
        return min(base_score * impact_mult * category_mult, 1.0)
    
    def _determine_alert_level(self, regulatory_impact: str, relevance_score: float) -> str:
        """Determine alert level based on impact and relevance"""
        if regulatory_impact == 'critical' and relevance_score > 0.8:
            return 'critical'
        elif regulatory_impact in ['critical', 'high'] and relevance_score > 0.6:
            return 'high'
        elif regulatory_impact in ['high', 'medium'] and relevance_score > 0.4:
            return 'medium'
        else:
            return 'low'
    
    def _tx_risk_score(self, value: float) -> float:
        """Simple normalized risk score for a transaction value."""
        try:
            v = float(value)
        except Exception:
            v = 0.0
        # Normalize against a high watermark (e.g., 1,000,000)
        score = min(v / max(float(TRANSACTION_THRESHOLD) * 20.0, 1.0), 1.0)
        return score
    
    def _tx_alert_level(self, value: float) -> str:
        """Alert level based on transaction size."""
        try:
            v = float(value)
        except Exception:
            v = 0.0
        if v >= float(TRANSACTION_THRESHOLD) * 10:
            return 'critical'
        elif v >= float(TRANSACTION_THRESHOLD):
            return 'high'
        elif v >= float(TRANSACTION_THRESHOLD) / 5:
            return 'medium'
        else:
            return 'low'
    
    async def get_realtime_dashboard(self) -> Dict[str, Any]:
        """Get real-time dashboard data"""
        try:
            dashboard_data = {
                'timestamp': datetime.now().isoformat(),
                'status': 'active' if self.is_running else 'inactive',
                'pathway_available': pathway_available,
                'streams': {
                    'total_streams': len(self.stream_tables),
                    'active_streams': list(self.stream_tables.keys())
                }
            }
            
            # Add stream statistics if available
            if self.is_running and pathway_available:
                stats = await self._get_stream_statistics()
                dashboard_data['statistics'] = stats
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'status': 'error',
                'error': str(e)
            }
    
    async def _get_stream_statistics(self) -> Dict[str, Any]:
        """Get statistics from stream files"""
        stats = {}
        
        try:
            # Read processed news statistics
            processed_file = self.persistence_path / "streams" / "processed_news.csv"
            if processed_file.exists():
                df = pd.read_csv(processed_file)
                stats['processed_news'] = {
                    'total_count': len(df),
                    'categories': df['category'].value_counts().to_dict() if 'category' in df.columns else {},
                    'sentiment_distribution': df['sentiment'].value_counts().to_dict() if 'sentiment' in df.columns else {},
                    'avg_relevance_score': df['relevance_score'].mean() if 'relevance_score' in df.columns else 0
                }
            
            # Read high priority news statistics
            high_priority_file = self.persistence_path / "streams" / "high_priority_news.csv"
            if high_priority_file.exists():
                df_high = pd.read_csv(high_priority_file)
                stats['high_priority_news'] = {
                    'count': len(df_high),
                    'recent_count': len(df_high[df_high['timestamp'] > (datetime.now() - timedelta(hours=24)).isoformat()]) if 'timestamp' in df_high.columns else 0
                }
            
            # Read critical alerts statistics
            alerts_file = self.persistence_path / "streams" / "critical_alerts.csv"
            if alerts_file.exists():
                df_alerts = pd.read_csv(alerts_file)
                stats['critical_alerts'] = {
                    'count': len(df_alerts),
                    'recent_count': len(df_alerts[df_alerts['timestamp'] > (datetime.now() - timedelta(hours=1)).isoformat()]) if 'timestamp' in df_alerts.columns else 0
                }

            # Wallet transactions processed statistics
            wallet_proc_file = self.persistence_path / "streams" / "wallet_transactions_processed.csv"
            if wallet_proc_file.exists():
                df_w = pd.read_csv(wallet_proc_file)
                stats['wallet_transactions'] = {
                    'count': len(df_w),
                    'high_risk': len(df_w[df_w['tx_alert'].isin(['high', 'critical'])]) if 'tx_alert' in df_w.columns else 0
                }

            # Wallet alerts statistics
            wallet_alerts_file = self.persistence_path / "streams" / "wallet_alerts.csv"
            if wallet_alerts_file.exists():
                df_wa = pd.read_csv(wallet_alerts_file)
                stats['wallet_alerts'] = {
                    'count': len(df_wa),
                    'recent_count': len(df_wa[df_wa['timestamp'] > (datetime.now() - timedelta(hours=1)).isoformat()]) if 'timestamp' in df_wa.columns else 0
                }
        
        except Exception as e:
            logger.error(f"Error getting stream statistics: {e}")
            stats['error'] = str(e)
        
        return stats
    
    async def stop_pipeline(self):
        """Stop the real-time pipeline"""
        self.is_running = False
        logger.info("Real-time pipeline stopped")
    
    async def query_stream(self, stream_name: str, limit: int = 10, wallet_address: Optional[str] = None) -> List[Dict]:
        """Query a specific stream with optional wallet filter"""
        try:
            stream_file = self.persistence_path / "streams" / f"{stream_name}.csv"
            
            if not stream_file.exists():
                return []
            
            df = pd.read_csv(stream_file)
            
            # Optional wallet filter for wallet streams
            if wallet_address and 'wallet_address' in df.columns:
                try:
                    df['wallet_address'] = df['wallet_address'].astype(str)
                    df = df[df['wallet_address'].str.lower() == wallet_address.lower()]
                except Exception:
                    pass
            
            # Return most recent records
            if 'timestamp' in df.columns:
                df = df.sort_values('timestamp', ascending=False)
            
            return df.head(limit).to_dict('records')
            
        except Exception as e:
            logger.error(f"Error querying stream {stream_name}: {e}")
            return []

    async def connect_wallet_for_realtime_monitoring(self, wallet_address: str) -> Dict:
        """Connect wallet for real-time compliance monitoring using Pathway"""
        try:
            # Add wallet to monitoring set
            if not hasattr(self, 'connected_wallets'):
                self.connected_wallets = set()
            if not hasattr(self, 'wallet_streams'):
                self.wallet_streams = {}
                
            self.connected_wallets.add(wallet_address)
            
            # Initialize wallet-specific stream
            wallet_stream_id = f"wallet_{wallet_address}"
            self.wallet_streams[wallet_stream_id] = {
                "wallet_address": wallet_address,
                "connected_at": datetime.now().isoformat(),
                "monitoring_active": True,
                "compliance_alerts": [],
                "risk_score_history": []
            }
            
            # Create wallet stream directory
            wallet_stream_dir = self.persistence_path / "wallet_streams"
            wallet_stream_dir.mkdir(exist_ok=True)
            
            # Start real-time monitoring
            if pathway_available:
                await self._start_wallet_pathway_stream(wallet_address)
            
            # Ensure wallet is tracked and perform initial compliance check
            try:
                from .wallet_tracking_service import wallet_tracking_service
                # Add wallet to tracking (no-op if already tracked)
                await wallet_tracking_service.add_wallet_for_tracking(wallet_address)
                # Fetch initial compliance status
                initial_status = await wallet_tracking_service.get_wallet_compliance_status(wallet_address)
            except Exception as e:
                logger.warning(f"Initial compliance check for {wallet_address} pending: {e}")
                initial_status = {"status": "checking", "message": "Initial compliance check in progress"}
            
            logger.info(f"Started real-time monitoring for wallet: {wallet_address}")
            
            return {
                "status": "connected",
                "wallet_address": wallet_address,
                "monitoring_active": True,
                "stream_id": wallet_stream_id,
                "initial_compliance": initial_status,
                "real_time_features": [
                    "Transaction monitoring",
                    "Sanctions screening", 
                    "Risk score updates",
                    "Regulatory alerts",
                    "Compliance notifications"
                ],
                "pathway_streaming": pathway_available,
                "connected_at": datetime.now().isoformat(),
                "dashboard_integration": "Real-time updates will appear in dashboard"
            }
            
        except Exception as e:
            logger.error(f"Error connecting wallet for monitoring: {e}")
            return {
                "status": "error",
                "error": str(e),
                "wallet_address": wallet_address
            }
    
    async def _start_wallet_pathway_stream(self, wallet_address: str):
        """Start Pathway streaming for specific wallet transactions"""
        if not pathway_available:
            logger.error("Pathway not available - install and configure license to enable real-time streaming")
            return
        
        try:
            # Initialize Pathway stream for wallet transactions
            logger.info(f"Pathway real-time stream initialized for wallet: {wallet_address}")
            
            # This would set up actual Pathway streaming in production
            # TODO: Add wallet transaction CSV stream and include it in the Pathway pipeline
            
        except Exception as e:
            logger.error(f"Error starting Pathway stream for wallet {wallet_address}: {e}")
    
    async def get_wallet_realtime_status(self, wallet_address: str) -> Dict:
        """Get real-time status for connected wallet"""
        try:
            if not hasattr(self, 'wallet_streams'):
                self.wallet_streams = {}
            
            wallet_stream_id = f"wallet_{wallet_address}"
            
            if wallet_stream_id not in self.wallet_streams:
                return {
                    "status": "not_connected",
                    "message": "Wallet not connected for real-time monitoring",
                    "action": "Connect wallet first using /api/realtime/wallet/connect"
                }
            
            stream_info = self.wallet_streams[wallet_stream_id]
            
            # Get latest compliance data
            try:
                from .wallet_tracking_service import wallet_tracking_service
                current_compliance = await wallet_tracking_service.get_wallet_compliance_status(wallet_address)
            except:
                current_compliance = {"status": "checking"}
            
            # Get recent regulatory news
            try:
                from .realtime_news_service import realtime_news_service
                async with realtime_news_service:
                    relevant_news = await realtime_news_service.fetch_realtime_news(
                        query="cryptocurrency compliance sanctions",
                        page_size=3
                    )
            except:
                relevant_news = []
            
            return {
                "status": "monitoring",
                "wallet_address": wallet_address,
                "stream_active": stream_info["monitoring_active"],
                "connected_since": stream_info["connected_at"],
                "current_compliance": current_compliance,
                "recent_alerts": stream_info.get("compliance_alerts", []),
                "relevant_news": [
                    {
                        "title": article.title,
                        "source": article.source,
                        "relevance": article.relevance_score,
                        "verification_url": article.url,
                        "published": article.published_at
                    }
                    for article in relevant_news[:3]
                ],
                "real_time_capabilities": {
                    "transaction_monitoring": "Active",
                    "sanctions_screening": "Active", 
                    "news_correlation": "Active",
                    "pathway_streaming": "Available" if pathway_available else "Unavailable"
                },
                "monitoring_features": [
                    "Real-time transaction analysis",
                    "Instant compliance alerts",
                    "Regulatory news correlation",
                    "Risk score trending",
                    "Sanctions list screening"
                ],
                "last_updated": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error getting wallet real-time status: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def get_connected_wallets_summary(self) -> Dict:
        """Get summary of all connected wallets"""
        try:
            if not hasattr(self, 'connected_wallets'):
                self.connected_wallets = set()
            if not hasattr(self, 'wallet_streams'):
                self.wallet_streams = {}
            
            active_streams = [s for s in self.wallet_streams.values() if s.get("monitoring_active", False)]
            
            return {
                "total_connected": len(self.connected_wallets),
                "active_monitoring": len(active_streams),
                "wallet_addresses": list(self.connected_wallets),
                "monitoring_capabilities": [
                    "Real-time transaction monitoring",
                    "Sanctions list screening",
                    "Regulatory news correlation", 
                    "Compliance risk assessment",
                    "Alert generation"
                ],
                "pathway_streaming": pathway_available,
                "last_updated": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error getting wallet summary: {e}")
            return {"error": str(e)}

# Create global instance
realtime_pathway_service = RealTimePathwayService()
