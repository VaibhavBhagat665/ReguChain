"""Configuration module for ReguChain Watch"""
import os
from pathlib import Path

# API Keys
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")

# Pathway Configuration
PATHWAY_KEY = os.getenv("PATHWAY_KEY", "")
PATHWAY_MODE = os.getenv("PATHWAY_MODE", "streaming")
PATHWAY_STREAMING_MODE = os.getenv("PATHWAY_STREAMING_MODE", "realtime")
PATHWAY_PERSISTENCE_BACKEND = os.getenv("PATHWAY_PERSISTENCE_BACKEND", "filesystem")
PATHWAY_PERSISTENCE_PATH = os.getenv("PATHWAY_PERSISTENCE_PATH", "./pathway_data")
PATHWAY_MONITORING_LEVEL = os.getenv("PATHWAY_MONITORING_LEVEL", "info")

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./reguchain.db")

# Vector Store
VECTOR_DB_TYPE = os.getenv("VECTOR_DB_TYPE", "faiss")
FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "./faiss_index")

# Embeddings
EMBEDDINGS_PROVIDER = os.getenv("EMBEDDINGS_PROVIDER", "google")
EMBEDDINGS_MODEL = os.getenv("EMBEDDINGS_MODEL", "models/embedding-001")
EMBEDDINGS_DIMENSION = int(os.getenv("EMBEDDINGS_DIMENSION", "768"))

# LLM
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "google")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-pro")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))

# Blockchain
ETHEREUM_RPC_URL = os.getenv("ETHEREUM_RPC_URL", "https://eth-mainnet.g.alchemy.com/v2/demo")
POLYGON_RPC_URL = os.getenv("POLYGON_RPC_URL", "https://polygon-rpc.com")
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY", "")

# Risk Assessment
RISK_SCORE_THRESHOLD = float(os.getenv("RISK_SCORE_THRESHOLD", "50"))
TRANSACTION_THRESHOLD = float(os.getenv("TRANSACTION_THRESHOLD", "10000"))

# Data Sources
OFAC_SDN_URL = "https://www.treasury.gov/ofac/downloads/sdn.csv"
SEC_RSS_URL = "https://www.sec.gov/rss/litigation/litreleases.xml"
CFTC_RSS_URL = "https://www.cftc.gov/RSS/cftcrss.xml"
FINRA_RSS_URL = "https://www.finra.org/rss/news/all"
NEWSAPI_ENDPOINT = "https://newsapi.org/v2/everything"

# Ensure directories exist
Path(PATHWAY_PERSISTENCE_PATH).mkdir(parents=True, exist_ok=True)
Path(FAISS_INDEX_PATH).parent.mkdir(parents=True, exist_ok=True)
