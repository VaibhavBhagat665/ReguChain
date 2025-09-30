"""Data ingestion module for ReguChain Watch"""
import asyncio
import csv
import io
import json
import logging
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import aiohttp
import requests

from .config import (
    OFAC_SDN_URL, SEC_RSS_URL, CFTC_RSS_URL, FINRA_RSS_URL,
    NEWSAPI_KEY, NEWSAPI_ENDPOINT, ETHEREUM_RPC_URL
)
from .database import save_document, save_transaction
from .vector_store import vector_store
from .langchain_agent import langchain_agent
from .realtime_news_service import realtime_news_service

logger = logging.getLogger(__name__)

class DataIngester:
    """Handles data ingestion from multiple sources"""
    
    def __init__(self):
        self.sources = {
            "OFAC": self.ingest_ofac,
            "SEC": lambda: self.ingest_rss(SEC_RSS_URL, "SEC"),
            "CFTC": lambda: self.ingest_rss(CFTC_RSS_URL, "CFTC"),
            "FINRA": lambda: self.ingest_rss(FINRA_RSS_URL, "FINRA"),
            "NewsAPI": self.ingest_newsapi,
            "Blockchain": self.ingest_blockchain
        }
        self.ingestion_running = False
    
    async def ingest_ofac(self) -> List[Dict]:
        """Ingest OFAC SDN list"""
        documents = []
        try:
            response = requests.get(OFAC_SDN_URL, timeout=30)
            if response.status_code == 200:
                # Parse CSV
                csv_data = io.StringIO(response.text)
                reader = csv.DictReader(csv_data)
                
                count = 0
                for row in reader:
                    if count >= 100:  # Limit for demo
                        break
                    
                    # Extract relevant fields
                    name = row.get("SDN Name", "")
                    address = row.get("Address", "")
                    program = row.get("Program", "")
                    
                    if name:
                        text = f"OFAC Sanction: {name}"
                        if address:
                            text += f" - Address: {address}"
                        if program:
                            text += f" - Program: {program}"
                        
                        doc = {
                            "source": "OFAC",
                            "text": text,
                            "link": OFAC_SDN_URL,
                            "metadata": {
                                "name": name,
                                "address": address,
                                "program": program,
                                "type": "sanction"
                            }
                        }
                        documents.append(doc)
                        count += 1
                
                logger.info(f"Ingested {len(documents)} OFAC entries")
        except Exception as e:
            logger.error(f"Error ingesting OFAC data: {e}")
            # Return empty list on error; do not inject mock data
            documents = []
        
        return documents
    
    async def ingest_rss(self, url: str, source: str) -> List[Dict]:
        """Ingest RSS feed"""
        documents = []
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                
                # Find all items in the RSS feed
                items = root.findall(".//item")[:20]  # Limit to 20 items
                
                for item in items:
                    title = item.findtext("title", "")
                    description = item.findtext("description", "")
                    link = item.findtext("link", "")
                    pub_date = item.findtext("pubDate", "")
                    
                    if title or description:
                        text = f"{title}\n{description}"
                        doc = {
                            "source": source,
                            "text": text,
                            "link": link,
                            "metadata": {
                                "title": title,
                                "published": pub_date,
                                "type": "regulatory_news"
                            }
                        }
                        documents.append(doc)
                
                logger.info(f"Ingested {len(documents)} items from {source} RSS")
        except Exception as e:
            logger.error(f"Error ingesting RSS from {source}: {e}")
            # Return empty list on error; do not inject mock data
            documents = []
        
        return documents
    
    async def ingest_newsapi(self) -> List[Dict]:
        """Ingest news from NewsAPI.org or NewsData.io using realtime_news_service (real only)"""
        documents: List[Dict] = []
        try:
            async with realtime_news_service:
                articles = await realtime_news_service.fetch_realtime_news(
                    query="cryptocurrency OR blockchain OR SEC OR CFTC OR regulatory OR compliance",
                    page_size=50
                )
            for article in articles:
                text = f"{article.title}\n{article.description}\n{article.content or ''}"
                documents.append({
                    "source": article.source,
                    "text": text[:2000],
                    "link": article.url,
                    "metadata": {
                        "title": article.title,
                        "published": article.published_at,
                        "type": "news",
                        "keywords": article.keywords,
                        "sentiment": article.sentiment,
                        "api_source": getattr(realtime_news_service, 'api_type', 'unknown')
                    }
                })
            logger.info(f"Ingested {len(documents)} news articles from realtime_news_service")
        except Exception as e:
            logger.error(f"Error ingesting news data: {e}")
        return documents
    
    async def ingest_blockchain(self, addresses: List[str] = None) -> List[Dict]:
        """Ingest blockchain transaction data from real APIs only"""
        documents: List[Dict] = []
        try:
            # Require explicit addresses; do not use demo addresses
            if not addresses:
                return documents
            from .blockchain_service import blockchain_service
            for address in addresses:
                txs = await blockchain_service.get_transactions(address, limit=20)
                for tx in txs:
                    save_transaction(
                        tx.hash,
                        tx.from_address,
                        tx.to_address,
                        float(tx.value),
                        tx.timestamp
                    )
                    documents.append({
                        "source": "Blockchain",
                        "text": f"Transaction {tx.hash} from {tx.from_address} to {tx.to_address} for {tx.value} ETH",
                        "link": f"https://etherscan.io/tx/{tx.hash}",
                        "metadata": {
                            "tx_hash": tx.hash,
                            "from": tx.from_address,
                            "to": tx.to_address,
                            "amount": float(tx.value),
                            "timestamp": tx.timestamp,
                            "block_number": tx.block_number
                        }
                    })
            logger.info(f"Ingested {len(documents)} blockchain transactions from real APIs")
        except Exception as e:
            logger.error(f"Error ingesting blockchain data: {e}")
        return documents
    
    async def ingest_all(self) -> Dict:
        """Ingest data from all sources"""
        results = {}
        all_documents = []
        
        for source_name, ingest_func in self.sources.items():
            try:
                logger.info(f"Ingesting from {source_name}")
                docs = await ingest_func()
                results[source_name] = len(docs)
                all_documents.extend(docs)
            except Exception as e:
                logger.error(f"Error ingesting from {source_name}: {e}")
                results[source_name] = 0
        
        # Add documents to vector store
        if all_documents:
            texts = [doc["text"] for doc in all_documents]
            metadata = [doc for doc in all_documents]
            ids = vector_store.add_documents(texts, metadata)
            
            # Also add to LangChain knowledge base
            try:
                langchain_docs = [
                    {
                        "content": doc["text"],
                        "source": doc["source"],
                        "title": doc.get("metadata", {}).get("title", ""),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    for doc in all_documents
                ]
                langchain_agent.add_documents_to_knowledge_base(langchain_docs)
                logger.info(f"Added {len(langchain_docs)} documents to LangChain knowledge base")
            except Exception as e:
                logger.error(f"Error adding documents to LangChain: {e}")
            
            # Save to database
            for doc, embedding_id in zip(all_documents, ids):
                save_document(
                    source=doc["source"],
                    text=doc["text"],
                    link=doc.get("link", ""),
                    metadata=doc.get("metadata", {}),
                    embedding_id=embedding_id
                )
        
        logger.info(f"Total documents ingested: {len(all_documents)}")
        return {
            "sources": results,
            "total": len(all_documents),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    # Removed simulate_ingestion to enforce real-data only

# Global ingester instance
ingester = DataIngester()
