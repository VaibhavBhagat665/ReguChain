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
            return default
    # Fallback to environment variables if no config file exists
    def get_config(section, key, default=''):
        return os.getenv(f"{section}_{key}", default)

# API Keys
NEWSAPI_KEY = get_config('API_KEYS', 'NEWSAPI_KEY', '')
GROQ_API_KEY = get_config('API_KEYS', 'GROQ_API_KEY', '') or os.getenv('GROQ_API_KEY', '')

# Pathway Configuration
PATHWAY_KEY = get_config('API_KEYS', 'PATHWAY_KEY', '')
PATHWAY_STREAMING_MODE = get_config('API_KEYS', 'PATHWAY_STREAMING_MODE', 'realtime')
PATHWAY_PERSISTENCE_BACKEND = get_config('API_KEYS', 'PATHWAY_PERSISTENCE_BACKEND', 'filesystem')
PATHWAY_PERSISTENCE_PATH = get_config('API_KEYS', 'PATHWAY_PERSISTENCE_PATH', './pathway_data')
PATHWAY_MONITORING_LEVEL = get_config('API_KEYS', 'PATHWAY_MONITORING_LEVEL', 'info')

# Database
DATABASE_URL = get_config('API_KEYS', 'DATABASE_URL', 'sqlite:///./reguchain.db')

# Vector Store
VECTOR_DB_TYPE = get_config('API_KEYS', 'VECTOR_DB_TYPE', 'faiss')
FAISS_INDEX_PATH = get_config('API_KEYS', 'FAISS_INDEX_PATH', './faiss_index')

# Embeddings (Disable if using free LLM)
DISABLE_EMBEDDINGS = get_config('API_KEYS', 'DISABLE_EMBEDDINGS', 'false').lower() == 'true'
DISABLE_VECTOR_STORE = get_config('API_KEYS', 'DISABLE_VECTOR_STORE', 'false').lower() == 'true'

if DISABLE_EMBEDDINGS:
    EMBEDDINGS_PROVIDER = 'none'
    EMBEDDINGS_MODEL = 'none'
else:
    EMBEDDINGS_PROVIDER = get_config('API_KEYS', 'EMBEDDINGS_PROVIDER', 'google')
    EMBEDDINGS_MODEL = get_config('API_KEYS', 'EMBEDDINGS_MODEL', 'models/embedding-001')

EMBEDDINGS_DIMENSION = int(get_config('API_KEYS', 'EMBEDDINGS_DIMENSION', '768'))

# LLM Configuration - Use Groq if available, fallback to Google
if GROQ_API_KEY:
    LLM_PROVIDER = get_config('API_KEYS', 'LLM_PROVIDER', 'groq')
    LLM_MODEL = get_config('API_KEYS', 'LLM_MODEL', 'llama3-8b-8192')
else:
    LLM_PROVIDER = get_config('API_KEYS', 'LLM_PROVIDER', 'google')
    LLM_MODEL = get_config('API_KEYS', 'LLM_MODEL', 'gemini-pro')

LLM_TEMPERATURE = float(get_config('API_KEYS', 'LLM_TEMPERATURE', '0.3'))

# Blockchain
ETHEREUM_RPC_URL = get_config('API_KEYS', 'ETHEREUM_RPC_URL', 'https://eth-mainnet.g.alchemy.com/v2/demo')
POLYGON_RPC_URL = get_config('API_KEYS', 'POLYGON_RPC_URL', 'https://polygon-rpc.com')
ETHERSCAN_API_KEY = get_config('API_KEYS', 'ETHERSCAN_API_KEY', '')

# Risk Assessment
RISK_SCORE_THRESHOLD = float(get_config('API_KEYS', 'RISK_SCORE_THRESHOLD', '50'))
TRANSACTION_THRESHOLD = float(get_config('API_KEYS', 'TRANSACTION_THRESHOLD', '10000'))

# Data Sources
OFAC_SDN_URL = "https://www.treasury.gov/ofac/downloads/sdn.csv"
SEC_RSS_URL = "https://www.sec.gov/rss/litigation/litreleases.xml"
CFTC_RSS_URL = "https://www.cftc.gov/RSS/cftcrss.xml"
FINRA_RSS_URL = "https://www.finra.org/rss/news/all"
NEWSAPI_ENDPOINT = "https://newsapi.org/v2/everything"

# Ensure directories exist
Path(PATHWAY_PERSISTENCE_PATH).mkdir(parents=True, exist_ok=True)
Path(FAISS_INDEX_PATH).parent.mkdir(parents=True, exist_ok=True)
