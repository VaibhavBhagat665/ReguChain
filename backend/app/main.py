"""Main FastAPI application for ReguChain AI Agent"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, List
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .models import (
    AgentRequest, AgentResponse, WalletAnalysisRequest, WalletAnalysisResponse,
    StatusResponse, StatusUpdate, ConversationHistory, AgentCapability,
    Evidence, OnchainMatch, TransactionData
)
from .config import GOOGLE_API_KEY, LLM_MODEL, LLM_TEMPERATURE
from .database import get_recent_documents, get_documents_by_ids, get_transactions_for_address
from .vector_store import vector_store
from .risk import risk_engine
from .ingest import ingester
from .ai_agent import ai_agent

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
    title="ReguChain AI Agent API",
    description="Advanced AI Agent for Blockchain Regulatory Compliance",
    version="2.0.0",
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



@app.post("/api/agent/chat", response_model=AgentResponse)
async def chat_with_agent(request: AgentRequest):
    """Chat with the AI agent"""
    try:
        response = await ai_agent.process_request(request)
        return response
    except Exception as e:
        logger.error(f"Error in agent chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/wallet/analyze", response_model=WalletAnalysisResponse)
async def analyze_wallet(request: WalletAnalysisRequest):
    """Comprehensive wallet analysis"""
    try:
        # Get transaction data
        tx_data = get_transactions_for_address(request.address, limit=20)
        
        # Convert to TransactionData objects
        transactions = [
            TransactionData(
                hash=tx.get("tx", "unknown"),
                from_address=tx.get("from", "unknown"),
                to_address=tx.get("to", "unknown"),
                value=str(tx.get("amount", 0)),
                timestamp=tx.get("timestamp", datetime.utcnow().isoformat()),
                risk_score=float(tx.get("risk_score", 0)) if tx.get("risk_score") else None
            )
            for tx in tx_data[:10]  # Recent 10 transactions
        ]
        
        # Calculate risk score
        risk_score, risk_reasons = risk_engine.calculate_risk_score(
            request.address, [], tx_data
        )
        
        # Determine compliance status
        if risk_score >= 70:
            compliance_status = "HIGH RISK - Immediate Review Required"
        elif risk_score >= 40:
            compliance_status = "MEDIUM RISK - Enhanced Monitoring"
        else:
            compliance_status = "LOW RISK - Standard Monitoring"
        
        # Get recommendations
        recommendations = risk_engine.get_recommendations(risk_score, risk_reasons)
        
        # Generate analysis summary
        analysis_summary = f"""Wallet {request.address} has been analyzed with a risk score of {risk_score}/100. 
Total transactions analyzed: {len(tx_data)}. 
Compliance status: {compliance_status}."""
        
        return WalletAnalysisResponse(
            address=request.address,
            risk_score=risk_score,
            compliance_status=compliance_status,
            total_transactions=len(tx_data),
            recent_transactions=transactions,
            risk_factors=risk_reasons,
            recommendations=recommendations,
            analysis_summary=analysis_summary
        )
        
    except Exception as e:
        logger.error(f"Error analyzing wallet: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/agent/capabilities", response_model=List[AgentCapability])
async def get_agent_capabilities():
    """Get AI agent capabilities"""
    return ai_agent.get_capabilities()

@app.get("/api/conversation/{conversation_id}", response_model=ConversationHistory)
async def get_conversation(conversation_id: str):
    """Get conversation history"""
    history = ai_agent.get_conversation_history(conversation_id)
    if not history:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return history


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
        
        # Get agent capabilities
        capabilities = ai_agent.get_capabilities()
        
        # Count active conversations
        active_conversations = len(ai_agent.conversations)
        
        return StatusResponse(
            last_updates=last_updates,
            total_documents=index_stats.get("documents", 0),
            index_stats=index_stats,
            agent_capabilities=capabilities,
            active_conversations=active_conversations
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
