'use client';

import { useState, useEffect } from 'react';
import { Shield, Bot, AlertCircle, CheckCircle, Brain, Activity, TrendingUp, Users, FileText, Zap, MessageCircle, BarChart3, Eye, Search, Wallet } from 'lucide-react';
import AIAgentChat from '../components/AIAgentChat';
import WalletConnect from '../components/WalletConnect';
import RiskGauge from '../components/RiskGauge';
import LiveFeed from '../components/LiveFeed';
import EvidenceExplorer from '../components/EvidenceExplorer';
import { queryAPI } from '../lib/api';

export default function Home() {
  const [loading, setLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [notification, setNotification] = useState(null);
  const [connectedAddress, setConnectedAddress] = useState('');
  const [agentCapabilities, setAgentCapabilities] = useState([]);
  const [systemStatus, setSystemStatus] = useState(null);
  const [selectedExample, setSelectedExample] = useState(null);
  const [showChat, setShowChat] = useState(false);

  // Example questions for the AI agent
  const exampleQuestions = [
    {
      id: 1,
      question: "Analyze my wallet for compliance risks",
      category: "Risk Assessment",
      priority: "high",
      icon: Shield,
      description: "Get a comprehensive risk analysis of your connected wallet"
    },
    {
      id: 2,
      question: "What are the latest OFAC sanctions?",
      category: "Regulatory Updates",
      priority: "medium",
      icon: FileText,
      description: "Stay updated with the latest regulatory changes and sanctions"
    },
    {
      id: 3,
      question: "Check if this address is on any watchlists",
      category: "Address Screening",
      priority: "high",
      icon: Search,
      description: "Screen addresses against global sanctions and watchlists"
    },
    {
      id: 4,
      question: "What compliance requirements apply to DeFi protocols?",
      category: "DeFi Compliance",
      priority: "medium",
      icon: Brain,
      description: "Understand regulatory requirements for decentralized finance"
    },
    {
      id: 5,
      question: "Monitor my wallet for suspicious activity",
      category: "Real-time Monitoring",
      priority: "medium",
      icon: Eye,
      description: "Set up continuous monitoring for your wallet activities"
    }
  ];

  useEffect(() => {
    // Initialize system status and capabilities
    console.log('ReguChain API URL:', process.env.NEXT_PUBLIC_API_URL);
    fetchSystemStatus();
    fetchAgentCapabilities();
  }, []);

  const handleExampleClick = (example) => {
    setSelectedExample(example);
    setShowChat(true);
    // You can also auto-send the question to the chat
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high': return 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-300';
      case 'medium': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-300';
      case 'low': return 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-300';
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-300';
    }
  };

  const fetchSystemStatus = async () => {
    try {
      const response = await fetch('/api/status');
      if (response.ok) {
        const status = await response.json();
        setSystemStatus(status);
      }
    } catch (error) {
      console.error('Error fetching system status:', error);
    }
  };

  const fetchAgentCapabilities = async () => {
    try {
      const response = await fetch('/api/agent/capabilities');
      if (response.ok) {
        const capabilities = await response.json();
        setAgentCapabilities(capabilities);
      }
    } catch (error) {
      console.error('Error fetching agent capabilities:', error);
    }
  };

  const handleAnalysisResult = (result) => {
    setAnalysisResult(result);
    setNotification({
      type: 'success',
      message: 'AI analysis completed successfully',
    });
  };

  const handleWalletConnect = (address, options = {}) => {
    setConnectedAddress(address);
    if (address) {
      setNotification({
        type: 'success',
        message: `Wallet connected successfully. The AI agent is ready to help analyze ${address.substring(0, 6)}...${address.substring(address.length - 4)}`,
      });
    }
  };


  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 dark:from-gray-900 dark:via-slate-900 dark:to-indigo-950">
      {/* Header */}
      <header className="bg-white/80 dark:bg-gray-900/80 backdrop-blur-lg shadow-sm border-b border-gray-200/50 dark:border-gray-700/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl shadow-lg">
                <Shield className="w-8 h-8 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold bg-gradient-to-r from-gray-900 to-gray-600 dark:from-white dark:to-gray-300 bg-clip-text text-transparent">
                  Your Compliance Dashboard ✨
                </h1>
                <p className="text-lg text-gray-600 dark:text-gray-400 mt-1">
                  AI-powered compliance guidance, recommendations, and blockchain insights
                </p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-right">
                <p className="text-sm text-gray-500 dark:text-gray-400">Welcome back, Compliance Expert!</p>
                <p className="text-xs text-gray-400 dark:text-gray-500">2 interests tracked</p>
              </div>
              <button className="px-4 py-2 text-sm bg-gray-100 dark:bg-gray-800 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors">
                Sign Out
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Notification */}
      {notification && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-4">
          <div
            className={`p-4 rounded-lg flex items-start gap-3 ${
              notification.type === 'success'
                ? 'bg-green-50 dark:bg-green-900/20 text-green-800 dark:text-green-300'
                : 'bg-red-50 dark:bg-red-900/20 text-red-800 dark:text-red-300'
            }`}
          >
            {notification.type === 'success' ? (
              <CheckCircle className="w-5 h-5 mt-0.5" />
            ) : (
              <AlertCircle className="w-5 h-5 mt-0.5" />
            )}
            <p className="text-sm">{notification.message}</p>
          </div>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6">
        <div className="flex items-center gap-8 border-b border-gray-200 dark:border-gray-700">
          <button className="flex items-center gap-2 px-4 py-3 border-b-2 border-blue-500 text-blue-600 dark:text-blue-400 font-medium">
            <BarChart3 className="w-4 h-4" />
            Overview
          </button>
          <button className="flex items-center gap-2 px-4 py-3 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white">
            <Brain className="w-4 h-4" />
            AI Insights
          </button>
          <button className="flex items-center gap-2 px-4 py-3 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white">
            <TrendingUp className="w-4 h-4" />
            Roadmap
          </button>
          <button className="flex items-center gap-2 px-4 py-3 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white">
            <MessageCircle className="w-4 h-4" />
            AI Mentor
          </button>
          <button className="flex items-center gap-2 px-4 py-3 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white">
            <FileText className="w-4 h-4" />
            Resume
          </button>
        </div>
      </div>

      {/* AI Insights & Quick Actions */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-8">
        <div className="flex items-center gap-2 mb-6">
          <Zap className="w-6 h-6 text-blue-600" />
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">AI Insights & Quick Actions</h2>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Wallet Connection Card */}
          <div className="lg:col-span-1">
            <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-sm rounded-2xl shadow-xl border border-gray-200/50 dark:border-gray-700/50 p-6 h-full">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-gradient-to-br from-green-500 to-emerald-600 rounded-lg">
                  <Wallet className="w-5 h-5 text-white" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Wallet Connection</h3>
              </div>
              <WalletConnect onAddressSelect={handleWalletConnect} />
            </div>
          </div>

          {/* Example Questions Grid */}
          <div className="lg:col-span-3">
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              {exampleQuestions.map((example) => {
                const IconComponent = example.icon;
                return (
                  <div
                    key={example.id}
                    onClick={() => handleExampleClick(example)}
                    className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-sm rounded-2xl shadow-xl border border-gray-200/50 dark:border-gray-700/50 p-6 cursor-pointer hover:shadow-2xl hover:scale-105 transition-all duration-300 group"
                  >
                    <div className="flex items-start justify-between mb-4">
                      <div className="p-3 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl group-hover:scale-110 transition-transform duration-300">
                        <IconComponent className="w-6 h-6 text-white" />
                      </div>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(example.priority)}`}>
                        {example.priority}
                      </span>
                    </div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                      {example.category}
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                      {example.description}
                    </p>
                    <div className="flex items-center justify-between">
                      <button className="px-4 py-2 bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 rounded-lg text-sm font-medium hover:bg-blue-100 dark:hover:bg-blue-900/40 transition-colors">
                        Ask AI
                      </button>
                      <div className="text-xs text-gray-400">
                        Click to explore
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* AI Chat Interface - Show when example is clicked or wallet is connected */}
        {(showChat || connectedAddress) && (
          <div className="mt-8">
            <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-sm rounded-2xl shadow-xl border border-gray-200/50 dark:border-gray-700/50 p-6">
              <div className="flex items-center gap-3 mb-6">
                <div className="p-2 bg-gradient-to-br from-purple-500 to-pink-600 rounded-lg">
                  <Bot className="w-5 h-5 text-white" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white">AI Compliance Assistant</h3>
                {selectedExample && (
                  <span className="px-3 py-1 bg-blue-100 dark:bg-blue-900/20 text-blue-800 dark:text-blue-300 rounded-full text-sm">
                    {selectedExample.category}
                  </span>
                )}
              </div>
              <AIAgentChat 
                walletAddress={connectedAddress}
                onAnalysisResult={handleAnalysisResult}
                initialQuestion={selectedExample?.question}
              />
            </div>
          </div>
        )}

        {/* Analysis Results with Enhanced Visuals */}
        {analysisResult && (
          <div className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
            {analysisResult.risk_assessment && (
              <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-sm rounded-2xl shadow-xl border border-gray-200/50 dark:border-gray-700/50 p-6">
                <RiskGauge
                  score={analysisResult.risk_assessment.score}
                  reasons={analysisResult.risk_assessment.factors || []}
                  recommendations={analysisResult.suggested_actions || []}
                />
              </div>
            )}
            {analysisResult.blockchain_data && (
              <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-sm rounded-2xl shadow-xl border border-gray-200/50 dark:border-gray-700/50 p-6">
                <div className="flex items-center gap-3 mb-6">
                  <div className="p-2 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg">
                    <Brain className="w-5 h-5 text-white" />
                  </div>
                  <h3 className="text-xl font-semibold text-gray-900 dark:text-white">Blockchain Analysis</h3>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center p-4 bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-xl">
                    <p className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                      {analysisResult.blockchain_data.total_transactions || 0}
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">Transactions</p>
                  </div>
                  <div className="text-center p-4 bg-gradient-to-br from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 rounded-xl">
                    <p className="text-3xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
                      {analysisResult.blockchain_data.risk_score || 0}
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">Risk Score</p>
                  </div>
                  <div className="text-center p-4 bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 rounded-xl">
                    <p className="text-3xl font-bold bg-gradient-to-r from-green-600 to-emerald-600 bg-clip-text text-transparent">
                      {analysisResult.blockchain_data.unique_counterparties || 0}
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">Counterparties</p>
                  </div>
                  <div className="text-center p-4 bg-gradient-to-br from-orange-50 to-red-50 dark:from-orange-900/20 dark:to-red-900/20 rounded-xl">
                    <p className="text-3xl font-bold bg-gradient-to-r from-orange-600 to-red-600 bg-clip-text text-transparent">
                      {analysisResult.blockchain_data.transaction_volume?.toFixed(2) || '0.00'}
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">Volume (ETH)</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Footer */}
      <footer className="mt-12 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              © 2024 ReguChain AI Agent. Advanced blockchain compliance monitoring.
            </p>
            <div className="flex items-center gap-4 text-xs text-gray-500">
              {systemStatus && (
                <>
                  <span>Documents: {systemStatus.total_documents}</span>
                  <span>Active Conversations: {systemStatus.active_conversations}</span>
                  <span>Capabilities: {agentCapabilities.length}</span>
                </>
              )}
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
