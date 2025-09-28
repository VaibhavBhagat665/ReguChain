"""Pydantic models for API requests and responses"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum

class MessageRole(str, Enum):
    """Chat message roles"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class ChatMessage(BaseModel):
    """Chat message model"""
    role: MessageRole
    content: str
    timestamp: str
    metadata: Optional[Dict[str, Any]] = {}

class AgentRequest(BaseModel):
    """AI Agent request model"""
    message: str = Field(..., description="User message to the AI agent")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for context")
    wallet_address: Optional[str] = Field(None, description="Connected wallet address")
    context: Optional[Dict[str, Any]] = Field({}, description="Additional context")

class AgentCapability(BaseModel):
    """Agent capability description"""
    name: str
    description: str
    enabled: bool

class AgentResponse(BaseModel):
    """AI Agent response model"""
    message: str
    conversation_id: str
    risk_assessment: Optional[Dict[str, Any]] = None
    blockchain_data: Optional[Dict[str, Any]] = None
    suggested_actions: Optional[List[str]] = []
    confidence: float = Field(default=0.8, ge=0, le=1)
    capabilities_used: Optional[List[str]] = []
    follow_up_questions: Optional[List[str]] = []

class WalletAnalysisRequest(BaseModel):
    """Wallet analysis request"""
    address: str = Field(..., description="Wallet address to analyze")
    analysis_type: str = Field(default="comprehensive", description="Type of analysis")
    include_transactions: bool = Field(default=True, description="Include transaction analysis")
    include_compliance: bool = Field(default=True, description="Include compliance check")

class TransactionData(BaseModel):
    """Transaction data model"""
    hash: str
    from_address: str
    to_address: str
    value: str
    gas_used: Optional[str] = None
    timestamp: str
    block_number: Optional[int] = None
    risk_score: Optional[float] = None

class WalletAnalysisResponse(BaseModel):
    """Wallet analysis response"""
    address: str
    risk_score: float = Field(..., ge=0, le=100)
    compliance_status: str
    total_transactions: int
    recent_transactions: List[TransactionData]
    risk_factors: List[str]
    recommendations: List[str]
    analysis_summary: str

class Evidence(BaseModel):
    """Evidence model"""
    source: str
    snippet: str
    timestamp: str
    link: str
    relevance_score: Optional[float] = None

class OnchainMatch(BaseModel):
    """On-chain transaction match"""
    tx: str
    amount: float
    timestamp: str
    from_address: Optional[str] = Field(None, alias="from")
    to_address: Optional[str] = Field(None, alias="to")
    risk_indicators: Optional[List[str]] = []

class ConversationHistory(BaseModel):
    """Conversation history model"""
    conversation_id: str
    messages: List[ChatMessage]
    created_at: str
    updated_at: str
    wallet_address: Optional[str] = None

class StatusUpdate(BaseModel):
    """Status update model"""
    id: int
    source: str
    text: str
    timestamp: str
    link: str

class StatusResponse(BaseModel):
    """Status response model"""
    last_updates: List[StatusUpdate]
    total_documents: int
    index_stats: Dict
    agent_capabilities: List[AgentCapability]
    active_conversations: int
