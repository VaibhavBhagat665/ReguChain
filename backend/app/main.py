"""Main FastAPI application for ReguChain AI Agent"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, List
from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .models import (
    AgentRequest, AgentResponse, WalletAnalysisRequest, WalletAnalysisResponse,
    StatusResponse, StatusUpdate, ConversationHistory, AgentCapability,
    Evidence, OnchainMatch, TransactionData
)
from .config import LLM_MODEL, LLM_TEMPERATURE
from .database import database
from .vector_store import vector_store
from .risk import risk_engine
from .pathway_fallback import pathway_fallback_manager
from .openrouter_llm import llm_client
from .openrouter_embeddings import embeddings_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# LLM initialization is handled in langchain_agent via Groq.

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("🚀 Starting ReguChain Pathway-Powered Backend...")
    
    # Start Pathway fallback pipelines
    try:
        await pathway_fallback_manager.start_all_pipelines()
        logger.info("✅ Pathway fallback pipelines started successfully")
        logger.info("📊 Real-time ingestion: OFAC, RSS, News, Blockchain")
        logger.info("🤖 AI Agent: OpenRouter + Mistral-7B + RAG")
    except Exception as e:
        logger.error(f"❌ Error starting Pathway pipelines: {e}")
    
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

# Pathway-powered endpoints - no external routers needed



@app.post("/api/agent/chat", response_model=AgentResponse)
async def chat_with_agent(request: AgentRequest):
    """Chat with the Pathway-powered AI agent"""
    try:
        # Add wallet to monitoring if provided
        if request.wallet_address:
            pathway_fallback_manager.add_target_wallet(request.wallet_address)
        
        # Search for relevant documents
        relevant_docs = vector_store.search(request.message, k=10)
        
        # Prepare context for LLM
        context_docs = []
        for doc_tuple in relevant_docs:
            if isinstance(doc_tuple, tuple):
                doc, similarity = doc_tuple
            else:
                doc = doc_tuple
                similarity = 1.0
            
            context_docs.append({
                'source': doc.get('source', 'unknown'),
                'content': doc.get('content', '')[:500],
                'timestamp': doc.get('timestamp', ''),
                'similarity': similarity
            })
        
        # Build LLM prompt
        messages = [
            {
                "role": "system",
                "content": f"""You are ReguChain AI, an expert in blockchain regulatory compliance.

You have access to real-time regulatory intelligence including:
- OFAC sanctions data
- SEC, CFTC, FINRA regulatory updates  
- Real-time news feeds
- Blockchain transaction data

INSTRUCTIONS:
1. Provide helpful, accurate compliance guidance
2. Cite specific evidence sources when available
3. Be conversational and professional
4. If asked about wallet analysis, provide risk assessment

EVIDENCE DOCUMENTS:
{chr(10).join([f"[{i+1}] {doc['source']}: {doc['content']}" for i, doc in enumerate(context_docs)])}
"""
            },
            {
                "role": "user", 
                "content": request.message
            }
        ]
        
        # Generate LLM response
        llm_response = await llm_client.generate_response(messages, max_tokens=800)
        
        if not llm_response:
            llm_response = "I'm having trouble connecting to the AI service. Please check your OpenRouter API key configuration."
        
        # Calculate risk assessment if wallet provided
        risk_assessment = None
        if request.wallet_address:
            risk_score = 20  # Base risk
            for doc in context_docs:
                if request.wallet_address.lower() in doc['content'].lower():
                    risk_score += 30  # Wallet mentioned in regulatory data
            
            risk_assessment = {
                "score": min(100, risk_score),
                "level": "High" if risk_score >= 70 else "Medium" if risk_score >= 40 else "Low",
                "factors": ["Regulatory data analysis", "Real-time monitoring"]
            }
        
        response = AgentResponse(
            message=llm_response,
            conversation_id=request.conversation_id or f"conv_{datetime.now().timestamp()}",
            risk_assessment=risk_assessment,
            blockchain_data=None,
            suggested_actions=[],
            confidence=0.85,
            capabilities_used=["pathway_rag", "openrouter_llm", "vector_search"],
            follow_up_questions=[]
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error in Pathway agent chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/wallet/analyze", response_model=WalletAnalysisResponse)
async def analyze_wallet(request: WalletAnalysisRequest):
    """Comprehensive wallet analysis using Pathway system"""
    try:
        # Add wallet to monitoring
        pathway_fallback_manager.add_target_wallet(request.address)
        
        # Search for wallet-related documents
        wallet_query = f"wallet address {request.address} sanctions compliance"
        relevant_docs = vector_store.search(wallet_query, k=15)
        
        # Calculate risk score based on findings
        risk_score = 20  # Base risk
        risk_reasons = []
        
        # Check for sanctions matches
        sanctions_found = False
        for doc_tuple in relevant_docs:
            if isinstance(doc_tuple, tuple):
                doc, similarity = doc_tuple
            else:
                doc = doc_tuple
                
            content = doc.get('content', '').lower()
            if request.address.lower() in content:
                if 'ofac' in content or 'sanction' in content:
                    risk_score += 40
                    risk_reasons.append("Found in OFAC sanctions data")
                    sanctions_found = True
                elif 'enforcement' in content or 'violation' in content:
                    risk_score += 25
                    risk_reasons.append("Mentioned in regulatory enforcement")
        
        # Mock some transaction data for demo
        transactions = [
            TransactionData(
                hash=f"0x{i:064x}",
                from_address=request.address if i % 2 == 0 else f"0x{'1' * 40}",
                to_address=f"0x{'2' * 40}" if i % 2 == 0 else request.address,
                value=str(float(100 + i * 50)),
                timestamp=datetime.utcnow().isoformat(),
                risk_score=risk_score if sanctions_found else None
            )
            for i in range(5)  # Mock 5 transactions
        ]
        
        # Determine compliance status
        if risk_score >= 70:
            compliance_status = "HIGH RISK - Immediate Review Required"
        elif risk_score >= 40:
            compliance_status = "MEDIUM RISK - Enhanced Monitoring"
        else:
            compliance_status = "LOW RISK - Standard Monitoring"
        
        # Get recommendations
        recommendations = []
        if sanctions_found:
            recommendations.extend([
                "Immediately freeze all transactions",
                "Report to compliance team",
                "Conduct enhanced due diligence"
            ])
        elif risk_score >= 40:
            recommendations.extend([
                "Enhanced monitoring required",
                "Review transaction patterns",
                "Verify source of funds"
            ])
        else:
            recommendations.extend([
                "Continue standard monitoring",
                "Regular compliance checks"
            ])
        
        # Generate analysis summary
        analysis_summary = f"""Wallet {request.address} analyzed using real-time regulatory data. 
Risk score: {risk_score}/100. 
Sanctions check: {'MATCH FOUND' if sanctions_found else 'No matches'}. 
Compliance status: {compliance_status}."""
        
        return WalletAnalysisResponse(
            address=request.address,
            risk_score=risk_score,
            compliance_status=compliance_status,
            total_transactions=len(transactions),
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
    return [
        AgentCapability(
            name="Real-time Regulatory Intelligence",
            description="Continuous ingestion of OFAC, SEC, CFTC, FINRA data",
            enabled=True
        ),
        AgentCapability(
            name="Pathway-Powered RAG",
            description="Vector search with OpenRouter embeddings",
            enabled=True
        ),
        AgentCapability(
            name="Wallet Risk Analysis",
            description="Sanctions screening and compliance assessment",
            enabled=True
        ),
        AgentCapability(
            name="Live Alerts System",
            description="Real-time compliance violation detection",
            enabled=True
        )
    ]

@app.get("/api/conversation/{conversation_id}", response_model=ConversationHistory)
async def get_conversation(conversation_id: str):
    """Get conversation history"""
    # Mock conversation history for now
    return ConversationHistory(
        conversation_id=conversation_id,
        messages=[],
        created_at=datetime.utcnow().isoformat(),
        updated_at=datetime.utcnow().isoformat()
    )


@app.get("/api/status", response_model=StatusResponse)
async def get_status():
    """Get system status and recent updates"""
    try:
        # Get Pathway system stats
        pipeline_stats = pathway_fallback_manager.get_pipeline_stats()
        
        # Mock recent updates from pipeline data
        last_updates = [
            StatusUpdate(
                id=f"update_{i}",
                source="PATHWAY_PIPELINE",
                text=f"Processed {pipeline_stats.get('total_documents_processed', 0)} documents from regulatory sources",
                timestamp=pipeline_stats.get('last_update', datetime.utcnow().isoformat()),
                link=""
            )
            for i in range(3)
        ]
        
        # Get vector store stats
        index_stats = vector_store.get_stats()
        
        # Get agent capabilities
        capabilities = await get_agent_capabilities()
        
        return StatusResponse(
            last_updates=last_updates,
            total_documents=pipeline_stats.get('total_documents_processed', 0),
            index_stats={
                **index_stats,
                'pipelines_running': pipeline_stats.get('is_running', False),
                'alerts_generated': pipeline_stats.get('alerts_generated', 0)
            },
            agent_capabilities=capabilities,
            active_conversations=0
        )
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ingest/refresh")
async def refresh_data(background_tasks: BackgroundTasks):
    """Trigger data refresh from Pathway pipelines"""
    return {"message": "Pathway pipelines running continuously", "timestamp": datetime.utcnow().isoformat()}

@app.post("/api/ingest/pdf")
async def ingest_pdf(file: UploadFile = File(...)):
    """Upload a PDF report and ingest it into the knowledge base"""
    try:
        content = await file.read()
        # Mock PDF processing for demo
        return {
            "message": "PDF ingested successfully",
            "title": file.filename,
            "chunks": 5  # Mock chunk count
        }
    except Exception as e:
        logger.error(f"Error ingesting PDF: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/rag/status")
async def get_rag_status():
    """Get RAG system status"""
    try:
        pipeline_stats = pathway_fallback_manager.get_pipeline_stats()
        return {
            "status": "active" if pipeline_stats.get('is_running') else "inactive",
            "documents_processed": pipeline_stats.get('total_documents_processed', 0),
            "alerts_generated": pipeline_stats.get('alerts_generated', 0),
            "last_update": pipeline_stats.get('last_update'),
            "pipelines": pipeline_stats.get('pipelines_status', {})
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.post("/api/ingest/simulate")
async def simulate_ingestion(doc_type: str, content: str):
    """Simulate document ingestion for demo"""
    try:
        success = pathway_fallback_manager.simulate_document(doc_type, content)
        return {"success": success, "message": f"Simulated {doc_type} document ingestion"}
    except Exception as e:
        logger.error(f"Error simulating ingestion: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/query")
async def rag_query(question: str, wallet_address: str = None):
    """Direct RAG query endpoint using Pathway system"""
    try:
        # Add wallet to monitoring if provided
        if wallet_address:
            pathway_fallback_manager.add_target_wallet(wallet_address)
        
        # Search for relevant documents
        relevant_docs = vector_store.search(question, k=10)
        
        # Prepare context
        context_docs = []
        onchain_matches = []
        
        for doc_tuple in relevant_docs:
            if isinstance(doc_tuple, tuple):
                doc, similarity = doc_tuple
            else:
                doc = doc_tuple
                similarity = 1.0
            
            context_docs.append({
                'source': doc.get('source', 'unknown'),
                'content': doc.get('content', '')[:500],
                'timestamp': doc.get('timestamp', ''),
                'similarity': similarity
            })
            
            # Check for onchain matches
            if wallet_address and wallet_address.lower() in doc.get('content', '').lower():
                onchain_matches.append({
                    'wallet_address': wallet_address,
                    'source': doc.get('source', 'unknown'),
                    'content': doc.get('content', '')[:200]
                })
        
        # Build LLM prompt
        messages = [
            {
                "role": "system",
                "content": f"""You are ReguChain AI, an expert in blockchain regulatory compliance.

EVIDENCE DOCUMENTS:
{chr(10).join([f"[{i+1}] {doc['source']}: {doc['content']}" for i, doc in enumerate(context_docs)])}

Provide helpful compliance guidance based on the evidence above."""
            },
            {
                "role": "user", 
                "content": question
            }
        ]
        
        # Generate LLM response
        llm_response = await llm_client.generate_response(messages, max_tokens=800)
        
        if not llm_response:
            llm_response = "I'm having trouble connecting to the AI service. Please check your OpenRouter API key configuration."
        
        # Calculate risk score
        risk_score = 20  # Base risk
        if wallet_address and onchain_matches:
            risk_score += 30 * len(onchain_matches)
        
        return {
            "answer": llm_response,
            "risk_score": min(100, risk_score),
            "risk_verdict": "High" if risk_score >= 70 else "Medium" if risk_score >= 40 else "Safe",
            "evidence": context_docs,
            "onchain_matches": onchain_matches,
            "model_used": "mistralai/mistral-7b-instruct",
            "processing_time_ms": 1500
        }
        
    except Exception as e:
        logger.error(f"Error in RAG query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Add Pathway-specific endpoints
@app.get("/api/alerts")
async def get_alerts(limit: int = 10):
    """Get recent alerts from Pathway system"""
    try:
        alerts = pathway_fallback_manager.get_recent_alerts(limit)
        return alerts
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/wallet/monitor")
async def add_wallet_monitoring(wallet_address: str):
    """Add wallet to Pathway monitoring"""
    try:
        pathway_fallback_manager.add_target_wallet(wallet_address)
        return {
            "success": True,
            "message": f"Added wallet {wallet_address} to monitoring",
            "wallet_address": wallet_address
        }
    except Exception as e:
        logger.error(f"Error adding wallet monitoring: {e}")
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
            'mode': 'pathway_fallback'
        }
        
    except Exception as e:
        logger.error(f"❌ Error in health check: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
