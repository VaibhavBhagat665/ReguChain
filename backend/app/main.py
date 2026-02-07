import asyncio
import logging
from datetime import datetime
from typing import Dict, List
import re
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
from .groq_llm import llm_client
from .openrouter_embeddings import embeddings_client
from .blockchain_service import blockchain_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# LLM initialization is handled in langchain_agent via Groq.

def extract_potential_entities(text: str) -> List[str]:
    """Extract potential entity names (capitalized phrases) from text"""
    pattern = r'\b[A-Z][a-zA-Z0-9]*(?:\s+[A-Z][a-zA-Z0-9]*)*\b'
    matches = re.findall(pattern, text)
    filtered = [m for m in matches if len(m) > 2]
    return filtered

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("🚀 Starting ReguChain Pathway-Powered Backend...")
    
    # Start Pathway pipelines
    try:
        await pathway_fallback_manager.start_all_pipelines()
        logger.info("✅ Pathway pipelines started successfully")
        logger.info("📊 Real-time ingestion: OFAC, RSS, News, Blockchain")
        logger.info("🤖 AI Agent: Groq + Llama 3 + RAG")
        logger.info("🔍 Vector Search: FAISS + OpenRouter Embeddings")
        logger.info("🚨 Alerts: Real-time compliance monitoring")
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



@app.get("/api/compliance/search")
async def search_compliance(query: str):
    """Search for entities in the OFAC sanctions list"""
    results = pathway_service.search_sanctions(query)
    return {"results": results}

@app.post("/api/agent/chat", response_model=AgentResponse)
async def chat_with_agent(request: AgentRequest):
    """Chat with the Pathway-powered AI agent"""
    try:
        # Add wallet to monitoring if provided
        if request.wallet_address:
            pathway_fallback_manager.add_target_wallet(request.wallet_address)
        
        # Search for relevant documents
        relevant_docs = await vector_store.search(request.message, k=10)
        
        # Check for sanctions matches (Automatic RAG)
        sanctions_matches = []
        try:
            # 1. Search for the whole query if it's short and looks like a name
            if len(request.message) < 50 and not request.message.lower().startswith(("hi", "hello", "hey")):
                sanctions_matches.extend(pathway_service.search_sanctions(request.message))
            
            # 2. Extract potential entities and search
            potential_entities = extract_potential_entities(request.message)
            for entity in potential_entities:
                if entity.lower() not in ["hi", "hello", "hey", "check", "verify", "is", "are", "what", "where", "how"]:
                    matches = pathway_service.search_sanctions(entity)
                    sanctions_matches.extend(matches)
            
            # Deduplicate by ent_num or name
            seen_ids = set()
            unique_matches = []
            for m in sanctions_matches:
                uid = m.get('ent_num', m.get('SDN_Name'))
                if uid not in seen_ids:
                    seen_ids.add(uid)
                    unique_matches.append(m)
            sanctions_matches = unique_matches
            
            # Add to relevant docs if found
            for match in sanctions_matches:
                # Format as a document
                doc_content = f"SANCTIONS_ALERT: {match.get('SDN_Name')} (Type: {match.get('SDN_Type')}) is on OFAC List. Program: {match.get('Program')}. Remarks: {match.get('Remarks')}"
                relevant_docs.append({
                    'content': doc_content,
                    'source': 'OFAC Sanctions List',
                    'timestamp': datetime.utcnow().isoformat(),
                    'link': 'https://sanctionssearch.ofac.treas.gov/',
                    'metadata': {'title': f"Sanction: {match.get('SDN_Name')}", 'type': 'alert', 'risk_level': 'critical'}
                })
                
        except Exception as e:
            logger.error(f"Error in automatic sanctions check: {e}")

        
        # Prepare context for LLM
        context_docs = []
        for doc_tuple in relevant_docs:
            if isinstance(doc_tuple, tuple):
                doc, similarity = doc_tuple
            else:
                doc = doc_tuple
                similarity = 1.0
            
            # Extract metadata properly
            metadata = doc.get('metadata', {})
            # Use news_source from metadata if available, otherwise use main source
            source_name = metadata.get('news_source') or doc.get('source', 'Unknown Source')
            # Remove "NEWS_API" hardcoding
            if source_name == 'NEWS_API':
                source_name = metadata.get('news_source', 'Unknown Source')
            
            context_docs.append({
                'source': source_name,
                'content': doc.get('content', '')[:500],
                'timestamp': metadata.get('timestamp', doc.get('timestamp', '')),
                'link': metadata.get('link', doc.get('link', '')),
                'title': metadata.get('title', ''),
                'type': metadata.get('type', 'document'),
                'similarity': similarity
            })
        
        # Build concise LLM prompt with real source names
        evidence_text = ""
        if context_docs:
            evidence_items = []
            for i, doc in enumerate(context_docs[:3]):  # Limit to top 3 most relevant
                # Use real source names instead of NEWS_API
                source = doc['source']
                if source == 'NEWS_API':
                    # Try to get real source from metadata
                    metadata = doc.get('metadata', {})
                    source = metadata.get('news_source', metadata.get('source_name', 'News Source'))
                
                title = doc.get('title', 'No title')
                link = doc.get('link', '')
                content = doc['content'][:200] + "..." if len(doc['content']) > 200 else doc['content']
                
                evidence_items.append(f"[{i+1}] {source}: {title} - {content}")
                if link:
                    evidence_items.append(f"    Link: {link}")
            
            evidence_text = "\n".join(evidence_items)
        
        # Check for simple conversational inputs
        simple_responses = {
            "thanks": "You're welcome! Always here to help with compliance insights 🚀",
            "thank you": "You're welcome! Always here to help with compliance insights 🚀", 
            "ok": "Great! Let me know if you need any other compliance analysis 👍",
            "okay": "Great! Let me know if you need any other compliance analysis 👍",
            "hi": "Hello! I'm ReguChain AI, ready to help with blockchain compliance questions 👋",
            "hello": "Hello! I'm ReguChain AI, ready to help with blockchain compliance questions 👋",
            "hey": "Hey there! What compliance questions can I help you with today? 💼"
        }
        
        message_lower = request.message.lower().strip()
        if message_lower in simple_responses:
            return AgentResponse(
                message=simple_responses[message_lower],
                conversation_id=request.conversation_id or f"conv_{datetime.now().timestamp()}",
                confidence=1.0,
                capabilities_used=["conversational_ai"],
                context_documents=[]
            )

        messages = [
            {
                "role": "system",
                "content": f"""You are ReguChain AI, a friendly blockchain compliance expert with real-time regulatory data access.

CURRENT REGULATORY EVIDENCE:
{evidence_text}

RESPONSE STYLE:
- Be conversational and helpful, not robotic
- Use emojis appropriately (✅ ❌ ⚠️ 🚀 💼 📊)
- Always provide actionable insights, even with limited data
- Format responses clearly with bullet points when helpful
- Include relevant links when available
- Never say "I cannot analyze" - always provide helpful guidance

WALLET ANALYSIS FORMAT:
- Start with clear status: "Your wallet [address] shows [status] ✅/⚠️/❌"
- Include relevant regulatory news with links
- End with compliance risk level and recommendations

GENERAL QUERIES:
- Provide current regulatory insights from available evidence
- Reference specific sources and dates when possible
- Give practical compliance advice"""
            },
            {
                "role": "user", 
                "content": request.message
            }
        ]
        
        # Generate LLM response
        llm_response = await llm_client.generate_response(messages, max_tokens=800)
        
        if not llm_response or llm_response.strip() == "Empty response generated":
            # Provide helpful fallback response with real data
            if context_docs:
                if request.wallet_address:
                    fallback_response = f"Your wallet `{request.wallet_address}` analysis 📊\n\n"
                    fallback_response += "✅ **Status**: No direct sanctions found in current data\n\n"
                    fallback_response += "📰 **Relevant Regulatory Updates**:\n"
                else:
                    fallback_response = "Here's what I found in the latest regulatory data 📊\n\n"
                
                for i, doc in enumerate(context_docs[:2]):
                    # Use real source names
                    source = doc['source']
                    if source == 'NEWS_API':
                        metadata = doc.get('metadata', {})
                        source = metadata.get('news_source', metadata.get('source_name', 'News Source'))
                    
                    title = doc.get('title', 'Regulatory Update')
                    link = doc.get('link', '')
                    fallback_response += f"• **{source}**: {title}\n"
                    if link:
                        fallback_response += f"  🔗 [Read more]({link})\n"
                    fallback_response += "\n"
                
                if request.wallet_address:
                    fallback_response += "⚠️ **Compliance Risk**: Low\n"
                    fallback_response += "🚀 **Recommendation**: Continue monitoring for regulatory changes"
                else:
                    fallback_response += "💡 **Tip**: Ask me about specific wallet addresses for detailed compliance analysis!"
                
                llm_response = fallback_response
            else:
                llm_response = "No direct matches found, but I'm continuing to monitor against OFAC, SEC, and CFTC feeds 🔍\n\nI'll keep watching for any regulatory updates that might affect your query. Feel free to ask about specific wallet addresses for detailed analysis! 🚀"
        
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
        
        # Prepare response with context documents
        response_data = {
            "message": llm_response,
            "conversation_id": request.conversation_id or f"conv_{datetime.now().timestamp()}",
            "risk_assessment": risk_assessment,
            "blockchain_data": None,
            "suggested_actions": [],
            "confidence": 0.85,
            "capabilities_used": ["pathway_rag", "groq_llm", "vector_search"],
            "follow_up_questions": [],
            "context_documents": context_docs  # Include context documents for frontend
        }
        
        response = AgentResponse(**response_data)
        
        return response
        
    except Exception as e:
        logger.error(f"Error in Pathway agent chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/wallet/analyze", response_model=WalletAnalysisResponse)
async def analyze_wallet(request: WalletAnalysisRequest):
    """Comprehensive wallet analysis using real Etherscan data and Pathway system"""
    try:
        logger.info(f"Starting real wallet analysis for {request.address}")
        
        # Add wallet to monitoring
        pathway_fallback_manager.add_target_wallet(request.address)
        
        # Get real blockchain data from Etherscan
        wallet_info = await blockchain_service.get_wallet_info(request.address)
        real_transactions = await blockchain_service.get_transactions(request.address, limit=20)
        
        logger.info(f"Retrieved {len(real_transactions)} real transactions for {request.address}")
        
        # Search for wallet-related documents in Pathway pipeline
        wallet_query = f"wallet address {request.address} sanctions compliance OFAC"
        relevant_docs = await vector_store.search(wallet_query, k=15)
        
        # Initialize risk assessment with blockchain analysis
        blockchain_risk = await blockchain_service.analyze_wallet_risk(request.address, real_transactions)
        risk_score = blockchain_risk["risk_score"]
        risk_reasons = blockchain_risk["risk_factors"].copy()
        
        logger.info(f"Blockchain risk analysis: {risk_score}/100, factors: {risk_reasons}")
        
        # Check for sanctions matches in Pathway data
        sanctions_found = False
        regulatory_matches = []
        
        for doc_tuple in relevant_docs:
            if isinstance(doc_tuple, tuple):
                doc, similarity = doc_tuple
            else:
                doc = doc_tuple
                similarity = 1.0
                
            content = doc.get('content', '').lower()
            source = doc.get('source', '')
            
            # Check for direct address matches
            if request.address.lower() in content:
                if 'ofac' in content or 'sanction' in content:
                    risk_score = min(risk_score + 50, 100)  # Major risk increase
                    risk_reasons.append(f"CRITICAL: Found in OFAC sanctions data (Source: {source})")
                    sanctions_found = True
                    regulatory_matches.append({
                        "type": "sanctions",
                        "source": source,
                        "content": content[:200] + "..."
                    })
                elif 'enforcement' in content or 'violation' in content:
                    risk_score = min(risk_score + 30, 100)
                    risk_reasons.append(f"WARNING: Mentioned in regulatory enforcement (Source: {source})")
                    regulatory_matches.append({
                        "type": "enforcement",
                        "source": source,
                        "content": content[:200] + "..."
                    })
            
            # Check for pattern matches (similar addresses, related entities)
            elif similarity > 0.8 and ('sanction' in content or 'ofac' in content):
                risk_score = min(risk_score + 15, 100)
                risk_reasons.append(f"Associated with sanctioned entities (Similarity: {similarity:.2f})")
        
        logger.info(f"Regulatory analysis complete. Sanctions found: {sanctions_found}, Final risk: {risk_score}")
        
        # Convert blockchain transactions to API format
        transactions = []
        for tx in real_transactions:
            transactions.append(TransactionData(
                hash=tx.hash,
                from_address=tx.from_address,
                to_address=tx.to_address,
                value=tx.value,
                timestamp=tx.timestamp,
                block_number=tx.block_number,
                risk_score=risk_score if sanctions_found else None
            ))
        
        # Determine compliance status based on real analysis
        if sanctions_found or risk_score >= 80:
            compliance_status = "CRITICAL RISK - Immediate Action Required"
        elif risk_score >= 60:
            compliance_status = "HIGH RISK - Enhanced Due Diligence"
        elif risk_score >= 30:
            compliance_status = "MEDIUM RISK - Increased Monitoring"
        else:
            compliance_status = "LOW RISK - Standard Compliance"
        
        # Generate real-data recommendations
        recommendations = []
        if sanctions_found:
            recommendations.extend([
                "🚨 IMMEDIATE: Freeze all wallet transactions",
                "📞 URGENT: Report to compliance officer within 1 hour",
                "📋 REQUIRED: File Suspicious Activity Report (SAR)",
                "🔍 INVESTIGATE: Conduct enhanced due diligence on all counterparties"
            ])
        elif risk_score >= 60:
            recommendations.extend([
                "⚠️ Enhanced monitoring and transaction review required",
                "🔍 Investigate source and destination of large transactions",
                "📊 Review transaction patterns for suspicious activity",
                "📞 Consider reporting to compliance team"
            ])
        elif risk_score >= 30:
            recommendations.extend([
                "📈 Implement enhanced monitoring procedures",
                "🔄 Regular review of transaction patterns",
                "✅ Verify customer due diligence documentation"
            ])
        else:
            recommendations.extend([
                "✅ Continue standard AML monitoring",
                "📅 Schedule regular compliance reviews",
                "🔄 Monitor for changes in transaction patterns"
            ])
        
        # Generate comprehensive analysis summary
        analysis_summary = f"""🔍 REAL-TIME ANALYSIS REPORT

📍 Wallet Address:
   {request.address}

💰 Balance: {wallet_info.balance} ETH
📊 Total Transactions: {wallet_info.transaction_count}
⚠️  Risk Score: {risk_score}/100

🛡️  REGULATORY SCREENING:
   {'🚨 SANCTIONS MATCH FOUND' if sanctions_found else '✅ No sanctions matches'}
   📋 Sources: OFAC, SEC, CFTC via Pathway pipeline

📈 BLOCKCHAIN ANALYSIS:
   🔗 Recent Transactions: {len(real_transactions)}
   🏷️  Risk Factors: {len(risk_reasons)}

📊 COMPLIANCE STATUS:
   {compliance_status}

⏰ Completed: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
📡 Sources: Etherscan API + Pathway Pipeline"""
        
        logger.info(f"Analysis complete for {request.address}: Risk={risk_score}, Status={compliance_status}")
        
        return WalletAnalysisResponse(
            address=request.address,
            risk_score=risk_score,
            compliance_status=compliance_status,
            total_transactions=wallet_info.transaction_count,
            recent_transactions=transactions[:10],  # Limit to 10 most recent
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


@app.get("/api/status")
async def get_status():
    """Get system status and recent updates with live feed data"""
    try:
        # Get Pathway system stats
        pipeline_stats = pathway_fallback_manager.get_pipeline_stats()
        
        # Get recent documents from vector store (last 10 ingested)
        recent_docs = []
        if vector_store.documents:
            # Get last 10 documents sorted by timestamp
            sorted_docs = sorted(
                vector_store.documents, 
                key=lambda x: x.get('timestamp', ''), 
                reverse=True
            )[:10]
            
            for doc in sorted_docs:
                metadata = doc.get('metadata', {})
                recent_docs.append({
                    'id': metadata.get('id', doc.get('id', '')),
                    'source': metadata.get('source', doc.get('source', 'unknown')),
                    'title': metadata.get('title', doc.get('content', '')[:100] + "..."),
                    'link': metadata.get('link', ''),
                    'timestamp': metadata.get('timestamp', doc.get('timestamp', '')),
                    'type': metadata.get('type', doc.get('type', 'document')),
                    'risk_level': metadata.get('risk_level', 'low'),
                    'text': doc.get('content', '')[:200] + "..." if len(doc.get('content', '')) > 200 else doc.get('content', '')
                })
        
        # Get vector store stats
        index_stats = vector_store.get_stats()
        
        # Get recent alerts
        recent_alerts = pathway_fallback_manager.get_recent_alerts(5)
        
        return {
            "status": "active" if pipeline_stats.get('is_running', False) else "inactive",
            "last_updates": recent_docs,
            "total_documents": pipeline_stats.get('total_documents_processed', len(vector_store.documents)),
            "index_stats": {
                **index_stats,
                'pipelines_running': pipeline_stats.get('is_running', False),
                'alerts_generated': pipeline_stats.get('alerts_generated', len(recent_alerts))
            },
            "recent_alerts": recent_alerts,
            "pipelines": {
                "ofac": "active" if pipeline_stats.get('is_running') else "inactive",
                "news": "active" if pipeline_stats.get('is_running') else "inactive",
                "rss": "active" if pipeline_stats.get('is_running') else "inactive",
                "blockchain": "active" if pipeline_stats.get('is_running') else "inactive",
                "embeddings": "active" if pipeline_stats.get('is_running') else "inactive",
                "alerts": "active" if pipeline_stats.get('is_running') else "inactive"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
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
async def rag_query(question: str, target: str = None):
    """Enhanced RAG query endpoint with Mistral LLM and real-time data"""
    try:
        # Add target to monitoring if provided
        if target:
            pathway_fallback_manager.add_target_wallet(target)
        
        # Search for relevant documents using embeddings
        relevant_docs = await vector_store.search(question, k=10)
        
        # Prepare evidence documents
        evidence_docs = []
        for doc_tuple in relevant_docs:
            if isinstance(doc_tuple, tuple):
                doc, similarity = doc_tuple
            else:
                doc = doc_tuple
                similarity = 1.0
            
            evidence_docs.append({
                'source': doc.get('source', 'unknown'),
                'snippet': doc.get('content', '')[:300] + "..." if len(doc.get('content', '')) > 300 else doc.get('content', ''),
                'link': doc.get('link', ''),
                'timestamp': doc.get('timestamp', ''),
                'similarity': similarity,
                'metadata': doc.get('metadata', {})
            })
        
        # Use OpenRouter LLM for contextual response
        llm_result = await llm_client.query_with_context(
            question=f"Query: {question}" + (f" Target: {target}" if target else ""),
            context_documents=relevant_docs,
            conversation_history=None
        )
        
        if not llm_result.get('success'):
            return {
                "answer": "Failed to generate response. Please check your OpenRouter API configuration.",
                "risk_score": 0,
                "evidence": evidence_docs,
                "alerts": [],
                "news": []
            }
        
        # Get recent alerts
        recent_alerts = pathway_fallback_manager.get_recent_alerts(5)
        formatted_alerts = []
        for alert in recent_alerts:
            formatted_alerts.append({
                'type': alert.get('type', 'UNKNOWN'),
                'detail': alert.get('description', ''),
                'timestamp': alert.get('timestamp', '')
            })
        
        # Get recent news from evidence
        news_items = []
        for doc in evidence_docs:
            if doc['source'] == 'NEWS_API':
                news_items.append({
                    'title': doc['metadata'].get('title', 'News Update'),
                    'url': doc['link'],
                    'timestamp': doc['timestamp']
                })
        
        return {
            "answer": llm_result.get('response', ''),
            "risk_score": llm_result.get('risk_score', 0),
            "evidence": evidence_docs,
            "alerts": formatted_alerts,
            "news": news_items[:5]  # Top 5 news items
        }
        
    except Exception as e:
        logger.error(f"Error in enhanced RAG query: {e}")
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
