"""
Real-time news service using NewsData.io API
"""
import logging
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import feedparser
from bs4 import BeautifulSoup

from .config import NEWSAPI_KEY

logger = logging.getLogger(__name__)

class NewsService:
    """Service for fetching real-time regulatory news"""
    
    def __init__(self):
        self.newsdata_api_key = NEWSAPI_KEY
        self.newsdata_base_url = "https://newsdata.io/api/1/news"
        self.categories = ["business", "politics", "technology"]
        self.keywords = [
            "SEC", "CFTC", "regulatory", "compliance", "cryptocurrency",
            "blockchain", "bitcoin", "ethereum", "DeFi", "stablecoin",
            "financial regulation", "AML", "KYC", "sanctions", "OFAC",
            "crypto regulation", "digital assets", "web3", "smart contracts"
        ]
        
        # RSS feeds for regulatory bodies
        self.rss_feeds = {
            "SEC": "https://www.sec.gov/rss/litigation/litreleases.xml",
            "CFTC": "https://www.cftc.gov/RSS/cftcrss.xml",
            "Treasury": "https://www.treasury.gov/rss/PRESS.XML",
            "Federal Reserve": "https://www.federalreserve.gov/feeds/press_all.xml",
            "OCC": "https://www.occ.gov/rss/news-issuances.xml",
            "FINRA": "https://www.finra.org/rss/news/all",
            "DOJ": "https://www.justice.gov/feeds/opa/justice-news.xml"
        }
    
    async def fetch_newsdata_articles(self, query: Optional[str] = None, 
                                     category: Optional[str] = None,
                                     from_date: Optional[str] = None) -> List[Dict]:
        """Fetch articles from NewsData.io API"""
        articles = []
        
        if not self.newsdata_api_key:
            logger.warning("NewsData API key not configured")
            return articles
        
        try:
            params = {
                "apikey": self.newsdata_api_key,
                "language": "en",
                "country": "us"
            }
            
            # Add search query
            if query:
                params["q"] = query
            else:
                # Use default crypto/regulatory keywords
                params["q"] = " OR ".join(self.keywords[:5])  # Limit keywords
            
            # Add category filter
            if category:
                params["category"] = category
            
            # Add date filter (last 7 days if not specified)
            if from_date:
                params["from_date"] = from_date
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.newsdata_base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get("status") == "success":
                            for article in data.get("results", []):
                                articles.append({
                                    "title": article.get("title", ""),
                                    "description": article.get("description", ""),
                                    "content": article.get("content", ""),
                                    "url": article.get("link", ""),
                                    "source": article.get("source_id", ""),
                                    "published_at": article.get("pubDate", ""),
                                    "category": article.get("category", []),
                                    "keywords": article.get("keywords", []),
                                    "image_url": article.get("image_url", ""),
                                    "sentiment": article.get("sentiment", "neutral"),
                                    "api_source": "newsdata"
                                })
                            logger.info(f"Fetched {len(articles)} articles from NewsData.io")
                        else:
                            logger.error(f"NewsData API error: {data.get('message', 'Unknown error')}")
                    else:
                        logger.error(f"NewsData API HTTP error: {response.status}")
                        
        except Exception as e:
            logger.error(f"Error fetching NewsData articles: {e}")
        
        return articles
    
    async def fetch_rss_feeds(self) -> List[Dict]:
        """Fetch articles from regulatory RSS feeds"""
        articles = []
        
        for source, feed_url in self.rss_feeds.items():
            try:
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries[:10]:  # Limit to 10 recent entries per feed
                    # Clean HTML from description
                    description = entry.get("summary", "")
                    if description:
                        soup = BeautifulSoup(description, "html.parser")
                        description = soup.get_text()
                    
                    articles.append({
                        "title": entry.get("title", ""),
                        "description": description[:500],  # Limit description length
                        "content": description,
                        "url": entry.get("link", ""),
                        "source": source,
                        "published_at": entry.get("published", ""),
                        "category": ["regulatory", "government"],
                        "keywords": self._extract_keywords(entry.get("title", "") + " " + description),
                        "image_url": "",
                        "sentiment": "neutral",
                        "api_source": "rss"
                    })
                
                logger.info(f"Fetched {len(feed.entries[:10])} articles from {source} RSS")
                
            except Exception as e:
                logger.error(f"Error fetching RSS feed from {source}: {e}")
        
        return articles
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords from text"""
        found_keywords = []
        text_lower = text.lower()
        
        for keyword in self.keywords:
            if keyword.lower() in text_lower:
                found_keywords.append(keyword)
        
        return found_keywords[:5]  # Return top 5 keywords
    
    async def search_news(self, query: str, include_rss: bool = True) -> List[Dict]:
        """Search for news articles with a specific query"""
        all_articles = []
        
        # Fetch from NewsData API
        newsdata_articles = await self.fetch_newsdata_articles(query=query)
        all_articles.extend(newsdata_articles)
        
        # Fetch from RSS feeds if requested
        if include_rss:
            rss_articles = await self.fetch_rss_feeds()
            # Filter RSS articles by query
            query_lower = query.lower()
            filtered_rss = [
                article for article in rss_articles
                if query_lower in article["title"].lower() or 
                   query_lower in article["description"].lower()
            ]
            all_articles.extend(filtered_rss)
        
        # Sort by publication date (most recent first)
        all_articles.sort(key=lambda x: x.get("published_at", ""), reverse=True)
        
        return all_articles
    
    async def get_regulatory_updates(self, hours: int = 24) -> List[Dict]:
        """Get recent regulatory updates from all sources"""
        all_articles = []
        
        # Calculate date filter
        from_date = (datetime.utcnow() - timedelta(hours=hours)).strftime("%Y-%m-%d")
        
        # Fetch from NewsData API with regulatory keywords
        for keyword in ["SEC", "CFTC", "regulatory compliance", "cryptocurrency regulation"]:
            articles = await self.fetch_newsdata_articles(
                query=keyword,
                category="business",
                from_date=from_date
            )
            all_articles.extend(articles)
            
            # Respect API rate limits
            await asyncio.sleep(1)
        
        # Fetch from RSS feeds
        rss_articles = await self.fetch_rss_feeds()
        all_articles.extend(rss_articles)
        
        # Remove duplicates based on URL
        seen_urls = set()
        unique_articles = []
        for article in all_articles:
            if article["url"] not in seen_urls:
                seen_urls.add(article["url"])
                unique_articles.append(article)
        
        # Sort by publication date
        unique_articles.sort(key=lambda x: x.get("published_at", ""), reverse=True)
        
        logger.info(f"Collected {len(unique_articles)} unique regulatory updates")
        
        return unique_articles
    
    async def analyze_sentiment(self, articles: List[Dict]) -> Dict:
        """Analyze overall sentiment of articles"""
        sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
        
        for article in articles:
            sentiment = article.get("sentiment", "neutral").lower()
            if sentiment in sentiment_counts:
                sentiment_counts[sentiment] += 1
            else:
                sentiment_counts["neutral"] += 1
        
        total = sum(sentiment_counts.values())
        if total > 0:
            sentiment_percentages = {
                k: (v / total) * 100 for k, v in sentiment_counts.items()
            }
        else:
            sentiment_percentages = {"positive": 0, "negative": 0, "neutral": 100}
        
        return {
            "counts": sentiment_counts,
            "percentages": sentiment_percentages,
            "overall": max(sentiment_counts, key=sentiment_counts.get) if total > 0 else "neutral"
        }

# Create singleton instance
news_service = NewsService()
