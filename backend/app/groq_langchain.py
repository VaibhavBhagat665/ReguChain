"""
Groq integration with LangChain for ReguChain
"""
import os
from typing import Dict, Any, List, Optional
from langchain.llms.base import LLM
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from langchain.callbacks.manager import CallbackManagerForLLMRun
import logging

logger = logging.getLogger(__name__)

class GroqLLM(LLM):
    """Custom LangChain LLM wrapper for Groq"""
    
    groq_api_key: str
    model_name: str = "llama-3.1-8b-instant"
    temperature: float = 0.3
    max_tokens: int = 1000
    
    def __init__(self, groq_api_key: str, model_name: str = "llama-3.1-8b-instant", **kwargs):
        super().__init__(**kwargs)
        self.groq_api_key = groq_api_key
        self.model_name = model_name
        
        # Initialize Groq client
        try:
            import groq
            self.client = groq.Groq(api_key=groq_api_key)
        except ImportError:
            raise ImportError("Please install groq: pip install groq")
    
    @property
    def _llm_type(self) -> str:
        return "groq"
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """Call Groq API"""
        try:
            response = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=self.model_name,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                stop=stop
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            return f"Error: {str(e)}"
    
    @property
    def _identifying_params(self) -> Dict[str, Any]:
        """Get identifying parameters"""
        return {
            "model_name": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }

class GroqChatLLM:
    """Chat interface for Groq"""
    
    def __init__(self, groq_api_key: str, model_name: str = "llama-3.1-8b-instant"):
        self.groq_api_key = groq_api_key
        self.model_name = model_name
        
        try:
            import groq
            self.client = groq.Groq(api_key=groq_api_key)
        except ImportError:
            raise ImportError("Please install groq: pip install groq")
    
    def generate_response(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate response from messages"""
        try:
            response = self.client.chat.completions.create(
                messages=messages,
                model=self.model_name,
                max_tokens=kwargs.get('max_tokens', 1000),
                temperature=kwargs.get('temperature', 0.3)
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Groq chat error: {e}")
            return f"Error: {str(e)}"

def create_groq_langchain_agent(groq_api_key: str, model_name: str = "llama-3.1-8b-instant"):
    """Create a LangChain agent using Groq"""
    
    # Create Groq LLM
    llm = GroqLLM(
        groq_api_key=groq_api_key,
        model_name=model_name,
        temperature=0.3,
        max_tokens=1000
    )
    
    return llm

def test_groq_integration(groq_api_key: str):
    """Test Groq integration"""
    try:
        llm = create_groq_langchain_agent(groq_api_key)
        
        # Test prompt
        response = llm("What are the latest trends in cryptocurrency regulation? Keep it brief.")
        
        print(f"✅ Groq LangChain integration working!")
        print(f"Response: {response[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Groq integration error: {e}")
        return False

# Simple non-LangChain version for immediate use
class SimpleGroqAgent:
    """Simple Groq agent without LangChain dependencies"""
    
    def __init__(self, api_key: str, model: str = "llama-3.1-8b-instant"):
        self.api_key = api_key
        self.model = model
        
        try:
            import groq
            self.client = groq.Groq(api_key=api_key)
        except ImportError:
            raise ImportError("Install groq: pip install groq")
    
    def query(self, prompt: str, context: Dict = None) -> Dict[str, Any]:
        """Query Groq with context"""
        try:
            # Build enhanced prompt with context
            if context:
                enhanced_prompt = f"""
Context: {context.get('user_context', {})}
Intent: {context.get('intent', 'general')}
Capabilities: {context.get('capabilities_needed', [])}

User Query: {prompt}

Please provide a helpful response as ReguChain AI, focusing on regulatory compliance and blockchain analysis.
"""
            else:
                enhanced_prompt = prompt
            
            response = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are ReguChain AI, an expert in blockchain regulatory compliance and risk analysis."
                    },
                    {
                        "role": "user", 
                        "content": enhanced_prompt
                    }
                ],
                model=self.model,
                max_tokens=800,
                temperature=0.3
            )
            
            return {
                "success": True,
                "response": response.choices[0].message.content,
                "model": self.model,
                "provider": "groq"
            }
            
        except Exception as e:
            logger.error(f"Groq query error: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": "I apologize, but I'm experiencing technical difficulties. Please try again."
            }
