"""
Pathway Risk Alerts Pipeline
Real-time risk alerts based on ingested data
"""
import pathway as pw
from datetime import datetime
from typing import Dict, Any, List
import logging
from ..config import RISK_SCORE_THRESHOLD, TRANSACTION_THRESHOLD

logger = logging.getLogger(__name__)

class AlertsPathwayPipeline:
    """Pathway-powered risk alerts system"""
    
    def __init__(self):
        self.target_wallets = set()
        self.alert_history = []
        
    def add_target_wallet(self, wallet_address: str):
        """Add wallet to monitoring for alerts"""
        self.target_wallets.add(wallet_address.lower())
        logger.info(f"🎯 Added wallet to alert monitoring: {wallet_address}")
    
    def create_risk_alerts_pipeline(self, source_table: pw.Table):
        """Create Pathway pipeline for risk alerts"""
        
        @pw.udf
        def generate_risk_alerts(docs: pw.Table) -> pw.Table:
            """Generate risk alerts from incoming documents"""
            alerts = []
            
            # Convert to list for processing
            doc_list = docs.to_pandas().to_dict('records') if not docs.is_empty() else []
            
            if not doc_list:
                return pw.Table.empty()
            
            logger.info(f"🔍 Analyzing {len(doc_list)} documents for risk alerts...")
            
            for doc in doc_list:
                try:
                    doc_alerts = self._analyze_document_for_alerts(doc)
                    alerts.extend(doc_alerts)
                except Exception as e:
                    logger.error(f"Error analyzing document {doc.get('id', 'unknown')} for alerts: {e}")
                    continue
            
            if alerts:
                logger.info(f"🚨 Generated {len(alerts)} risk alerts")
                # Store alerts in history
                self.alert_history.extend(alerts)
                # Keep only last 100 alerts
                self.alert_history = self.alert_history[-100:]
            
            return pw.Table.from_pandas(pw.pandas.DataFrame(alerts)) if alerts else pw.Table.empty()
        
        # Apply risk analysis to source table
        risk_alerts = source_table.select(
            alert_data=generate_risk_alerts(pw.this)
        ).flatten(pw.this.alert_data)
        
        return risk_alerts
    
    def _analyze_document_for_alerts(self, doc: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze a single document for risk alerts"""
        alerts = []
        
        doc_id = doc.get('id', '')
        source = doc.get('source', '')
        text = doc.get('text', '')
        metadata = doc.get('metadata', {})
        doc_type = doc.get('type', '')
        
        # Alert 1: Sanctions-related alerts
        if self._is_sanctions_related(doc):
            # Check if any target wallets are mentioned
            mentioned_wallets = self._extract_wallet_addresses(text)
            target_matches = [w for w in mentioned_wallets if w.lower() in self.target_wallets]
            
            if target_matches:
                for wallet in target_matches:
                    alert = {
                        'id': f"sanction_alert_{doc_id}_{wallet}",
                        'type': 'SANCTIONS_MATCH',
                        'severity': 'CRITICAL',
                        'title': f'Target Wallet Found in Sanctions Data',
                        'description': f'Wallet {wallet} mentioned in {source} sanctions data',
                        'wallet_address': wallet,
                        'source_document': doc_id,
                        'source': source,
                        'evidence': text[:500] + "..." if len(text) > 500 else text,
                        'risk_score': 95,
                        'timestamp': datetime.now().isoformat(),
                        'metadata': {
                            'document_type': doc_type,
                            'original_metadata': metadata
                        }
                    }
                    alerts.append(alert)
            else:
                # General sanctions alert
                alert = {
                    'id': f"sanction_general_{doc_id}",
                    'type': 'SANCTIONS_UPDATE',
                    'severity': 'HIGH',
                    'title': f'New Sanctions Entry',
                    'description': f'New sanctions data from {source}',
                    'wallet_address': None,
                    'source_document': doc_id,
                    'source': source,
                    'evidence': text[:500] + "..." if len(text) > 500 else text,
                    'risk_score': metadata.get('risk_level') == 'critical' and 90 or 70,
                    'timestamp': datetime.now().isoformat(),
                    'metadata': {
                        'document_type': doc_type,
                        'original_metadata': metadata
                    }
                }
                alerts.append(alert)
        
        # Alert 2: High-value transaction alerts
        if doc_type == 'blockchain_transaction':
            value_eth = metadata.get('value_eth', 0)
            threshold_eth = TRANSACTION_THRESHOLD / 1000  # Convert to ETH
            
            if value_eth > threshold_eth:
                from_addr = metadata.get('from_address', '')
                to_addr = metadata.get('to_address', '')
                
                # Check if involves target wallets
                is_target_involved = (from_addr.lower() in self.target_wallets or 
                                    to_addr.lower() in self.target_wallets)
                
                severity = 'CRITICAL' if is_target_involved else 'HIGH'
                risk_score = 85 if is_target_involved else 65
                
                alert = {
                    'id': f"high_value_tx_{doc_id}",
                    'type': 'HIGH_VALUE_TRANSACTION',
                    'severity': severity,
                    'title': f'High-Value Transaction Detected',
                    'description': f'Transaction of {value_eth:.4f} ETH detected',
                    'wallet_address': from_addr if from_addr.lower() in self.target_wallets else to_addr if to_addr.lower() in self.target_wallets else None,
                    'source_document': doc_id,
                    'source': source,
                    'evidence': text,
                    'risk_score': risk_score,
                    'timestamp': datetime.now().isoformat(),
                    'metadata': {
                        'document_type': doc_type,
                        'transaction_value': value_eth,
                        'from_address': from_addr,
                        'to_address': to_addr,
                        'target_involved': is_target_involved,
                        'original_metadata': metadata
                    }
                }
                alerts.append(alert)
        
        # Alert 3: Regulatory enforcement alerts
        if self._is_enforcement_related(doc):
            mentioned_wallets = self._extract_wallet_addresses(text)
            target_matches = [w for w in mentioned_wallets if w.lower() in self.target_wallets]
            
            if target_matches:
                for wallet in target_matches:
                    alert = {
                        'id': f"enforcement_alert_{doc_id}_{wallet}",
                        'type': 'ENFORCEMENT_ACTION',
                        'severity': 'CRITICAL',
                        'title': f'Target Wallet in Enforcement Action',
                        'description': f'Wallet {wallet} mentioned in regulatory enforcement',
                        'wallet_address': wallet,
                        'source_document': doc_id,
                        'source': source,
                        'evidence': text[:500] + "..." if len(text) > 500 else text,
                        'risk_score': 90,
                        'timestamp': datetime.now().isoformat(),
                        'metadata': {
                            'document_type': doc_type,
                            'original_metadata': metadata
                        }
                    }
                    alerts.append(alert)
        
        # Alert 4: High-risk news alerts
        if doc_type == 'regulatory_news' and metadata.get('risk_level') in ['critical', 'high']:
            alert = {
                'id': f"news_alert_{doc_id}",
                'type': 'REGULATORY_NEWS',
                'severity': 'HIGH' if metadata.get('risk_level') == 'high' else 'CRITICAL',
                'title': f'High-Risk Regulatory News',
                'description': f'Important regulatory news from {metadata.get("news_source", "unknown")}',
                'wallet_address': None,
                'source_document': doc_id,
                'source': source,
                'evidence': text[:500] + "..." if len(text) > 500 else text,
                'risk_score': 80 if metadata.get('risk_level') == 'high' else 95,
                'timestamp': datetime.now().isoformat(),
                'metadata': {
                    'document_type': doc_type,
                    'news_source': metadata.get('news_source'),
                    'sentiment': metadata.get('sentiment'),
                    'original_metadata': metadata
                }
            }
            alerts.append(alert)
        
        return alerts
    
    def _is_sanctions_related(self, doc: Dict[str, Any]) -> bool:
        """Check if document is sanctions-related"""
        source = doc.get('source', '').upper()
        doc_type = doc.get('type', '')
        
        return (source.startswith('OFAC') or 
                doc_type == 'sanction' or
                'sanction' in doc.get('text', '').lower())
    
    def _is_enforcement_related(self, doc: Dict[str, Any]) -> bool:
        """Check if document is enforcement-related"""
        text = doc.get('text', '').lower()
        enforcement_keywords = [
            'enforcement', 'penalty', 'fine', 'violation', 
            'investigation', 'prosecution', 'lawsuit', 'cease and desist'
        ]
        
        return any(keyword in text for keyword in enforcement_keywords)
    
    def _extract_wallet_addresses(self, text: str) -> List[str]:
        """Extract potential wallet addresses from text"""
        import re
        
        # Ethereum address pattern (0x followed by 40 hex characters)
        eth_pattern = r'0x[a-fA-F0-9]{40}'
        
        matches = re.findall(eth_pattern, text)
        return list(set(matches))  # Remove duplicates
    
    def get_recent_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent alerts"""
        return sorted(self.alert_history, key=lambda x: x['timestamp'], reverse=True)[:limit]
    
    def get_alerts_by_wallet(self, wallet_address: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get alerts for specific wallet"""
        wallet_lower = wallet_address.lower()
        wallet_alerts = [
            alert for alert in self.alert_history 
            if alert.get('wallet_address', '').lower() == wallet_lower
        ]
        return sorted(wallet_alerts, key=lambda x: x['timestamp'], reverse=True)[:limit]

# Global instance
alerts_pathway_pipeline = AlertsPathwayPipeline()
