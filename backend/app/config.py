"""Configuration module for ReguChain Watch"""
import os
import configparser
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Look for .env file in the project root (parent of backend)
    env_path = Path(__file__).parent.parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Loaded environment variables from: {env_path}")
    else:
        print(f"⚠️ No .env file found at: {env_path}")
except ImportError:
    print("⚠️ python-dotenv not installed, using system environment variables only")

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

# API Keys - Read directly from environment variables
NEWSAPI_KEY = os.getenv('NEWSAPI_KEY', get_config('API_KEYS', 'NEWSAPI_KEY', ''))
GROQ_API_KEY = os.getenv('GROQ_API_KEY', get_config('API_KEYS', 'GROQ_API_KEY', ''))
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', get_config('API_KEYS', 'OPENROUTER_API_KEY', ''))

# Pathway Configuration
PATHWAY_KEY = os.getenv('PATHWAY_KEY', get_config('API_KEYS', 'PATHWAY_KEY', ''))
PATHWAY_MODE = os.getenv('PATHWAY_MODE', get_config('API_KEYS', 'PATHWAY_MODE', 'streaming'))
PATHWAY_STREAMING_MODE = os.getenv('PATHWAY_STREAMING_MODE', get_config('API_KEYS', 'PATHWAY_STREAMING_MODE', 'realtime'))
PATHWAY_PERSISTENCE_BACKEND = os.getenv('PATHWAY_PERSISTENCE_BACKEND', get_config('API_KEYS', 'PATHWAY_PERSISTENCE_BACKEND', 'filesystem'))
PATHWAY_PERSISTENCE_PATH = os.getenv('PATHWAY_PERSISTENCE_PATH', get_config('API_KEYS', 'PATHWAY_PERSISTENCE_PATH', './pathway_data'))
PATHWAY_MONITORING_LEVEL = os.getenv('PATHWAY_MONITORING_LEVEL', get_config('API_KEYS', 'PATHWAY_MONITORING_LEVEL', 'info'))

# Database
DATABASE_URL = os.getenv('DATABASE_URL', get_config('API_KEYS', 'DATABASE_URL', 'sqlite:///./reguchain.db'))

# Vector Store
VECTOR_DB_TYPE = os.getenv('VECTOR_DB_TYPE', get_config('API_KEYS', 'VECTOR_DB_TYPE', 'faiss'))
FAISS_INDEX_PATH = os.getenv('FAISS_INDEX_PATH', get_config('API_KEYS', 'FAISS_INDEX_PATH', './faiss_index'))

DISABLE_EMBEDDINGS = get_config('API_KEYS', 'DISABLE_EMBEDDINGS', 'false').lower() == 'true'
DISABLE_VECTOR_STORE = get_config('API_KEYS', 'DISABLE_VECTOR_STORE', 'false').lower() == 'true'
if DISABLE_EMBEDDINGS:
    EMBEDDINGS_PROVIDER = 'none'
    EMBEDDINGS_MODEL = 'none'
    EMBEDDINGS_DIMENSION = int(os.getenv('EMBEDDINGS_DIMENSION', '0'))
else:
    EMBEDDINGS_PROVIDER = os.getenv('EMBEDDINGS_PROVIDER', 'openrouter')
    EMBEDDINGS_MODEL = os.getenv('EMBEDDINGS_MODEL', 'text-embedding-3-small')
    # text-embedding-3-small dimension is 1536
    EMBEDDINGS_DIMENSION = int(os.getenv('EMBEDDINGS_DIMENSION', '1536'))

# LLM Configuration - OpenRouter for Pathway
LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'openrouter')
LLM_MODEL = os.getenv('LLM_MODEL', 'mistralai/mistral-7b-instruct')
LLM_TEMPERATURE = float(os.getenv('LLM_TEMPERATURE', '0.3'))

# Blockchain
ETHEREUM_RPC_URL = os.getenv('ETHEREUM_RPC_URL', 'https://eth-mainnet.g.alchemy.com/v2/demo')
POLYGON_RPC_URL = os.getenv('POLYGON_RPC_URL', 'https://polygon-rpc.com')
ETHERSCAN_API_KEY = os.getenv('ETHERSCAN_API_KEY', '')

# Risk Assessment
RISK_SCORE_THRESHOLD = float(os.getenv('RISK_SCORE_THRESHOLD', '50'))
TRANSACTION_THRESHOLD = float(os.getenv('TRANSACTION_THRESHOLD', '10000.0'))

# OFAC Sanctions Lists
OFAC_SDN_URL = os.getenv('OFAC_SDN_URL', 'https://www.treasury.gov/ofac/downloads/sdn.csv')
OFAC_CONSOLIDATED_URL = os.getenv('OFAC_CONSOLIDATED_URL', 'https://www.treasury.gov/ofac/downloads/consolidated/consolidated.xml')

# RSS Regulatory Feeds
SEC_RSS_URL = os.getenv('SEC_RSS_URL', 'https://www.sec.gov/news/pressreleases.rss')
CFTC_RSS_URL = os.getenv('CFTC_RSS_URL', 'https://www.cftc.gov/news/rss')
FINRA_RSS_URL = os.getenv('FINRA_RSS_URL', 'https://www.finra.org/about/news-center/rss')

# NewsData.io API configuration
NEWSAPI_ENDPOINT = os.getenv('NEWSAPI_ENDPOINT', 'https://newsdata.io/api/1/news')
