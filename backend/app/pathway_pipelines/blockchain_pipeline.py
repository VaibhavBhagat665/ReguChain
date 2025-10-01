"""
Pathway Blockchain Pipeline
Continuous ingestion of Ethereum and Polygon transactions
"""
import pathway as pw
import requests
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging
from ..config import ETHEREUM_RPC_URL, POLYGON_RPC_URL, ETHERSCAN_API_KEY, TRANSACTION_THRESHOLD

logger = logging.getLogger(__name__)

class BlockchainPathwayPipeline:
    """Pathway-powered blockchain transaction ingestion"""
    
    def __init__(self):
        self.ethereum_rpc = ETHEREUM_RPC_URL
        self.polygon_rpc = POLYGON_RPC_URL
        self.etherscan_key = ETHERSCAN_API_KEY
        self.transaction_threshold = TRANSACTION_THRESHOLD
        self.last_block_processed = {}
        self.target_wallets = set()
        
    def add_target_wallet(self, wallet_address: str):
        """Add wallet to monitoring list"""
        self.target_wallets.add(wallet_address.lower())
        logger.info(f"📍 Added target wallet: {wallet_address}")
    
    def create_blockchain_pipeline(self):
        """Create Pathway pipeline for blockchain transactions"""
        
        @pw.udf
        def fetch_blockchain_data() -> pw.Table:
            """Fetch latest blockchain transactions"""
            all_documents = []
            
            # Fetch from Ethereum
            if self.ethereum_rpc:
                eth_docs = self._fetch_chain_transactions(self.ethereum_rpc, "ethereum")
                all_documents.extend(eth_docs)
            
            # Fetch from Polygon
            if self.polygon_rpc:
                poly_docs = self._fetch_chain_transactions(self.polygon_rpc, "polygon")
                all_documents.extend(poly_docs)
            
            # Fetch target wallet transactions via Etherscan
            if self.etherscan_key and self.target_wallets:
                for wallet in self.target_wallets:
                    wallet_docs = self._fetch_wallet_transactions(wallet)
                    all_documents.extend(wallet_docs)
            
            logger.info(f"🎯 Total blockchain documents: {len(all_documents)}")
            return pw.Table.from_pandas(pw.pandas.DataFrame(all_documents)) if all_documents else pw.Table.empty()
        
        # Create periodic trigger every 1 minute
        trigger = pw.io.http.rest_connector(
            host="localhost",
            port=8080,
            route="/trigger/blockchain",
            schema=pw.Schema.from_types(trigger=str),
            autocommit_duration_ms=60000  # 1 minute
        )
        
        # Transform trigger into blockchain data
        blockchain_data = trigger.select(
            data=fetch_blockchain_data()
        ).flatten(pw.this.data)
        
        # Add processing metadata
        blockchain_data = blockchain_data.select(
            *pw.this,
            processed_at=datetime.now().isoformat(),
            pipeline_type='blockchain_transactions'
        )
        
        return blockchain_data
    
    def _fetch_chain_transactions(self, rpc_url: str, chain: str) -> List[Dict[str, Any]]:
        """Fetch transactions from a specific blockchain"""
        documents = []
        
        try:
            logger.info(f"🔍 Fetching {chain} transactions...")
            
            # Get latest block number
            latest_block = self._get_latest_block(rpc_url)
            if not latest_block:
                return documents
            
            # Determine starting block
            last_processed = self.last_block_processed.get(chain, latest_block - 5)
            start_block = max(last_processed + 1, latest_block - 10)  # Process last 10 blocks max
            
            # Process blocks
            for block_num in range(start_block, latest_block + 1):
                block_docs = self._fetch_block_transactions(rpc_url, block_num, chain)
                documents.extend(block_docs)
                self.last_block_processed[chain] = block_num
            
            logger.info(f"✅ Fetched {len(documents)} transactions from {chain} (blocks {start_block}-{latest_block})")
            
        except Exception as e:
            logger.error(f"❌ Error fetching {chain} transactions: {e}")
        
        return documents
    
    def _get_latest_block(self, rpc_url: str) -> Optional[int]:
        """Get latest block number"""
        try:
            payload = {
                "jsonrpc": "2.0",
                "method": "eth_blockNumber",
                "params": [],
                "id": 1
            }
            
            response = requests.post(rpc_url, json=payload, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            block_hex = data.get('result')
            if block_hex:
                return int(block_hex, 16)
                
        except Exception as e:
            logger.error(f"❌ Error getting latest block: {e}")
        
        return None
    
    def _fetch_block_transactions(self, rpc_url: str, block_number: int, chain: str) -> List[Dict[str, Any]]:
        """Fetch transactions from a specific block"""
        documents = []
        
        try:
            payload = {
                "jsonrpc": "2.0",
                "method": "eth_getBlockByNumber",
                "params": [hex(block_number), True],
                "id": 1
            }
            
            response = requests.post(rpc_url, json=payload, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            block = data.get('result')
            if not block:
                return documents
            
            # Process transactions
            transactions = block.get('transactions', [])
            
            for tx in transactions:
                tx_hash = tx.get('hash', '')
                from_addr = tx.get('from', '').lower()
                to_addr = tx.get('to', '').lower() if tx.get('to') else ''
                value_hex = tx.get('value', '0x0')
                
                # Convert value from hex to decimal (wei)
                try:
                    value_wei = int(value_hex, 16)
                    value_eth = value_wei / 10**18  # Convert to ETH
                except:
                    value_eth = 0
                
                # Check if this involves target wallets or high value
                is_target_match = (from_addr in self.target_wallets or 
                                 to_addr in self.target_wallets)
                is_high_value = value_eth > (self.transaction_threshold / 1000)  # Convert to ETH
                
                # Only process if it's a target match or high value
                if is_target_match or is_high_value:
                    risk_level = self._assess_transaction_risk(value_eth, is_target_match)
                    
                    doc = {
                        'id': f"{chain.lower()}_tx_{tx_hash}",
                        'source': f"{chain.upper()}_BLOCKCHAIN",
                        'text': f"{chain} Transaction: {from_addr} -> {to_addr} ({value_eth:.4f} ETH)",
                        'timestamp': datetime.now().isoformat(),
                        'link': f"https://{'etherscan.io' if chain == 'ethereum' else 'polygonscan.com'}/tx/{tx_hash}",
                        'type': 'blockchain_transaction',
                        'metadata': {
                            'chain': chain,
                            'hash': tx_hash,
                            'from_address': from_addr,
                            'to_address': to_addr,
                            'value_wei': str(value_wei),
                            'value_eth': value_eth,
                            'block_number': block_number,
                            'category': 'blockchain_transaction',
                            'onchain_match': is_target_match,
                            'risk_level': risk_level,
                            'is_high_value': is_high_value
                        }
                    }
                    documents.append(doc)
            
        except Exception as e:
            logger.error(f"❌ Error fetching block {block_number}: {e}")
        
        return documents
    
    def _fetch_wallet_transactions(self, wallet_address: str) -> List[Dict[str, Any]]:
        """Fetch recent transactions for a specific wallet using Etherscan API"""
        documents = []
        
        try:
            if not self.etherscan_key:
                return documents
            
            logger.info(f"🔍 Fetching Etherscan transactions for {wallet_address}")
            
            url = "https://api.etherscan.io/api"
            params = {
                'module': 'account',
                'action': 'txlist',
                'address': wallet_address,
                'startblock': 0,
                'endblock': 99999999,
                'page': 1,
                'offset': 20,  # Last 20 transactions
                'sort': 'desc',
                'apikey': self.etherscan_key
            }
            
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            if data.get('status') != '1':
                return documents
            
            # Process transactions
            transactions = data.get('result', [])
            
            for tx in transactions:
                tx_hash = tx.get('hash', '')
                from_addr = tx.get('from', '').lower()
                to_addr = tx.get('to', '').lower()
                value_wei = int(tx.get('value', '0'))
                value_eth = value_wei / 10**18
                timestamp = int(tx.get('timeStamp', 0))
                
                risk_level = self._assess_transaction_risk(value_eth, True)
                
                doc = {
                    'id': f"etherscan_tx_{tx_hash}",
                    'source': 'ETHERSCAN_API',
                    'text': f"Ethereum Transaction: {from_addr} -> {to_addr} ({value_eth:.4f} ETH)",
                    'timestamp': datetime.fromtimestamp(timestamp).isoformat(),
                    'link': f"https://etherscan.io/tx/{tx_hash}",
                    'type': 'wallet_transaction',
                    'metadata': {
                        'chain': 'ethereum',
                        'hash': tx_hash,
                        'from_address': from_addr,
                        'to_address': to_addr,
                        'value_wei': str(value_wei),
                        'value_eth': value_eth,
                        'block_number': int(tx.get('blockNumber', 0)),
                        'category': 'wallet_transaction',
                        'target_wallet': wallet_address.lower(),
                        'onchain_match': True,
                        'risk_level': risk_level
                    }
                }
                documents.append(doc)
            
            logger.info(f"✅ Fetched {len(documents)} transactions for wallet {wallet_address}")
            
        except Exception as e:
            logger.error(f"❌ Error fetching wallet transactions: {e}")
        
        return documents
    
    def _assess_transaction_risk(self, value_eth: float, is_target_match: bool) -> str:
        """Assess transaction risk level"""
        if is_target_match:
            return 'high'  # Any transaction involving target wallets
        elif value_eth > 1000:
            return 'high'  # Very high value
        elif value_eth > 100:
            return 'medium'  # High value
        elif value_eth > 10:
            return 'low'  # Medium value
        else:
            return 'minimal'

# Global instance
blockchain_pathway_pipeline = BlockchainPathwayPipeline()
