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
    from app.realtime_news_service import realtime_news_service
    from app.realtime_pathway_service import realtime_pathway_service
    from app.ingest import ingester
    
    # Initialize database
    logger.info("Initializing database...")
    init_db()
    
    # Initialize vector store
    logger.info("Initializing vector store...")
    stats = vector_store.get_stats()
    logger.info(f"Vector store stats: {stats}")
    
    # Test real-time news service
    logger.info("Testing real-time news service...")
    try:
        async with realtime_news_service:
            articles = await realtime_news_service.fetch_realtime_news(
                query="cryptocurrency regulation SEC CFTC",
                page_size=3
            )
            logger.info(f"Realtime news test: Found {len(articles)} articles")
            headlines = await realtime_news_service.fetch_top_headlines(page_size=1)
            logger.info(f"Headlines test: Found {len(headlines)} article(s)")
    except Exception as e:
        logger.error(f"Realtime news test failed: {e}")
    
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
    
    # Start Pathway streaming if available (use realtime service)
    logger.info("Checking Pathway streaming...")
    try:
        if realtime_pathway_service.pathway_key:
            await realtime_pathway_service.start_realtime_pipeline()
            logger.info("Realtime Pathway pipeline started")
        else:
            logger.info("PATHWAY_KEY not configured - real-time streaming disabled")
    except Exception as e:
        logger.warning(f"Realtime Pathway pipeline not available: {e}")
    
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
