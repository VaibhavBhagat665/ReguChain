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
            # Add sample data for demo
            documents = [
                {
                    "source": "OFAC",
                    "text": "OFAC Sanction: Demo Sanctioned Entity - Address: 0xDEMO123 - Program: Cyber Sanctions",
                    "link": OFAC_SDN_URL,
                    "metadata": {"type": "sanction", "demo": True}
                }
            ]
        
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
            # Add sample data for demo
            documents = [
                {
                    "source": source,
                    "text": f"{source} Alert: New regulatory action against crypto exchange for AML violations",
                    "link": url,
                    "metadata": {"type": "regulatory_news", "demo": True}
                }
            ]
        
        return documents
    
    async def ingest_newsapi(self) -> List[Dict]:
        """Ingest news from NewsAPI"""
        documents = []
        
        if not NEWSAPI_KEY:
            logger.warning("NewsAPI key not configured, using sample data")
            return [
                {
                    "source": "NewsAPI",
                    "text": "Breaking: Major cryptocurrency exchange faces sanctions for compliance failures",
                    "link": "https://example.com/news",
                    "metadata": {"type": "news", "demo": True}
                }
            ]
        
        try:
            # Search for regulatory and crypto news
            keywords = ["sanction OR OFAC OR crypto hack OR DeFi exploit"]
            params = {
                "q": keywords,
                "apiKey": NEWSAPI_KEY,
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": 20
            }
            
            response = requests.get(NEWSAPI_ENDPOINT, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                articles = data.get("articles", [])
                
                for article in articles:
                    title = article.get("title", "")
                    description = article.get("description", "")
                    content = article.get("content", "")
                    url = article.get("url", "")
                    published = article.get("publishedAt", "")
                    
                    text = f"{title}\n{description}\n{content}"
                    doc = {
                        "source": "NewsAPI",
                        "text": text,
                        "link": url,
                        "metadata": {
                            "title": title,
                            "published": published,
                            "type": "news"
                        }
                    }
                    documents.append(doc)
                
                logger.info(f"Ingested {len(documents)} news articles")
        except Exception as e:
            logger.error(f"Error ingesting NewsAPI data: {e}")
        
        return documents
    
    async def ingest_blockchain(self, addresses: List[str] = None) -> List[Dict]:
        """Ingest blockchain transaction data"""
        documents = []
        
        # Default demo addresses
        if not addresses:
            addresses = ["0xDEMO0001", "0xDEMO0002"]
        
        try:
            # For demo, create sample transactions
            for address in addresses:
                # Simulate transactions
                tx_data = {
                    "tx_hash": f"0x{'a' * 64}",
                    "from": address,
                    "to": "0x" + "b" * 40,
                    "amount": 15000.0,  # Above threshold for demo
                    "timestamp": datetime.utcnow()
                }
                
                # Save to database
                save_transaction(
                    tx_data["tx_hash"],
                    tx_data["from"],
                    tx_data["to"],
                    tx_data["amount"],
                    tx_data["timestamp"]
                )
                
                # Create document
                text = f"Transaction from {tx_data['from']} to {tx_data['to']} for {tx_data['amount']} ETH"
                doc = {
                    "source": "Blockchain",
                    "text": text,
                    "link": f"https://etherscan.io/tx/{tx_data['tx_hash']}",
                    "metadata": tx_data
                }
                documents.append(doc)
            
            logger.info(f"Ingested {len(documents)} blockchain transactions")
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
    
    async def simulate_ingestion(self, target: str = None) -> Dict:
        """Simulate ingestion of a new sanction/news entry"""
        if not target:
            target = "0xDEMO" + "".join([str(i) for i in range(10)])
        
        # Create simulated documents
        simulated_docs = [
            {
                "source": "OFAC",
                "text": f"URGENT: New OFAC sanction added for wallet {target} - Linked to ransomware operations",
                "link": "https://www.treasury.gov/ofac/sanctions",
                "metadata": {
                    "type": "sanction",
                    "severity": "critical",
                    "wallet": target,
                    "simulated": True
                }
            },
            {
                "source": "NewsAPI",
                "text": f"Breaking News: Wallet {target} identified in major DeFi hack, $10M stolen",
                "link": "https://example.com/breaking-news",
                "metadata": {
                    "type": "news",
                    "severity": "high",
                    "wallet": target,
                    "simulated": True
                }
            }
        ]
        
        # Add to vector store
        texts = [doc["text"] for doc in simulated_docs]
        ids = vector_store.add_documents(texts, simulated_docs)
        
        # Save to database
        saved_docs = []
        for doc, embedding_id in zip(simulated_docs, ids):
            saved = save_document(
                source=doc["source"],
                text=doc["text"],
                link=doc.get("link", ""),
                metadata=doc.get("metadata", {}),
                embedding_id=embedding_id
            )
            saved_docs.append(saved.to_dict())
        
        logger.info(f"Simulated ingestion for target: {target}")
        
        return {
            "target": target,
            "documents_added": len(saved_docs),
            "documents": saved_docs,
            "timestamp": datetime.utcnow().isoformat(),
            "message": f"Successfully simulated sanctions for {target}"
        }

# Global ingester instance
ingester = DataIngester()
