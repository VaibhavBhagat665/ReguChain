"""
Groq LLM Client
Real LLM responses using Groq API with Llama models
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
import json
from groq import AsyncGroq
from .config import GROQ_API_KEY, LLM_MODEL

logger = logging.getLogger(__name__)

class GroqLLMClient:
    """Groq LLM client for real-time intelligent responses"""
    
    def __init__(self):
        self.api_key = GROQ_API_KEY
        # Default to Llama 3.1 8B Instant (replaces deprecated llama3-8b-8192)
        self.model = "llama-3.1-8b-instant"
        if LLM_MODEL and "llama" in LLM_MODEL.lower():
             self.model = LLM_MODEL
        
        self.client = None
        if not self.api_key:
            logger.warning("⚠️ Groq API key not configured")
        else:
            self.client = AsyncGroq(api_key=self.api_key)
    
    async def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> Optional[str]:
        """Generate response using Groq chat completions API"""
        
        if not self.client:
            return "Groq API key not configured. Please set GROQ_API_KEY environment variable."
        
        try:
            logger.info(f"🤖 Generating response with {self.model} via Groq...")
            
            completion = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False
            )
            
            content = completion.choices[0].message.content
            
            if not content:
                logger.error("Empty content in Groq response.")
                return "Empty response generated"
            
            logger.info(f"✅ Generated response ({len(content)} chars)")
            return content
            
        except Exception as e:
            logger.error(f"❌ Error generating response with Groq: {e}")
            return f"Error generating response: {str(e)}"
    
    async def query_with_context(
        self, 
        question: str, 
        context_documents: List[Dict[str, Any]], 
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """Query LLM with retrieved context documents"""
        
        try:
            # Build context from retrieved documents
            context_text = ""
            evidence_sources = []
            
            for i, doc in enumerate(context_documents[:10]):  # Top 10 documents
                content = doc.get('content', '')
                metadata = doc.get('metadata', {})
                source = metadata.get('source', 'Unknown')
                
                context_text += f"[Evidence {i+1}] Source: {source}\n{content}\n\n"
                evidence_sources.append({
                    'id': i+1,
                    'source': source,
                    'content': content[:200] + "..." if len(content) > 200 else content,
                    'metadata': metadata
                })
            
            # Build system prompt
            system_prompt = f"""You are ReguChain AI, an expert in blockchain regulatory compliance and risk analysis.

You have access to real-time regulatory intelligence, sanctions data, news feeds, and blockchain transaction data.

INSTRUCTIONS:
1. Analyze the provided evidence documents carefully
2. Provide accurate, specific answers based on the evidence
3. Always cite evidence sources using [Evidence X] format
4. Assess risk levels: critical, high, medium, low
5. Provide actionable recommendations
6. Be concise but comprehensive
7. If evidence is insufficient, clearly state limitations

EVIDENCE DOCUMENTS:
{context_text}

Respond with structured analysis including:
- Direct answer to the question
- Risk assessment with reasoning
- Cited evidence sources
- Actionable recommendations"""

            # Build messages
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add conversation history if provided
            if conversation_history:
                messages.extend(conversation_history[-6:])  # Last 3 exchanges
            
            # Add current question
            messages.append({"role": "user", "content": question})
            
            # Generate response
            response_text = await self.generate_response(messages, max_tokens=1500)
            
            if not response_text:
                return {
                    "success": False,
                    "response": "Failed to generate response",
                    "error": "Empty response from LLM"
                }
            
            # Extract risk assessment from response
            risk_score = self._extract_risk_score(response_text, context_documents)
            
            return {
                "success": True,
                "response": response_text,
                "risk_score": risk_score,
                "evidence_sources": evidence_sources,
                "model_used": self.model,
                "context_documents_count": len(context_documents)
            }
            
        except Exception as e:
            logger.error(f"❌ Error in query_with_context: {e}")
            return {
                "success": False,
                "response": f"Error processing query: {str(e)}",
                "error": str(e)
            }
    
    def _extract_risk_score(self, response_text: str, context_documents: List[Dict]) -> int:
        """Extract numerical risk score from response and context"""
        response_lower = response_text.lower()
        
        # Check for explicit risk mentions in response
        if any(word in response_lower for word in ['critical', 'severe', 'high risk']):
            base_score = 80
        elif any(word in response_lower for word in ['high', 'significant', 'concerning']):
            base_score = 60
        elif any(word in response_lower for word in ['medium', 'moderate', 'some risk']):
            base_score = 40
        elif any(word in response_lower for word in ['low', 'minimal', 'slight']):
            base_score = 20
        else:
            base_score = 30  # Default moderate risk
        
        # Adjust based on context documents
        high_risk_sources = sum(1 for doc in context_documents 
                               if doc.get('metadata', {}).get('risk_level') in ['critical', 'high'])
        
        if high_risk_sources > 3:
            base_score += 20
        elif high_risk_sources > 1:
            base_score += 10
        
        # Clamp to 0-100
        return max(0, min(100, base_score))
    
    async def test_connection(self) -> bool:
        """Test Groq LLM API connection"""
        try:
            messages = [{"role": "user", "content": "Hello, this is a test."}]
            response = await self.generate_response(messages, max_tokens=50)
            return response is not None and "Error" not in response
        except:
            return False

# Global instance
llm_client = GroqLLMClient()
