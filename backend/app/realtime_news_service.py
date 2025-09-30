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

from .config import NEWSAPI_KEY, GROQ_API_KEY

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
        self.client = None
        self.session = None
        
        # Initialize News API client - Support both NewsAPI.org and NewsData.io
        if NEWSAPI_KEY:
            try:
                if NEWSAPI_KEY.startswith("pub_"):
                    # NewsData.io API key
                    self.api_type = "newsdata"
                    self.api_key = NEWSAPI_KEY
                    self.client = None  # Use direct HTTP requests for NewsData.io
                    logger.info("NewsData.io API key detected - using direct HTTP client")
                else:
                    # NewsAPI.org key
                    from newsapi import NewsApiClient
                    self.api_type = "newsapi"
                    self.client = NewsApiClient(api_key=NEWSAPI_KEY)
                    logger.info("NewsAPI.org client initialized successfully")
            except ImportError:
                logger.error("newsapi-python not installed. Install with: pip install newsapi-python")
                self.client = None
                self.api_type = "none"
            except Exception as e:
                logger.error(f"Error initializing News API client: {e}")
                self.client = None
                self.api_type = "none"
        else:
            logger.warning("No News API key provided")
            self.client = None
            self.api_type = "none"
        
        # Initialize Groq for analysis
        self.groq_api_key = GROQ_API_KEY
        if self.groq_api_key:
            try:
                from groq import Groq
                self.groq_client = Groq(api_key=self.groq_api_key)
                logger.info("Groq API initialized for news analysis")
            except Exception as e:
                logger.error(f"Failed to initialize Groq API: {e}")
                self.groq_client = None
        else:
            logger.warning("No Groq API key provided")
            self.groq_client = None
    
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
        """Fetch real-time news from News API or NewsData.io"""
        # NewsAPI.org client path
        if self.api_type == "newsapi":
            if not self.client:
                logger.error("News API client not initialized - missing NEWSAPI_KEY")
                return []
            try:
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
                articles: List[NewsArticle] = []
                for article_data in articles_response['articles']:
                    try:
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
                logger.warning("News API failed - returning empty list instead of fake data")
                return []
        
        # NewsData.io HTTP path
        if self.api_type == "newsdata":
            try:
                import aiohttp
                url = "https://newsdata.io/api/1/news"
                params = {
                    "apikey": self.api_key,
                    "q": query,
                    "language": language,
                    "page": 1
                }
                articles: List[NewsArticle] = []
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, params=params) as r:
                        data = await r.json()
                        for a in data.get('results', [])[:page_size]:
                            article_data = {
                                'title': a.get('title'),
                                'description': a.get('description'),
                                'content': a.get('content') or a.get('description') or '',
                                'url': a.get('link'),
                                'source': {'name': (a.get('source_id') or 'NewsData.io')},
                                'author': a.get('creator', ['Unknown'])[0] if a.get('creator') else 'Unknown',
                                'publishedAt': a.get('pubDate')
                            }
                            processed = await self._process_article(article_data)
                            if processed:
                                articles.append(processed)
                logger.info(f"Fetched and processed {len(articles)} articles from NewsData.io")
                return articles
            except Exception as e:
                logger.error(f"Error fetching news from NewsData.io: {e}")
                return []
        
        logger.error("Unknown news API type; ensure NEWSAPI_KEY is set correctly")
        return []

    async def fetch_top_headlines(
        self,
        category: str = "business",
        country: str = "us",
        page_size: int = 20
    ) -> List[NewsArticle]:
        """Fetch top headlines from the news provider"""
        if not self.client and self.api_type != "newsdata":
            logger.error("News API client not initialized - missing NEWSAPI_KEY")
            return []
        try:
            articles: List[NewsArticle] = []
            if self.api_type == "newsapi" and self.client:
                resp = self.client.get_top_headlines(category=category, country=country, page_size=page_size)
                if resp.get('status') != 'ok':
                    logger.error(f"News API error: {resp.get('message', 'Unknown error')}")
                    return []
                for article_data in resp.get('articles', []):
                    processed = await self._process_article(article_data)
                    if processed:
                        articles.append(processed)
                return articles
            elif self.api_type == "newsdata":
                # Minimal NewsData.io headlines via HTTP (category/country mapped best-effort)
                import aiohttp
                url = "https://newsdata.io/api/1/news"
                params = {
                    "apikey": self.api_key,
                    "category": category,
                    "country": country,
                    "language": "en",
                    "page": 1
                }
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, params=params) as r:
                        data = await r.json()
                        for a in data.get('results', [])[:page_size]:
                            article_data = {
                                'title': a.get('title'),
                                'description': a.get('description'),
                                'content': a.get('content') or a.get('description') or '',
                                'url': a.get('link'),
                                'source': {'name': (a.get('source_id') or 'NewsData.io')},
                                'author': a.get('creator', ['Unknown'])[0] if a.get('creator') else 'Unknown',
                                'publishedAt': a.get('pubDate')
                            }
                            processed = await self._process_article(article_data)
                            if processed:
                                articles.append(processed)
                return articles
            else:
                return []
        except Exception as e:
            logger.error(f"Error fetching top headlines: {e}")
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
            analysis = await self._analyze_with_groq(title, description, content)
            
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
    
    async def _analyze_with_groq(self, title: str, description: str, content: str) -> Dict:
        """Analyze article content using Groq AI"""
        if not self.groq_client:
            return self._basic_analysis(title, description, content)
        
        try:
            # Create analysis prompt
            prompt = f"""Analyze this news article and return ONLY a JSON response with this exact structure:
{{
    "category": "regulatory|compliance|defi|blockchain|general",
    "sentiment": "positive|negative|neutral", 
    "relevance_score": 0.0-1.0,
    "keywords": ["keyword1", "keyword2", "keyword3"],
    "entities": ["entity1", "entity2"]
}}

Article Title: {title}
Article Description: {description}
Article Content: {content[:500]}...

Focus on cryptocurrency, blockchain, DeFi, regulatory compliance, and financial technology topics.
Return ONLY the JSON, no other text."""
            
            response = self.groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a financial news analyst. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.1-8b-instant",
                temperature=0.1,
                max_tokens=500
            )
            
            # Parse JSON response
            try:
                analysis_text = response.choices[0].message.content.strip()
                # Remove any markdown formatting
                if analysis_text.startswith("```json"):
                    analysis_text = analysis_text.replace("```json", "").replace("```", "").strip()
                
                analysis = json.loads(analysis_text)
                return analysis
            except json.JSONDecodeError:
                logger.warning("Failed to parse Groq JSON response, using basic analysis")
                return self._basic_analysis(title, description, content)
                
        except Exception as e:
            logger.error(f"Error in Groq analysis: {e}")
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
