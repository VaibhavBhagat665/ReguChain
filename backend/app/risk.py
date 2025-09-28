"""Risk assessment engine for ReguChain Watch"""
import re
import logging
from typing import List, Dict, Tuple
from .config import RISK_SCORE_THRESHOLD, TRANSACTION_THRESHOLD

logger = logging.getLogger(__name__)

class RiskEngine:
    """Risk assessment engine"""
    
    def __init__(self):
        self.risk_keywords = {
            "critical": ["OFAC", "sanction", "sanctioned", "blacklist", "terrorist", "money laundering"],
            "high": ["hack", "fraud", "scam", "exploit", "theft", "stolen"],
            "medium": ["suspicious", "unusual", "investigation", "violation", "breach"],
            "low": ["monitoring", "review", "audit", "compliance", "regulation"]
        }
    
    def calculate_risk_score(
        self,
        target: str,
        retrieved_docs: List[Dict],
        onchain_matches: List[Dict]
    ) -> Tuple[float, List[str]]:
        """
        Calculate risk score from 0-100
        Returns: (score, reasons)
        """
        score = 0
        reasons = []
        
        if not target:
            return 0, ["No target specified"]
        
        # Normalize target for matching
        target_lower = target.lower()
        
        # Check retrieved documents
        for doc in retrieved_docs:
            doc_text = doc.get("text", "").lower()
            doc_source = doc.get("source", "").lower()
            
            # Check if target appears in document
            if target_lower in doc_text:
                score += 70
                reasons.append(f"Target '{target}' found in {doc.get('source', 'document')}")
            
            # Check for OFAC/sanction mentions
            if any(keyword in doc_source for keyword in ["ofac", "sanction"]):
                score += 40
                reasons.append(f"Document from sanctions source: {doc.get('source', 'unknown')}")
            elif any(keyword in doc_text for keyword in ["ofac", "sanction", "sanctioned"]):
                score += 40
                reasons.append("Sanctions-related content found")
            
            # Check for hack/fraud mentions
            if any(keyword in doc_text for keyword in ["hack", "fraud", "exploit", "theft"]):
                score += 20
                reasons.append("Security incident keywords detected")
            
            # Check for other risk keywords
            for level, keywords in self.risk_keywords.items():
                matches = [kw for kw in keywords if kw in doc_text]
                if matches:
                    if level == "critical":
                        score += 30
                    elif level == "high":
                        score += 20
                    elif level == "medium":
                        score += 10
                    else:
                        score += 5
                    
                    if matches and len(reasons) < 10:  # Limit reasons
                        reasons.append(f"{level.capitalize()} risk keywords: {', '.join(matches[:3])}")
        
        # Check on-chain transactions
        high_value_txs = []
        for tx in onchain_matches:
            amount = tx.get("amount", 0)
            if amount > TRANSACTION_THRESHOLD:
                score += 15
                high_value_txs.append(f"${amount:,.2f}")
        
        if high_value_txs:
            reasons.append(f"High-value transactions: {', '.join(high_value_txs[:3])}")
        
        # Clamp score to 0-100
        score = max(0, min(100, score))
        
        # Add risk level to reasons
        if score >= 70:
            risk_level = "HIGH RISK"
        elif score >= 40:
            risk_level = "MEDIUM RISK"
        else:
            risk_level = "LOW RISK"
        
        reasons.insert(0, f"Risk Level: {risk_level}")
        
        return score, reasons
    
    def assess_wallet_risk(self, address: str, transactions: List[Dict]) -> Dict:
        """Assess risk for a wallet address"""
        risk_indicators = []
        
        # Check if address format is valid
        if not re.match(r'^0x[a-fA-F0-9]{40}$', address):
            risk_indicators.append("Invalid address format")
        
        # Analyze transaction patterns
        total_volume = sum(tx.get("amount", 0) for tx in transactions)
        high_value_count = sum(1 for tx in transactions if tx.get("amount", 0) > TRANSACTION_THRESHOLD)
        
        if total_volume > TRANSACTION_THRESHOLD * 10:
            risk_indicators.append(f"High transaction volume: ${total_volume:,.2f}")
        
        if high_value_count > 3:
            risk_indicators.append(f"Multiple high-value transactions: {high_value_count}")
        
        # Check for known risky addresses (demo purposes)
        risky_addresses = [
            "0x0000000000000000000000000000000000000000",
            "0xDEADBEEF",
            "0xDEMO"
        ]
        
        if any(addr in address.upper() for addr in risky_addresses):
            risk_indicators.append("Known risky address pattern")
        
        return {
            "address": address,
            "risk_indicators": risk_indicators,
            "transaction_count": len(transactions),
            "total_volume": total_volume,
            "high_value_transactions": high_value_count
        }
    
    def get_risk_category(self, score: float) -> str:
        """Get risk category from score"""
        if score >= 70:
            return "HIGH"
        elif score >= 40:
            return "MEDIUM"
        else:
            return "LOW"
    
    def get_recommendations(self, score: float, reasons: List[str]) -> List[str]:
        """Get actionable recommendations based on risk score"""
        recommendations = []
        
        if score >= 70:
            recommendations.extend([
                "Immediately block or freeze any pending transactions",
                "Report to compliance team for further investigation",
                "Document all interactions for regulatory reporting"
            ])
        elif score >= 40:
            recommendations.extend([
                "Enhance monitoring of this entity",
                "Request additional KYC documentation",
                "Review transaction history for patterns"
            ])
        else:
            recommendations.extend([
                "Continue standard monitoring procedures",
                "Update risk assessment in 30 days",
                "No immediate action required"
            ])
        
        return recommendations

# Global risk engine instance
risk_engine = RiskEngine()
