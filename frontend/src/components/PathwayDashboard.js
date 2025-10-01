/**
 * Pathway-Powered ReguChain Dashboard
 * Real-time alerts and RAG queries with Pathway pipelines
 */
import React, { useState, useEffect, useCallback } from 'react';
import { AlertTriangle, Shield, Activity, Search, Zap, Database, TrendingUp, Bell } from 'lucide-react';

const PathwayDashboard = () => {
  const [query, setQuery] = useState('');
  const [walletAddress, setWalletAddress] = useState('');
  const [response, setResponse] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [alertsLoading, setAlertsLoading] = useState(false);

  // Fetch system status
  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch('/api/status');
      const data = await res.json();
      setStatus(data);
    } catch (error) {
      console.error('Error fetching status:', error);
    }
  }, []);

  // Fetch alerts
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

  // Submit query
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

      // If wallet address provided, add to monitoring
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

  // Simulate alert
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

      // Refresh alerts after simulation
      setTimeout(fetchAlerts, 2000);
    } catch (error) {
      console.error('Error simulating alert:', error);
    }
  };

  // Auto-refresh data
  useEffect(() => {
    fetchStatus();
    fetchAlerts();

    const interval = setInterval(() => {
      fetchStatus();
      fetchAlerts();
    }, 30000); // Refresh every 30 seconds

    return () => clearInterval(interval);
  }, [fetchStatus, fetchAlerts]);

  const getRiskColor = (verdict) => {
    switch (verdict?.toLowerCase()) {
      case 'high': return 'text-red-600 bg-red-50 border-red-200';
      case 'medium': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'safe': return 'text-green-600 bg-green-50 border-green-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'critical': return 'text-red-600 bg-red-100';
      case 'high': return 'text-orange-600 bg-orange-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      default: return 'text-blue-600 bg-blue-100';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-3">
              <Zap className="h-8 w-8 text-blue-600" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">ReguChain Pathway</h1>
                <p className="text-sm text-gray-500">Real-time Regulatory Intelligence</p>
              </div>
            </div>
            
            {/* Status Indicator */}
            <div className="flex items-center space-x-4">
              <div className={`flex items-center space-x-2 px-3 py-1 rounded-full text-sm ${
                status?.pipelines_running ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
              }`}>
                <Activity className="h-4 w-4" />
                <span>{status?.pipelines_running ? 'Pipelines Active' : 'Pipelines Inactive'}</span>
              </div>
              
              <div className="text-sm text-gray-600">
                <div>Docs: {status?.total_documents || 0}</div>
                <div>Alerts: {status?.total_alerts || 0}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Query Panel */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <div className="flex items-center space-x-2 mb-4">
                <Search className="h-5 w-5 text-blue-600" />
                <h2 className="text-lg font-semibold text-gray-900">RAG Query</h2>
              </div>
              
              <form onSubmit={handleQuery} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Question
                  </label>
                  <textarea
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Ask about regulatory compliance, sanctions, or analyze a wallet..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    rows={3}
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Wallet Address (Optional)
                  </label>
                  <input
                    type="text"
                    value={walletAddress}
                    onChange={(e) => setWalletAddress(e.target.value)}
                    placeholder="0x..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                
                <div className="flex space-x-3">
                  <button
                    type="submit"
                    disabled={loading}
                    className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center space-x-2"
                  >
                    {loading ? (
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    ) : (
                      <>
                        <Search className="h-4 w-4" />
                        <span>Query</span>
                      </>
                    )}
                  </button>
                  
                  <button
                    type="button"
                    onClick={simulateAlert}
                    className="bg-orange-600 text-white px-4 py-2 rounded-md hover:bg-orange-700 flex items-center space-x-2"
                  >
                    <AlertTriangle className="h-4 w-4" />
                    <span>Simulate Alert</span>
                  </button>
                </div>
              </form>
              
              {/* Response */}
              {response && (
                <div className="mt-6 border-t pt-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-gray-900">Analysis Result</h3>
                    <div className={`px-3 py-1 rounded-full text-sm font-medium border ${getRiskColor(response.risk_verdict)}`}>
                      {response.risk_verdict} ({response.risk_score}/100)
                    </div>
                  </div>
                  
                  <div className="bg-gray-50 rounded-lg p-4 mb-4">
                    <p className="text-gray-800 whitespace-pre-wrap">{response.answer}</p>
                  </div>
                  
                  {/* Evidence */}
                  {response.evidence && response.evidence.length > 0 && (
                    <div className="mb-4">
                      <h4 className="font-medium text-gray-900 mb-2">Evidence Sources</h4>
                      <div className="space-y-2">
                        {response.evidence.map((evidence, index) => (
                          <div key={index} className="bg-blue-50 border border-blue-200 rounded p-3">
                            <div className="flex justify-between items-start mb-1">
                              <span className="font-medium text-blue-900">{evidence.source}</span>
                              <span className={`px-2 py-1 rounded text-xs ${getRiskColor(evidence.risk_level)}`}>
                                {evidence.risk_level}
                              </span>
                            </div>
                            <p className="text-sm text-blue-800">{evidence.content}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {/* Onchain Matches */}
                  {response.onchain_matches && response.onchain_matches.length > 0 && (
                    <div>
                      <h4 className="font-medium text-gray-900 mb-2">Onchain Matches</h4>
                      <div className="space-y-2">
                        {response.onchain_matches.map((match, index) => (
                          <div key={index} className="bg-red-50 border border-red-200 rounded p-3">
                            <div className="flex justify-between items-start">
                              <div>
                                <p className="font-medium text-red-900">{match.wallet_address}</p>
                                <p className="text-sm text-red-700">Value: {match.value} ETH</p>
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
                  
                  <div className="mt-4 text-xs text-gray-500">
                    Model: {response.model_used} • Processing: {response.processing_time_ms}ms
                  </div>
                </div>
              )}
            </div>
          </div>
          
          {/* Alerts Panel */}
          <div>
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-2">
                  <Bell className="h-5 w-5 text-red-600" />
                  <h2 className="text-lg font-semibold text-gray-900">Live Alerts</h2>
                </div>
                <button
                  onClick={fetchAlerts}
                  disabled={alertsLoading}
                  className="text-blue-600 hover:text-blue-800 text-sm"
                >
                  {alertsLoading ? 'Loading...' : 'Refresh'}
                </button>
              </div>
              
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {alerts.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <Shield className="h-12 w-12 mx-auto mb-2 text-gray-300" />
                    <p>No alerts detected</p>
                    <p className="text-sm">System monitoring active</p>
                  </div>
                ) : (
                  alerts.map((alert) => (
                    <div key={alert.id} className="border rounded-lg p-3 hover:bg-gray-50">
                      <div className="flex items-start justify-between mb-2">
                        <div className={`px-2 py-1 rounded text-xs font-medium ${getSeverityColor(alert.severity)}`}>
                          {alert.severity}
                        </div>
                        <div className="text-xs text-gray-500">
                          {new Date(alert.timestamp).toLocaleTimeString()}
                        </div>
                      </div>
                      
                      <h4 className="font-medium text-gray-900 mb-1">{alert.title}</h4>
                      <p className="text-sm text-gray-600 mb-2">{alert.description}</p>
                      
                      {alert.wallet_address && (
                        <div className="text-xs text-blue-600 font-mono bg-blue-50 px-2 py-1 rounded">
                          {alert.wallet_address}
                        </div>
                      )}
                      
                      <div className="flex justify-between items-center mt-2">
                        <span className="text-xs text-gray-500">{alert.type}</span>
                        <span className="text-xs font-medium text-red-600">
                          Risk: {alert.risk_score}/100
                        </span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
            
            {/* System Stats */}
            <div className="mt-6 bg-white rounded-lg shadow-sm border p-6">
              <div className="flex items-center space-x-2 mb-4">
                <Database className="h-5 w-5 text-green-600" />
                <h2 className="text-lg font-semibold text-gray-900">Pipeline Stats</h2>
              </div>
              
              {status && (
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Status</span>
                    <span className={`text-sm font-medium ${
                      status.pipelines_running ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {status.status}
                    </span>
                  </div>
                  
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Documents</span>
                    <span className="text-sm font-medium text-gray-900">
                      {status.total_documents.toLocaleString()}
                    </span>
                  </div>
                  
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Alerts</span>
                    <span className="text-sm font-medium text-gray-900">
                      {status.total_alerts.toLocaleString()}
                    </span>
                  </div>
                  
                  {status.last_update && (
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Last Update</span>
                      <span className="text-sm text-gray-500">
                        {new Date(status.last_update).toLocaleTimeString()}
                      </span>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PathwayDashboard;
