"""Main FastAPI application for ReguChain Watch"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, List
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .models import (
    QueryRequest, QueryResponse, Evidence, OnchainMatch,
    StatusResponse, StatusUpdate, SimulateRequest, SimulateResponse,
    HealthResponse
)
from .config import GOOGLE_API_KEY, LLM_MODEL, LLM_TEMPERATURE
from .database import get_recent_documents, get_documents_by_ids, get_transactions_for_address
from .vector_store import vector_store
from .risk import risk_engine
from .ingest import ingester

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import Gemini for LLM generation
genai = None
try:
    import google.generativeai as genai
    genai.configure(api_key=GOOGLE_API_KEY)
    logger.info("Gemini API configured successfully")
except ImportError:
    logger.warning("Google GenAI SDK not available")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("Starting ReguChain Watch backend...")
    
    # Initial data ingestion
    try:
        await ingester.ingest_all()
        logger.info("Initial data ingestion completed")
    except Exception as e:
        logger.error(f"Error during initial ingestion: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down ReguChain Watch backend...")

# Create FastAPI app
app = FastAPI(
    title="ReguChain Watch API",
    description="Real-time RAG for regulatory compliance",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def generate_llm_answer(question: str, target: str, evidence: List[Dict], risk_score: float, risk_reasons: List[str]) -> str:
    """Generate final answer using Gemini LLM"""
    
    # Prepare evidence text
    evidence_text = "\n".join([
        f"{i+1}. Source: {e.get('source', 'Unknown')} - {e.get('text', '')[:200]}..."
        for i, e in enumerate(evidence[:5])
    ])
    
    # Determine risk level
    if risk_score >= 70:
        verdict = "HIGH RISK"
    elif risk_score >= 40:
        verdict = "MEDIUM RISK"
    else:
        verdict = "LOW RISK"
    
    # Create prompt
    prompt = f"""
    You are a regulatory compliance expert. Analyze the following information and provide a clear assessment.
    
    Question: {question}
    Target: {target or 'Not specified'}
    Risk Score: {risk_score}/100
    Risk Level: {verdict}
    
    Evidence:
    {evidence_text}
    
    Risk Indicators:
    {chr(10).join(risk_reasons[:5])}
    
    Provide:
    1. A clear verdict (Safe/Medium Risk/High Risk)
    2. One-sentence rationale
    3. Reference to evidence numbers used
    4. 2-3 actionable next steps
    
    Keep your response concise and professional.
    """
    
    # Try to use Gemini
    if genai and GOOGLE_API_KEY:
        try:
            model = genai.GenerativeModel(LLM_MODEL)
            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": LLM_TEMPERATURE,
                    "max_output_tokens": 500,
                }
            )
            return response.text
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
    
    # Fallback response
    fallback_answer = f"""
**Verdict: {verdict}**

**Rationale:** Based on the analysis of {len(evidence)} documents, the target shows a risk score of {risk_score}/100.

**Evidence Used:** Documents 1-{min(3, len(evidence))} from regulatory sources.

**Recommended Actions:**
1. {'Immediate action required - block transactions' if risk_score >= 70 else 'Enhanced monitoring recommended'}
2. {'Report to compliance team immediately' if risk_score >= 70 else 'Review transaction history'}
3. {'Freeze associated accounts pending investigation' if risk_score >= 70 else 'Update risk assessment in 30 days'}

**Risk Factors:**
{chr(10).join(f'• {reason}' for reason in risk_reasons[:3])}
    """
    
    return fallback_answer

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        services={
            "database": "connected",
            "vector_store": "ready",
            "gemini_api": "configured" if GOOGLE_API_KEY else "not configured",
            "ingestion": "ready"
        }
    )

@app.post("/api/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """Main query endpoint for RAG"""
    try:
        # Search vector store
        search_results = vector_store.search(request.question, k=5)
        
        # Extract documents
        retrieved_docs = [doc for doc, score in search_results]
        
        # Get on-chain matches if target is provided
        onchain_matches = []
        if request.target:
            tx_data = get_transactions_for_address(request.target, limit=5)
            onchain_matches = [
                OnchainMatch(
                    tx=tx["tx"],
                    amount=tx["amount"],
                    timestamp=tx["timestamp"],
                    from_address=tx.get("from"),
                    to_address=tx.get("to")
                )
                for tx in tx_data
            ]
        
        # Calculate risk score
        risk_score, risk_reasons = risk_engine.calculate_risk_score(
            request.target,
            retrieved_docs,
            [tx.dict() for tx in onchain_matches]
        )
        
        # Get recommendations
        recommendations = risk_engine.get_recommendations(risk_score, risk_reasons)
        
        # Generate LLM answer
        answer = generate_llm_answer(
            request.question,
            request.target,
            retrieved_docs,
            risk_score,
            risk_reasons
        )
        
        # Prepare evidence
        evidence = [
            Evidence(
                source=doc.get("source", "Unknown"),
                snippet=doc.get("text", "")[:200] + "...",
                timestamp=doc.get("timestamp", datetime.utcnow().isoformat()),
                link=doc.get("link", "")
            )
            for doc in retrieved_docs[:5]
        ]
        
        return QueryResponse(
            answer=answer,
            risk_score=risk_score,
            evidence=evidence,
            onchain_matches=onchain_matches,
            risk_reasons=risk_reasons,
            recommendations=recommendations
        )
    
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ingest/simulate", response_model=SimulateResponse)
async def simulate_ingestion(request: SimulateRequest = None):
    """Simulate ingestion of new sanction/news entry"""
    try:
        target = request.target if request else None
        result = await ingester.simulate_ingestion(target)
        return SimulateResponse(**result)
    except Exception as e:
        logger.error(f"Error simulating ingestion: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status", response_model=StatusResponse)
async def get_status():
    """Get system status and recent updates"""
    try:
        # Get recent documents
        recent_docs = get_recent_documents(limit=10)
        
        # Convert to status updates
        last_updates = [
            StatusUpdate(
                id=doc["id"],
                source=doc["source"],
                text=doc["text"][:200] + "..." if len(doc["text"]) > 200 else doc["text"],
                timestamp=doc["timestamp"],
                link=doc["link"] or ""
            )
            for doc in recent_docs
        ]
        
        # Get index stats
        index_stats = vector_store.get_stats()
        
        return StatusResponse(
            last_updates=last_updates,
            total_documents=index_stats.get("documents", 0),
            index_stats=index_stats
        )
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ingest/refresh")
async def refresh_data(background_tasks: BackgroundTasks):
    """Trigger data refresh from all sources"""
    background_tasks.add_task(ingester.ingest_all)
    return {"message": "Data refresh initiated", "timestamp": datetime.utcnow().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
