'use client';

import { useState, useEffect } from 'react';
import { Shield, Zap, Bot, Sparkles, Menu, ChevronRight, Activity, Wallet, AlertTriangle, CheckCircle, TrendingUp, RefreshCw } from 'lucide-react';
import { API_ENDPOINTS } from '../lib/api';
import WalletConnect from '../components/WalletConnect';
import AIAgentChat from '../components/AIAgentChat';
import LiveFeed from '../components/LiveFeed';
import AlertsPanel from '../components/AlertsPanel';

export default function Home() {
  // Wallet state managed via callback from WalletConnect component
  const [connectedAddress, setConnectedAddress] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [selectedExample, setSelectedExample] = useState(null);
  const [activeView, setActiveView] = useState('dashboard');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [alerts, setAlerts] = useState([]);
  const [complianceStatus, setComplianceStatus] = useState(null);
  const [isLoadingAlerts, setIsLoadingAlerts] = useState(false);

  // Handle wallet address changes from WalletConnect component
  const handleAddressSelect = (address) => {
    setConnectedAddress(address);
    setIsConnected(!!address);
  };

  // Fetch real alerts from backend
  const fetchAlerts = async () => {
    setIsLoadingAlerts(true);
    try {
      const res = await fetch(`${API_ENDPOINTS.alerts}?limit=5`);
      if (res.ok) {
        const data = await res.json();
        setAlerts(data);
      }
    } catch (err) {
      console.error('Failed to fetch alerts:', err);
    } finally {
      setIsLoadingAlerts(false);
    }
  };

  // Fetch compliance status for connected wallet
  const fetchComplianceStatus = async () => {
    if (!connectedAddress) return;
    try {
      const res = await fetch(API_ENDPOINTS.walletAnalyze, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ address: connectedAddress })
      });
      if (res.ok) {
        const data = await res.json();
        setComplianceStatus(data);
      }
    } catch (err) {
      console.error('Failed to fetch compliance status:', err);
    }
  };

  useEffect(() => {
    fetchAlerts();
    const interval = setInterval(fetchAlerts, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (connectedAddress) {
      fetchComplianceStatus();
    } else {
      setComplianceStatus(null);
    }
  }, [connectedAddress]);

  const exampleQuestions = [
    { id: 1, category: 'Risk Assessment', priority: 'high', icon: Shield, description: 'Get a comprehensive risk analysis of your connected wallet', question: 'Analyze my wallet for compliance risks' },
    { id: 2, category: 'OFAC Screening', priority: 'high', icon: AlertTriangle, description: 'Screen addresses against OFAC sanctions list', question: 'Check if Aerocaribbean is on the OFAC list' },
    { id: 3, category: 'Regulatory Updates', priority: 'medium', icon: TrendingUp, description: 'Stay updated with the latest regulatory changes', question: 'What are the latest cryptocurrency regulations?' },
  ];

  const handleExampleClick = (example) => {
    setSelectedExample(example);
    setActiveView('assistant');
  };

  const handleNavClick = (view) => {
    setActiveView(view);
    if (typeof window !== 'undefined' && window.innerWidth < 1024) setSidebarOpen(false);
  };

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50 dark:bg-slate-950 font-sans text-slate-900 dark:text-slate-100">

      {/* Sidebar */}
      <aside className={`fixed lg:static inset-y-0 left-0 z-50 w-72 transform transition-transform duration-300 ease-in-out ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'} lg:translate-x-0 bg-white/70 dark:bg-slate-900/70 backdrop-blur-xl border-r border-slate-200/50 dark:border-slate-800/50 flex flex-col`}>
        {/* Brand */}
        <div className="p-6 flex items-center gap-3">
          <div className="relative p-2 bg-gradient-to-br from-blue-600 to-cyan-500 rounded-xl shadow-lg shadow-blue-500/20">
            <Shield className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-display font-bold tracking-tight bg-gradient-to-r from-blue-600 to-cyan-500 bg-clip-text text-transparent">
              ReguChain
            </h1>
            <p className="text-[10px] uppercase tracking-wider text-slate-500 font-semibold">Compliance AI</p>
          </div>
        </div>

        {/* Navigation - Simplified */}
        <nav className="flex-1 px-4 py-6 space-y-1 overflow-y-auto custom-scrollbar">
          <NavItem icon={Zap} label="Dashboard" active={activeView === 'dashboard'} onClick={() => handleNavClick('dashboard')} />
          <NavItem icon={Bot} label="AI Assistant" active={activeView === 'assistant'} onClick={() => handleNavClick('assistant')} />
          <NavItem icon={Activity} label="Live Monitoring" active={activeView === 'monitoring'} onClick={() => handleNavClick('monitoring')} />
        </nav>

        {/* Wallet Status */}
        <div className="p-4 border-t border-slate-200/50 dark:border-slate-800/50 bg-slate-50/50 dark:bg-slate-900/50">
          <div className="glass-card p-3 flex items-center gap-3">
            <div className={`p-2 rounded-full ${isConnected ? 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400' : 'bg-slate-100 dark:bg-slate-800 text-slate-400'}`}>
              <Wallet className="w-4 h-4" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-slate-500 truncate">Wallet</p>
              <p className="text-sm font-semibold truncate text-slate-900 dark:text-white">
                {connectedAddress ? `${connectedAddress.substring(0, 6)}...${connectedAddress.substring(38)}` : 'Not Connected'}
              </p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden relative">
        {/* Background */}
        <div className="absolute top-0 left-0 w-full h-full overflow-hidden -z-10 pointer-events-none">
          <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-blue-500/10 rounded-full blur-[100px] animate-float"></div>
          <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-purple-500/10 rounded-full blur-[100px] animate-float" style={{ animationDelay: '2s' }}></div>
        </div>

        {/* Header - No Settings/Notifications */}
        <header className="flex items-center justify-between px-8 py-4 bg-white/40 dark:bg-slate-900/40 backdrop-blur-md border-b border-slate-200/30 dark:border-slate-800/30 sticky top-0 z-30">
          <div className="flex items-center gap-4">
            <button onClick={() => setSidebarOpen(!sidebarOpen)} className="lg:hidden p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors">
              <Menu className="w-6 h-6" />
            </button>
            <h2 className="text-xl font-display font-semibold text-slate-800 dark:text-slate-100">
              {activeView === 'dashboard' ? 'Overview' : activeView === 'assistant' ? 'AI Assistant' : 'Live Monitoring'}
            </h2>
          </div>
        </header>

        {/* Main Area */}
        <main className="flex-1 overflow-y-auto p-4 lg:p-8 custom-scrollbar">

          {activeView === 'dashboard' && (
            <div className="max-w-6xl mx-auto space-y-8 animate-fade-in">
              {/* Hero */}
              <div className="text-center space-y-4 mb-12 py-10">
                <div className="inline-flex items-center px-3 py-1 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-300 text-xs font-medium mb-4 border border-blue-200 dark:border-blue-800">
                  <Sparkles className="w-3 h-3 mr-2" />
                  Powered by Llama 3 & Real-time OFAC Data
                </div>
                <h2 className="text-4xl lg:text-5xl font-display font-bold text-slate-900 dark:text-white tracking-tight">
                  Next-Gen <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-cyan-500">Compliance</span> Intelligence
                </h2>
                <p className="text-lg text-slate-600 dark:text-slate-400 max-w-2xl mx-auto leading-relaxed">
                  Connect your wallet to monitor transactions and get real-time compliance alerts.
                </p>
              </div>

              {/* Wallet Connect */}
              <div className="max-w-md mx-auto mb-16 relative group">
                <div className="absolute -inset-1 bg-gradient-to-r from-blue-600 to-cyan-500 rounded-2xl blur opacity-25 group-hover:opacity-50 transition duration-1000"></div>
                <div className="relative">
                  <WalletConnect onAddressSelect={handleAddressSelect} />
                </div>
              </div>

              {/* Quick Actions */}
              <div>
                <div className="flex items-center gap-2 mb-6 text-slate-500 dark:text-slate-400 text-sm font-semibold uppercase tracking-wider">
                  <Zap className="w-4 h-4" /> Quick Actions
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {exampleQuestions.map((example) => {
                    const Icon = example.icon;
                    return (
                      <button
                        key={example.id}
                        onClick={() => handleExampleClick(example)}
                        className="group text-left p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm hover:shadow-xl hover:border-blue-500/30 transition-all duration-300 hover:-translate-y-1"
                      >
                        <div className={`w-12 h-12 rounded-xl mb-4 flex items-center justify-center ${example.priority === 'high' ? 'bg-rose-50 dark:bg-rose-900/20 text-rose-600' : 'bg-amber-50 dark:bg-amber-900/20 text-amber-600'}`}>
                          <Icon className="w-6 h-6" />
                        </div>
                        <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-2">{example.category}</h3>
                        <p className="text-sm text-slate-500 dark:text-slate-400">{example.description}</p>
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>
          )}

          {activeView === 'assistant' && (
            <div className="max-w-[1600px] mx-auto grid grid-cols-1 lg:grid-cols-12 gap-6 h-full animate-slide-in">
              <div className="lg:col-span-8 flex flex-col gap-6">
                <div className="glass-card flex-1 min-h-[600px] flex flex-col relative overflow-hidden">
                  <div className="p-4 border-b border-slate-200/50 dark:border-slate-800/50 flex items-center gap-3 bg-white/50 dark:bg-slate-900/50">
                    <div className="p-2 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-lg shadow-md">
                      <Bot className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-slate-900 dark:text-white">AI Compliance Agent</h3>
                      <p className="text-xs text-slate-500 flex items-center gap-1">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span> Online
                      </p>
                    </div>
                  </div>
                  <div className="flex-1 overflow-hidden relative">
                    <AIAgentChat walletAddress={connectedAddress} initialQuestion={selectedExample?.question} />
                  </div>
                </div>
              </div>
              <div className="lg:col-span-4 space-y-6">
                <LiveFeed />
                <AlertsPanel />
              </div>
            </div>
          )}

          {activeView === 'monitoring' && (
            <div className="max-w-4xl mx-auto animate-fade-in">
              {!isConnected ? (
                <div className="text-center py-20">
                  <Wallet className="w-16 h-16 text-slate-300 mx-auto mb-6" />
                  <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">Connect Your Wallet</h2>
                  <p className="text-slate-500 dark:text-slate-400 mb-8">Connect your wallet to access live monitoring features.</p>
                  <div className="max-w-sm mx-auto">
                    <WalletConnect onAddressSelect={handleAddressSelect} />
                  </div>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Compliance Status Card */}
                  <div className="glass-card p-6">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Compliance Status</h3>
                      <button onClick={fetchComplianceStatus} className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors">
                        <RefreshCw className="w-4 h-4 text-slate-500" />
                      </button>
                    </div>
                    {complianceStatus ? (
                      <div className="space-y-4">
                        <div className={`p-4 rounded-xl flex items-center gap-4 ${complianceStatus.risk_score < 30 ? 'bg-green-50 dark:bg-green-900/20' : complianceStatus.risk_score < 70 ? 'bg-yellow-50 dark:bg-yellow-900/20' : 'bg-red-50 dark:bg-red-900/20'}`}>
                          {complianceStatus.risk_score < 30 ? (
                            <CheckCircle className="w-8 h-8 text-green-600" />
                          ) : (
                            <AlertTriangle className="w-8 h-8 text-yellow-600" />
                          )}
                          <div>
                            <p className="font-semibold text-slate-900 dark:text-white">{complianceStatus.compliance_status}</p>
                            <p className="text-sm text-slate-600 dark:text-slate-400">Risk Score: {complianceStatus.risk_score}/100</p>
                          </div>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <div className="p-4 bg-slate-50 dark:bg-slate-800 rounded-xl">
                            <p className="text-sm text-slate-500">Total Transactions</p>
                            <p className="text-2xl font-bold text-slate-900 dark:text-white">{complianceStatus.total_transactions}</p>
                          </div>
                          <div className="p-4 bg-slate-50 dark:bg-slate-800 rounded-xl">
                            <p className="text-sm text-slate-500">Risk Factors</p>
                            <p className="text-2xl font-bold text-slate-900 dark:text-white">{complianceStatus.risk_factors?.length || 0}</p>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="text-center py-8 text-slate-500">Loading compliance data...</div>
                    )}
                  </div>

                  {/* Real-time Alerts */}
                  <div className="glass-card p-6">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Real-time Alerts</h3>
                      <button onClick={fetchAlerts} disabled={isLoadingAlerts} className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors">
                        <RefreshCw className={`w-4 h-4 text-slate-500 ${isLoadingAlerts ? 'animate-spin' : ''}`} />
                      </button>
                    </div>
                    {alerts.length > 0 ? (
                      <div className="space-y-3">
                        {alerts.map((alert, idx) => (
                          <div key={idx} className={`p-4 rounded-xl border ${alert.type === 'critical' ? 'bg-red-50 border-red-200 dark:bg-red-900/20 dark:border-red-800' : 'bg-yellow-50 border-yellow-200 dark:bg-yellow-900/20 dark:border-yellow-800'}`}>
                            <div className="flex items-start gap-3">
                              <AlertTriangle className={`w-5 h-5 mt-0.5 ${alert.type === 'critical' ? 'text-red-600' : 'text-yellow-600'}`} />
                              <div>
                                <p className="font-medium text-slate-900 dark:text-white">{alert.description || alert.title || 'Alert'}</p>
                                <p className="text-xs text-slate-500 mt-1">{alert.timestamp}</p>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-center py-8 text-slate-500">
                        {isLoadingAlerts ? 'Loading...' : 'No alerts at this time ✅'}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

function NavItem({ icon: Icon, label, active = false, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 ${active
        ? 'bg-blue-500/10 text-blue-600 dark:text-blue-400'
        : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
        }`}>
      <Icon className={`w-5 h-5 ${active ? 'text-blue-500' : 'text-slate-400'}`} />
      {label}
    </button>
  );
}
