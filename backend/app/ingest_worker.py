"""Background worker for continuous data ingestion"""
import asyncio
import logging
import signal
import sys
from datetime import datetime
from .ingest import ingester

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IngestWorker:
    """Background worker for periodic data ingestion"""
    
    def __init__(self, interval_seconds=300):  # Default 5 minutes
        self.interval = interval_seconds
        self.running = False
        
    async def start(self):
        """Start the ingestion worker"""
        self.running = True
        logger.info(f"Starting ingestion worker with {self.interval}s interval")
        
        while self.running:
            try:
                logger.info(f"Running ingestion cycle at {datetime.utcnow()}")
                result = await ingester.ingest_all()
                logger.info(f"Ingestion complete: {result}")
            except Exception as e:
                logger.error(f"Error during ingestion: {e}")
            
            # Wait for next cycle
            await asyncio.sleep(self.interval)
    
    def stop(self):
        """Stop the worker"""
        self.running = False
        logger.info("Stopping ingestion worker")

# Global worker instance
worker = IngestWorker()

def signal_handler(sig, frame):
    """Handle shutdown signals"""
    logger.info("Received shutdown signal")
    worker.stop()
    sys.exit(0)

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run the worker
    asyncio.run(worker.start())
