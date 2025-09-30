"""
Real Blockchain Data Integration Service
Provides real-time blockchain data for wallet analysis
"""
import asyncio
import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import aiohttp
import json
from dataclasses import dataclass

# No Google dependency required here

logger = logging.getLogger(__name__)

@dataclass
class BlockchainTransaction:
    """Blockchain transaction data"""
    hash: str
    from_address: str
    to_address: str
    value: str
    timestamp: str
    gas_used: Optional[str] = None
    block_number: Optional[int] = None
    status: str = "success"
    token_transfers: List[Dict] = None

@dataclass
class WalletInfo:
    """Wallet information"""
    address: str
    balance: str
    transaction_count: int
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None
    labels: List[str] = None

class BlockchainDataService:
    """Service for fetching real blockchain data"""
    
    def __init__(self):
        self.etherscan_api_key = os.getenv("ETHERSCAN_API_KEY")
        self.alchemy_api_key = os.getenv("ALCHEMY_API_KEY")
        self.moralis_api_key = os.getenv("MORALIS_API_KEY")
        
        # Free API endpoints (no key required)
        self.free_endpoints = {
            "etherscan_free": "https://api.etherscan.io/api",
            "blockchair": "https://api.blockchair.com/ethereum",
            "ethplorer": "https://api.ethplorer.io"
        }
        
        # Rate limiting
        self.last_request_time = {}
        self.min_request_interval = 0.2  # 200ms between requests
    
    async def get_wallet_info(self, address: str) -> WalletInfo:
        """Get comprehensive wallet information"""
        try:
            # Try multiple data sources for reliability
            balance_data = await self._get_wallet_balance(address)
            transaction_count = await self._get_transaction_count(address)
            
            return WalletInfo(
                address=address,
                balance=balance_data.get("balance", "0"),
                transaction_count=transaction_count,
                first_seen=balance_data.get("first_seen"),
                last_seen=balance_data.get("last_seen"),
                labels=balance_data.get("labels", [])
            )
            
        except Exception as e:
            logger.error(f"Error getting wallet info for {address}: {e}")
            return WalletInfo(
                address=address,
                balance="0",
                transaction_count=0,
                labels=[]
            )
    
    async def get_transactions(self, address: str, limit: int = 20) -> List[BlockchainTransaction]:
        """Get recent transactions for a wallet (real APIs only)"""
        try:
            transactions = await self._get_etherscan_transactions(address, limit)
            return transactions or []
        except Exception as e:
            logger.error(f"Error getting transactions for {address}: {e}")
            return []
    
    async def _get_wallet_balance(self, address: str) -> Dict[str, Any]:
        """Get wallet balance from multiple sources"""
        try:
            # Try Etherscan API (free tier)
            url = f"{self.free_endpoints['etherscan_free']}"
            params = {
                "module": "account",
                "action": "balance",
                "address": address,
                "tag": "latest"
            }
            
            # Add API key if available
            if self.etherscan_api_key:
                params["apikey"] = self.etherscan_api_key
            
            await self._rate_limit("etherscan")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("status") == "1":
                            balance_wei = int(data.get("result", "0"))
                            balance_eth = balance_wei / 10**18
                            
                            return {
                                "balance": f"{balance_eth:.6f}",
                                "balance_wei": str(balance_wei),
                                "source": "etherscan"
                            }
            
            # On failure, return empty balance to avoid mock data
            return {
                "balance": "0",
                "balance_wei": "0",
                "source": "unavailable"
            }
            
        except Exception as e:
            logger.error(f"Error getting balance for {address}: {e}")
            return {"balance": "0", "balance_wei": "0", "source": "error"}
    
    async def _get_transaction_count(self, address: str) -> int:
        """Get transaction count for address"""
        try:
            url = f"{self.free_endpoints['etherscan_free']}"
            params = {
                "module": "proxy",
                "action": "eth_getTransactionCount",
                "address": address,
                "tag": "latest"
            }
            
            # Add API key if available
            if self.etherscan_api_key:
                params["apikey"] = self.etherscan_api_key
            
            await self._rate_limit("etherscan")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("result"):
                            return int(data["result"], 16)  # Convert hex to int
            
            # On failure, return 0 to avoid mock values
            return 0
            
        except Exception as e:
            logger.error(f"Error getting transaction count for {address}: {e}")
            return 0
    
    async def _get_etherscan_transactions(self, address: str, limit: int) -> List[BlockchainTransaction]:
        """Get transactions from Etherscan API"""
        try:
            url = f"{self.free_endpoints['etherscan_free']}"
            params = {
                "module": "account",
                "action": "txlist",
                "address": address,
                "startblock": 0,
                "endblock": 99999999,
                "page": 1,
                "offset": min(limit, 10),  # Free tier limit
                "sort": "desc"
            }
            
            # Add API key if available
            if self.etherscan_api_key:
                params["apikey"] = self.etherscan_api_key
            
            await self._rate_limit("etherscan")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("status") == "1" and data.get("result"):
                            transactions = []
                            for tx in data["result"]:
                                transaction = BlockchainTransaction(
                                    hash=tx.get("hash", ""),
                                    from_address=tx.get("from", ""),
                                    to_address=tx.get("to", ""),
                                    value=str(int(tx.get("value", "0")) / 10**18),  # Convert to ETH
                                    gas_used=tx.get("gasUsed"),
                                    timestamp=datetime.fromtimestamp(int(tx.get("timeStamp", "0"))).isoformat(),
                                    block_number=int(tx.get("blockNumber", "0")),
                                    status="success" if tx.get("txreceipt_status") == "1" else "failed"
                                )
                                transactions.append(transaction)
                            return transactions
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting Etherscan transactions for {address}: {e}")
            return []
    
    # Removed mock transaction generator to enforce real data usage
    
    async def _rate_limit(self, service: str):
        """Simple rate limiting"""
        now = datetime.utcnow().timestamp()
        last_request = self.last_request_time.get(service, 0)
        
        if now - last_request < self.min_request_interval:
            await asyncio.sleep(self.min_request_interval - (now - last_request))
        
        self.last_request_time[service] = datetime.utcnow().timestamp()
    
    async def analyze_wallet_risk(self, address: str, transactions: List[BlockchainTransaction]) -> Dict[str, Any]:
        """Analyze wallet for risk factors"""
        risk_factors = []
        risk_score = 0
        
        # Analyze transaction patterns
        if len(transactions) > 50:
            risk_factors.append("High transaction volume")
            risk_score += 10
        
        # Check for large transactions
        large_transactions = [tx for tx in transactions if float(tx.value) > 10]
        if large_transactions:
            risk_factors.append(f"Large transactions detected ({len(large_transactions)})")
            risk_score += 15
        
        # Check for rapid transactions
        if len(transactions) > 10:
            recent_24h = [tx for tx in transactions 
                         if datetime.fromisoformat(tx.timestamp.replace('Z', '')) > 
                         datetime.utcnow() - timedelta(hours=24)]
            if len(recent_24h) > 10:
                risk_factors.append("High frequency trading detected")
                risk_score += 20
        
        # Check for known risky addresses (mock check)
        known_risky = ["0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb4"]
        for tx in transactions:
            if tx.from_address in known_risky or tx.to_address in known_risky:
                risk_factors.append("Interaction with flagged addresses")
                risk_score += 25
                break
        
        # Age analysis
        if transactions:
            oldest_tx = min(transactions, key=lambda x: x.timestamp)
            account_age = datetime.utcnow() - datetime.fromisoformat(oldest_tx.timestamp.replace('Z', ''))
            if account_age.days < 30:
                risk_factors.append("New account (less than 30 days)")
                risk_score += 15
        
        return {
            "risk_score": min(risk_score, 100),
            "risk_factors": risk_factors,
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "transaction_count": len(transactions),
            "unique_counterparties": len(set([tx.from_address for tx in transactions] + 
                                           [tx.to_address for tx in transactions])) - 1
        }

# Global blockchain service instance
blockchain_service = BlockchainDataService()
