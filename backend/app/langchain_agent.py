"""
LangChain-based AI Agent for ReguChain with RAG capabilities
"""
import logging
import json
from typing import List, Dict, Optional, Any
from datetime import datetime

from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.chains import RetrievalQA, LLMChain
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.callbacks import StreamingStdOutCallbackHandler
from langchain.schema import Document

from .config import (
    GROQ_API_KEY, LLM_MODEL, LLM_TEMPERATURE, 
    LLM_PROVIDER, FAISS_INDEX_PATH, DISABLE_EMBEDDINGS, DISABLE_VECTOR_STORE
)
from .realtime_news_service import realtime_news_service
from .groq_langchain import SimpleGroqAgent, create_groq_langchain_agent
from .risk import risk_engine
from .blockchain_service import blockchain_service

logger = logging.getLogger(__name__)

class LangChainAgent:
    """Advanced LangChain-based agent for regulatory compliance"""
    
    def __init__(self):
        self.llm = None
        self.embeddings = None
        self.vector_store = None
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        self.tools = []
        self.agent = None
        self.agent_executor = None
        
        # Initialize components
        self._initialize_llm()
        self._initialize_embeddings()
        self._initialize_vector_store()
        self._initialize_tools()
        self._initialize_agent()
    
    def _initialize_llm(self):
        """Initialize LLM - Groq only"""
        try:
            if GROQ_API_KEY:
                self.llm = create_groq_langchain_agent(GROQ_API_KEY, LLM_MODEL)
                logger.info(f"Groq LLM initialized successfully with model: {LLM_MODEL}")
            else:
                # Use simple Groq agent if API not available (limited capability)
                self.simple_groq = SimpleGroqAgent(None, LLM_MODEL)
                logger.warning("GROQ_API_KEY missing; using simple Groq agent with limited features")
        except Exception as e:
            logger.error(f"Error initializing LLM: {e}")
            self.llm = None
    
    def _initialize_embeddings(self):
        """Initialize embeddings model"""
        if DISABLE_EMBEDDINGS:
            logger.info("Embeddings disabled - skipping initialization")
            self.embeddings = None
            return
            
        try:
            # Use HuggingFace embeddings only (no Google)
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu'}
            )
            logger.info("HuggingFace embeddings initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing HuggingFace embeddings: {e}")
            self.embeddings = None
    
    def _initialize_vector_store(self):
        """Initialize FAISS vector store"""
        try:
            # Try to load existing index
            self.vector_store = FAISS.load_local(
                FAISS_INDEX_PATH,
                self.embeddings,
                allow_dangerous_deserialization=True
            )
            logger.info("Loaded existing FAISS index")
        except Exception as e:
            logger.info(f"Creating new FAISS index: {e}")
            # Create new index with sample documents
            sample_docs = [
                Document(
                    page_content="ReguChain is an advanced regulatory compliance platform for blockchain.",
                    metadata={"source": "system", "type": "info"}
                ),
                Document(
                    page_content="The platform provides real-time monitoring of regulatory updates from SEC, CFTC, and other agencies.",
                    metadata={"source": "system", "type": "feature"}
                )
            ]
            self.vector_store = FAISS.from_documents(sample_docs, self.embeddings)
    
    def _initialize_tools(self):
        """Initialize agent tools"""
        
        # Tool for searching regulatory news (uses realtime_news_service)
        def search_news_tool(query: str) -> str:
            """Search for regulatory news and updates"""
            try:
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                articles = loop.run_until_complete(
                    realtime_news_service.fetch_realtime_news(query=query, page_size=5)
                )
                if articles:
                    results = []
                    for a in articles[:5]:
                        results.append(
                            f"Title: {a.title}\n"
                            f"Source: {a.source}\n"
                            f"Relevance: {a.relevance_score:.2f}\n"
                            f"URL: {a.url}\n"
                        )
                    return "\n".join(results)
                return "No news articles found for the query."
            except Exception as e:
                return f"Error searching news: {str(e)}"
        
        # Tool for wallet analysis
        def analyze_wallet_tool(address: str) -> str:
            """Analyze blockchain wallet for compliance risks (real APIs)"""
            try:
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                txs = loop.run_until_complete(blockchain_service.get_transactions(address, limit=10))
                legacy_txs = [{
                    "tx": tx.hash,
                    "amount": float(tx.value),
                    "timestamp": tx.timestamp,
                    "from": tx.from_address,
                    "to": tx.to_address
                } for tx in txs]
                risk_score, risk_factors = risk_engine.calculate_risk_score(address, [], legacy_txs)
                result = f"Wallet Analysis for {address}:\n"
                result += f"Risk Score: {risk_score}/100\n"
                result += f"Risk Level: {'HIGH' if risk_score >= 70 else 'MEDIUM' if risk_score >= 40 else 'LOW'}\n"
                result += f"Total Transactions Analyzed: {len(legacy_txs)}\n"
                if risk_factors:
                    result += "\nRisk Factors:\n"
                    for factor in risk_factors[:5]:
                        result += f"- {factor}\n"
                return result
            except Exception as e:
                return f"Error analyzing wallet: {str(e)}"
        
        # Tool for RAG search
        def rag_search_tool(query: str) -> str:
            """Search regulatory knowledge base using RAG"""
            try:
                if self.vector_store:
                    docs = self.vector_store.similarity_search(query, k=3)
                    if docs:
                        results = []
                        for doc in docs:
                            results.append(f"Content: {doc.page_content[:300]}...\n"
                                         f"Source: {doc.metadata.get('source', 'Unknown')}")
                        return "\n\n".join(results)
                    else:
                        return "No relevant documents found in knowledge base."
                else:
                    return "Vector store not initialized."
            except Exception as e:
                return f"Error searching knowledge base: {str(e)}"
        
        # Tool for getting regulatory updates
        def get_regulatory_updates_tool(hours: str = "24") -> str:
            """Get recent regulatory updates from the last N hours (via realtime news)"""
            try:
                import asyncio
                from datetime import datetime, timedelta
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                hours_int = int(hours)
                since = (datetime.utcnow() - timedelta(hours=hours_int)).isoformat()
                articles = loop.run_until_complete(
                    realtime_news_service.fetch_realtime_news(
                        query="SEC OR CFTC OR FINRA OR OFAC OR regulation OR enforcement",
                        page_size=20
                    )
                )
                recent = [a for a in articles if a.published_at >= since]
                if recent:
                    result = f"Regulatory Updates (Last {hours_int} hours):\n"
                    result += f"Total Updates: {len(recent)}\n\n"
                    for a in recent[:5]:
                        result += f"• {a.title}\n  Source: {a.source} | Published: {a.published_at}\n\n"
                    return result
                return f"No regulatory updates found in the last {hours_int} hours."
            except Exception as e:
                return f"Error getting regulatory updates: {str(e)}"
        
        # Create tools list
        self.tools = [
            Tool(
                name="search_news",
                func=search_news_tool,
                description="Search for regulatory news and updates. Input should be a search query."
            ),
            Tool(
                name="analyze_wallet",
                func=analyze_wallet_tool,
                description="Analyze a blockchain wallet for compliance risks. Input should be a wallet address."
            ),
            Tool(
                name="search_knowledge_base",
                func=rag_search_tool,
                description="Search the regulatory knowledge base using RAG. Input should be a search query."
            ),
            Tool(
                name="get_regulatory_updates",
                func=get_regulatory_updates_tool,
                description="Get recent regulatory updates. Input should be number of hours to look back (default: 24)."
            )
        ]
    
    def _initialize_agent(self):
        """Initialize the ReAct agent"""
        if not self.llm:
            logger.warning("LLM not initialized, agent creation skipped")
            return
        
        # Create agent prompt
        prompt = PromptTemplate(
            input_variables=["input", "tools", "tool_names", "agent_scratchpad", "chat_history"],
            template="""You are ReguChain AI, an expert regulatory compliance assistant specializing in blockchain and cryptocurrency regulations.

You have access to the following tools:
{tools}

Tool Names: {tool_names}

Previous conversation:
{chat_history}

To answer questions, you can use these tools by following this format:
Thought: I need to [describe what you need to do]
Action: [tool_name]
Action Input: [input for the tool]
Observation: [tool output will appear here]

You can repeat the Thought/Action/Action Input/Observation cycle as needed.

When you have enough information to answer, respond with:
Thought: I now have enough information to provide a comprehensive answer
Final Answer: [your detailed response]

Current question: {input}

{agent_scratchpad}"""
        )
        
        try:
            # Create the agent
            self.agent = create_react_agent(
                llm=self.llm,
                tools=self.tools,
                prompt=prompt
            )
            
            # Create agent executor
            self.agent_executor = AgentExecutor(
                agent=self.agent,
                tools=self.tools,
                memory=self.memory,
                verbose=True,
                max_iterations=5,
                handle_parsing_errors=True
            )
            
            logger.info("ReAct agent initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing agent: {e}")
    
    def add_documents_to_knowledge_base(self, documents: List[Dict]):
        """Add documents to the vector store"""
        try:
            # Convert to LangChain documents
            docs = []
            for doc in documents:
                docs.append(Document(
                    page_content=doc.get("content", ""),
                    metadata={
                        "source": doc.get("source", "unknown"),
                        "title": doc.get("title", ""),
                        "timestamp": doc.get("timestamp", datetime.utcnow().isoformat())
                    }
                ))
            
            # Split documents
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            split_docs = text_splitter.split_documents(docs)
            
            # Add to vector store
            if self.vector_store:
                self.vector_store.add_documents(split_docs)
                # Save the updated index
                self.vector_store.save_local(FAISS_INDEX_PATH)
                logger.info(f"Added {len(split_docs)} document chunks to knowledge base")
            
        except Exception as e:
            logger.error(f"Error adding documents to knowledge base: {e}")
    
    def query(self, question: str, context: Optional[Dict] = None) -> Dict:
        """Query the agent with a question"""
        try:
            # If we have a simple Groq agent (fallback), use it
            if hasattr(self, 'simple_groq') and self.simple_groq:
                return self.simple_groq.query(question, context)
            
            # Otherwise use the full LangChain agent if available
            if self.agent_executor:
                # Add context to the question if provided
                if context:
                    question = f"Context: {json.dumps(context)}\n\nQuestion: {question}"
                
                # Run the agent
                response = self.agent_executor.run(input=question)
                
                return {
                    "success": True,
                    "response": response,
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                # Fallback response if agent not initialized
                return {
                    "success": False,
                    "response": "AI Agent is initializing. Please try again in a moment.",
                    "error": "Agent not fully initialized"
                }
                
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                "success": False,
                "response": "I encountered an error processing your request. Please try again.",
                "error": str(e)
            }
    
    def clear_memory(self):
        """Clear conversation memory"""
        self.memory.clear()
        logger.info("Conversation memory cleared")

# Create singleton instance
langchain_agent = LangChainAgent()
