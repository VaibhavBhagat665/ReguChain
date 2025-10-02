"""
Pathway News Pipeline
Continuous ingestion of regulatory news via NewsData.io
"""
import pathway as pw
import requests
from datetime import datetime
from typing import Dict, Any, List
import logging
from ..config import NEWSAPI_ENDPOINT, NEWSAPI_KEY

logger = logging.getLogger(__name__)

class NewsPathwayPipeline:
    """Pathway-powered news ingestion via NewsData.io"""
    
    def __init__(self):
        self.api_endpoint = NEWSAPI_ENDPOINT
        self.api_key = NEWSAPI_KEY
        self.seen_articles = set()
        
        # Search queries for regulatory news
        self.queries = [
            "sanctions cryptocurrency",
            "OFAC blockchain",
            "crypto fraud enforcement",
            "SEC cryptocurrency regulation",
            "CFTC digital assets",
            "FinCEN virtual currency",
            "regulatory compliance blockchain"
        ]
    
    def create_news_pipeline(self):
        """Create Pathway pipeline for news feeds"""
        
        @pw.udf
        def fetch_news_data() -> pw.Table:
            """Fetch news for all regulatory queries"""
            if not self.api_key:
                logger.warning("⚠️ NewsAPI key not configured, skipping news ingestion")
                return pw.Table.empty()
            
            all_documents = []
            
            for query in self.queries:
                try:
                    logger.info(f"🔍 Fetching news for query: {query}")
                    
                    params = {
                        'apikey': self.api_key,
                        'q': query,
                        'language': 'en',
                        'category': 'business,politics',
                        'size': 10,
                        'timeframe': '24h'
                    }
                    
                    response = requests.get(self.api_endpoint, params=params, timeout=30)
                    response.raise_for_status()
                    
                    data = response.json()
                    articles = data.get('results', [])
                    
                    for article in articles:
                        # Create unique ID
                        article_id = f"news_{hash(article.get('link', ''))}"
                        
                        # Skip if already seen
                        if article_id in self.seen_articles:
                            continue
                        
                        self.seen_articles.add(article_id)
                        
                        title = article.get('title', '')
                        description = article.get('description', '')
                        content = article.get('content', '')
                        link = article.get('link', '')
                        pub_date = article.get('pubDate', '')
                        source = article.get('source_id', '')
                        
                        # Combine content
                        full_content = f"{title} {description} {content}".strip()
                        
                        # Assess risk and sentiment
                        risk_level = self._assess_risk_level(full_content)
                        sentiment = self._assess_sentiment(full_content)
                        
                        doc = {
                            'id': article_id,
                            'source': 'NEWS_API',
                            'text': f"Regulatory News: {full_content}",
                            'timestamp': datetime.now().isoformat(),
                            'link': link,
                            'type': 'regulatory_news',
                            'metadata': {
                                'title': title,
                                'description': description,
                                'published': pub_date,
                                'news_source': source,
                                'query': query,
                                'category': 'regulatory_news',
                                'risk_level': risk_level,
                                'sentiment': sentiment
                            }
                        }
                        all_documents.append(doc)
                    
                    logger.info(f"✅ Fetched {len([d for d in all_documents if d['metadata']['query'] == query])} new articles for '{query}'")
                    
                except Exception as e:
                    logger.error(f"❌ Error fetching news for '{query}': {e}")
                    continue
            
            logger.info(f"🎯 Total news documents: {len(all_documents)}")
            return pw.Table.from_pandas(pw.pandas.DataFrame(all_documents)) if all_documents else pw.Table.empty()
        
        # Create periodic trigger every 10 minutes
        trigger = pw.io.http.rest_connector(
            host="localhost",
            port=8080,
            route="/trigger/news_feeds",
            schema=pw.Schema.from_types(trigger=str),
            autocommit_duration_ms=600000  # 10 minutes
        )
        
        # Transform trigger into news data
        news_data = trigger.select(
            data=fetch_news_data()
        ).flatten(pw.this.data)
        
        # Add processing metadata
        news_data = news_data.select(
            *pw.this,
            processed_at=datetime.now().isoformat(),
            pipeline_type='news_regulatory'
        )
        
        return news_data
    
    def _assess_risk_level(self, content: str) -> str:
        """Assess risk level based on content"""
        content_lower = content.lower()
        
        critical_keywords = [
            'enforcement action', 'criminal charges', 'fraud investigation',
            'sanctions imposed', 'license revoked', 'cease operations'
        ]
        
        high_risk_keywords = [
            'enforcement', 'penalty', 'fine', 'violation', 'sanctions',
            'fraud', 'investigation', 'lawsuit', 'prosecution'
        ]
        
        medium_risk_keywords = [
            'regulation', 'compliance', 'guidance', 'warning',
            'advisory', 'requirement', 'oversight'
        ]
        
        if any(keyword in content_lower for keyword in critical_keywords):
            return 'critical'
        elif any(keyword in content_lower for keyword in high_risk_keywords):
            return 'high'
        elif any(keyword in content_lower for keyword in medium_risk_keywords):
            return 'medium'
        else:
            return 'low'
    
    def _assess_sentiment(self, content: str) -> str:
        """Assess sentiment of the news"""
        content_lower = content.lower()
        
        negative_keywords = [
            'ban', 'prohibition', 'crackdown', 'investigation', 'fraud',
            'penalty', 'fine', 'violation', 'illegal', 'unauthorized'
        ]
        
        positive_keywords = [
            'approval', 'support', 'framework', 'clarity', 'guidance',
            'partnership', 'innovation', 'adoption', 'legitimate'
        ]
        
        negative_count = sum(1 for keyword in negative_keywords if keyword in content_lower)
        positive_count = sum(1 for keyword in positive_keywords if keyword in content_lower)
        
        if negative_count > positive_count:
            return 'negative'
        elif positive_count > negative_count:
            return 'positive'
        else:
            return 'neutral'
    
    def fetch_real_data(self) -> List[Dict]:
        """Fetch real news data without Pathway connectors"""
        if not self.api_key:
            logger.warning("⚠️ NewsAPI key not configured, skipping news ingestion")
            return []
        
        all_documents = []
        
        for query in self.queries:
            try:
                logger.info(f"🔍 Fetching news for query: {query}")
                
                params = {
                    'apikey': self.api_key,
                    'q': query,
                    'language': 'en',
                    'category': 'business,politics',
                    'size': 10,
                    'timeframe': '24h'
                }
                
                response = requests.get(self.api_endpoint, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                articles = data.get('results', [])
                
                for article in articles:
                    # Create unique ID
                    article_id = f"news_{hash(article.get('link', ''))}"
                    
                    # Skip if already seen
                    if article_id in self.seen_articles:
                        continue
                    
                    self.seen_articles.add(article_id)
                    
                    title = article.get('title', '')
                    description = article.get('description', '')
                    content = article.get('content', '')
                    link = article.get('link', '')
                    pub_date = article.get('pubDate', '')
                    source = article.get('source_id', '')
                    
                    # Combine content
                    full_content = f"{title} {description} {content}".strip()
                    
                    # Assess risk and sentiment
                    risk_level = self._assess_risk_level(full_content)
                    sentiment = self._assess_sentiment(full_content)
                    
                    content_text = f"Regulatory News: {full_content}"
                    doc = {
                        'id': article_id,
                        'source': 'NEWS_API',
                        'content': content_text,
                        'text': content_text,  # For compatibility
                        'timestamp': datetime.now().isoformat(),
                        'link': link,
                        'type': 'regulatory_news',
                        'metadata': {
                            'title': title,
                            'description': description,
                            'published': pub_date,
                            'news_source': source,
                            'query': query,
                            'category': 'regulatory_news',
                            'risk_level': risk_level,
                            'sentiment': sentiment,
                            'source': 'NEWS_API'
                        }
                    }
                    all_documents.append(doc)
                
                logger.info(f"✅ Fetched {len([d for d in all_documents if d['metadata']['query'] == query])} new articles for '{query}'")
                
            except Exception as e:
                logger.error(f"❌ Error fetching news for '{query}': {e}")
                continue
        
        logger.info(f"🎯 Total news documents: {len(all_documents)}")
        return all_documents

# Global instance
news_pathway_pipeline = NewsPathwayPipeline()
