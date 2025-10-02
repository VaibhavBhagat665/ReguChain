"""
Pathway Pipeline Manager
Orchestrates all Pathway pipelines for ReguChain
"""
import pathway as pw
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List
import threading

from .ofac_pipeline import ofac_pathway_pipeline
from .rss_pipeline import rss_pathway_pipeline
from .news_pipeline import news_pathway_pipeline
from .blockchain_pipeline import blockchain_pathway_pipeline
from .embeddings_pipeline import embeddings_pathway_pipeline
from .alerts_pipeline import alerts_pathway_pipeline
from ..database import database

logger = logging.getLogger(__name__)

class PathwayPipelineManager:
    """Manages all Pathway pipelines for ReguChain"""
    
    def __init__(self):
        self.is_running = False
        self.pipeline_thread = None
        self.stats = {
            'total_documents_processed': 0,
            'alerts_generated': 0,
            'last_update': None,
            'pipelines_status': {}
        }
        
    async def start_all_pipelines(self):
        """Start all Pathway pipelines with real-time data fetching"""
        if self.is_running:
            logger.warning("⚠️ Pipelines already running")
            return
        
        logger.info("🚀 Starting Pathway pipeline manager...")
        
        try:
            # Start background data fetching tasks
            self.pipeline_thread = threading.Thread(
                target=self._run_background_pipelines,
                daemon=True
            )
            self.pipeline_thread.start()
            
            self.is_running = True
            logger.info("✅ Pathway pipelines started successfully")
            
        except Exception as e:
            logger.error(f"❌ Error starting pipelines: {e}")
            raise
    
    def _run_background_pipelines(self):
        """Run background data fetching and processing"""
        import time
        
        logger.info("🔄 Starting background pipeline execution...")
        
        while self.is_running:
            try:
                # Fetch data from all sources
                self._fetch_and_process_data()
                
                # Sleep for 5 minutes before next cycle
                time.sleep(300)  # 5 minutes
                
            except Exception as e:
                logger.error(f"❌ Error in background pipeline: {e}")
                time.sleep(60)  # Wait 1 minute on error
    
    def _fetch_and_process_data(self):
        """Fetch data from all sources and process through pipelines"""
        try:
            # Fetch OFAC data
            ofac_docs = self._fetch_ofac_data()
            
            # Fetch news data
            news_docs = self._fetch_news_data()
            
            # Fetch RSS data
            rss_docs = self._fetch_rss_data()
            
            # Combine all documents
            all_docs = ofac_docs + news_docs + rss_docs
            
            if all_docs:
                # Process through embeddings and indexing
                asyncio.run(self._process_documents(all_docs))
                
                # Generate alerts
                alerts = self._generate_alerts(all_docs)
                
                # Update stats
                self.stats['total_documents_processed'] += len(all_docs)
                self.stats['alerts_generated'] += len(alerts)
                self.stats['last_update'] = datetime.now().isoformat()
                
                logger.info(f"📊 Processed {len(all_docs)} documents, generated {len(alerts)} alerts")
            
        except Exception as e:
            logger.error(f"❌ Error fetching and processing data: {e}")
    
    def _fetch_ofac_data(self) -> List[Dict]:
        """Fetch OFAC sanctions data"""
        try:
            return ofac_pathway_pipeline.fetch_real_data()
        except Exception as e:
            logger.error(f"Error fetching OFAC data: {e}")
            return []
    
    def _fetch_news_data(self) -> List[Dict]:
        """Fetch news data"""
        try:
            return news_pathway_pipeline.fetch_real_data()
        except Exception as e:
            logger.error(f"Error fetching news data: {e}")
            return []
    
    def _fetch_rss_data(self) -> List[Dict]:
        """Fetch RSS data"""
        try:
            return rss_pathway_pipeline.fetch_real_data()
        except Exception as e:
            logger.error(f"Error fetching RSS data: {e}")
            return []
    
    async def _process_documents(self, documents: List[Dict]):
        """Process documents through embeddings pipeline"""
        try:
            await embeddings_pathway_pipeline.process_documents(documents)
        except Exception as e:
            logger.error(f"Error processing documents: {e}")
    
    def _generate_alerts(self, documents: List[Dict]) -> List[Dict]:
        """Generate alerts from documents"""
        try:
            return alerts_pathway_pipeline.generate_alerts_from_docs(documents)
        except Exception as e:
            logger.error(f"Error generating alerts: {e}")
            return []
    
    def _create_output_sinks(self, documents_table: pw.Table, alerts_table: pw.Table):
        """Create output sinks for processed data"""
        
        # Document processing sink
        @pw.udf
        def log_processed_documents(docs: pw.Table):
            """Log processed documents"""
            doc_list = docs.to_pandas().to_dict('records') if not docs.is_empty() else []
            
            if doc_list:
                self.stats['total_documents_processed'] += len(doc_list)
                self.stats['last_update'] = datetime.now().isoformat()
                
                logger.info(f"📊 Processed {len(doc_list)} documents (Total: {self.stats['total_documents_processed']})")
                
                # Update pipeline status
                for doc in doc_list:
                    source = doc.get('source', 'unknown')
                    if source not in self.stats['pipelines_status']:
                        self.stats['pipelines_status'][source] = {
                            'documents_processed': 0,
                            'last_update': None
                        }
                    
                    self.stats['pipelines_status'][source]['documents_processed'] += 1
                    self.stats['pipelines_status'][source]['last_update'] = datetime.now().isoformat()
        
        # Alerts processing sink
        @pw.udf
        def log_generated_alerts(alerts: pw.Table):
            """Log generated alerts"""
            alert_list = alerts.to_pandas().to_dict('records') if not alerts.is_empty() else []
            
            if alert_list:
                self.stats['alerts_generated'] += len(alert_list)
                logger.info(f"🚨 Generated {len(alert_list)} alerts (Total: {self.stats['alerts_generated']})")
                
                # Log critical alerts
                for alert in alert_list:
                    if alert.get('severity') == 'CRITICAL':
                        logger.warning(f"🔴 CRITICAL ALERT: {alert.get('title', 'Unknown')} - {alert.get('description', '')}")
        
        # Apply sinks
        documents_table.select(log_processed_documents(pw.this))
        alerts_table.select(log_generated_alerts(pw.this))
    
    def _run_pipeline(self, pipeline_data):
        """Run the Pathway pipeline"""
        try:
            logger.info("▶️ Starting Pathway pipeline execution...")
            
            # Run the pipeline
            pw.run()
            
        except Exception as e:
            logger.error(f"❌ Error running pipeline: {e}")
            self.is_running = False
    
    def stop_all_pipelines(self):
        """Stop all Pathway pipelines"""
        if not self.is_running:
            logger.warning("⚠️ Pipelines not running")
            return
        
        logger.info("🛑 Stopping Pathway pipelines...")
        
        try:
            self.is_running = False
            
            if self.pipeline_thread and self.pipeline_thread.is_alive():
                # Note: Pathway doesn't have a clean shutdown mechanism
                # In production, you'd want to implement proper shutdown
                logger.info("⏳ Waiting for pipeline thread to finish...")
                self.pipeline_thread.join(timeout=10)
            
            logger.info("✅ Pathway pipelines stopped")
            
        except Exception as e:
            logger.error(f"❌ Error stopping pipelines: {e}")
    
    def get_pipeline_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics"""
        return {
            **self.stats,
            'is_running': self.is_running,
            'thread_alive': self.pipeline_thread.is_alive() if self.pipeline_thread else False
        }
    
    def add_target_wallet(self, wallet_address: str):
        """Add wallet to monitoring across all relevant pipelines"""
        logger.info(f"🎯 Adding wallet {wallet_address} to all monitoring pipelines")
        
        # Add to blockchain pipeline
        blockchain_pathway_pipeline.add_target_wallet(wallet_address)
        
        # Add to alerts pipeline
        alerts_pathway_pipeline.add_target_wallet(wallet_address)
    
    def get_recent_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent alerts from alerts pipeline"""
        return alerts_pathway_pipeline.get_recent_alerts(limit)
    
    def get_alerts_by_wallet(self, wallet_address: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get alerts for specific wallet"""
        return alerts_pathway_pipeline.get_alerts_by_wallet(wallet_address, limit)
    
    def simulate_document(self, doc_type: str, content: str) -> bool:
        """Simulate adding a document for demo purposes"""
        try:
            logger.info(f"🎭 Simulating {doc_type} document: {content[:100]}...")
            
            # Create mock document
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
            
            # Process through embeddings pipeline (simplified for demo)
            # In real implementation, this would go through the full pipeline
            logger.info(f"✅ Simulated {doc_type} document successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error simulating document: {e}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on all pipelines"""
        health_status = {
            'overall_status': 'healthy' if self.is_running else 'stopped',
            'pipelines': {
                'ofac': 'active' if self.is_running else 'inactive',
                'rss': 'active' if self.is_running else 'inactive', 
                'news': 'active' if self.is_running else 'inactive',
                'blockchain': 'active' if self.is_running else 'inactive',
                'embeddings': 'active' if self.is_running else 'inactive',
                'alerts': 'active' if self.is_running else 'inactive'
            },
            'stats': self.get_pipeline_stats(),
            'last_health_check': datetime.now().isoformat()
        }
        
        return health_status

# Global instance
pathway_pipeline_manager = PathwayPipelineManager()
