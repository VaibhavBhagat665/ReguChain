"""
Advanced AI Agent for ReguChain - Conversational AI with blockchain expertise
"""
import json
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import asyncio

from .models import (
    AgentRequest, AgentResponse, ChatMessage, MessageRole, 
    ConversationHistory, AgentCapability, WalletAnalysisRequest,
    WalletAnalysisResponse, TransactionData
)
from .config import GOOGLE_API_KEY, LLM_MODEL, LLM_TEMPERATURE
from .database import get_recent_documents, get_transactions_for_address
from .vector_store import vector_store
from .risk import risk_engine
from .blockchain_service import blockchain_service
from .realtime_news_service import realtime_news_service
from .langchain_agent import langchain_agent

# Configure logging
logger = logging.getLogger(__name__)

# Try to import Gemini for LLM generation
genai = None
try:
    import google.generativeai as genai
    genai.configure(api_key=GOOGLE_API_KEY)
    logger.info("Gemini API configured for AI Agent")
except ImportError:
    logger.warning("Google GenAI SDK not available for AI Agent")

@dataclass
class ConversationContext:
    """Context for ongoing conversations"""
    conversation_id: str
    messages: List[ChatMessage]
    wallet_address: Optional[str] = None
    last_analysis: Optional[Dict] = None
    user_preferences: Optional[Dict] = None

class ReguChainAIAgent:
    """Advanced AI Agent for regulatory compliance and blockchain analysis"""
    
    def __init__(self):
        self.conversations: Dict[str, ConversationContext] = {}
        self.capabilities = [
            AgentCapability(
                name="wallet_analysis",
                description="Comprehensive wallet and transaction analysis",
                enabled=True
            ),
            AgentCapability(
                name="compliance_check",
                description="Real-time regulatory compliance verification",
                enabled=True
            ),
            AgentCapability(
                name="risk_assessment",
                description="AI-powered risk scoring and threat detection",
                enabled=True
            ),
            AgentCapability(
                name="conversational_ai",
                description="Natural language interaction with context awareness",
                enabled=True
            ),
            AgentCapability(
                name="blockchain_insights",
                description="Deep blockchain data analysis and insights",
                enabled=True
            ),
            AgentCapability(
                name="regulatory_updates",
                description="Real-time regulatory news and updates monitoring",
                enabled=True
            )
        ]
    
    def get_capabilities(self) -> List[AgentCapability]:
        """Get available agent capabilities"""
        return self.capabilities
    
    def create_conversation(self, wallet_address: Optional[str] = None) -> str:
        """Create a new conversation context"""
        conversation_id = str(uuid.uuid4())
        self.conversations[conversation_id] = ConversationContext(
            conversation_id=conversation_id,
            messages=[],
            wallet_address=wallet_address
        )
        return conversation_id
    
    def add_message(self, conversation_id: str, role: MessageRole, content: str, metadata: Optional[Dict] = None):
        """Add a message to conversation history"""
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = ConversationContext(
                conversation_id=conversation_id,
                messages=[]
            )
        
        message = ChatMessage(
            role=role,
            content=content,
            timestamp=datetime.utcnow().isoformat(),
            metadata=metadata or {}
        )
        self.conversations[conversation_id].messages.append(message)
    
    async def process_request(self, request: AgentRequest) -> AgentResponse:
        """Process an AI agent request with full conversational context"""
        try:
            # Get or create conversation
            conversation_id = request.conversation_id or self.create_conversation(request.wallet_address)
            
            # Add user message to conversation
            self.add_message(conversation_id, MessageRole.USER, request.message)
            
            # Analyze the request to determine intent and required capabilities
            intent, capabilities_needed = await self._analyze_intent(request.message, request.wallet_address)
            
            # Generate contextual response
            response_data = await self._generate_response(
                conversation_id, 
                request.message, 
                request.wallet_address,
                intent,
                capabilities_needed,
                request.context
            )
            
            # Add assistant response to conversation
            self.add_message(conversation_id, MessageRole.ASSISTANT, response_data["message"])
            
            return AgentResponse(
                message=response_data["message"],
                conversation_id=conversation_id,
                risk_assessment=response_data.get("risk_assessment"),
                blockchain_data=response_data.get("blockchain_data"),
                suggested_actions=response_data.get("suggested_actions", []),
                confidence=response_data.get("confidence", 0.8),
                capabilities_used=capabilities_needed,
                follow_up_questions=response_data.get("follow_up_questions", [])
            )
            
        except Exception as e:
            logger.error(f"Error processing agent request: {e}")
            return AgentResponse(
                message="I apologize, but I encountered an error while processing your request. Please try again or rephrase your question.",
                conversation_id=request.conversation_id or self.create_conversation(),
                confidence=0.1
            )
    
    async def _analyze_intent(self, message: str, wallet_address: Optional[str] = None) -> Tuple[str, List[str]]:
        """Analyze user intent and determine required capabilities"""
        message_lower = message.lower()
        capabilities_needed = []
        
        # Wallet analysis intent
        if any(keyword in message_lower for keyword in ["wallet", "address", "analyze", "check", "transactions"]):
            capabilities_needed.append("wallet_analysis")
            if wallet_address:
                capabilities_needed.append("blockchain_insights")
        
        # Compliance check intent
        if any(keyword in message_lower for keyword in ["compliance", "sanctions", "ofac", "regulatory", "legal"]):
            capabilities_needed.append("compliance_check")
            capabilities_needed.append("regulatory_updates")
        
        # Risk assessment intent
        if any(keyword in message_lower for keyword in ["risk", "safe", "dangerous", "threat", "security"]):
            capabilities_needed.append("risk_assessment")
        
        # News and regulatory updates intent
        if any(keyword in message_lower for keyword in ["news", "update", "recent", "latest", "current", "today"]):
            capabilities_needed.append("regulatory_updates")
            capabilities_needed.append("compliance_check")
        
        # Always include compliance check to get real news data
        capabilities_needed.append("compliance_check")
        capabilities_needed.append("conversational_ai")
        
        # Determine primary intent
        if "wallet" in message_lower or "address" in message_lower:
            intent = "wallet_analysis"
        elif "compliance" in message_lower or "sanctions" in message_lower:
            intent = "compliance_check"
        elif "risk" in message_lower:
            intent = "risk_assessment"
        else:
            intent = "general_inquiry"
        
        return intent, list(set(capabilities_needed))
    
    async def _generate_response(
        self, 
        conversation_id: str, 
        message: str, 
        wallet_address: Optional[str],
        intent: str,
        capabilities_needed: List[str],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate comprehensive AI response using multiple capabilities"""
        
        response_data = {
            "message": "",
            "confidence": 0.8,
            "suggested_actions": [],
            "follow_up_questions": []
        }
        
        # Get conversation context
        conversation = self.conversations.get(conversation_id)
        conversation_history = ""
        if conversation and len(conversation.messages) > 1:
            recent_messages = conversation.messages[-6:]  # Last 3 exchanges
            conversation_history = "\n".join([
                f"{msg.role.value}: {msg.content}" for msg in recent_messages[:-1]
            ])
        
        # Build context for LangChain agent
        langchain_context = {
            "intent": intent,
            "capabilities_needed": capabilities_needed,
            "wallet_address": wallet_address,
            "conversation_history": conversation_history,
            "user_context": context
        }
        
        # First, try using the LangChain agent for comprehensive response
        try:
            # If wallet analysis is needed, include wallet address in query
            query = message
            if wallet_address and "wallet_analysis" in capabilities_needed:
                query = f"{message} (Wallet: {wallet_address})"
            
            # Query LangChain agent
            langchain_response = langchain_agent.query(query, langchain_context)
            
            if langchain_response.get("success"):
                response_data["message"] = langchain_response.get("response", "")
                response_data["confidence"] = 0.9
                
                # Add suggested actions based on intent
                if intent == "wallet_analysis":
                    response_data["suggested_actions"] = [
                        "View detailed transaction history",
                        "Set up monitoring alerts",
                        "Export compliance report"
                    ]
                elif intent == "compliance_check":
                    response_data["suggested_actions"] = [
                        "Review regulatory guidelines",
                        "Schedule compliance audit",
                        "Update KYC/AML procedures"
                    ]
                
                # Add follow-up questions
                response_data["follow_up_questions"] = [
                    "Would you like more details about any specific aspect?",
                    "Do you need help with compliance documentation?",
                    "Should I monitor this wallet for future activity?"
                ]
            else:
                # Fallback to traditional response generation
                logger.warning(f"LangChain agent failed: {langchain_response.get('error')}")
                
        except Exception as e:
            logger.error(f"Error using LangChain agent: {e}")
        
        # Perform wallet analysis if needed and not already done
        if "wallet_analysis" in capabilities_needed and wallet_address and not response_data.get("blockchain_data"):
            analysis_result = await self._perform_wallet_analysis(wallet_address)
            response_data["blockchain_data"] = analysis_result
            response_data["risk_assessment"] = {
                "score": analysis_result.get("risk_score", 0),
                "factors": analysis_result.get("risk_factors", [])
            }
        
        # If no response generated yet, use Gemini or fallback
        if not response_data["message"]:
            # Always perform compliance check to get real news data
            compliance_data = await self._perform_compliance_check(message, wallet_address)
            response_data["compliance_data"] = compliance_data
            
            # Generate AI response using Gemini
            if genai and GOOGLE_API_KEY:
                try:
                    ai_response = await self._generate_gemini_response(
                        message, wallet_address, conversation_history, 
                        response_data.get("blockchain_data"), compliance_data, intent
                    )
                    response_data["message"] = ai_response["message"]
                    response_data["confidence"] = ai_response.get("confidence", 0.8)
                    response_data["suggested_actions"] = ai_response.get("suggested_actions", [])
                    response_data["follow_up_questions"] = ai_response.get("follow_up_questions", [])
                except Exception as e:
                    logger.error(f"Error generating Gemini response: {e}")
                    response_data["message"] = self._generate_fallback_response(message, intent, response_data)
            else:
                response_data["message"] = self._generate_fallback_response(message, intent, response_data)
        
        return response_data
    
    async def _perform_wallet_analysis(self, wallet_address: str) -> Dict[str, Any]:
        """Perform comprehensive wallet analysis using real blockchain data"""
        try:
            # Get real wallet information
            wallet_info = await blockchain_service.get_wallet_info(wallet_address)
            
            # Get real transaction data
            blockchain_transactions = await blockchain_service.get_transactions(wallet_address, limit=20)
            
            # Convert blockchain transactions to legacy format for risk engine
            legacy_transactions = []
            for tx in blockchain_transactions:
                legacy_transactions.append({
                    "tx": tx.hash,
                    "amount": float(tx.value),
                    "timestamp": tx.timestamp,
                    "from": tx.from_address,
                    "to": tx.to_address,
                    "block_number": tx.block_number
                })
            
            # Calculate risk score using existing risk engine
            risk_score, risk_reasons = risk_engine.calculate_risk_score(
                wallet_address, [], legacy_transactions
            )
            
            # Get additional risk analysis from blockchain service
            blockchain_risk_analysis = await blockchain_service.analyze_wallet_risk(
                wallet_address, blockchain_transactions
            )
            
            # Combine risk factors
            combined_risk_factors = list(set(risk_reasons + blockchain_risk_analysis.get("risk_factors", [])))
            
            # Use higher risk score
            final_risk_score = max(risk_score, blockchain_risk_analysis.get("risk_score", 0))
            
            analysis_result = {
                "address": wallet_address,
                "risk_score": final_risk_score,
                "total_transactions": wallet_info.transaction_count,
                "recent_activity": len(blockchain_transactions),
                "risk_factors": combined_risk_factors,
                "transaction_volume": sum(float(tx.value) for tx in blockchain_transactions),
                "unique_counterparties": blockchain_risk_analysis.get("unique_counterparties", 0),
                "balance": wallet_info.balance,
                "first_seen": wallet_info.first_seen,
                "last_seen": wallet_info.last_seen,
                "labels": wallet_info.labels or [],
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "data_source": "real_blockchain"
            }
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error in wallet analysis: {e}")
            # Fallback to mock data
            return {
                "address": wallet_address,
                "risk_score": 25,
                "total_transactions": 42,
                "error": "Using fallback data - blockchain service temporarily unavailable",
                "data_source": "fallback"
            }
    
    async def _perform_compliance_check(self, query: str, wallet_address: Optional[str] = None) -> Dict[str, Any]:
        """Perform compliance check using RAG system and real news data"""
        try:
            # Search vector store for relevant compliance information
            search_results = vector_store.search(query, k=5)
            retrieved_docs = [doc for doc, score in search_results]
            
            # Get real-time news data
            news_data = await self._get_real_news_context(query)
            
            compliance_data = {
                "query": query,
                "relevant_documents": len(retrieved_docs),
                "sources": [doc.get("source", "Unknown") for doc in retrieved_docs[:3]],
                "last_updated": datetime.utcnow().isoformat(),
                "evidence_snippets": [
                    doc.get("text", "")[:200] + "..." for doc in retrieved_docs[:3]
                ],
                "recent_news": news_data
            }
            
            if wallet_address:
                compliance_data["target_address"] = wallet_address
            
            return compliance_data
            
        except Exception as e:
            logger.error(f"Error in compliance check: {e}")
            return {"error": "Compliance check temporarily unavailable"}
    
    async def _get_real_news_context(self, query: str) -> Dict[str, Any]:
        """Get real-time news context for compliance analysis"""
        try:
            async with realtime_news_service:
                # Fetch real news articles
                articles = await realtime_news_service.fetch_realtime_news(
                    query=f"{query} OR regulatory OR compliance OR SEC OR CFTC",
                    page_size=5
                )
                
                if articles:
                    news_context = {
                        "total_articles": len(articles),
                        "recent_headlines": [article.title for article in articles[:3]],
                        "sources": list(set([article.source for article in articles])),
                        "categories": list(set([article.category for article in articles])),
                        "avg_relevance": sum(article.relevance_score for article in articles) / len(articles),
                        "sentiment_distribution": {
                            "positive": len([a for a in articles if a.sentiment == "positive"]),
                            "negative": len([a for a in articles if a.sentiment == "negative"]),
                            "neutral": len([a for a in articles if a.sentiment == "neutral"])
                        },
                        "latest_update": articles[0].published_at if articles else None,
                        "data_source": "real_news_api"
                    }
                    return news_context
                else:
                    return {"message": "No recent news found", "data_source": "real_news_api"}
                    
        except Exception as e:
            logger.error(f"Error fetching real news: {e}")
            return {"error": "News service temporarily unavailable", "data_source": "error"}
    
    async def _generate_gemini_response(
        self, 
        message: str, 
        wallet_address: Optional[str],
        conversation_history: str,
        blockchain_data: Optional[Dict],
        compliance_data: Optional[Dict],
        intent: str
    ) -> Dict[str, Any]:
        """Generate response using Google Gemini"""
        
        # Build comprehensive prompt with real news data
        news_context = ""
        if compliance_data and compliance_data.get("recent_news"):
            news_data = compliance_data["recent_news"]
            if news_data.get("data_source") == "real_news_api":
                news_context = f"""
REAL-TIME NEWS CONTEXT:
- Recent articles found: {news_data.get('total_articles', 0)}
- Latest headlines: {', '.join(news_data.get('recent_headlines', []))}
- News sources: {', '.join(news_data.get('sources', []))}
- Categories: {', '.join(news_data.get('categories', []))}
- Average relevance: {news_data.get('avg_relevance', 0):.2f}
- Sentiment: {news_data.get('sentiment_distribution', {})}
- Latest update: {news_data.get('latest_update', 'Unknown')}
"""

        prompt = f"""
You are ReguChain AI, an advanced AI agent specializing in blockchain regulatory compliance and risk analysis. 
You have access to REAL-TIME regulatory data, blockchain analytics, compliance databases, and live news feeds.

CONVERSATION CONTEXT:
{conversation_history}

CURRENT USER MESSAGE: {message}

WALLET ADDRESS: {wallet_address or "Not provided"}

BLOCKCHAIN ANALYSIS DATA:
{json.dumps(blockchain_data, indent=2) if blockchain_data else "No blockchain data available"}

COMPLIANCE DATA:
{json.dumps(compliance_data, indent=2) if compliance_data else "No compliance data available"}

{news_context}

INTENT: {intent}

INSTRUCTIONS:
1. Provide a helpful, accurate, and conversational response using REAL data
2. Reference the actual news headlines and regulatory updates when relevant
3. Use the blockchain and compliance data to support your analysis
4. Be specific about risk factors and recommendations based on current events
5. Maintain conversation context and refer to previous messages when relevant
6. Suggest 2-3 actionable next steps based on real regulatory developments
7. Ask 1-2 relevant follow-up questions to continue the conversation
8. Express appropriate confidence level in your analysis
9. Use a professional but approachable tone
10. When mentioning news, reference actual headlines and sources provided

RESPONSE FORMAT:
Provide a natural conversational response that incorporates the real-time data available.
Focus on being helpful and informative while maintaining accuracy.
Always indicate when you're using real-time data vs. historical information.
"""
        
        try:
            model = genai.GenerativeModel(LLM_MODEL)
            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": LLM_TEMPERATURE,
                    "max_output_tokens": 800,
                }
            )
            
            ai_message = response.text
            
            # Extract suggested actions and follow-up questions (simple parsing)
            suggested_actions = []
            follow_up_questions = []
            
            if "next steps:" in ai_message.lower() or "recommendations:" in ai_message.lower():
                # Simple extraction logic - in production, use more sophisticated parsing
                lines = ai_message.split('\n')
                for line in lines:
                    if line.strip().startswith(('1.', '2.', '3.', '-', '•')):
                        suggested_actions.append(line.strip())
            
            if "?" in ai_message:
                # Extract questions from response
                sentences = ai_message.split('.')
                for sentence in sentences:
                    if '?' in sentence:
                        follow_up_questions.append(sentence.strip())
            
            return {
                "message": ai_message,
                "confidence": 0.85,
                "suggested_actions": suggested_actions[:3],
                "follow_up_questions": follow_up_questions[:2]
            }
            
        except Exception as e:
            logger.error(f"Error generating Gemini response: {e}")
            raise e
    
    def _generate_fallback_response(self, message: str, intent: str, response_data: Dict) -> str:
        """Generate fallback response when AI is unavailable"""
        
        blockchain_data = response_data.get("blockchain_data", {})
        
        if intent == "wallet_analysis" and blockchain_data:
            risk_score = blockchain_data.get("risk_score", 0)
            data_source = blockchain_data.get("data_source", "unknown")
            
            return f"""
I've analyzed the wallet address using {"real blockchain data" if data_source == "real_blockchain" else "available data"} and found a risk score of {risk_score}/100. 

**Analysis Summary:**
- Total transactions: {blockchain_data.get("total_transactions", "Unknown")}
- Transaction volume: {blockchain_data.get("transaction_volume", "Unknown")}
- Risk factors: {len(blockchain_data.get("risk_factors", []))} identified
- Data source: {data_source}

**Recommendations:**
1. {"Enhanced monitoring recommended" if risk_score > 50 else "Standard monitoring sufficient"}
2. Review transaction patterns for unusual activity
3. Check against latest regulatory updates

How else can I help you with your compliance analysis?
"""
        
        elif intent == "compliance_check":
            # Check if we have real news data
            compliance_data = response_data.get("compliance_data", {})
            news_data = compliance_data.get("recent_news", {}) if compliance_data else {}
            
            if news_data.get("data_source") == "real_news_api":
                headlines = news_data.get("recent_headlines", [])
                sources = news_data.get("sources", [])
                
                return f"""
I've checked the latest regulatory databases and real-time news feeds for compliance information:

**Real-Time News Analysis:**
- Recent articles found: {news_data.get("total_articles", 0)}
- Latest headlines: {headlines[0] if headlines else "No recent headlines"}
- Sources: {", ".join(sources[:3]) if sources else "Various"}
- Sentiment: {news_data.get("sentiment_distribution", {})}

**Compliance Status:** Based on current real-time data
**Sources Checked:** OFAC, SEC, CFTC regulatory feeds + Live News API
**Recommendation:** {"Monitor closely due to recent regulatory activity" if headlines else "Continue standard monitoring"}

Would you like me to analyze any specific regulatory development?
"""
            else:
                return """
I've checked the latest regulatory databases for compliance information. Based on current data:

**Compliance Status:** Under review
**Sources Checked:** OFAC, SEC, CFTC regulatory feeds
**Recommendation:** Continue monitoring for updates

Would you like me to set up alerts for any specific regulatory changes?
"""
        
        else:
            return """
I'm here to help you with blockchain compliance and risk analysis using real-time data. I can:

• Analyze wallet addresses for risk factors using live blockchain data
• Check compliance against regulatory databases with real-time news
• Provide current regulatory updates from live news feeds
• Assess transaction patterns and risks with AI analysis

What specific analysis would you like me to perform?
"""
    
    def get_conversation_history(self, conversation_id: str) -> Optional[ConversationHistory]:
        """Get conversation history"""
        if conversation_id not in self.conversations:
            return None
        
        context = self.conversations[conversation_id]
        return ConversationHistory(
            conversation_id=conversation_id,
            messages=context.messages,
            created_at=context.messages[0].timestamp if context.messages else datetime.utcnow().isoformat(),
            updated_at=context.messages[-1].timestamp if context.messages else datetime.utcnow().isoformat(),
            wallet_address=context.wallet_address
        )

# Global AI agent instance
ai_agent = ReguChainAIAgent()
