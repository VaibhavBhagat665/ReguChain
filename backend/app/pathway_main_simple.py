"""
Simplified Pathway-Powered FastAPI Application for ReguChain
Uses fallback system that works without full Pathway license
"""
import asyncio
import logging
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .pathway_fallback import pathway_fallback_manager
from .openrouter_llm import llm_client
from .openrouter_embeddings import embeddings_client
from .vector_store import vector_store
from .config import LLM_MODEL, EMBEDDINGS_MODEL

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models
class QueryRequest(BaseModel):
    question: str
    wallet_address: Optional[str] = None

class QueryResponse(BaseModel):
    answer: str
    risk_score: int
    risk_verdict: str
    evidence: List[Dict[str, Any]]
    onchain_matches: List[Dict[str, Any]]
    model_used: str
    processing_time_ms: int

class AlertResponse(BaseModel):
    id: str
    type: str
    severity: str
    title: str
    description: str
    wallet_address: Optional[str]
    risk_score: int
    timestamp: str
    evidence: str

class StatusResponse(BaseModel):
    status: str
    pipelines_running: bool
    total_documents: int
    total_alerts: int
    last_update: Optional[str]
    pipeline_stats: Dict[str, Any]

class SimulateRequest(BaseModel):
    doc_type: str
    content: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("🚀 Starting ReguChain Pathway-Powered Backend (Fallback Mode)...")
    
    try:
        # Start fallback pipelines
        await pathway_fallback_manager.start_all_pipelines()
        logger.info("✅ Fallback pipelines started")
        
        # Wait for initialization
        await asyncio.sleep(2)
        
    except Exception as e:
        logger.error(f"❌ Error during startup: {e}")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down ReguChain backend...")
    try:
        pathway_fallback_manager.stop_all_pipelines()
        logger.info("✅ Pipelines stopped")
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}")

# Create FastAPI app
app = FastAPI(
    title="ReguChain Pathway API (Fallback)",
    description="Pathway-powered real-time regulatory compliance (fallback mode)",
    version="2.0.0-fallback",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "ReguChain Pathway API (Fallback Mode)",
        "version": "2.0.0-fallback",
        "status": "running",
        "powered_by": "Pathway Fallback + OpenRouter + FastAPI"
    }

@app.post("/api/query", response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    """RAG query endpoint with fallback-powered data"""
    start_time = datetime.now()
    
    try:
        logger.info(f"🔍 Processing query: {request.question[:100]}...")
        
        # Add wallet to monitoring if provided
        if request.wallet_address:
            pathway_fallback_manager.add_target_wallet(request.wallet_address)
        
        # Generate query embedding
        query_embedding = await embeddings_client.embed_text(request.question)
        if not query_embedding:
            raise HTTPException(status_code=500, detail="Failed to generate query embedding")
        
        # Search vector store for relevant documents
        relevant_docs = vector_store.search(
            query=request.question,
            k=10
        )
        
        if not relevant_docs:
            return QueryResponse(
                answer="I don't have sufficient data to answer your question yet. The system is continuously ingesting real-time data. Please try again in a few minutes.",
                risk_score=0,
                risk_verdict="Unknown",
                evidence=[],
                onchain_matches=[],
                model_used="no_data",
                processing_time_ms=int((datetime.now() - start_time).total_seconds() * 1000)
            )
        
        # Prepare context for LLM
        context_docs = []
        onchain_matches = []
        
        for doc_tuple in relevant_docs:
            # Handle tuple format (doc, similarity_score)
            if isinstance(doc_tuple, tuple):
                doc, similarity = doc_tuple
            else:
                doc = doc_tuple
                similarity = 1.0
            
            context_docs.append({
                'source': doc.get('source', 'unknown'),
                'content': doc.get('content', '')[:500],
                'risk_level': doc.get('metadata', {}).get('risk_level', 'low'),
                'timestamp': doc.get('timestamp', ''),
                'similarity': similarity
            })
            
            # Check for onchain matches
            if doc.get('metadata', {}).get('onchain_match'):
                onchain_matches.append({
                    'wallet_address': doc.get('metadata', {}).get('from_address', ''),
                    'transaction_hash': doc.get('metadata', {}).get('hash', ''),
                    'value': doc.get('metadata', {}).get('value_eth', 0),
                    'risk_level': doc.get('metadata', {}).get('risk_level', 'low')
                })
        
        # Build LLM prompt
        messages = [
            {
                "role": "system",
                "content": f"""You are ReguChain AI, an expert in blockchain regulatory compliance and risk analysis.

You have access to real-time regulatory intelligence including:
- OFAC sanctions data
- SEC, CFTC, FINRA regulatory updates  
- Real-time news feeds
- Blockchain transaction data

INSTRUCTIONS:
1. Analyze the provided evidence documents carefully
2. Provide a clear risk verdict: Safe, Medium, or High
3. Calculate a risk score (0-100)
4. Cite specific evidence sources
5. Be concise but comprehensive

TARGET: {request.wallet_address or 'General inquiry'}

EVIDENCE DOCUMENTS:
{chr(10).join([f"[{i+1}] {doc['source']}: {doc['content']}" for i, doc in enumerate(context_docs)])}
"""
            },
            {
                "role": "user", 
                "content": request.question
            }
        ]
        
        # Generate LLM response
        llm_response = await llm_client.generate_response(messages, max_tokens=800)
        
        if not llm_response:
            raise HTTPException(status_code=500, detail="Failed to generate LLM response")
        
        # Calculate risk score based on evidence
        risk_score = calculate_risk_score(context_docs, onchain_matches)
        risk_verdict = get_risk_verdict(risk_score)
        
        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        logger.info(f"✅ Query processed in {processing_time}ms - Risk: {risk_verdict} ({risk_score})")
        
        return QueryResponse(
            answer=llm_response,
            risk_score=risk_score,
            risk_verdict=risk_verdict,
            evidence=context_docs,
            onchain_matches=onchain_matches,
            model_used=LLM_MODEL or "mistralai/mistral-7b-instruct",
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"❌ Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/alerts", response_model=List[AlertResponse])
async def get_alerts(limit: int = 10):
    """Get recent risk alerts from fallback pipelines"""
    try:
        alerts = pathway_fallback_manager.get_recent_alerts(limit)
        
        return [
            AlertResponse(
                id=alert['id'],
                type=alert['type'],
                severity=alert['severity'],
                title=alert['title'],
                description=alert['description'],
                wallet_address=alert.get('wallet_address'),
                risk_score=alert['risk_score'],
                timestamp=alert['timestamp'],
                evidence=alert['evidence']
            )
            for alert in alerts
        ]
        
    except Exception as e:
        logger.error(f"❌ Error getting alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status", response_model=StatusResponse)
async def get_status():
    """Get system status"""
    try:
        pipeline_stats = pathway_fallback_manager.get_pipeline_stats()
        vector_stats = vector_store.get_stats()
        
        return StatusResponse(
            status="running" if pipeline_stats['is_running'] else "stopped",
            pipelines_running=pipeline_stats['is_running'],
            total_documents=pipeline_stats['total_documents_processed'],
            total_alerts=pipeline_stats['alerts_generated'],
            last_update=pipeline_stats['last_update'],
            pipeline_stats={
                **pipeline_stats,
                'vector_store': vector_stats
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Error getting status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ingest/simulate")
async def simulate_ingestion(request: SimulateRequest):
    """Simulate document ingestion for demo"""
    try:
        success = pathway_fallback_manager.simulate_document(
            request.doc_type, 
            request.content
        )
        
        return {
            "success": success,
            "message": f"Simulated {request.doc_type} document ingestion",
            "content_preview": request.content[:100] + "..." if len(request.content) > 100 else request.content
        }
        
    except Exception as e:
        logger.error(f"❌ Error simulating ingestion: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/wallet/monitor")
async def add_wallet_monitoring(wallet_address: str):
    """Add wallet to monitoring"""
    try:
        pathway_fallback_manager.add_target_wallet(wallet_address)
        
        return {
            "success": True,
            "message": f"Added wallet {wallet_address} to monitoring",
            "wallet_address": wallet_address
        }
        
    except Exception as e:
        logger.error(f"❌ Error adding wallet monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        pipeline_stats = pathway_fallback_manager.get_pipeline_stats()
        
        return {
            'overall_status': 'healthy' if pipeline_stats['is_running'] else 'stopped',
            'pipelines': {
                'ofac': 'active' if pipeline_stats['is_running'] else 'inactive',
                'rss': 'active' if pipeline_stats['is_running'] else 'inactive', 
                'news': 'active' if pipeline_stats['is_running'] else 'inactive',
                'blockchain': 'active' if pipeline_stats['is_running'] else 'inactive',
                'embeddings': 'active' if pipeline_stats['is_running'] else 'inactive',
                'alerts': 'active' if pipeline_stats['is_running'] else 'inactive'
            },
            'stats': pipeline_stats,
            'last_health_check': datetime.now().isoformat(),
            'mode': 'fallback'
        }
        
    except Exception as e:
        logger.error(f"❌ Error in health check: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Helper functions
def calculate_risk_score(context_docs: List[Dict], onchain_matches: List[Dict]) -> int:
    """Calculate risk score based on evidence"""
    base_score = 20  # Base risk
    
    # Risk from document evidence
    for doc in context_docs:
        risk_level = doc.get('risk_level', 'low')
        if risk_level == 'critical':
            base_score += 30
        elif risk_level == 'high':
            base_score += 20
        elif risk_level == 'medium':
            base_score += 10
        elif risk_level == 'low':
            base_score += 5
    
    # Risk from onchain matches
    if onchain_matches:
        base_score += 25  # Onchain involvement increases risk
        
        for match in onchain_matches:
            if match.get('risk_level') == 'high':
                base_score += 15
    
    # Clamp to 0-100
    return max(0, min(100, base_score))

def get_risk_verdict(risk_score: int) -> str:
    """Convert risk score to verdict"""
    if risk_score >= 70:
        return "High"
    elif risk_score >= 40:
        return "Medium"
    else:
        return "Safe"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
