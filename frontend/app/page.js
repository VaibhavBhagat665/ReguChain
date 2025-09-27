'use client';

import { useState } from 'react';
import { Shield, Zap, BarChart3, Brain, FileText, Search, Eye, Bot } from 'lucide-react';
import WalletConnect from '../components/WalletConnect';
import AIAgentChat from '../components/AIAgentChat';

export default function Home() {
  const [connectedAddress, setConnectedAddress] = useState('');
  const [selectedExample, setSelectedExample] = useState(null);
  const [showChat, setShowChat] = useState(false);

  const exampleQuestions = [
    { id: 1, category: 'Risk Assessment', priority: 'high', icon: Shield, description: 'Get a comprehensive risk analysis of your connected wallet', question: 'Analyze my wallet for compliance risks' },
    { id: 2, category: 'Regulatory Updates', priority: 'medium', icon: FileText, description: 'Stay updated with the latest regulatory changes and sanctions', question: 'What are the latest OFAC sanctions?' },
    { id: 3, category: 'Address Screening', priority: 'high', icon: Search, description: 'Screen addresses against global sanctions and watchlists', question: 'Check if this address is on any watchlists' },
    { id: 4, category: 'DeFi Compliance', priority: 'medium', icon: Brain, description: 'Understand regulatory requirements for decentralized finance', question: 'What compliance requirements apply to DeFi protocols?' },
    { id: 5, category: 'Real-time Monitoring', priority: 'medium', icon: Eye, description: 'Set up continuous monitoring for your wallet activities', question: 'Monitor my wallet for suspicious activity' }
  ];

  const handleWalletConnect = (address) => {
    setConnectedAddress(address);
    setShowChat(true);
  };

  const handleExampleClick = (example) => {
    setSelectedExample(example);
    setShowChat(true);
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
                <p className="text-lg text-gray-600 dark:text-gray-400 mt-1">AI-powered compliance guidance, recommendations, and blockchain insights</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-right">
                <p className="text-sm text-gray-500 dark:text-gray-400">Welcome back, Compliance Expert!</p>
                <p className="text-xs text-gray-400 dark:text-gray-500">2 interests tracked</p>
              </div>
              <button className="px-4 py-2 text-sm bg-gray-100 dark:bg-gray-800 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors">Sign Out</button>
            </div>
          </div>
        </div>
      </header>

      {/* Overview - AI Insights & Quick Actions */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-8">
        <div className="flex items-center gap-2 mb-6">
          <Zap className="w-6 h-6 text-blue-600" />
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">AI Insights & Quick Actions</h2>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Wallet Connection Card */}
          <div className="lg:col-span-1">
            <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-sm rounded-2xl shadow-xl border border-gray-200/50 dark:border-gray-700/50 p-6 h-full">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-gradient-to-br from-green-500 to-emerald-600 rounded-lg">
                  <BarChart3 className="w-5 h-5 text-white" />
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
                  <div key={example.id} onClick={() => handleExampleClick(example)} className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-sm rounded-2xl shadow-xl border border-gray-200/50 dark:border-gray-700/50 p-6 cursor-pointer hover:shadow-2xl hover:scale-105 transition-all duration-300 group">
                    <div className="flex items-start justify-between mb-4">
                      <div className="p-3 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl group-hover:scale-110 transition-transform duration-300">
                        <IconComponent className="w-6 h-6 text-white" />
                      </div>
                      <span className="px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">{example.priority}</span>
                    </div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">{example.category}</h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">{example.description}</p>
                    <div className="flex items-center justify-between">
                      <button className="px-4 py-2 bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 rounded-lg text-sm font-medium hover:bg-blue-100 dark:hover:bg-blue-900/40 transition-colors">Ask AI</button>
                      <div className="text-xs text-gray-400">Click to explore</div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* AI Chat Interface */}
        {(showChat || connectedAddress) && (
          <div className="mt-8">
            <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-sm rounded-2xl shadow-xl border border-gray-200/50 dark:border-gray-700/50 p-6">
              <div className="flex items-center gap-3 mb-6">
                <div className="p-2 bg-gradient-to-br from-purple-500 to-pink-600 rounded-lg">
                  <Bot className="w-5 h-5 text-white" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white">AI Compliance Assistant</h3>
                {selectedExample && <span className="px-3 py-1 bg-blue-100 dark:bg-blue-900/20 text-blue-800 dark:text-blue-300 rounded-full text-sm">{selectedExample.category}</span>}
              </div>
              <AIAgentChat walletAddress={connectedAddress} initialQuestion={selectedExample?.question} />
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
