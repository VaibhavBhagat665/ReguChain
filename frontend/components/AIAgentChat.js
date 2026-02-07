'use client';

import { useState, useEffect, useRef } from 'react';
import { Send, Bot, User, Loader, MessageSquare, Brain, Shield, Activity, Sparkles, Copy, ThumbsUp, ThumbsDown } from 'lucide-react';
import { v4 as uuidv4 } from 'uuid';
import { queryAPI } from '../lib/api';
import EnhancedQueryResults from './EnhancedQueryResults';

export default function AIAgentChat({ walletAddress, onAnalysisResult, initialQuestion }) {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const [agentCapabilities, setAgentCapabilities] = useState([]);
  const [lastQueryResult, setLastQueryResult] = useState(null);
  const messagesEndRef = useRef(null);


  const mountedRef = useRef(true);
  const sendControllerRef = useRef(null);
  const initialSentRef = useRef(false);

  useEffect(() => {
    // Track mounted state to avoid setState after unmount
    mountedRef.current = true;
    const controller = new AbortController();

    // Initialize conversation
    initializeConversation();
    // Fetch agent capabilities with abort signal
    fetchCapabilities(controller.signal);

    return () => {
      mountedRef.current = false;
      try { controller.abort(); } catch (e) { }
      if (sendControllerRef.current) {
        try { sendControllerRef.current.abort(); } catch (e) { }
      }
    };
  }, []);

  useEffect(() => {
    // Auto-scroll to bottom when new messages arrive
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // When wallet connects, send a greeting message
    if (walletAddress && messages.length === 0) {
      sendWelcomeMessage();
    }
  }, [walletAddress]);

  useEffect(() => {
    // If there's an initial question, send it only once after welcome message
    if (!initialSentRef.current && initialQuestion && messages.length > 0) {
      initialSentRef.current = true;
      setInputMessage(initialQuestion);
      setTimeout(() => {
        sendMessage(initialQuestion);
      }, 500);
    }
  }, [initialQuestion, messages.length]);

  const scrollToBottom = () => {
    // Only scroll if user is near bottom to avoid interrupting reading
    if (messagesEndRef.current) {
      const container = messagesEndRef.current.parentElement;
      const isNearBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 100;
      if (isNearBottom || messages.length <= 2) {
        messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
      }
    }
  };

  const initializeConversation = () => {
    const newConversationId = uuidv4();
    setConversationId(newConversationId);

    // Add welcome message
    const welcomeMessage = {
      id: uuidv4(),
      role: 'assistant',
      content: `👋 Hello! I'm ReguChain AI, your advanced blockchain compliance assistant. I can help you with:

• **Wallet Analysis** - Comprehensive risk assessment and transaction analysis
• **Compliance Checks** - Real-time regulatory database verification  
• **Risk Monitoring** - Continuous threat detection and alerts
• **Regulatory Updates** - Latest compliance news and requirements

${walletAddress ? `I see you have wallet ${walletAddress.substring(0, 6)}...${walletAddress.substring(walletAddress.length - 4)} connected. Would you like me to analyze it?` : 'Connect your wallet to get started with personalized analysis!'}`,
      timestamp: new Date().toISOString(),
      metadata: {}
    };

    setMessages([welcomeMessage]);
  };

  const sendWelcomeMessage = () => {
    const welcomeMessage = {
      id: uuidv4(),
      role: 'assistant',
      content: `🔗 Great! I can see your wallet is now connected. Let me provide you with some quick insights:

**Connected Wallet:** ${walletAddress}

I can help you:
1. **Analyze** this wallet for compliance risks
2. **Monitor** it for ongoing regulatory changes  
3. **Check** specific transactions or addresses
4. **Explain** any compliance concerns

What would you like to explore first?`,
      timestamp: new Date().toISOString(),
      metadata: { walletAddress }
    };

    setMessages(prev => [...prev, welcomeMessage]);
  };

  const fetchCapabilities = async (signal = undefined) => {
    try {
      const response = await fetch('/api/agent/capabilities', { signal });
      if (response.ok) {
        const capabilities = await response.json();
        if (mountedRef.current) setAgentCapabilities(capabilities);
      }
    } catch (error) {
      if (error.name === 'AbortError') return; // expected on unmount
      console.error('Error fetching capabilities:', error);
    }
  };

  const sendMessage = async (messageToSend = null) => {
    const rawMessage = messageToSend ?? inputMessage;
    const messageContent = typeof rawMessage === 'string'
      ? rawMessage
      : rawMessage?.content ?? '';
    const trimmedMessage = messageContent.trim();

    if (!trimmedMessage || isLoading) return;

    const userMessage = {
      id: uuidv4(),
      role: 'user',
      content: trimmedMessage,
      timestamp: new Date().toISOString(),
      metadata: {}
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    if (mountedRef.current) setIsLoading(true);

    // Abort previous chat request if any
    if (sendControllerRef.current) {
      try { sendControllerRef.current.abort(); } catch (e) { }
    }
    const controller = new AbortController();
    sendControllerRef.current = controller;

    try {
      // Use the enhanced query API
      const agentResponse = await queryAPI(trimmedMessage, walletAddress, conversationId);
      if (!mountedRef.current) return;

      // Store the enhanced query result
      setLastQueryResult(agentResponse);

      const assistantMessage = {
        id: uuidv4(),
        role: 'assistant',
        content: agentResponse.answer || agentResponse.message || 'I received your query but couldn\'t generate a proper response.',
        timestamp: new Date().toISOString(),
        metadata: {
          risk_score: agentResponse.risk_score,
          evidence: agentResponse.evidence,
          alerts: agentResponse.alerts,
          news: agentResponse.news,
          confidence: agentResponse.confidence,
          suggested_actions: agentResponse.suggested_actions || [],
          follow_up_questions: agentResponse.follow_up_questions || [],
          enhanced_result: agentResponse
        }
      };

      setMessages(prev => [...prev, assistantMessage]);

      // If there's analysis data, pass it to parent component
      if (agentResponse.risk_score !== undefined || agentResponse.evidence) {
        onAnalysisResult && onAnalysisResult({
          risk_score: agentResponse.risk_score,
          evidence: agentResponse.evidence,
          alerts: agentResponse.alerts,
          news: agentResponse.news
        });
      }

    } catch (error) {
      if (error && error.name === 'AbortError') {
        // Abort is expected on unmount or on new requests - do nothing
        console.warn('Chat request aborted');
        return;
      }
      console.error('Error sending message:', error);

      // Provide a transparent error message and guidance.
      if (mountedRef.current) {
        const assistantMessage = {
          id: uuidv4(),
          role: 'assistant',
          content: `I couldn't reach the AI service. Please ensure the backend API is running and configured.\n\n✅ **API Status Check:**\n- Backend: http://localhost:8000/api/health\n- Groq API: Check your .env file for GROQ_API_KEY\n- NewsData.io API: Check your .env file for NEWSAPI_KEY\n\n**Error:** ${error.message || 'Connection failed'}\n\n**Troubleshooting:**\n1. Ensure backend is running: \`python -m uvicorn app.main:app --reload\`\n2. Check your .env file has valid API keys\n3. Test connection: \`python scripts/test_groq_connection.py\``,
          timestamp: new Date().toISOString(),
          metadata: {}
        };
        setMessages(prev => [...prev, assistantMessage]);
      }
    } finally {
      if (mountedRef.current) setIsLoading(false);
      sendControllerRef.current = null;
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const sendQuickQuery = (query) => {
    setInputMessage(query);
    // Auto-send after a brief delay to show the message in input
    setTimeout(() => {
      sendMessage(query);
    }, 100);
  };

  const formatMessage = (content) => {
    // Simple markdown-like formatting
    return content
      .replace(/\*\*(.*?)\*\*/g, '<strong class="text-blue-600 dark:text-blue-400">$1</strong>')
      .replace(/\*(.*?)\*/g, '<em class="text-slate-600 dark:text-slate-300">$1</em>')
      .replace(/\n/g, '<br/>')
      .replace(/•/g, '<span class="text-blue-500 mr-2">•</span>');
  };

  return (
    <div className="flex flex-col h-full bg-white/30 dark:bg-slate-900/40 backdrop-blur-sm rounded-none lg:rounded-b-2xl">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex animate-fade-in ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div className={`flex gap-3 max-w-[85%] ${message.role === 'user' ? 'flex-row-reverse' : ''}`}>

              {/* Avatar */}
              <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 shadow-md ${message.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-white dark:bg-slate-800 text-blue-600 dark:text-blue-400 border border-slate-100 dark:border-slate-700'
                }`}>
                {message.role === 'user' ? <User className="w-5 h-5" /> : <Bot className="w-5 h-5" />}
              </div>

              {/* Message Bubble */}
              <div className={`flex flex-col ${message.role === 'user' ? 'items-end' : 'items-start'}`}>
                <div className={`p-4 rounded-2xl shadow-sm ${message.role === 'user'
                    ? 'bg-gradient-to-br from-blue-600 to-blue-700 text-white rounded-tr-none'
                    : 'bg-white dark:bg-slate-800 border border-slate-100 dark:border-slate-700 text-slate-800 dark:text-slate-100 rounded-tl-none'
                  }`}>
                  {/* Content */}
                  <div className="text-sm leading-relaxed" dangerouslySetInnerHTML={{ __html: formatMessage(message.content) }}></div>

                  {/* Metadata / Actions for Assistant */}
                  {message.role === 'assistant' && (
                    <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-700/50 flex flex-col gap-3">

                      {/* Confidence & Actions */}
                      <div className="flex items-center justify-between gap-4">
                        {message.metadata.confidence && (
                          <div className="flex items-center gap-1.5 text-xs text-slate-400 bg-slate-50 dark:bg-slate-900/50 px-2 py-1 rounded-md">
                            <Sparkles className="w-3 h-3 text-amber-400" />
                            <span>{Math.round(message.metadata.confidence * 100)}% Confidence</span>
                          </div>
                        )}
                        <div className="flex items-center gap-2">
                          <button className="p-1 text-slate-400 hover:text-blue-500 transition-colors"><Copy className="w-3.5 h-3.5" /></button>
                          <button className="p-1 text-slate-400 hover:text-emerald-500 transition-colors"><ThumbsUp className="w-3.5 h-3.5" /></button>
                        </div>
                      </div>

                      {/* Suggested Actions */}
                      {message.metadata.suggested_actions && message.metadata.suggested_actions.length > 0 && (
                        <div className="flex flex-wrap gap-2">
                          {message.metadata.suggested_actions.slice(0, 3).map((action, idx) => (
                            <button
                              key={idx}
                              onClick={() => sendQuickQuery(action)}
                              className="text-xs px-3 py-1.5 bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 rounded-lg hover:bg-blue-100 dark:hover:bg-blue-900/40 transition-colors border border-blue-100 dark:border-blue-900/30"
                            >
                              {action}
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
                <span className="text-[10px] text-slate-400 mt-1 px-1">{new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
              </div>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start animate-fade-in">
            <div className="flex gap-3 max-w-[85%]">
              <div className="w-8 h-8 rounded-full bg-white dark:bg-slate-800 text-blue-600 dark:text-blue-400 border border-slate-100 dark:border-slate-700 flex items-center justify-center shadow-md">
                <Bot className="w-5 h-5" />
              </div>
              <div className="bg-white dark:bg-slate-800 border border-slate-100 dark:border-slate-700 rounded-2xl rounded-tl-none p-4 shadow-sm flex items-center gap-3">
                <Loader className="w-4 h-4 text-blue-600 animate-spin" />
                <span className="text-sm text-slate-500 dark:text-slate-400 font-medium">Analyzing regulatory data...</span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 bg-white/60 dark:bg-slate-900/60 backdrop-blur-md border-t border-slate-200 dark:border-slate-800 rounded-b-2xl">
        <div className="relative flex items-end gap-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-2 shadow-sm focus-within:ring-2 focus-within:ring-blue-500/20 focus-within:border-blue-500 transition-all">
          <textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask about compliance risks, sanctions, or wallet activity..."
            className="flex-1 max-h-32 min-h-[44px] w-full bg-transparent border-none focus:ring-0 text-sm text-slate-900 dark:text-slate-100 placeholder-slate-400 resize-none py-2.5 px-3"
            rows="1"
          />
          <button
            onClick={() => sendMessage()}
            disabled={!inputMessage.trim() || isLoading}
            className={`p-2.5 rounded-lg mb-0.5 transition-all duration-200 ${!inputMessage.trim() || isLoading
                ? 'bg-slate-100 dark:bg-slate-700 text-slate-400 cursor-not-allowed'
                : 'bg-gradient-to-r from-blue-600 to-cyan-600 text-white shadow-md hover:shadow-lg hover:scale-105 active:scale-95'
              }`}
          >
            {isLoading ? <Loader className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
          </button>
        </div>
        <div className="mt-2 text-center">
          <p className="text-[10px] text-slate-400">
            ReguChain AI can make mistakes. Verify important information.
          </p>
        </div>
      </div>
    </div>
  );
}
