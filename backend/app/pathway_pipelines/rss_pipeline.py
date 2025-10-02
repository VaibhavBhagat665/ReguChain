"""
Pathway RSS Regulatory Feeds Pipeline
Continuous ingestion of SEC, CFTC, FINRA RSS feeds
"""
import pathway as pw
import feedparser
import requests
from datetime import datetime
from typing import Dict, Any, List
import logging
from ..config import SEC_RSS_URL, CFTC_RSS_URL, FINRA_RSS_URL

logger = logging.getLogger(__name__)

class RSSPathwayPipeline:
    """Pathway-powered RSS regulatory feeds ingestion"""
    
    def __init__(self):
        self.feeds = {
            "SEC": SEC_RSS_URL,
            "CFTC": CFTC_RSS_URL,
            "FINRA": FINRA_RSS_URL
        }
        self.seen_items = set()
        
    def create_rss_pipeline(self):
        """Create Pathway pipeline for RSS feeds"""
        
        @pw.udf
        def fetch_rss_feeds() -> pw.Table:
            """Fetch and parse all RSS feeds"""
            all_documents = []
            
            for source, url in self.feeds.items():
                if not url:
                    continue
                    
                try:
                    logger.info(f"🔍 Fetching {source} RSS feed...")
                    
                    # Fetch RSS feed
                    response = requests.get(url, timeout=30)
                    response.raise_for_status()
                    
                    # Parse RSS
                    feed = feedparser.parse(response.text)
                    
                    for entry in feed.entries:
                        # Create unique ID
                        item_id = f"{source.lower()}_{hash(entry.link)}"
                        
                        # Skip if already seen
                        if item_id in self.seen_items:
                            continue
                        
                        self.seen_items.add(item_id)
                        
                        # Extract content
                        title = entry.get('title', '')
                        summary = entry.get('summary', '')
                        link = entry.get('link', '')
                        published = entry.get('published', '')
                        
                        # Parse published date
                        try:
                            if published:
                                pub_date = datetime.strptime(published, '%a, %d %b %Y %H:%M:%S %Z')
                            else:
                                pub_date = datetime.now()
                        except:
                            pub_date = datetime.now()
                        
                        # Assess risk level
                        risk_level = self._assess_risk_level(title, summary)
                        
                        # Map source to friendly names
                        source_names = {
                            'SEC': 'Securities and Exchange Commission',
                            'CFTC': 'Commodity Futures Trading Commission', 
                            'FINRA': 'Financial Industry Regulatory Authority'
                        }
                        source_display = source_names.get(source, source)
                        
                        doc = {
                            'id': item_id,
                            'source': source_display,
                            'text': f"{source} Regulatory Update: {title} - {summary}",
                            'timestamp': datetime.now().isoformat(),
                            'link': link,
                            'type': 'regulatory_update',
                            'metadata': {
                                'title': title,
                                'summary': summary,
                                'published': pub_date.isoformat(),
                                'category': 'regulatory_update',
                                'risk_level': risk_level,
                                'source_agency': source
                            }
                        }
                        all_documents.append(doc)
                    
                    logger.info(f"✅ Fetched {len([d for d in all_documents if d['metadata'].get('source_agency') == source])} new items from {source}")
                    
                except Exception as e:
                    logger.error(f"❌ Error fetching {source} RSS feed: {e}")
                    continue
            
            logger.info(f"🎯 Total RSS documents: {len(all_documents)}")
            return pw.Table.from_pandas(pw.pandas.DataFrame(all_documents)) if all_documents else pw.Table.empty()
        
        # Create periodic trigger every 5 minutes
        trigger = pw.io.http.rest_connector(
            host="localhost",
            port=8080,
            route="/trigger/rss_feeds",
            schema=pw.Schema.from_types(trigger=str),
            autocommit_duration_ms=300000  # 5 minutes
        )
        
        # Transform trigger into RSS data
        rss_data = trigger.select(
            data=fetch_rss_feeds()
        ).flatten(pw.this.data)
        
        # Add processing metadata
        rss_data = rss_data.select(
            *pw.this,
            processed_at=datetime.now().isoformat(),
            pipeline_type='rss_regulatory'
        )
        
        return rss_data
    
    def _assess_risk_level(self, title: str, summary: str) -> str:
        """Assess risk level based on content"""
        content = f"{title} {summary}".lower()
        
        high_risk_keywords = [
            'enforcement', 'penalty', 'fine', 'violation', 'sanctions',
            'fraud', 'investigation', 'cease and desist', 'suspension'
        ]
        
        medium_risk_keywords = [
            'guidance', 'rule', 'regulation', 'compliance', 'warning',
            'advisory', 'notice', 'requirement'
        ]
        
        if any(keyword in content for keyword in high_risk_keywords):
            return 'high'
        elif any(keyword in content for keyword in medium_risk_keywords):
            return 'medium'
        else:
            return 'low'
    
    def fetch_real_data(self) -> List[Dict]:
        """Fetch real RSS data without Pathway connectors"""
        all_documents = []
        
        for source, url in self.feeds.items():
            if not url:
                continue
                
            try:
                logger.info(f"🔍 Fetching {source} RSS feed...")
                
                # Fetch RSS feed
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                
                # Parse RSS
                feed = feedparser.parse(response.text)
                
                for entry in feed.entries:
                    # Create unique ID
                    item_id = f"{source.lower()}_{hash(entry.link)}"
                    
                    # Skip if already seen
                    if item_id in self.seen_items:
                        continue
                    
                    self.seen_items.add(item_id)
                    
                    # Extract content
                    title = entry.get('title', '')
                    summary = entry.get('summary', '')
                    link = entry.get('link', '')
                    published = entry.get('published', '')
                    
                    # Parse published date
                    try:
                        if published:
                            pub_date = datetime.strptime(published, '%a, %d %b %Y %H:%M:%S %Z')
                        else:
                            pub_date = datetime.now()
                    except:
                        pub_date = datetime.now()
                    
                    # Assess risk level
                    risk_level = self._assess_risk_level(title, summary)
                    
                    content_text = f"{source} Regulatory Update: {title} - {summary}"
                    doc = {
                        'id': item_id,
                        'source': f"{source}_RSS",
                        'content': content_text,
                        'text': content_text,  # For compatibility
                        'timestamp': datetime.now().isoformat(),
                        'link': link,
                        'type': 'regulatory_update',
                        'metadata': {
                            'title': title,
                            'summary': summary,
                            'published': pub_date.isoformat(),
                            'category': 'regulatory_update',
                            'risk_level': risk_level,
                            'source': f"{source}_RSS"
                        }
                    }
                    all_documents.append(doc)
                
                logger.info(f"✅ Fetched {len([d for d in all_documents if d['source'].startswith(source)])} new items from {source}")
                
            except Exception as e:
                logger.error(f"❌ Error fetching {source} RSS feed: {e}")
                continue
        
        logger.info(f"🎯 Total RSS documents: {len(all_documents)}")
        return all_documents

# Global instance
rss_pathway_pipeline = RSSPathwayPipeline()
