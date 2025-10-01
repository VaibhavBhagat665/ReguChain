'use client';

import { useState, useEffect, useCallback } from 'react';
import { Shield, Zap, BarChart3, Brain, FileText, Search, Eye, Bot, Sparkles, AlertTriangle, Activity, Database, TrendingUp, Bell } from 'lucide-react';

// Wallet Connect Component
const WalletConnect = ({ onAddressSelect }) => {
  const [address, setAddress] = useState('');

  const handleConnect = () => {
    if (address.trim()) {
      onAddressSelect(address);
    }
  };

  return (
    <div className="space-y-3">
      <input
        type="text"
        value={address}
        onChange={(e) => setAddress(e.target.value)}
        placeholder="Enter wallet address..."
        className="w-full px-4 py-2.5 bg-white/70 dark:bg-gray-700/50 border border-gray-300/50 dark:border-gray-600/50 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500 text-sm"
      />
      <button
        onClick={handleConnect}
        className="w-full px-4 py-2.5 bg-gradient-to-r from-emerald-500 to-teal-600 text-white rounded-xl text-sm font-semibold hover:shadow-lg hover:scale-105 transition-all duration-300"
      >
        Connect Wallet
      </button>
    </div>
  );
};

// AI Agent Chat Component
const AIAgentChat = ({ walletAddress, initialQuestion }) => {
  const [query, setQuery] = useState(initialQuestion || '');
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (initialQuestion) {
      setQuery(initialQuestion);
    }
  }, [initialQuestion]);

  const handleQuery = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    try {
      const res = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: query,
          wallet_address: walletAddress || null
        })
      });

      const data = await res.json();
      setResponse(data);

      if (walletAddress) {
        await fetch('/api/wallet/monitor', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ wallet_address: walletAddress })
        });
      }
    } catch (error) {
      console.error('Error submitting query:', error);
      setResponse({
        answer: 'Error processing query. Please try again.',
        risk_score: 0,
        risk_verdict: 'Error',
        evidence: [],
        onchain_matches: []
      });
    } finally {
      setLoading(false);
    }
  };

  const getRiskColor = (verdict) => {
    switch (verdict?.toLowerCase()) {
      case 'high': return 'text-red-600 bg-red-50 border-red-200 dark:text-red-400 dark:bg-red-900/20 dark:border-red-700/30';
      case 'medium': return 'text-yellow-600 bg-yellow-50 border-yellow-200 dark:text-yellow-400 dark:bg-yellow-900/20 dark:border-yellow-700/30';
      case 'safe': return 'text-green-600 bg-green-50 border-green-200 dark:text-green-400 dark:bg-green-900/20 dark:border-green-700/30';
      default: return 'text-gray-600 bg-gray-50 border-gray-200 dark:text-gray-400 dark:bg-gray-800/20 dark:border-gray-700/30';
    }
  };

  return (
    <div className="space-y-4">
      <form onSubmit={handleQuery} className="space-y-4">
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask about regulatory compliance, sanctions, or analyze a wallet..."
          className="w-full px-4 py-3 bg-white/70 dark:bg-gray-700/50 border border-gray-300/50 dark:border-gray-600/50 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500 text-sm resize-none"
          rows={4}
        />
        <button
          type="submit"
          disabled={loading}
          className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white px-6 py-3 rounded-xl hover:shadow-lg disabled:opacity-50 flex items-center justify-center space-x-2 font-semibold transition-all duration-300"
        >
          {loading ? (
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
          ) : (
            <>
              <Search className="h-5 w-5" />
              <span>Analyze</span>
            </>
          )}
        </button>
      </form>

      {response && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="text-lg font-semibold text-gray-900 dark:text-white">Analysis Result</h4>
            <div className={`px-4 py-1.5 rounded-full text-sm font-medium border ${getRiskColor(response.risk_verdict)}`}>
              {response.risk_verdict} ({response.risk_score}/100)
            </div>
          </div>

          <div className="bg-gradient-to-br from-blue-50/50 to-purple-50/50 dark:from-blue-900/10 dark:to-purple-900/10 rounded-xl p-4 border border-blue-200/30 dark:border-blue-700/30">
            <p className="text-gray-800 dark:text-gray-200 whitespace-pre-wrap">{response.answer}</p>
          </div>

          {response.evidence && response.evidence.length > 0 && (
            <div>
              <h5 className="font-medium text-gray-900 dark:text-white mb-3">Evidence Sources</h5>
              <div className="space-y-2">
                {response.evidence.map((evidence, index) => (
                  <div key={index} className="bg-blue-50/50 dark:bg-blue-900/20 border border-blue-200/50 dark:border-blue-700/30 rounded-xl p-3">
                    <div className="flex justify-between items-start mb-1">
                      <span className="font-medium text-blue-900 dark:text-blue-300">{evidence.source}</span>
                      <span className={`px-2 py-1 rounded text-xs ${getRiskColor(evidence.risk_level)}`}>
                        {evidence.risk_level}
                      </span>
                    </div>
                    <p className="text-sm text-blue-800 dark:text-blue-200">{evidence.content}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {response.onchain_matches && response.onchain_matches.length > 0 && (
            <div>
              <h5 className="font-medium text-gray-900 dark:text-white mb-3">Onchain Matches</h5>
              <div className="space-y-2">
                {response.onchain_matches.map((match, index) => (
                  <div key={index} className="bg-red-50/50 dark:bg-red-900/20 border border-red-200/50 dark:border-red-700/30 rounded-xl p-3">
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="font-medium text-red-900 dark:text-red-300 font-mono text-sm">{match.wallet_address}</p>
                        <p className="text-sm text-red-700 dark:text-red-200">Value: {match.value} ETH</p>
                      </div>
                      <span className={`px-2 py-1 rounded text-xs ${getRiskColor(match.risk_level)}`}>
                        {match.risk_level}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="text-xs text-gray-500 dark:text-gray-400 mt-4">
            Model: {response.model_used} • Processing: {response.processing_time_ms}ms
          </div>
        </div>
      )}
    </div>
  );
};

// News Feed Component
const NewsFeed = () => {
  return (
    <div className="bg-white/50 dark:bg-gray-800/50 backdrop-blur-xl rounded-3xl shadow-lg border border-gray-200/30 dark:border-gray-700/30 p-6">
      <div className="flex items-center gap-3 mb-4">
        <div className="p-2 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl shadow-md">
          <FileText className="w-5 h-5 text-white" />
        </div>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Regulatory News</h3>
      </div>
      <p className="text-sm text-gray-600 dark:text-gray-400">Latest updates will appear here</p>
    </div>
  );
};

// Wallet Realtime Panel Component
const WalletRealtimePanel = ({ walletAddress }) => {
  const [alerts, setAlerts] = useState([]);
  const [alertsLoading, setAlertsLoading] = useState(false);

  const fetchAlerts = useCallback(async () => {
    try {
      setAlertsLoading(true);
      const res = await fetch('/api/alerts?limit=10');
      const data = await res.json();
      setAlerts(data);
    } catch (error) {
      console.error('Error fetching alerts:', error);
    } finally {
      setAlertsLoading(false);
    }
  }, []);

  const simulateAlert = async () => {
    try {
      await fetch('/api/ingest/simulate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          doc_type: 'sanction',
          content: `OFAC has sanctioned wallet ${walletAddress || '0x1234567890abcdef'} for money laundering activities. Immediate compliance action required.`
        })
      });
      setTimeout(fetchAlerts, 2000);
    } catch (error) {
      console.error('Error simulating alert:', error);
    }
  };

  useEffect(() => {
    fetchAlerts();
    const interval = setInterval(fetchAlerts, 30000);
    return () => clearInterval(interval);
  }, [fetchAlerts]);

  const getSeverityColor = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'critical': return 'text-red-600 bg-red-100 dark:text-red-400 dark:bg-red-900/30';
      case 'high': return 'text-orange-600 bg-orange-100 dark:text-orange-400 dark:bg-orange-900/30';
      case 'medium': return 'text-yellow-600 bg-yellow-100 dark:text-yellow-400 dark:bg-yellow-900/30';
      default: return 'text-blue-600 bg-blue-100 dark:text-blue-400 dark:bg-blue-900/30';
    }
  };

  return (
    <div className="bg-white/50 dark:bg-gray-800/50 backdrop-blur-xl rounded-3xl shadow-lg border border-gray-200/30 dark:border-gray-700/30 p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-gradient-to-br from-red-500 to-pink-600 rounded-xl shadow-md">
            <Bell className="w-5 h-5 text-white" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Live Alerts</h3>
        </div>
        <button
          onClick={fetchAlerts}
          disabled={alertsLoading}
          className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 text-sm font-medium"
        >
          {alertsLoading ? 'Loading...' : 'Refresh'}
        </button>
      </div>

      {walletAddress && (
        <button
          onClick={simulateAlert}
          className="w-full mb-4 bg-gradient-to-r from-orange-500 to-red-600 text-white px-4 py-2 rounded-xl hover:shadow-lg flex items-center justify-center space-x-2 text-sm font-semibold transition-all duration-300"
        >
          <AlertTriangle className="h-4 w-4" />
          <span>Simulate Alert</span>
        </button>
      )}

      <div className="space-y-3 max-h-96 overflow-y-auto">
        {alerts.length === 0 ? (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            <Shield className="h-12 w-12 mx-auto mb-2 text-gray-300 dark:text-gray-600" />
            <p className="font-medium">No alerts detected</p>
            <p className="text-sm">System monitoring active</p>
          </div>
        ) : (
          alerts.map((alert) => (
            <div key={alert.id} className="border border-gray-200/50 dark:border-gray-700/50 rounded-xl p-3 hover:bg-gray-50/50 dark:hover:bg-gray-700/30 transition-colors">
              <div className="flex items-start justify-between mb-2">
                <div className={`px-2 py-1 rounded text-xs font-medium ${getSeverityColor(alert.severity)}`}>
                  {alert.severity}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  {new Date(alert.timestamp).toLocaleTimeString()}
                </div>
              </div>

              <h4 className="font-medium text-gray-900 dark:text-white mb-1">{alert.title}</h4>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">{alert.description}</p>

              {alert.wallet_address && (
                <div className="text-xs text-blue-600 dark:text-blue-400 font-mono bg-blue-50 dark:bg-blue-900/20 px-2 py-1 rounded">
                  {alert.wallet_address}
                </div>
              )}

              <div className="flex justify-between items-center mt-2">
                <span className="text-xs text-gray-500 dark:text-gray-400">{alert.type}</span>
                <span className="text-xs font-medium text-red-600 dark:text-red-400">
                  Risk: {alert.risk_score}/100
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

// Pipeline Stats Component
const PipelineStats = () => {
  const [status, setStatus] = useState(null);

  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch('/api/status');
      const data = await res.json();
      setStatus(data);
    } catch (error) {
      console.error('Error fetching status:', error);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 30000);
    return () => clearInterval(interval);
  }, [fetchStatus]);

  return (
    <div className="bg-white/50 dark:bg-gray-800/50 backdrop-blur-xl rounded-3xl shadow-lg border border-gray-200/30 dark:border-gray-700/30 p-6">
      <div className="flex items-center gap-3 mb-4">
        <div className="p-2 bg-gradient-to-br from-green-500 to-emerald-600 rounded-xl shadow-md">
          <Database className="w-5 h-5 text-white" />
        </div>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Pipeline Stats</h3>
      </div>

      {status && (
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600 dark:text-gray-400">Status</span>
            <span className={`text-sm font-medium px-3 py-1 rounded-full ${
              status.pipelines_running ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
            }`}>
              {status.status}
            </span>
          </div>

          <div className="flex justify-between">
            <span className="text-sm text-gray-600 dark:text-gray-400">Documents</span>
            <span className="text-sm font-medium text-gray-900 dark:text-white">
              {status.total_documents?.toLocaleString() || 0}
            </span>
          </div>

          <div className="flex justify-between">
            <span className="text-sm text-gray-600 dark:text-gray-400">Alerts</span>
            <span className="text-sm font-medium text-gray-900 dark:text-white">
              {status.total_alerts?.toLocaleString() || 0}
            </span>
          </div>

          {status.last_update && (
            <div className="flex justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-400">Last Update</span>
              <span className="text-sm text-gray-500 dark:text-gray-400">
                {new Date(status.last_update).toLocaleTimeString()}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Main Component
export default function Home() {
  const [connectedAddress, setConnectedAddress] = useState('');
  const [selectedExample, setSelectedExample] = useState(null);
  const [showChat, setShowChat] = useState(false);
  const [status, setStatus] = useState(null);

  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch('/api/status');
      const data = await res.json();
      setStatus(data);
    } catch (error) {
      console.error('Error fetching status:', error);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 30000);
    return () => clearInterval(interval);
  }, [fetchStatus]);

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
              {status && (
                <div className={`flex items-center space-x-2 px-4 py-2 rounded-full text-sm font-medium ${
                  status.pipelines_running ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
                }`}>
                  <Activity className="h-4 w-4" />
                  <span>{status.pipelines_running ? 'Pipelines Active' : 'Pipelines Inactive'}</span>
                </div>
              )}
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
                <WalletRealtimePanel walletAddress={connectedAddress} />
                <PipelineStats />
                <NewsFeed />
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
