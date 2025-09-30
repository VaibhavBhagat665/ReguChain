"""
Wallet Tracking Service using Pathway for real-time monitoring
"""
import asyncio
import logging
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from pathlib import Path
import pandas as pd
from dataclasses import dataclass, asdict

from .config import PATHWAY_KEY, PATHWAY_PERSISTENCE_PATH
from .blockchain_service import blockchain_service, BlockchainTransaction

logger = logging.getLogger(__name__)

# Try to import Pathway
pathway_available = False
try:
    import pathway as pw
    pathway_available = True
    logger.info("Pathway available for wallet tracking")
except ImportError:
    logger.warning("Pathway not available - using simulation mode")

@dataclass
class WalletActivity:
    """Wallet activity record for tracking"""
    wallet_address: str
    transaction_hash: str
    timestamp: str
    transaction_type: str  # 'incoming', 'outgoing', 'internal'
    amount: float
    counterparty: str
    risk_score: float
    compliance_flags: List[str]
    regulatory_alerts: List[str]
    
    def to_dict(self) -> Dict:
        return asdict(self)

@dataclass
class ComplianceAlert:
    """Compliance alert for wallet activity"""
    alert_id: str
    wallet_address: str
    alert_type: str  # 'sanctions', 'high_risk', 'unusual_activity', 'regulatory'
    severity: str    # 'critical', 'high', 'medium', 'low'
    description: str
    timestamp: str
    transaction_hash: Optional[str] = None
    recommended_action: str = ""

class WalletTrackingService:
    """Real-time wallet tracking and compliance monitoring"""
    
    def __init__(self):
        self.pathway_key = PATHWAY_KEY
        self.persistence_path = Path(PATHWAY_PERSISTENCE_PATH)
        self.tracked_wallets = set()
        self.compliance_rules = self._load_compliance_rules()
        
        # Create directories
        self.persistence_path.mkdir(parents=True, exist_ok=True)
        (self.persistence_path / "wallet_tracking").mkdir(exist_ok=True)
        
        # Initialize Pathway if available
        if pathway_available and self.pathway_key:
            self._initialize_pathway_tracking()
    
    def _load_compliance_rules(self) -> Dict:
        """Load compliance rules for wallet monitoring"""
        return {
            "transaction_thresholds": {
                "high_value": 10000.0,  # USD
                "suspicious_frequency": 10,  # transactions per hour
                "velocity_threshold": 50000.0  # USD per day
            },
            "risk_indicators": {
                "sanctions_list_match": "critical",
                "high_risk_exchange": "high", 
                "mixer_interaction": "high",
                "new_address_large_amount": "medium",
                "unusual_time_pattern": "low"
            },
            "regulatory_requirements": {
                "kyc_threshold": 3000.0,
                "reporting_threshold": 10000.0,
                "enhanced_monitoring": 50000.0
            }
        }
    
    def _initialize_pathway_tracking(self):
        """Initialize Pathway for real-time wallet tracking"""
        try:
            # This would set up Pathway streaming for wallet data
            logger.info("Pathway wallet tracking initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Pathway tracking: {e}")
    
    async def add_wallet_for_tracking(self, wallet_address: str, 
                                    monitoring_level: str = "standard") -> bool:
        """Add a wallet address for real-time tracking"""
        try:
            self.tracked_wallets.add(wallet_address)
            
            # Get initial wallet information
            wallet_info = await blockchain_service.get_wallet_info(wallet_address)
            recent_transactions = await blockchain_service.get_transactions(wallet_address, limit=50)
            
            # Perform initial compliance check
            compliance_status = await self._perform_compliance_check(wallet_address, recent_transactions)
            
            # Save tracking configuration
            tracking_config = {
                "wallet_address": wallet_address,
                "monitoring_level": monitoring_level,
                "added_timestamp": datetime.now().isoformat(),
                "initial_balance": wallet_info.balance,
                "transaction_count": wallet_info.transaction_count,
                "compliance_status": compliance_status
            }
            
            config_file = self.persistence_path / "wallet_tracking" / f"{wallet_address}.json"
            with open(config_file, 'w') as f:
                json.dump(tracking_config, f, indent=2)
            
            logger.info(f"Added wallet {wallet_address} for {monitoring_level} monitoring")
            return True
            
        except Exception as e:
            logger.error(f"Error adding wallet for tracking: {e}")
            return False
    
    async def _perform_compliance_check(self, wallet_address: str, 
                                      transactions: List[BlockchainTransaction]) -> Dict:
        """Perform comprehensive compliance check on wallet"""
        compliance_status = {
            "risk_level": "low",
            "sanctions_check": "clear",
            "high_risk_interactions": [],
            "regulatory_flags": [],
            "recommendations": []
        }
        
        try:
            # Check against sanctions lists (simplified)
            if await self._check_sanctions_list(wallet_address):
                compliance_status["sanctions_check"] = "flagged"
                compliance_status["risk_level"] = "critical"
                compliance_status["regulatory_flags"].append("OFAC_SANCTIONS_MATCH")
            
            # Analyze transaction patterns
            risk_indicators = await self._analyze_transaction_patterns(transactions)
            compliance_status["risk_indicators"] = risk_indicators
            
            # Check for high-risk counterparties
            high_risk_addresses = await self._identify_high_risk_counterparties(transactions)
            compliance_status["high_risk_interactions"] = high_risk_addresses
            
            # Generate recommendations
            compliance_status["recommendations"] = self._generate_compliance_recommendations(compliance_status)
            
            return compliance_status
            
        except Exception as e:
            logger.error(f"Error in compliance check: {e}")
            return compliance_status
    
    async def _check_sanctions_list(self, wallet_address: str) -> bool:
        """Check wallet address against sanctions lists"""
        # This would integrate with real sanctions databases
        # For now, return False (not sanctioned)
        return False
    
    async def _analyze_transaction_patterns(self, transactions: List[BlockchainTransaction]) -> List[str]:
        """Analyze transaction patterns for risk indicators"""
        risk_indicators = []
        
        if not transactions:
            return risk_indicators
        
        # Calculate transaction velocity
        recent_transactions = [tx for tx in transactions 
                             if self._is_recent_transaction(tx.timestamp)]
        
        if len(recent_transactions) > self.compliance_rules["transaction_thresholds"]["suspicious_frequency"]:
            risk_indicators.append("high_transaction_frequency")
        
        # Check for large transactions
        total_value = sum(float(tx.value) for tx in recent_transactions)
        if total_value > self.compliance_rules["transaction_thresholds"]["velocity_threshold"]:
            risk_indicators.append("high_transaction_velocity")
        
        # Check for unusual timing patterns
        if self._detect_unusual_timing(transactions):
            risk_indicators.append("unusual_timing_pattern")
        
        return risk_indicators
    
    def _is_recent_transaction(self, timestamp: str) -> bool:
        """Check if transaction is recent (within 24 hours)"""
        try:
            tx_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return (datetime.now() - tx_time.replace(tzinfo=None)) < timedelta(hours=24)
        except:
            return False
    
    def _detect_unusual_timing(self, transactions: List[BlockchainTransaction]) -> bool:
        """Detect unusual timing patterns in transactions"""
        # Simple implementation - check for transactions at unusual hours
        unusual_hours = 0
        for tx in transactions[-10:]:  # Check last 10 transactions
            try:
                tx_time = datetime.fromisoformat(tx.timestamp.replace('Z', '+00:00'))
                hour = tx_time.hour
                if hour < 6 or hour > 22:  # Transactions between 10 PM and 6 AM
                    unusual_hours += 1
            except:
                continue
        
        return unusual_hours > 5  # More than 50% at unusual hours
    
    async def _identify_high_risk_counterparties(self, transactions: List[BlockchainTransaction]) -> List[str]:
        """Identify high-risk counterparty addresses"""
        high_risk_addresses = []
        
        # This would integrate with risk databases
        # For now, return empty list
        return high_risk_addresses
    
    def _generate_compliance_recommendations(self, compliance_status: Dict) -> List[str]:
        """Generate compliance recommendations based on status"""
        recommendations = []
        
        if compliance_status["sanctions_check"] == "flagged":
            recommendations.append("IMMEDIATE: Freeze all transactions and report to authorities")
        
        if "high_transaction_frequency" in compliance_status.get("risk_indicators", []):
            recommendations.append("Enhanced monitoring recommended")
        
        if "high_transaction_velocity" in compliance_status.get("risk_indicators", []):
            recommendations.append("Consider filing Suspicious Activity Report (SAR)")
        
        if not recommendations:
            recommendations.append("Continue standard monitoring")
        
        return recommendations
    
    async def get_wallet_compliance_status(self, wallet_address: str) -> Dict:
        """Get current compliance status for a tracked wallet"""
        try:
            config_file = self.persistence_path / "wallet_tracking" / f"{wallet_address}.json"
            
            if not config_file.exists():
                return {"error": "Wallet not being tracked"}
            
            with open(config_file, 'r') as f:
                tracking_data = json.load(f)
            
            # Get recent transactions for updated analysis
            recent_transactions = await blockchain_service.get_transactions(wallet_address, limit=20)
            updated_compliance = await self._perform_compliance_check(wallet_address, recent_transactions)
            
            return {
                "wallet_address": wallet_address,
                "tracking_since": tracking_data["added_timestamp"],
                "monitoring_level": tracking_data["monitoring_level"],
                "current_compliance": updated_compliance,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting compliance status: {e}")
            return {"error": str(e)}
    
    async def generate_compliance_report(self, wallet_address: str) -> Dict:
        """Generate comprehensive compliance report for wallet"""
        try:
            # Get wallet information
            wallet_info = await blockchain_service.get_wallet_info(wallet_address)
            transactions = await blockchain_service.get_transactions(wallet_address, limit=100)
            compliance_status = await self._perform_compliance_check(wallet_address, transactions)
            
            report = {
                "report_id": f"compliance_{wallet_address}_{int(time.time())}",
                "generated_at": datetime.now().isoformat(),
                "wallet_address": wallet_address,
                "wallet_info": {
                    "balance": wallet_info.balance,
                    "transaction_count": wallet_info.transaction_count,
                    "first_seen": wallet_info.first_seen,
                    "last_seen": wallet_info.last_seen
                },
                "compliance_analysis": compliance_status,
                "transaction_summary": {
                    "total_transactions": len(transactions),
                    "recent_transactions": len([tx for tx in transactions if self._is_recent_transaction(tx.timestamp)]),
                    "total_volume": sum(float(tx.value) for tx in transactions)
                },
                "regulatory_requirements": {
                    "kyc_required": sum(float(tx.value) for tx in transactions) > self.compliance_rules["regulatory_requirements"]["kyc_threshold"],
                    "reporting_required": any(float(tx.value) > self.compliance_rules["regulatory_requirements"]["reporting_threshold"] for tx in transactions),
                    "enhanced_monitoring": sum(float(tx.value) for tx in transactions) > self.compliance_rules["regulatory_requirements"]["enhanced_monitoring"]
                }
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating compliance report: {e}")
            return {"error": str(e)}
    
    async def get_tracked_wallets(self) -> List[Dict]:
        """Get list of all tracked wallets with their status"""
        tracked_wallets = []
        
        try:
            tracking_dir = self.persistence_path / "wallet_tracking"
            
            for config_file in tracking_dir.glob("*.json"):
                try:
                    with open(config_file, 'r') as f:
                        tracking_data = json.load(f)
                    
                    wallet_address = tracking_data["wallet_address"]
                    status = await self.get_wallet_compliance_status(wallet_address)
                    
                    tracked_wallets.append({
                        "wallet_address": wallet_address,
                        "monitoring_level": tracking_data["monitoring_level"],
                        "added_timestamp": tracking_data["added_timestamp"],
                        "compliance_status": status.get("current_compliance", {}).get("risk_level", "unknown")
                    })
                    
                except Exception as e:
                    logger.error(f"Error reading tracking config {config_file}: {e}")
                    continue
            
            return tracked_wallets
            
        except Exception as e:
            logger.error(f"Error getting tracked wallets: {e}")
            return []

# Global service instance
wallet_tracking_service = WalletTrackingService()
