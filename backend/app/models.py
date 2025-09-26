"""Pydantic models for API requests and responses"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime

class QueryRequest(BaseModel):
    """Query request model"""
    question: str = Field(..., description="The question to ask")
    target: Optional[str] = Field(None, description="Target wallet address or entity name")

class Evidence(BaseModel):
    """Evidence model"""
    source: str
    snippet: str
    timestamp: str
    link: str

class OnchainMatch(BaseModel):
    """On-chain transaction match"""
    tx: str
    amount: float
    timestamp: str
    from_address: Optional[str] = Field(None, alias="from")
    to_address: Optional[str] = Field(None, alias="to")

class QueryResponse(BaseModel):
    """Query response model"""
    answer: str
    risk_score: float = Field(..., ge=0, le=100)
    evidence: List[Evidence]
    onchain_matches: List[OnchainMatch]
    risk_reasons: Optional[List[str]] = []
    recommendations: Optional[List[str]] = []

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

class SimulateRequest(BaseModel):
    """Simulate ingestion request"""
    target: Optional[str] = Field(None, description="Target wallet or entity to simulate")

class SimulateResponse(BaseModel):
    """Simulate ingestion response"""
    target: str
    documents_added: int
    documents: List[Dict]
    timestamp: str
    message: str

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: str
    services: Dict[str, str]
