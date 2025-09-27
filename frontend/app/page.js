'use client';

import { useState, useEffect } from 'react';
import { Shield, Bot, AlertCircle, CheckCircle, Brain, Activity } from 'lucide-react';
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

  useEffect(() => {
    // Initialize system status and capabilities
    console.log('ReguChain API URL:', process.env.NEXT_PUBLIC_API_URL);
    fetchSystemStatus();
    fetchAgentCapabilities();
  }, []);

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
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Shield className="w-8 h-8 text-primary-600" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                  ReguChain AI Agent
                </h1>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Advanced AI Agent for Blockchain Regulatory Compliance
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {systemStatus && (
                <div className="flex items-center gap-2 px-3 py-1 bg-green-50 dark:bg-green-900/20 rounded-full">
                  <Bot className="w-4 h-4 text-green-600 dark:text-green-400" />
                  <span className="text-sm text-green-700 dark:text-green-300">
                    AI Agent Online
                  </span>
                </div>
              )}
              {agentCapabilities.length > 0 && (
                <div className="flex items-center gap-1">
                  {agentCapabilities.slice(0, 3).map((capability, index) => (
                    <div
                      key={capability.name}
                      className="p-1 bg-primary-50 dark:bg-primary-900/20 rounded"
                      title={capability.description}
                    >
                      {capability.name === 'wallet_analysis' && <Shield className="w-3 h-3 text-primary-600" />}
                      {capability.name === 'conversational_ai' && <Bot className="w-3 h-3 text-primary-600" />}
                      {capability.name === 'blockchain_insights' && <Brain className="w-3 h-3 text-primary-600" />}
                      {capability.name === 'risk_assessment' && <Activity className="w-3 h-3 text-primary-600" />}
                    </div>
                  ))}
                </div>
              )}
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

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column */}
          <div className="lg:col-span-2 space-y-6">
            {/* Wallet Connection */}
            <WalletConnect onAddressSelect={handleWalletConnect} />
            
            {/* AI Agent Chat Interface */}
            <AIAgentChat 
              walletAddress={connectedAddress}
              onAnalysisResult={handleAnalysisResult}
            />

            {/* Analysis Results */}
            {analysisResult && (
              <>
                {analysisResult.risk_assessment && (
                  <RiskGauge
                    score={analysisResult.risk_assessment.score}
                    reasons={analysisResult.risk_assessment.factors || []}
                    recommendations={analysisResult.suggested_actions || []}
                  />
                )}
                {analysisResult.blockchain_data && (
                  <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
                    <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                      <Brain className="w-5 h-5 text-primary-600" />
                      Blockchain Analysis
                    </h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="text-center">
                        <p className="text-2xl font-bold text-primary-600">
                          {analysisResult.blockchain_data.total_transactions || 0}
                        </p>
                        <p className="text-sm text-gray-600 dark:text-gray-400">Transactions</p>
                      </div>
                      <div className="text-center">
                        <p className="text-2xl font-bold text-primary-600">
                          {analysisResult.blockchain_data.risk_score || 0}
                        </p>
                        <p className="text-sm text-gray-600 dark:text-gray-400">Risk Score</p>
                      </div>
                      <div className="text-center">
                        <p className="text-2xl font-bold text-primary-600">
                          {analysisResult.blockchain_data.unique_counterparties || 0}
                        </p>
                        <p className="text-sm text-gray-600 dark:text-gray-400">Counterparties</p>
                      </div>
                      <div className="text-center">
                        <p className="text-2xl font-bold text-primary-600">
                          {analysisResult.blockchain_data.transaction_volume?.toFixed(2) || '0.00'}
                        </p>
                        <p className="text-sm text-gray-600 dark:text-gray-400">Volume (ETH)</p>
                      </div>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>

          {/* Right Column - Live Feed */}
          <div className="lg:col-span-1">
            <LiveFeed />
          </div>
        </div>
      </main>

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
