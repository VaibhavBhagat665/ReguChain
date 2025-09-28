"""
Minimal backend server with basic functionality
"""
import os
import sys
from pathlib import Path
from datetime import datetime
import logging

# Setup path and logging
sys.path.insert(0, str(Path(__file__).parent))
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import uvicorn

# Create FastAPI app
app = FastAPI(
    title="ReguChain AI Agent API",
    description="Blockchain Regulatory Compliance Platform",
    version="2.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class AgentRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    wallet_address: Optional[str] = None
    context: Optional[Dict[str, Any]] = {}

class AgentResponse(BaseModel):
    message: str
    conversation_id: str
    confidence: float = 0.8
    suggested_actions: List[str] = []

class WalletAnalysisRequest(BaseModel):
    address: str

class StatusResponse(BaseModel):
    status: str
    total_documents: int
    active_conversations: int
    last_updates: List[Dict]

# Endpoints
@app.get("/")
async def root():
    return {"message": "ReguChain Watch API is running!", "version": "2.0.0"}

@app.get("/api/status")
async def get_status():
    """Get system status"""
    return {
        "status": "operational",
        "total_documents": 42,
        "active_conversations": 1,
        "last_updates": [
            {
                "id": 1,
                "source": "SEC",
                "text": "SEC announces new cryptocurrency compliance framework",
                "timestamp": datetime.utcnow().isoformat(),
                "link": "https://www.sec.gov"
            },
            {
                "id": 2,
                "source": "CFTC",
                "text": "CFTC issues guidance on DeFi platforms",
                "timestamp": datetime.utcnow().isoformat(),
                "link": "https://www.cftc.gov"
            }
        ],
        "index_stats": {
            "documents": 42,
            "vectors": 100
        },
        "agent_capabilities": [
            {"name": "wallet_analysis", "description": "Analyze blockchain wallets", "enabled": True},
            {"name": "compliance_check", "description": "Check regulatory compliance", "enabled": True},
            {"name": "risk_assessment", "description": "Assess transaction risks", "enabled": True}
        ]
    }

@app.post("/api/agent/chat")
async def chat_with_agent(request: AgentRequest):
    """Chat with AI agent"""
    import uuid
    
    # Simple response for testing
    response_message = f"I received your message: '{request.message}'. "
    
    if "regulation" in request.message.lower() or "sec" in request.message.lower():
        response_message += "Based on the latest regulatory updates, the SEC has been focusing on increased oversight of cryptocurrency exchanges and DeFi platforms. Key areas include KYC/AML compliance, custody requirements, and market manipulation prevention."
    elif "wallet" in request.message.lower() or "address" in request.message.lower():
        response_message += "To analyze a wallet, please provide the wallet address. I can check for compliance risks, transaction patterns, and potential sanctions matches."
    else:
        response_message += "I can help you with regulatory compliance, wallet analysis, and risk assessment. What would you like to know?"
    
    return AgentResponse(
        message=response_message,
        conversation_id=str(uuid.uuid4()),
        confidence=0.85,
        suggested_actions=[
            "Check latest SEC regulations",
            "Analyze a wallet address",
            "View compliance requirements"
        ]
    )

@app.post("/api/wallet/analyze")
async def analyze_wallet(request: WalletAnalysisRequest):
    """Analyze wallet for compliance"""
    import random
    
    # Mock analysis for testing
    risk_score = random.uniform(10, 90)
    
    if risk_score >= 70:
        compliance_status = "HIGH RISK - Review Required"
    elif risk_score >= 40:
        compliance_status = "MEDIUM RISK - Monitor"
    else:
        compliance_status = "LOW RISK - Compliant"
    
    return {
        "address": request.address,
        "risk_score": round(risk_score, 2),
        "compliance_status": compliance_status,
        "total_transactions": random.randint(10, 1000),
        "recent_transactions": [],
        "risk_factors": [
            "Transaction volume within normal range",
            "No sanctions matches found",
            "Standard transaction patterns detected"
        ],
        "recommendations": [
            "Continue monitoring",
            "Implement transaction limits",
            "Regular compliance reviews"
        ],
        "analysis_summary": f"Wallet {request.address[:10]}... analyzed with risk score {round(risk_score, 2)}/100"
    }

@app.get("/api/agent/capabilities")
async def get_capabilities():
    """Get agent capabilities"""
    return [
        {"name": "wallet_analysis", "description": "Comprehensive wallet and transaction analysis", "enabled": True},
        {"name": "compliance_check", "description": "Real-time regulatory compliance verification", "enabled": True},
        {"name": "risk_assessment", "description": "AI-powered risk scoring", "enabled": True},
        {"name": "conversational_ai", "description": "Natural language interaction", "enabled": True},
        {"name": "blockchain_insights", "description": "Deep blockchain data analysis", "enabled": True},
        {"name": "regulatory_updates", "description": "Real-time regulatory monitoring", "enabled": True}
    ]

if __name__ == "__main__":
    logger.info("Starting ReguChain minimal backend server...")
    logger.info("Server will be available at http://localhost:8000")
    logger.info("API documentation at http://localhost:8000/docs")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
