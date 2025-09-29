"""
Real-time API endpoints for Pathway streaming and news analysis
"""
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel

from .realtime_pathway_service import realtime_pathway_service
from .realtime_news_service import realtime_news_service

logger = logging.getLogger(__name__)

# Create router
realtime_router = APIRouter(prefix="/api/realtime", tags=["realtime"])

class StreamStatus(BaseModel):
    """Stream status response model"""
    status: str
    timestamp: str
    pathway_available: bool
    news_api_available: bool
    gemini_available: bool
    active_streams: List[str]

class NewsQuery(BaseModel):
    """News query request model"""
    query: str = "cryptocurrency OR blockchain OR regulatory"
    sources: Optional[str] = None
    language: str = "en"
    page_size: int = 50

class DashboardData(BaseModel):
    """Dashboard data response model"""
    timestamp: str
    status: str
    total_articles_processed: int
    high_priority_count: int
    critical_alerts_count: int
    recent_categories: Dict[str, int]
    sentiment_distribution: Dict[str, int]
    avg_relevance_score: float

@realtime_router.get("/status", response_model=StreamStatus)
async def get_stream_status():
    """Get current status of real-time streams"""
    try:
        dashboard = await realtime_pathway_service.get_realtime_dashboard()
        
        return StreamStatus(
            status=dashboard.get('status', 'inactive'),
            timestamp=dashboard.get('timestamp', datetime.now().isoformat()),
            pathway_available=dashboard.get('pathway_available', False),
            news_api_available=bool(realtime_news_service.api_key),
            gemini_available=bool(realtime_news_service.gemini_model),
            active_streams=dashboard.get('streams', {}).get('active_streams', [])
        )
    except Exception as e:
        logger.error(f"Error getting stream status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@realtime_router.post("/start")
async def start_realtime_processing(background_tasks: BackgroundTasks):
    """Start real-time news processing and Pathway streaming"""
    try:
        if realtime_pathway_service.is_running:
            return {"message": "Real-time processing is already running", "status": "active"}
        
        # Start the pipeline in background
        background_tasks.add_task(realtime_pathway_service.start_realtime_pipeline)
        
        return {
            "message": "Real-time processing started successfully",
            "status": "starting",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error starting real-time processing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@realtime_router.post("/stop")
async def stop_realtime_processing():
    """Stop real-time news processing"""
    try:
        await realtime_pathway_service.stop_pipeline()
        
        return {
            "message": "Real-time processing stopped successfully",
            "status": "stopped",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error stopping real-time processing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@realtime_router.get("/dashboard")
async def get_realtime_dashboard():
    """Get real-time dashboard with comprehensive metrics"""
    try:
        dashboard = await realtime_pathway_service.get_realtime_dashboard()
        
        # Enhance with additional metrics
        if 'statistics' in dashboard:
            stats = dashboard['statistics']
            
            return {
                "timestamp": dashboard['timestamp'],
                "status": dashboard['status'],
                "pathway_available": dashboard.get('pathway_available', False),
                "total_articles_processed": stats.get('processed_news', {}).get('total_count', 0),
                "high_priority_count": stats.get('high_priority_news', {}).get('count', 0),
                "critical_alerts_count": stats.get('critical_alerts', {}).get('count', 0),
                "recent_categories": stats.get('processed_news', {}).get('categories', {}),
                "sentiment_distribution": stats.get('processed_news', {}).get('sentiment_distribution', {}),
                "avg_relevance_score": stats.get('processed_news', {}).get('avg_relevance_score', 0.0),
                "streams": dashboard.get('streams', {}),
                "recent_alerts": stats.get('critical_alerts', {}).get('recent_count', 0),
                "recent_high_priority": stats.get('high_priority_news', {}).get('recent_count', 0)
            }
        else:
            return dashboard
            
    except Exception as e:
        logger.error(f"Error getting dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@realtime_router.post("/news/fetch")
async def fetch_latest_news(query: NewsQuery):
    """Fetch latest news articles with AI analysis"""
    try:
        async with realtime_news_service:
            articles = await realtime_news_service.fetch_realtime_news(
                query=query.query,
                sources=query.sources,
                language=query.language,
                page_size=query.page_size
            )
        
        return {
            "message": f"Fetched {len(articles)} articles",
            "count": len(articles),
            "articles": [article.to_dict() for article in articles[:10]],  # Return first 10 for API response
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching news: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@realtime_router.get("/news/headlines")
async def get_top_headlines(
    category: str = Query("business", description="News category"),
    country: str = Query("us", description="Country code"),
    page_size: int = Query(20, description="Number of articles")
):
    """Get top headlines with regulatory focus"""
    try:
        async with realtime_news_service:
            articles = await realtime_news_service.fetch_top_headlines(
                category=category,
                country=country,
                page_size=page_size
            )
        
        return {
            "message": f"Fetched {len(articles)} headlines",
            "count": len(articles),
            "headlines": [article.to_dict() for article in articles],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching headlines: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@realtime_router.get("/streams/{stream_name}")
async def query_stream(
    stream_name: str,
    limit: int = Query(10, description="Number of records to return")
):
    """Query a specific data stream"""
    try:
        valid_streams = ['processed_news', 'high_priority_news', 'critical_alerts', 'realtime_news']
        
        if stream_name not in valid_streams:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid stream name. Valid streams: {valid_streams}"
            )
        
        records = await realtime_pathway_service.query_stream(stream_name, limit)
        
        return {
            "stream_name": stream_name,
            "count": len(records),
            "records": records,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying stream {stream_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@realtime_router.get("/alerts/critical")
async def get_critical_alerts(limit: int = Query(5, description="Number of alerts to return")):
    """Get critical regulatory alerts"""
    try:
        alerts = await realtime_pathway_service.query_stream('critical_alerts', limit)
        
        return {
            "message": f"Retrieved {len(alerts)} critical alerts",
            "count": len(alerts),
            "alerts": alerts,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting critical alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@realtime_router.get("/news/regulatory")
async def get_regulatory_news():
    """Get news specifically from regulatory sources"""
    try:
        async with realtime_news_service:
            articles = await realtime_news_service.get_regulatory_sources_news()
        
        return {
            "message": f"Fetched {len(articles)} regulatory articles",
            "count": len(articles),
            "articles": [article.to_dict() for article in articles],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching regulatory news: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@realtime_router.get("/health")
async def health_check():
    """Health check for real-time services"""
    try:
        # Check service availability
        services = {
            "pathway_service": realtime_pathway_service is not None,
            "news_service": realtime_news_service is not None,
            "pathway_available": realtime_pathway_service.pathway_key is not None,
            "news_api_available": realtime_news_service.api_key is not None,
            "gemini_available": realtime_news_service.gemini_model is not None,
            "pipeline_running": realtime_pathway_service.is_running
        }
        
        # Overall health status
        critical_services = ["pathway_service", "news_service"]
        health_status = "healthy" if all(services[service] for service in critical_services) else "degraded"
        
        if not services["pathway_available"] or not services["news_api_available"]:
            health_status = "limited"
        
        return {
            "status": health_status,
            "timestamp": datetime.now().isoformat(),
            "services": services,
            "message": "Real-time services health check completed"
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "message": "Health check failed"
        }

@realtime_router.post("/test/pipeline")
async def test_pipeline():
    """Test the real-time pipeline with sample data"""
    try:
        # Generate test data
        async with realtime_news_service:
            test_articles = await realtime_news_service._generate_mock_news()
        
        return {
            "message": "Pipeline test completed successfully",
            "test_articles_generated": len(test_articles),
            "sample_articles": [article.to_dict() for article in test_articles[:3]],
            "timestamp": datetime.now().isoformat(),
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Pipeline test error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
