"""
Real-time API endpoints for Pathway streaming and news analysis
"""
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel

from .realtime_news_service import realtime_news_service
from .realtime_pathway_service import realtime_pathway_service
from .wallet_tracking_service import wallet_tracking_service

logger = logging.getLogger(__name__)

# Create router
realtime_router = APIRouter(prefix="/api/realtime", tags=["realtime"])

class StreamStatus(BaseModel):
    """Stream status response model"""
    status: str
    timestamp: str
    pathway_available: bool
    news_api_available: bool
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
                # Wallet metrics via Pathway
                "wallet_transactions_count": stats.get('wallet_transactions', {}).get('count', 0),
                "wallet_high_risk_tx_count": stats.get('wallet_transactions', {}).get('high_risk', 0),
                "wallet_alerts_count": stats.get('wallet_alerts', {}).get('count', 0),
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
        
        # Format articles with verification links
        formatted_articles = []
        for article in articles[:10]:
            article_dict = article.to_dict()
            # Ensure URL is included for transparency
            article_dict["verification_url"] = article.url
            article_dict["source_verification"] = f"Verify at: {article.url}"
            formatted_articles.append(article_dict)
        
        return {
            "message": f"Fetched {len(articles)} real articles with verification links",
            "count": len(articles),
            "articles": formatted_articles,
            "data_source": "real_news_api",
            "transparency_note": "All articles include verification URLs for fact-checking",
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
    limit: int = Query(10, description="Number of records to return"),
    wallet_address: Optional[str] = Query(None, description="Filter by wallet address for wallet streams")
):
    """Query a specific data stream"""
    try:
        valid_streams = [
            'processed_news',
            'high_priority_news',
            'critical_alerts',
            'realtime_news',
            'wallet_transactions',
            'wallet_transactions_processed',
            'wallet_alerts'
        ]
        
        if stream_name not in valid_streams:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid stream name. Valid streams: {valid_streams}"
            )
        
        records = await realtime_pathway_service.query_stream(stream_name, limit, wallet_address)
        
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
            "groq_available": getattr(realtime_news_service, 'groq_client', None) is not None,
            "pipeline_running": realtime_pathway_service.is_running,
            "connected_wallets": len(getattr(realtime_pathway_service, 'connected_wallets', set()))
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

# Removed mock pipeline test endpoint to enforce real data only

# Wallet Tracking Endpoints
@realtime_router.post("/wallet/track")
async def add_wallet_tracking(wallet_address: str, monitoring_level: str = "standard"):
    """Add wallet address for real-time compliance tracking"""
    try:
        success = await wallet_tracking_service.add_wallet_for_tracking(
            wallet_address, monitoring_level
        )
        
        if success:
            return {
                "message": f"Wallet {wallet_address} added for {monitoring_level} monitoring",
                "wallet_address": wallet_address,
                "monitoring_level": monitoring_level,
                "timestamp": datetime.now().isoformat(),
                "status": "tracking_started"
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to add wallet for tracking")
            
    except Exception as e:
        logger.error(f"Error adding wallet tracking: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@realtime_router.get("/wallet/{wallet_address}/compliance")
async def get_wallet_compliance(wallet_address: str):
    """Get compliance status for tracked wallet with verification links"""
    try:
        compliance_status = await wallet_tracking_service.get_wallet_compliance_status(wallet_address)
        
        if "error" in compliance_status:
            raise HTTPException(status_code=404, detail=compliance_status["error"])
        
        # Add transparency information
        compliance_status["transparency_note"] = "All data sourced from public blockchain APIs"
        compliance_status["verification_methods"] = [
            "Blockchain transaction verification",
            "Cross-reference with public sanctions lists", 
            "Pattern analysis using regulatory guidelines"
        ]
        
        return compliance_status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting wallet compliance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@realtime_router.get("/wallet/{wallet_address}/report")
async def generate_compliance_report(wallet_address: str):
    """Generate comprehensive compliance report with verification data"""
    try:
        report = await wallet_tracking_service.generate_compliance_report(wallet_address)
        
        if "error" in report:
            raise HTTPException(status_code=404, detail=report["error"])
        
        # Add verification and transparency information
        report["verification_info"] = {
            "data_sources": ["Public blockchain APIs", "Regulatory databases"],
            "analysis_methods": ["Transaction pattern analysis", "Risk scoring algorithms"],
            "compliance_frameworks": ["AML/KYC guidelines", "OFAC sanctions screening"],
            "report_validity": "Based on publicly available data at time of generation"
        }
        
        return report
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating compliance report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@realtime_router.get("/wallet/tracked")
async def get_tracked_wallets():
    """Get list of all tracked wallets and their compliance status"""
    try:
        tracked_wallets = await wallet_tracking_service.get_tracked_wallets()
        
        return {
            "message": f"Found {len(tracked_wallets)} tracked wallets",
            "tracked_wallets": tracked_wallets,
            "timestamp": datetime.now().isoformat(),
            "monitoring_capabilities": [
                "Real-time transaction monitoring",
                "Sanctions list screening", 
                "Risk pattern detection",
                "Regulatory compliance checking"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting tracked wallets: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Real-time Pathway Wallet Connection Endpoints
@realtime_router.post("/wallet/connect")
async def connect_wallet_realtime(wallet_address: str):
    """Connect wallet for real-time Pathway monitoring"""
    try:
        result = await realtime_pathway_service.connect_wallet_for_realtime_monitoring(wallet_address)
        
        if result.get("status") == "connected":
            return {
                **result,
                "message": f"Wallet {wallet_address} connected for real-time monitoring",
                "pathway_features": [
                    "🔄 Real-time transaction streaming",
                    "⚡ Instant compliance alerts", 
                    "📊 Live risk score updates",
                    "📰 Regulatory news correlation",
                    "🚨 Sanctions screening"
                ],
                "next_steps": [
                    f"Check status: GET /api/realtime/wallet/{wallet_address}/status",
                    "View dashboard: GET /api/realtime/dashboard",
                    "Get compliance report: GET /api/realtime/wallet/{wallet_address}/report"
                ]
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to connect wallet"))
            
    except Exception as e:
        logger.error(f"Error connecting wallet for real-time monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@realtime_router.get("/wallet/{wallet_address}/status")
async def get_wallet_realtime_status(wallet_address: str):
    """Get real-time status for connected wallet"""
    try:
        status = await realtime_pathway_service.get_wallet_realtime_status(wallet_address)
        
        if status.get("status") == "not_connected":
            raise HTTPException(status_code=404, detail=status.get("message"))
        
        return {
            **status,
            "transparency_info": {
                "data_sources": ["Blockchain APIs", "News APIs", "Regulatory databases"],
                "real_time_processing": "Pathway streaming engine",
                "verification": "All data includes source URLs for verification"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting wallet real-time status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@realtime_router.get("/wallet/connected/summary")
async def get_connected_wallets_summary():
    """Get summary of all wallets connected for real-time monitoring"""
    try:
        summary = await realtime_pathway_service.get_connected_wallets_summary()
        
        return {
            **summary,
            "pathway_integration": {
                "streaming_engine": "Pathway real-time processing",
                "data_freshness": "Live updates",
                "monitoring_scope": "Transaction-level analysis"
            },
            "dashboard_features": [
                "Real-time wallet status",
                "Live compliance alerts",
                "Risk score trending",
                "Regulatory news correlation"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting connected wallets summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))
