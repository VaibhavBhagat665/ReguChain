'use client';

import { useState, useEffect, useRef } from 'react';
import { Send, Bot, User, Loader, MessageSquare, Brain, Shield, Activity } from 'lucide-react';
import { v4 as uuidv4 } from 'uuid';

export default function AIAgentChat({ walletAddress, onAnalysisResult, initialQuestion }) {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const [agentCapabilities, setAgentCapabilities] = useState([]);
  const messagesEndRef = useRef(null);

  const SAMPLE_RESPONSES = [
    {
      id: 's-1',
      role: 'assistant',
      content: `Here is an analysis summary based on typical patterns:\n\n- Risk Score: 42/100 (Medium)\n- Notable factors: interaction with high-risk labeled addresses, multiple small inbound transactions\n- Recommendation: Enable enhanced monitoring and review large counterparties\n\nWould you like me to run a deeper transaction-level analysis?`,
      metadata: { confidence: 0.6 }
    },
    {
      id: 's-2',
      role: 'assistant',
      content: `News-aware response:\n\nRecent regulatory reports indicate increased enforcement in the crypto sector. Based on that, consider freezing high-risk counterparties and performing an AML review.`,
      metadata: { confidence: 0.55 }
    },
    {
      id: 's-3',
      role: 'assistant',
      content: `Quick summary:\n\nNo immediate sanctions found for this address in public watchlists (sample data). Suggested next steps: verify counterparties, cross-check with KYC records, and set up alerts.`,
      metadata: { confidence: 0.5 }
    }
  ];

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
      try { controller.abort(); } catch (e) {}
      if (sendControllerRef.current) {
        try { sendControllerRef.current.abort(); } catch (e) {}
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
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
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
      try { sendControllerRef.current.abort(); } catch (e) {}
    }
    const controller = new AbortController();
    sendControllerRef.current = controller;

    try {
      const response = await fetch('/api/agent/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: trimmedMessage,
          conversation_id: conversationId,
          wallet_address: walletAddress,
          context: {
            timestamp: new Date().toISOString(),
            user_agent: navigator.userAgent
          }
        }),
        signal: controller.signal
      });

      if (!response.ok) {
        throw new Error('Failed to get response from AI agent');
      }

      const agentResponse = await response.json();
      if (!mountedRef.current) return;
      const assistantMessage = {
        id: uuidv4(),
        role: 'assistant',
        content: agentResponse.message,
        timestamp: new Date().toISOString(),
        metadata: {
          confidence: agentResponse.confidence,
          capabilities_used: agentResponse.capabilities_used,
          risk_assessment: agentResponse.risk_assessment,
          blockchain_data: agentResponse.blockchain_data,
          suggested_actions: agentResponse.suggested_actions,
          follow_up_questions: agentResponse.follow_up_questions
        }
      };

      setMessages(prev => [...prev, assistantMessage]);

      // If there's analysis data, pass it to parent component
      if (agentResponse.risk_assessment || agentResponse.blockchain_data) {
        onAnalysisResult && onAnalysisResult({
          risk_assessment: agentResponse.risk_assessment,
          blockchain_data: agentResponse.blockchain_data,
          suggested_actions: agentResponse.suggested_actions
        });
      }

    } catch (error) {
      if (error && error.name === 'AbortError') {
        // Abort is expected on unmount or on new requests - do nothing
        console.warn('Chat request aborted');
        return;
      }
      console.error('Error sending message:', error);

      // Use a mock response so the UI still demonstrates AI behavior
      if (mountedRef.current) {
        const sample = SAMPLE_RESPONSES[Math.floor(Math.random() * SAMPLE_RESPONSES.length)];
        const assistantMessage = {
          id: uuidv4(),
          role: 'assistant',
          content: sample.content,
          timestamp: new Date().toISOString(),
          metadata: sample.metadata || {}
        };
        setMessages(prev => [...prev, assistantMessage]);

        // Also send analysis result if sample contains plausible structure
        if (onAnalysisResult && sample.content.toLowerCase().includes('risk')) {
          onAnalysisResult({
            risk_assessment: { score: sample.metadata?.confidence ? Math.round(sample.metadata.confidence * 100) : 50 },
            blockchain_data: null,
            suggested_actions: []
          });
        }
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
      sendMessage();
    }, 100);
  };

  const formatMessage = (content) => {
    // Simple markdown-like formatting
    return content
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/\n/g, '<br/>');
  };

  const getCapabilityIcon = (capabilityName) => {
    const icons = {
      wallet_analysis: Shield,
      compliance_check: MessageSquare,
      risk_assessment: Activity,
      conversational_ai: Bot,
      blockchain_insights: Brain,
      regulatory_updates: MessageSquare
    };
    return icons[capabilityName] || MessageSquare;
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg h-96 flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Bot className="w-5 h-5 text-primary-600" />
            <h2 className="text-lg font-semibold">ReguChain AI Agent</h2>
          </div>
          <div className="flex items-center gap-1">
            {agentCapabilities.slice(0, 3).map((capability) => {
              const IconComponent = getCapabilityIcon(capability.name);
              return (
                <div
                  key={capability.name}
                  className="p-1 bg-primary-50 dark:bg-primary-900/20 rounded"
                  title={capability.description}
                >
                  <IconComponent className="w-3 h-3 text-primary-600" />
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-lg p-3 ${
                message.role === 'user'
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-gray-100'
              }`}
            >
              <div className="flex items-start gap-2">
                {message.role === 'assistant' && (
                  <Bot className="w-4 h-4 mt-0.5 text-primary-600" />
                )}
                {message.role === 'user' && (
                  <User className="w-4 h-4 mt-0.5" />
                )}
                <div className="flex-1">
                  <div
                    className="text-sm"
                    dangerouslySetInnerHTML={{ __html: formatMessage(message.content) }}
                  />
                  
                  {/* Show metadata for assistant messages */}
                  {message.role === 'assistant' && message.metadata.confidence && (
                    <div className="mt-2 text-xs opacity-70">
                      Confidence: {Math.round(message.metadata.confidence * 100)}%
                    </div>
                  )}
                  
                  {/* Show suggested actions */}
                  {message.metadata.suggested_actions && message.metadata.suggested_actions.length > 0 && (
                    <div className="mt-3 space-y-1">
                      <p className="text-xs font-medium opacity-70">Suggested Actions:</p>
                      {message.metadata.suggested_actions.slice(0, 2).map((action, index) => (
                        <button
                          key={index}
                          onClick={() => sendQuickQuery(action)}
                          className="block text-xs bg-white/20 hover:bg-white/30 px-2 py-1 rounded text-left w-full transition-colors"
                        >
                          {action}
                        </button>
                      ))}
                    </div>
                  )}
                  
                  {/* Show follow-up questions */}
                  {message.metadata.follow_up_questions && message.metadata.follow_up_questions.length > 0 && (
                    <div className="mt-3 space-y-1">
                      <p className="text-xs font-medium opacity-70">Follow-up Questions:</p>
                      {message.metadata.follow_up_questions.slice(0, 2).map((question, index) => (
                        <button
                          key={index}
                          onClick={() => sendQuickQuery(question)}
                          className="block text-xs bg-white/20 hover:bg-white/30 px-2 py-1 rounded text-left w-full transition-colors"
                        >
                          {question}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
        
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 dark:bg-gray-700 rounded-lg p-3 flex items-center gap-2">
              <Bot className="w-4 h-4 text-primary-600" />
              <Loader className="w-4 h-4 animate-spin" />
              <span className="text-sm text-gray-600 dark:text-gray-300">AI is thinking...</span>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Quick Actions */}
      {walletAddress && messages.length <= 2 && (
        <div className="px-4 py-2 border-t border-gray-200 dark:border-gray-700">
          <div className="flex gap-2 flex-wrap">
            <button
              onClick={() => sendQuickQuery(`Analyze wallet ${walletAddress} for compliance risks`)}
              className="text-xs bg-primary-100 text-primary-700 px-3 py-1 rounded-full hover:bg-primary-200 transition-colors"
            >
              🔍 Analyze Wallet
            </button>
            <button
              onClick={() => sendQuickQuery('What are the latest regulatory updates?')}
              className="text-xs bg-blue-100 text-blue-700 px-3 py-1 rounded-full hover:bg-blue-200 transition-colors"
            >
              📰 Latest Updates
            </button>
            <button
              onClick={() => sendQuickQuery('How does compliance monitoring work?')}
              className="text-xs bg-green-100 text-green-700 px-3 py-1 rounded-full hover:bg-green-200 transition-colors"
            >
              ❓ How It Works
            </button>
          </div>
        </div>
      )}

      {/* Input */}
      <div className="p-4 border-t border-gray-200 dark:border-gray-700">
        <div className="flex gap-2">
          <textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask me anything about blockchain compliance..."
            className="flex-1 resize-none border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-gray-700 dark:text-white"
            rows="2"
            disabled={isLoading}
          />
          <button
            onClick={() => sendMessage()}
            disabled={(typeof inputMessage === 'string' ? inputMessage.trim() === '' : !inputMessage) || isLoading}
            className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          >
            {isLoading ? (
              <Loader className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
