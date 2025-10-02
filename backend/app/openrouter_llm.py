"""
OpenRouter LLM Client with Mistral
Real LLM responses using OpenRouter API with Mistral model
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
import aiohttp
import json
from .config import OPENROUTER_API_KEY, LLM_MODEL

logger = logging.getLogger(__name__)

class OpenRouterLLMClient:
    """OpenRouter LLM client for real-time intelligent responses"""
    
    def __init__(self):
        self.api_key = OPENROUTER_API_KEY
        self.model = LLM_MODEL or "mistralai/mistral-7b-instruct"
        self.base_url = "https://openrouter.ai/api/v1"
        
        if not self.api_key:
            logger.warning("⚠️ OpenRouter API key not configured")
    
    async def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> Optional[str]:
        """Generate response using OpenRouter chat completions API"""
        
        if not self.api_key:
            return "OpenRouter API key not configured. Please set OPENROUTER_API_KEY environment variable."
        
        try:
            logger.info(f"🤖 Generating response with {self.model}...")
            
            # Prepare request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://reguchain.ai",
                "X-Title": "ReguChain"
            }
            
            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": False
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=60
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"OpenRouter LLM API error {response.status}: {error_text}")
                        return f"API Error: {response.status} - {error_text}"
                    
                    data = await response.json()
            
            # Extract response
            logger.info(f"OpenRouter response data: {json.dumps(data, indent=2)}")
            
            choices = data.get('choices', [])
            if not choices:
                logger.error(f"No choices in OpenRouter response. Full response: {data}")
                return "No response generated"
            
            message = choices[0].get('message', {})
            content = message.get('content', '').strip()
            
            if not content:
                logger.error(f"Empty content in OpenRouter response. Message: {message}, Full response: {data}")
                return "Empty response generated"
            
            logger.info(f"✅ Generated response ({len(content)} chars)")
            return content
            
        except asyncio.TimeoutError:
            logger.error("❌ OpenRouter LLM API timeout")
            return "Request timeout. Please try again."
        except Exception as e:
            logger.error(f"❌ Error generating response: {e}")
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
        """Test OpenRouter LLM API connection"""
        try:
            messages = [{"role": "user", "content": "Hello, this is a test."}]
            response = await self.generate_response(messages, max_tokens=50)
            return response is not None and len(response) > 0
        except:
            return False

# Global instance
llm_client = OpenRouterLLMClient()
