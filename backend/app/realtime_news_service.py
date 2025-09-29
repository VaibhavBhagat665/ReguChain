"""
Real-time News Service using News API for Pathway integration
"""
import asyncio
import logging
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, AsyncGenerator
import aiohttp
import requests
from dataclasses import dataclass, asdict
from newsapi import NewsApiClient

from .config import NEWSAPI_KEY, GOOGLE_API_KEY

logger = logging.getLogger(__name__)

@dataclass
class NewsArticle:
    """News article data structure"""
    id: str
    title: str
    description: str
    content: str
    url: str
    source: str
    author: str
    published_at: str
    category: str
    sentiment: str
    relevance_score: float
    keywords: List[str]
    entities: List[str]
    
    def to_dict(self) -> Dict:
        return asdict(self)

class RealTimeNewsService:
    """Real-time news service using News API"""
    
    def __init__(self):
        self.api_key = NEWSAPI_KEY
        self.gemini_api_key = GOOGLE_API_KEY
        self.client = None
        self.session = None
        
        # Initialize News API client if key is available
        if self.api_key:
            try:
                self.client = NewsApiClient(api_key=self.api_key)
                logger.info("News API client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize News API client: {e}")
        
        # Initialize Gemini for analysis
        if self.gemini_api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.gemini_api_key)
                self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
                logger.info("Gemini API initialized for news analysis")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini API: {e}")
                self.gemini_model = None
        else:
            self.gemini_model = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def fetch_realtime_news(self, 
                                 query: str = "cryptocurrency OR blockchain OR DeFi OR regulatory OR compliance",
                                 sources: Optional[str] = None,
                                 language: str = "en",
                                 sort_by: str = "publishedAt",
                                 page_size: int = 100) -> List[NewsArticle]:
        """Fetch real-time news from News API"""
        if not self.client:
            logger.warning("News API client not initialized - using mock data")
            return await self._generate_mock_news()
        
        try:
            # Fetch everything endpoint for real-time news
            articles_response = self.client.get_everything(
                q=query,
                sources=sources,
                language=language,
                sort_by=sort_by,
                page_size=page_size,
                from_param=(datetime.now() - timedelta(hours=24)).isoformat()
            )
            
            if articles_response['status'] != 'ok':
                logger.error(f"News API error: {articles_response.get('message', 'Unknown error')}")
                return []
            
            articles = []
            for article_data in articles_response['articles']:
                try:
                    # Process each article with AI analysis
                    processed_article = await self._process_article(article_data)
                    if processed_article:
                        articles.append(processed_article)
                except Exception as e:
                    logger.error(f"Error processing article: {e}")
                    continue
            
            logger.info(f"Fetched and processed {len(articles)} articles from News API")
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching news from API: {e}")
            return await self._generate_mock_news()
    
    async def fetch_top_headlines(self,
                                 category: str = "business",
                                 country: str = "us",
                                 page_size: int = 50) -> List[NewsArticle]:
        """Fetch top headlines from News API"""
        if not self.client:
            return await self._generate_mock_news()
        
        try:
            headlines_response = self.client.get_top_headlines(
                category=category,
                country=country,
                page_size=page_size
            )
            
            if headlines_response['status'] != 'ok':
                logger.error(f"News API error: {headlines_response.get('message', 'Unknown error')}")
                return []
            
            articles = []
            for article_data in headlines_response['articles']:
                try:
                    processed_article = await self._process_article(article_data)
                    if processed_article:
                        articles.append(processed_article)
                except Exception as e:
                    logger.error(f"Error processing headline: {e}")
                    continue
            
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching headlines: {e}")
            return []
    
    async def _process_article(self, article_data: Dict) -> Optional[NewsArticle]:
        """Process raw article data with AI analysis"""
        try:
            # Extract basic information
            title = article_data.get('title', '')
            description = article_data.get('description', '') or ''
            content = article_data.get('content', '') or description
            url = article_data.get('url', '')
            source_name = article_data.get('source', {}).get('name', 'Unknown')
            author = article_data.get('author', '') or 'Unknown'
            published_at = article_data.get('publishedAt', datetime.now().isoformat())
            
            # Skip articles with insufficient content
            if not title or len(title) < 10:
                return None
            
            # Generate unique ID
            article_id = f"news_{hash(url)}_{int(time.time())}"
            
            # AI-powered analysis
            analysis = await self._analyze_with_gemini(title, description, content)
            
            return NewsArticle(
                id=article_id,
                title=title,
                description=description,
                content=content,
                url=url,
                source=source_name,
                author=author,
                published_at=published_at,
                category=analysis.get('category', 'general'),
                sentiment=analysis.get('sentiment', 'neutral'),
                relevance_score=analysis.get('relevance_score', 0.5),
                keywords=analysis.get('keywords', []),
                entities=analysis.get('entities', [])
            )
            
        except Exception as e:
            logger.error(f"Error processing article: {e}")
            return None
    
    async def _analyze_with_gemini(self, title: str, description: str, content: str) -> Dict:
        """Analyze article content using Gemini AI"""
        if not self.gemini_model:
            return self._basic_analysis(title, description, content)
        
        try:
            # Prepare analysis prompt
            text_to_analyze = f"Title: {title}\nDescription: {description}\nContent: {content[:1000]}"
            
            prompt = f"""
            Analyze this news article for regulatory and compliance relevance:
            
            {text_to_analyze}
            
            Provide analysis in JSON format:
            {{
                "category": "regulatory|compliance|enforcement|guidance|technology|general",
                "sentiment": "positive|negative|neutral",
                "relevance_score": 0.0-1.0,
                "keywords": ["keyword1", "keyword2", ...],
                "entities": ["entity1", "entity2", ...],
                "regulatory_impact": "high|medium|low|none",
                "affected_sectors": ["sector1", "sector2", ...],
                "urgency": "critical|high|medium|low"
            }}
            
            Focus on cryptocurrency, blockchain, DeFi, regulatory compliance, and financial technology topics.
            """
            
            response = self.gemini_model.generate_content(prompt)
            
            # Parse JSON response
            try:
                analysis = json.loads(response.text.strip())
                return analysis
            except json.JSONDecodeError:
                logger.warning("Failed to parse Gemini JSON response, using basic analysis")
                return self._basic_analysis(title, description, content)
                
        except Exception as e:
            logger.error(f"Error in Gemini analysis: {e}")
            return self._basic_analysis(title, description, content)
    
    def _basic_analysis(self, title: str, description: str, content: str) -> Dict:
        """Basic keyword-based analysis as fallback"""
        text = f"{title} {description} {content}".lower()
        
        # Category detection
        category_keywords = {
            'regulatory': ['regulation', 'regulatory', 'sec', 'cftc', 'finra', 'compliance'],
            'enforcement': ['enforcement', 'penalty', 'fine', 'violation', 'lawsuit'],
            'compliance': ['compliance', 'aml', 'kyc', 'sanctions', 'ofac'],
            'technology': ['blockchain', 'cryptocurrency', 'defi', 'nft', 'smart contract']
        }
        
        category = 'general'
        for cat, keywords in category_keywords.items():
            if any(keyword in text for keyword in keywords):
                category = cat
                break
        
        # Sentiment analysis (basic)
        positive_words = ['growth', 'adoption', 'approval', 'partnership', 'innovation']
        negative_words = ['ban', 'penalty', 'violation', 'crash', 'hack', 'fraud']
        
        pos_count = sum(1 for word in positive_words if word in text)
        neg_count = sum(1 for word in negative_words if word in text)
        
        if pos_count > neg_count:
            sentiment = 'positive'
        elif neg_count > pos_count:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        # Relevance score
        relevance_keywords = ['crypto', 'blockchain', 'defi', 'regulatory', 'compliance', 'sec', 'cftc']
        relevance_score = min(sum(0.2 for keyword in relevance_keywords if keyword in text), 1.0)
        
        # Extract keywords
        keywords = []
        for keyword in relevance_keywords:
            if keyword in text:
                keywords.append(keyword)
        
        return {
            'category': category,
            'sentiment': sentiment,
            'relevance_score': relevance_score,
            'keywords': keywords,
            'entities': [],
            'regulatory_impact': 'medium' if relevance_score > 0.5 else 'low',
            'affected_sectors': ['cryptocurrency'] if 'crypto' in text else [],
            'urgency': 'medium' if category in ['regulatory', 'enforcement'] else 'low'
        }
    
    async def stream_news_continuously(self, 
                                     interval_seconds: int = 300,
                                     query: str = "cryptocurrency OR blockchain OR regulatory") -> AsyncGenerator[List[NewsArticle], None]:
        """Continuously stream news updates"""
        logger.info(f"Starting continuous news stream with {interval_seconds}s intervals")
        
        while True:
            try:
                # Fetch latest news
                articles = await self.fetch_realtime_news(query=query)
                
                if articles:
                    logger.info(f"Streaming {len(articles)} new articles")
                    yield articles
                else:
                    logger.warning("No articles fetched in this cycle")
                
                # Wait for next cycle
                await asyncio.sleep(interval_seconds)
                
            except Exception as e:
                logger.error(f"Error in news streaming: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    async def _generate_mock_news(self) -> List[NewsArticle]:
        """Generate mock news data for testing"""
        mock_articles = [
            NewsArticle(
                id=f"mock_{int(time.time())}_1",
                title="SEC Announces New Cryptocurrency Enforcement Guidelines",
                description="The Securities and Exchange Commission has released comprehensive guidelines for cryptocurrency enforcement actions.",
                content="The SEC today announced new enforcement guidelines that will impact how cryptocurrency exchanges operate in the United States...",
                url="https://example.com/sec-crypto-guidelines",
                source="SEC.gov",
                author="SEC Press Office",
                published_at=datetime.now().isoformat(),
                category="regulatory",
                sentiment="neutral",
                relevance_score=0.95,
                keywords=["SEC", "cryptocurrency", "enforcement", "guidelines"],
                entities=["SEC", "cryptocurrency exchanges"]
            ),
            NewsArticle(
                id=f"mock_{int(time.time())}_2",
                title="Major DeFi Protocol Implements Enhanced Compliance Measures",
                description="Leading decentralized finance protocol announces new AML and KYC compliance features.",
                content="In response to regulatory pressure, the DeFi protocol has implemented comprehensive compliance measures...",
                url="https://example.com/defi-compliance",
                source="CryptoNews",
                author="Jane Smith",
                published_at=(datetime.now() - timedelta(hours=2)).isoformat(),
                category="compliance",
                sentiment="positive",
                relevance_score=0.88,
                keywords=["DeFi", "compliance", "AML", "KYC"],
                entities=["DeFi protocol", "regulatory authorities"]
            ),
            NewsArticle(
                id=f"mock_{int(time.time())}_3",
                title="CFTC Issues Warning on Unregistered Crypto Derivatives",
                description="Commodity Futures Trading Commission warns against trading unregistered cryptocurrency derivatives.",
                content="The CFTC has issued a public warning regarding the risks of trading unregistered cryptocurrency derivatives...",
                url="https://example.com/cftc-warning",
                source="CFTC.gov",
                author="CFTC Communications",
                published_at=(datetime.now() - timedelta(hours=4)).isoformat(),
                category="enforcement",
                sentiment="negative",
                relevance_score=0.92,
                keywords=["CFTC", "derivatives", "warning", "unregistered"],
                entities=["CFTC", "cryptocurrency derivatives"]
            )
        ]
        
        logger.info(f"Generated {len(mock_articles)} mock articles")
        return mock_articles
    
    async def get_regulatory_sources_news(self) -> List[NewsArticle]:
        """Fetch news specifically from regulatory sources"""
        regulatory_sources = [
            "sec.gov",
            "cftc.gov",
            "treasury.gov",
            "federalreserve.gov"
        ]
        
        all_articles = []
        
        for source in regulatory_sources:
            try:
                articles = await self.fetch_realtime_news(
                    query="cryptocurrency OR blockchain OR digital assets",
                    sources=source
                )
                all_articles.extend(articles)
            except Exception as e:
                logger.error(f"Error fetching from {source}: {e}")
        
        return all_articles

# Create global instance
realtime_news_service = RealTimeNewsService()
