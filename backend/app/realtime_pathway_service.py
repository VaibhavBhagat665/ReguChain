"""
Real-time Pathway Service for streaming news and AI analysis
"""
import asyncio
import logging
import json
import time
import csv
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, AsyncGenerator
from pathlib import Path
import pandas as pd
from dataclasses import dataclass, asdict

from .config import (
    PATHWAY_KEY, PATHWAY_PERSISTENCE_PATH, GOOGLE_API_KEY, NEWSAPI_KEY
)
from .realtime_news_service import realtime_news_service, NewsArticle

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
    url: str
    
    def to_dict(self) -> Dict:
        return asdict(self)

class RealTimePathwayService:
    """Real-time Pathway service with actual streaming data"""
    
    def __init__(self):
        self.pathway_key = PATHWAY_KEY
        self.persistence_path = Path(PATHWAY_PERSISTENCE_PATH)
        self.is_running = False
        self.news_buffer = []
        self.stream_tables = {}
        
        # Ensure directories exist
        self.persistence_path.mkdir(parents=True, exist_ok=True)
        (self.persistence_path / "streams").mkdir(exist_ok=True)
        
        # Initialize Pathway if available
        if pathway_available and self.pathway_key:
            self._initialize_pathway()
        
        # Initialize Gemini for analysis
        if GOOGLE_API_KEY:
            try:
                import google.generativeai as genai
                genai.configure(api_key=GOOGLE_API_KEY)
                self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
                logger.info("Gemini API initialized for real-time analysis")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini API: {e}")
                self.gemini_model = None
        else:
            self.gemini_model = None
    
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
    
    async def _process_news_for_pathway(self, article: NewsArticle) -> Optional[ProcessedNews]:
        """Process news article for Pathway streaming"""
        try:
            # Enhanced analysis with Gemini if available
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
        """Enhanced analysis using Gemini AI"""
        if not self.gemini_model:
            return {
                'category': article.category,
                'sentiment': article.sentiment,
                'relevance_score': article.relevance_score,
                'regulatory_impact': 'medium',
                'keywords': article.keywords,
                'entities': article.entities
            }
        
        try:
            prompt = f"""
            Analyze this regulatory/compliance news article and provide detailed analysis:
            
            Title: {article.title}
            Description: {article.description}
            Source: {article.source}
            
            Provide analysis in JSON format:
            {{
                "category": "regulatory|compliance|enforcement|guidance|technology|market",
                "sentiment": "positive|negative|neutral",
                "relevance_score": 0.0-1.0,
                "regulatory_impact": "critical|high|medium|low|none",
                "urgency": "immediate|high|medium|low",
                "affected_sectors": ["sector1", "sector2"],
                "compliance_areas": ["AML", "KYC", "Securities", "Derivatives"],
                "keywords": ["keyword1", "keyword2"],
                "entities": ["entity1", "entity2"],
                "risk_level": "critical|high|medium|low",
                "action_required": "immediate|review|monitor|none"
            }}
            
            Focus on cryptocurrency, blockchain, DeFi, and financial regulatory compliance.
            """
            
            response = self.gemini_model.generate_content(prompt)
            analysis = json.loads(response.text.strip())
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in enhanced analysis: {e}")
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
            
            # Create the streaming table
            news_table = pw.io.csv.read(
                str(news_csv_path),
                schema=NewsStreamSchema,
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
            
            # Store references
            self.stream_tables = {
                'news': news_table,
                'processed': processed_news,
                'high_priority': high_priority_news,
                'critical_alerts': critical_alerts
            }
            
            logger.info("Pathway pipeline created successfully")
            
            # Run the computation
            pw.run(
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
            
        except Exception as e:
            logger.error(f"Error getting stream statistics: {e}")
            stats['error'] = str(e)
        
        return stats
    
    async def stop_pipeline(self):
        """Stop the real-time pipeline"""
        self.is_running = False
        logger.info("Real-time pipeline stopped")
    
    async def query_stream(self, stream_name: str, limit: int = 10) -> List[Dict]:
        """Query a specific stream"""
        try:
            stream_file = self.persistence_path / "streams" / f"{stream_name}.csv"
            
            if not stream_file.exists():
                return []
            
            df = pd.read_csv(stream_file)
            
            # Return most recent records
            if 'timestamp' in df.columns:
                df = df.sort_values('timestamp', ascending=False)
            
            return df.head(limit).to_dict('records')
            
        except Exception as e:
            logger.error(f"Error querying stream {stream_name}: {e}")
            return []

# Create global instance
realtime_pathway_service = RealTimePathwayService()
