'use client';

import { useState } from 'react';
import { Shield, Zap, BarChart3, Brain, FileText, Search, Eye, Bot, Sparkles } from 'lucide-react';
import WalletConnect from '../components/WalletConnect';
import AIAgentChat from '../components/AIAgentChat';
import NewsFeed from '../components/NewsFeed';
import WalletRealtimePanel from '../components/WalletRealtimePanel';
import LiveFeed from '../components/LiveFeed';
import AlertsPanel from '../components/AlertsPanel';

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
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-purple-50/20 dark:from-gray-950 dark:via-slate-900 dark:to-indigo-950/50">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-white/60 dark:bg-gray-900/60 backdrop-blur-xl shadow-sm border-b border-gray-200/30 dark:border-gray-700/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="relative p-3 bg-gradient-to-br from-blue-600 via-purple-600 to-pink-600 rounded-2xl shadow-lg">
                <Shield className="w-8 h-8 text-white" />
                <div className="absolute inset-0 bg-gradient-to-br from-blue-600 via-purple-600 to-pink-600 rounded-2xl blur-lg opacity-50 -z-10"></div>
              </div>
              <div>
                <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">
                  ReguChain
                </h1>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-0.5 flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-purple-500" />
                  AI-powered compliance guidance & blockchain insights
                </p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              {/* Removed welcome message and sign out button */}
            </div>
          </div>
        </div>
      </header>

      {/* Overview - AI Insights & Quick Actions */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-8 pb-12">
        <div className="flex items-center gap-3 mb-8">
          <div className="p-2 bg-gradient-to-br from-amber-400 to-orange-500 rounded-lg shadow-md">
            <Zap className="w-6 h-6 text-white" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">AI Insights & Quick Actions</h2>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Wallet Connection Card */}
          <div className="lg:col-span-1">
            <div className="bg-white/50 dark:bg-gray-800/50 backdrop-blur-xl rounded-3xl shadow-lg border border-gray-200/30 dark:border-gray-700/30 p-6 h-full hover:shadow-xl transition-all duration-500">
              <div className="flex items-center gap-3 mb-5">
                <div className="p-2.5 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-xl shadow-md">
                  <BarChart3 className="w-5 h-5 text-white" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Wallet Connection</h3>
              </div>
              <WalletConnect onAddressSelect={handleWalletConnect} />
            </div>
          </div>

          {/* Example Questions Grid */}
          <div className="lg:col-span-3">
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
              {exampleQuestions.map((example) => {
                const IconComponent = example.icon;
                const priorityColors = {
                  high: 'bg-rose-100 dark:bg-rose-900/30 text-rose-700 dark:text-rose-400',
                  medium: 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400'
                };
                return (
                  <div key={example.id} onClick={() => handleExampleClick(example)} className="relative bg-white/50 dark:bg-gray-800/50 backdrop-blur-xl rounded-3xl shadow-lg border border-gray-200/30 dark:border-gray-700/30 p-6 cursor-pointer hover:shadow-2xl hover:scale-[1.03] transition-all duration-500 group overflow-hidden">
                    <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 via-purple-500/5 to-pink-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500 rounded-3xl"></div>
                    <div className="relative z-10">
                      <div className="flex items-start justify-between mb-4">
                        <div className="relative p-3 bg-gradient-to-br from-blue-600 via-purple-600 to-pink-600 rounded-2xl shadow-md group-hover:scale-110 transition-transform duration-500">
                          <IconComponent className="w-6 h-6 text-white" />
                          <div className="absolute inset-0 bg-gradient-to-br from-blue-600 via-purple-600 to-pink-600 rounded-2xl blur-md opacity-0 group-hover:opacity-40 transition-opacity duration-500 -z-10"></div>
                        </div>
                        <span className={`px-3 py-1 rounded-full text-xs font-semibold ${priorityColors[example.priority]}`}>
                          {example.priority}
                        </span>
                      </div>
                      <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2 group-hover:text-transparent group-hover:bg-gradient-to-r group-hover:from-blue-600 group-hover:via-purple-600 group-hover:to-pink-600 group-hover:bg-clip-text transition-all duration-300">
                        {example.category}
                      </h3>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mb-5 leading-relaxed">{example.description}</p>
                      <div className="flex items-center justify-between">
                        <button className="px-5 py-2.5 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl text-sm font-semibold hover:shadow-lg hover:scale-105 transition-all duration-300">
                          Ask AI
                        </button>
                        <div className="text-xs text-gray-400 group-hover:text-purple-500 transition-colors duration-300">Explore →</div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* AI Chat Interface */}
        {(showChat || connectedAddress) && (
          <div className="mt-10 grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <div className="bg-white/50 dark:bg-gray-800/50 backdrop-blur-xl rounded-3xl shadow-lg border border-gray-200/30 dark:border-gray-700/30 p-6">
                <div className="flex items-center gap-3 mb-6">
                  <div className="relative p-2.5 bg-gradient-to-br from-purple-600 to-pink-600 rounded-xl shadow-md">
                    <Bot className="w-5 h-5 text-white" />
                    <div className="absolute inset-0 bg-gradient-to-br from-purple-600 to-pink-600 rounded-xl blur-md opacity-50 -z-10"></div>
                  </div>
                  <h3 className="text-xl font-bold text-gray-900 dark:text-white">AI Compliance Assistant</h3>
                  {selectedExample && (
                    <span className="px-4 py-1.5 bg-gradient-to-r from-blue-100 to-purple-100 dark:from-blue-900/20 dark:to-purple-900/20 text-blue-700 dark:text-blue-300 rounded-full text-sm font-medium border border-blue-200/30 dark:border-blue-700/30">
                      {selectedExample.category}
                    </span>
                  )}
                </div>
                <AIAgentChat walletAddress={connectedAddress} initialQuestion={selectedExample?.question} />
              </div>
            </div>

            <div className="lg:col-span-1">
              <div className="space-y-6">
                <LiveFeed />
                <AlertsPanel />
                <WalletRealtimePanel walletAddress={connectedAddress} />
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
