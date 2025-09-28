"""
Startup script for ReguChain backend with all integrations
"""
import os
import sys
import asyncio
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def initialize_services():
    """Initialize all backend services"""
    logger.info("Initializing ReguChain backend services...")
    
    # Import services
    from app.database import init_db
    from app.vector_store import vector_store
    from app.langchain_agent import langchain_agent
    from app.news_service import news_service
    from app.pathway_service import pathway_service
    from app.ingest import ingester
    
    # Initialize database
    logger.info("Initializing database...")
    init_db()
    
    # Initialize vector store
    logger.info("Initializing vector store...")
    stats = vector_store.get_stats()
    logger.info(f"Vector store stats: {stats}")
    
    # Test news service
    logger.info("Testing news service...")
    try:
        # Test NewsData API
        articles = await news_service.fetch_newsdata_articles(
            query="cryptocurrency regulation",
            category="business"
        )
        logger.info(f"NewsData API test: Found {len(articles)} articles")
        
        # Test RSS feeds
        rss_articles = await news_service.fetch_rss_feeds()
        logger.info(f"RSS feeds test: Found {len(rss_articles)} articles")
    except Exception as e:
        logger.error(f"News service test failed: {e}")
    
    # Test LangChain agent
    logger.info("Testing LangChain agent...")
    try:
        response = langchain_agent.query("What are the latest SEC regulations?")
        logger.info(f"LangChain test response: {response.get('success')}")
    except Exception as e:
        logger.error(f"LangChain test failed: {e}")
    
    # Initial data ingestion
    logger.info("Starting initial data ingestion...")
    try:
        results = await ingester.ingest_all()
        logger.info(f"Ingestion results: {results}")
    except Exception as e:
        logger.error(f"Initial ingestion failed: {e}")
    
    # Start Pathway streaming if available
    logger.info("Checking Pathway streaming...")
    try:
        if pathway_service.pathway_key:
            await pathway_service.start_streaming()
            logger.info("Pathway streaming started")
        else:
            logger.info("Pathway key not configured - streaming disabled")
    except Exception as e:
        logger.warning(f"Pathway streaming not available: {e}")
    
    logger.info("All services initialized successfully!")

def run_backend():
    """Run the FastAPI backend"""
    import uvicorn
    from app.main import app
    
    logger.info("Starting FastAPI server...")
    
    # Run initialization
    asyncio.run(initialize_services())
    
    # Start the server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    run_backend()
