"""Configuration module for ReguChain Watch"""
import os
import configparser
from pathlib import Path

# Load configuration from config.ini or config_free_llm.ini
config = configparser.ConfigParser()
config_paths = [
    Path(__file__).parent.parent.parent / 'config_free_llm.ini',
    Path(__file__).parent.parent.parent / 'config.ini'
]

config_loaded = False
for config_path in config_paths:
    if config_path.exists():
        config.read(config_path)
        config_loaded = True
        print(f"Loaded config from: {config_path.name}")
        break

if config_loaded:
    def get_config(section, key, default=''):
        try:
            return config.get(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return os.getenv(f"{section}_{key}", default)
else:
    def get_config(section, key, default=''):
        return os.getenv(f"{section}_{key}", default)

# API Keys
NEWSAPI_KEY = get_config('API_KEYS', 'NEWSAPI_KEY', '')
GROQ_API_KEY = get_config('API_KEYS', 'GROQ_API_KEY', '') or os.getenv('GROQ_API_KEY', '')
OPENROUTER_API_KEY = get_config('API_KEYS', 'OPENROUTER_API_KEY', '') or os.getenv('OPENROUTER_API_KEY', '')

# Pathway Configuration
PATHWAY_KEY = get_config('API_KEYS', 'PATHWAY_KEY', '')
PATHWAY_MODE = get_config('API_KEYS', 'PATHWAY_MODE', 'streaming')
PATHWAY_STREAMING_MODE = get_config('API_KEYS', 'PATHWAY_STREAMING_MODE', 'realtime')
PATHWAY_PERSISTENCE_BACKEND = get_config('API_KEYS', 'PATHWAY_PERSISTENCE_BACKEND', 'filesystem')
PATHWAY_PERSISTENCE_PATH = get_config('API_KEYS', 'PATHWAY_PERSISTENCE_PATH', './pathway_data')
PATHWAY_MONITORING_LEVEL = get_config('API_KEYS', 'PATHWAY_MONITORING_LEVEL', 'info')

# Database
DATABASE_URL = get_config('API_KEYS', 'DATABASE_URL', 'sqlite:///./reguchain.db')

# Vector Store
VECTOR_DB_TYPE = get_config('API_KEYS', 'VECTOR_DB_TYPE', 'faiss')
FAISS_INDEX_PATH = get_config('API_KEYS', 'FAISS_INDEX_PATH', './faiss_index')

DISABLE_EMBEDDINGS = get_config('API_KEYS', 'DISABLE_EMBEDDINGS', 'false').lower() == 'true'
DISABLE_VECTOR_STORE = get_config('API_KEYS', 'DISABLE_VECTOR_STORE', 'false').lower() == 'true'
if DISABLE_EMBEDDINGS:
    EMBEDDINGS_PROVIDER = 'none'
    EMBEDDINGS_MODEL = 'none'
    EMBEDDINGS_DIMENSION = int(get_config('API_KEYS', 'EMBEDDINGS_DIMENSION', '0'))
else:
    EMBEDDINGS_PROVIDER = get_config('API_KEYS', 'EMBEDDINGS_PROVIDER', 'huggingface')
    EMBEDDINGS_MODEL = get_config('API_KEYS', 'EMBEDDINGS_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
    # all-MiniLM-L6-v2 dimension is 384
    EMBEDDINGS_DIMENSION = int(get_config('API_KEYS', 'EMBEDDINGS_DIMENSION', '384'))

# LLM Configuration - OpenRouter for Pathway
LLM_PROVIDER = get_config('API_KEYS', 'LLM_PROVIDER', 'openrouter')
LLM_MODEL = get_config('API_KEYS', 'LLM_MODEL', 'mistralai/mistral-7b-instruct')
EMBEDDINGS_MODEL = get_config('API_KEYS', 'EMBEDDINGS_MODEL', 'text-embedding-3-small')

LLM_TEMPERATURE = float(get_config('API_KEYS', 'LLM_TEMPERATURE', '0.3'))

# Blockchain
ETHEREUM_RPC_URL = get_config('API_KEYS', 'ETHEREUM_RPC_URL', 'https://eth-mainnet.g.alchemy.com/v2/demo')
POLYGON_RPC_URL = get_config('API_KEYS', 'POLYGON_RPC_URL', 'https://polygon-rpc.com')
ETHERSCAN_API_KEY = get_config('API_KEYS', 'ETHERSCAN_API_KEY', '')

# Risk Assessment
RISK_SCORE_THRESHOLD = float(get_config('API_KEYS', 'RISK_SCORE_THRESHOLD', '50'))
TRANSACTION_THRESHOLD = float(get_config('API_KEYS', 'TRANSACTION_THRESHOLD', '10000.0'))

# OFAC Sanctions Lists
OFAC_SDN_URL = get_config('API_KEYS', 'OFAC_SDN_URL', 'https://www.treasury.gov/ofac/downloads/sdn.csv')
OFAC_CONSOLIDATED_URL = get_config('API_KEYS', 'OFAC_CONSOLIDATED_URL', 'https://www.treasury.gov/ofac/downloads/consolidated/consolidated.xml')

# RSS Regulatory Feeds
SEC_RSS_URL = get_config('API_KEYS', 'SEC_RSS_URL', 'https://www.sec.gov/news/pressreleases.rss')
CFTC_RSS_URL = get_config('API_KEYS', 'CFTC_RSS_URL', 'https://www.cftc.gov/news/rss')
FINRA_RSS_URL = get_config('API_KEYS', 'FINRA_RSS_URL', 'https://www.finra.org/about/news-center/rss')

# NewsData.io API configuration
NEWSAPI_ENDPOINT = "https://newsdata.io/api/1/news"
