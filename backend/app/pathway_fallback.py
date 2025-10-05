"""
Pathway Fallback System for ReguChain
Works without Pathway license using pandas and asyncio
"""
import asyncio
import pandas as pd
import requests
import csv
import xml.etree.ElementTree as ET
import feedparser
from datetime import datetime
from typing import Dict, Any, List
import logging
import json

from .config import (
    OFAC_SDN_URL, OFAC_CONSOLIDATED_URL, SEC_RSS_URL, CFTC_RSS_URL, 
    FINRA_RSS_URL, NEWSAPI_ENDPOINT, NEWSAPI_KEY, ETHEREUM_RPC_URL, 
    POLYGON_RPC_URL, ETHERSCAN_API_KEY, TRANSACTION_THRESHOLD
)
from .openrouter_embeddings import embeddings_client
from .vector_store import vector_store
from .database import database

logger = logging.getLogger(__name__)

class PathwayFallbackManager:
    """Fallback implementation using pandas and asyncio"""
    
    def __init__(self):
        self.is_running = False
        self.stats = {
            'total_documents_processed': 0,
            'alerts_generated': 0,
            'last_update': None,
            'pipelines_status': {}
        }
        self.alerts_history = []
        self.target_wallets = set()
        self.seen_items = set()
        
    async def start_all_pipelines(self):
        """Start all fallback pipelines"""
        if self.is_running:
            logger.warning("⚠️ Pipelines already running")
            return
        
        logger.info("🚀 Starting Pathway fallback pipelines...")
        self.is_running = True
        
        # Start background tasks
        asyncio.create_task(self._run_ingestion_loop())
        logger.info("✅ Fallback pipelines started successfully")
    
    async def _run_ingestion_loop(self):
        """Main ingestion loop"""
        while self.is_running:
            try:
                # Run all ingestion tasks
                await self._ingest_ofac_data()
                await self._ingest_rss_feeds()
                await self._ingest_news_data()
                await self._ingest_blockchain_data()
                
                # Update stats
                self.stats['last_update'] = datetime.now().isoformat()
                
                # Wait before next cycle
                await asyncio.sleep(300)  # 5 minutes
                
            except Exception as e:
                logger.error(f"❌ Error in ingestion loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    async def _ingest_ofac_data(self):
        """Ingest OFAC sanctions data"""
        try:
            logger.info("🔍 Fetching OFAC data...")
            
            # Fetch SDN data
            response = requests.get(OFAC_SDN_URL, timeout=30)
            response.raise_for_status()
            
            csv_reader = csv.DictReader(response.text.splitlines())
            documents = []
            
            for row in csv_reader:
                doc_id = f"ofac_sdn_{row.get('ent_num', '')}"
                if doc_id in self.seen_items:
                    continue
                
                self.seen_items.add(doc_id)
                
                doc = {
                    'id': doc_id,
                    'source': 'OFAC_SDN',
                    'text': f"OFAC SDN Entry: {row.get('name', '')} - {row.get('title', '')}",
                    'timestamp': datetime.now().isoformat(),
                    'link': OFAC_SDN_URL,
                    'type': 'sanction',
                    'metadata': {
                        'entity_number': row.get('ent_num', ''),
                        'name': row.get('name', ''),
                        'title': row.get('title', ''),
                        'risk_level': 'high'
                    }
                }
                documents.append(doc)
            
            # Process documents
            await self._process_documents(documents, 'OFAC')
            logger.info(f"✅ Processed {len(documents)} OFAC documents")
            
        except Exception as e:
            logger.error(f"❌ Error ingesting OFAC data: {e}")
    
    async def _ingest_rss_feeds(self):
        """Ingest RSS regulatory feeds"""
        feeds = {
            "SEC": SEC_RSS_URL,
            "CFTC": CFTC_RSS_URL,
            "FINRA": FINRA_RSS_URL
        }
        
        all_documents = []
        
        for source, url in feeds.items():
            if not url:
                continue
                
            try:
                logger.info(f"🔍 Fetching {source} RSS feed...")
                
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                
                feed = feedparser.parse(response.text)
                
                for entry in feed.entries:
                    item_id = f"{source.lower()}_{hash(entry.link)}"
                    
                    if item_id in self.seen_items:
                        continue
                    
                    self.seen_items.add(item_id)
                    
                    title = entry.get('title', '')
                    summary = entry.get('summary', '')
                    
                    doc = {
                        'id': item_id,
                        'source': f"{source}_RSS",
                        'text': f"{source} Regulatory Update: {title} - {summary}",
                        'timestamp': datetime.now().isoformat(),
                        'link': entry.get('link', ''),
                        'type': 'regulatory_update',
                        'metadata': {
                            'title': title,
                            'summary': summary,
                            'risk_level': self._assess_risk_level(title, summary)
                        }
                    }
                    all_documents.append(doc)
                
            except Exception as e:
                logger.error(f"❌ Error fetching {source} RSS: {e}")
        
        await self._process_documents(all_documents, 'RSS')
        logger.info(f"✅ Processed {len(all_documents)} RSS documents")
    
    async def _ingest_news_data(self):
        """Ingest news data from NewsData.io"""
        if not NEWSAPI_KEY:
            return
        
        queries = [
            "sanctions cryptocurrency",
            "OFAC blockchain",
            "crypto fraud enforcement"
        ]
        
        all_documents = []
        
        for query in queries:
            try:
                params = {
                    'apikey': NEWSAPI_KEY,
                    'q': query,
                    'language': 'en',
                    'size': 5
                }
                
                response = requests.get(NEWSAPI_ENDPOINT, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                articles = data.get('results', [])
                
                for article in articles:
                    article_id = f"news_{hash(article.get('link', ''))}"
                    
                    if article_id in self.seen_items:
                        continue
                    
                    self.seen_items.add(article_id)
                    
                    title = article.get('title', '')
                    description = article.get('description', '')
                    
                    doc = {
                        'id': article_id,
                        'source': 'NEWS_API',
                        'text': f"Regulatory News: {title} {description}",
                        'timestamp': datetime.now().isoformat(),
                        'link': article.get('link', ''),
                        'type': 'regulatory_news',
                        'metadata': {
                            'title': title,
                            'description': description,
                            'query': query,
                            'risk_level': self._assess_risk_level(title, description)
                        }
                    }
                    all_documents.append(doc)
                
            except Exception as e:
                logger.error(f"❌ Error fetching news for '{query}': {e}")
        
        await self._process_documents(all_documents, 'NEWS')
        logger.info(f"✅ Processed {len(all_documents)} news documents")
    
    async def _ingest_blockchain_data(self):
        """Ingest blockchain transaction data"""
        if not ETHERSCAN_API_KEY or not self.target_wallets:
            return
        
        all_documents = []
        
        for wallet in list(self.target_wallets)[:3]:  # Limit to 3 wallets
            try:
                url = "https://api.etherscan.io/api"
                params = {
                    'module': 'account',
                    'action': 'txlist',
                    'address': wallet,
                    'startblock': 0,
                    'endblock': 99999999,
                    'page': 1,
                    'offset': 10,
                    'sort': 'desc',
                    'apikey': ETHERSCAN_API_KEY
                }
                
                response = requests.get(url, params=params, timeout=15)
                response.raise_for_status()
                
                data = response.json()
                if data.get('status') != '1':
                    continue
                
                transactions = data.get('result', [])
                
                for tx in transactions:
                    tx_hash = tx.get('hash', '')
                    tx_id = f"etherscan_tx_{tx_hash}"
                    
                    if tx_id in self.seen_items:
                        continue
                    
                    self.seen_items.add(tx_id)
                    
                    from_addr = tx.get('from', '').lower()
                    to_addr = tx.get('to', '').lower()
                    value_wei = int(tx.get('value', '0'))
                    value_eth = value_wei / 10**18
                    
                    doc = {
                        'id': tx_id,
                        'source': 'ETHERSCAN_API',
                        'text': f"Ethereum Transaction: {from_addr} -> {to_addr} ({value_eth:.4f} ETH)",
                        'timestamp': datetime.fromtimestamp(int(tx.get('timeStamp', 0))).isoformat(),
                        'link': f"https://etherscan.io/tx/{tx_hash}",
                        'type': 'wallet_transaction',
                        'metadata': {
                            'hash': tx_hash,
                            'from_address': from_addr,
                            'to_address': to_addr,
                            'value_eth': value_eth,
                            'target_wallet': wallet.lower(),
                            'onchain_match': True,
                            'risk_level': 'high' if value_eth > 100 else 'medium'
                        }
                    }
                    all_documents.append(doc)
                
            except Exception as e:
                logger.error(f"❌ Error fetching wallet transactions: {e}")
        
        await self._process_documents(all_documents, 'BLOCKCHAIN')
        logger.info(f"✅ Processed {len(all_documents)} blockchain documents")
    
    async def _process_documents(self, documents: List[Dict], source: str):
        """Process documents through embeddings and generate alerts"""
        if not documents:
            return
        
        # Update stats
        self.stats['total_documents_processed'] += len(documents)
        if source not in self.stats['pipelines_status']:
            self.stats['pipelines_status'][source] = {
                'documents_processed': 0,
                'last_update': None
            }
        
        self.stats['pipelines_status'][source]['documents_processed'] += len(documents)
        self.stats['pipelines_status'][source]['last_update'] = datetime.now().isoformat()
        
        # Process each document
        for doc in documents:
            try:
                # Store in database
                await database.store_document(doc)
                
                # Generate embedding and store in vector store
                embedding = await embeddings_client.embed_text(doc['text'])
                if embedding:
                    vector_store.add_document(
                        doc_id=doc['id'],
                        content=doc['text'],
                        embedding=embedding,
                        metadata=doc['metadata']
                    )
                
                # Generate alerts
                alerts = self._generate_alerts_for_document(doc)
                self.alerts_history.extend(alerts)
                self.stats['alerts_generated'] += len(alerts)
                
                # Keep only last 100 alerts
                self.alerts_history = self.alerts_history[-100:]
                
            except Exception as e:
                logger.error(f"Error processing document {doc.get('id', 'unknown')}: {e}")
    
    def _generate_alerts_for_document(self, doc: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate alerts for a document"""
        alerts = []
        
        doc_id = doc.get('id', '')
        source = doc.get('source', '')
        text = doc.get('text', '')
        doc_type = doc.get('type', '')
        
        # Sanctions alerts
        if doc_type == 'sanction' or 'OFAC' in source:
            mentioned_wallets = self._extract_wallet_addresses(text)
            target_matches = [w for w in mentioned_wallets if w.lower() in self.target_wallets]
            
            if target_matches:
                for wallet in target_matches:
                    alert = {
                        'id': f"sanction_alert_{doc_id}_{wallet}",
                        'type': 'SANCTIONS_MATCH',
                        'severity': 'CRITICAL',
                        'title': 'Target Wallet Found in Sanctions Data',
                        'description': f'Wallet {wallet} mentioned in {source} sanctions data',
                        'wallet_address': wallet,
                        'source_document': doc_id,
                        'source': source,
                        'evidence': text[:500],
                        'risk_score': 95,
                        'timestamp': datetime.now().isoformat()
                    }
                    alerts.append(alert)
        
        # High-value transaction alerts
        if doc_type == 'wallet_transaction':
            metadata = doc.get('metadata', {})
            value_eth = metadata.get('value_eth', 0)
            
            if value_eth > 100:  # High value threshold
                alert = {
                    'id': f"high_value_tx_{doc_id}",
                    'type': 'HIGH_VALUE_TRANSACTION',
                    'severity': 'HIGH',
                    'title': 'High-Value Transaction Detected',
                    'description': f'Transaction of {value_eth:.4f} ETH detected',
                    'wallet_address': metadata.get('target_wallet'),
                    'source_document': doc_id,
                    'source': source,
                    'evidence': text,
                    'risk_score': 75,
                    'timestamp': datetime.now().isoformat()
                }
                alerts.append(alert)
        
        return alerts
    
    def _assess_risk_level(self, title: str, summary: str) -> str:
        """Assess risk level based on content"""
        content = f"{title} {summary}".lower()
        
        high_risk_keywords = [
            'enforcement', 'penalty', 'fine', 'violation', 'sanctions',
            'fraud', 'investigation', 'cease and desist'
        ]
        
        medium_risk_keywords = [
            'guidance', 'rule', 'regulation', 'compliance', 'warning'
        ]
        
        if any(keyword in content for keyword in high_risk_keywords):
            return 'high'
        elif any(keyword in content for keyword in medium_risk_keywords):
            return 'medium'
        else:
            return 'low'
    
    def _extract_wallet_addresses(self, text: str) -> List[str]:
        """Extract wallet addresses from text"""
        import re
        eth_pattern = r'0x[a-fA-F0-9]{40}'
        matches = re.findall(eth_pattern, text)
        return list(set(matches))
    
    def add_target_wallet(self, wallet_address: str):
        """Add wallet to monitoring"""
        self.target_wallets.add(wallet_address.lower())
        logger.info(f"🎯 Added wallet to monitoring: {wallet_address}")
    
    def get_recent_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent alerts"""
        return sorted(self.alerts_history, key=lambda x: x['timestamp'], reverse=True)[:limit]
    
    def get_pipeline_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics"""
        return {
            **self.stats,
            'is_running': self.is_running
        }
    
    def simulate_document(self, doc_type: str, content: str) -> bool:
        """Simulate adding a document"""
        try:
            mock_doc = {
                'id': f"demo_{doc_type}_{datetime.now().timestamp()}",
                'source': f"DEMO_{doc_type.upper()}",
                'text': content,
                'timestamp': datetime.now().isoformat(),
                'link': f"https://demo.reguchain.ai/{doc_type}",
                'type': doc_type,
                'metadata': {
                    'demo': True,
                    'risk_level': 'high' if 'sanction' in doc_type.lower() else 'medium',
                    'simulated': True
                }
            }
            
            # Generate alerts immediately for demo
            alerts = self._generate_alerts_for_document(mock_doc)
            self.alerts_history.extend(alerts)
            self.stats['alerts_generated'] += len(alerts)
            
            logger.info(f"✅ Simulated {doc_type} document with {len(alerts)} alerts")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error simulating document: {e}")
            return False
    
    def stop_all_pipelines(self):
        """Stop all pipelines"""
        self.is_running = False
        logger.info("🛑 Fallback pipelines stopped")

# Global instance
pathway_fallback_manager = PathwayFallbackManager()
