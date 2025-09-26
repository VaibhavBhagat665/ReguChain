'use client';

import { useState, useEffect } from 'react';
import { Shield, Zap, AlertCircle, CheckCircle } from 'lucide-react';
import QueryBox from '../components/QueryBox';
import WalletConnect from '../components/WalletConnect';
import RiskGauge from '../components/RiskGauge';
import LiveFeed from '../components/LiveFeed';
import EvidenceExplorer from '../components/EvidenceExplorer';
import { queryAPI, simulateIngestion, checkHealth } from '../lib/api';

export default function Home() {
  const [loading, setLoading] = useState(false);
  const [simulating, setSimulating] = useState(false);
  const [queryResult, setQueryResult] = useState(null);
  const [healthStatus, setHealthStatus] = useState(null);
  const [notification, setNotification] = useState(null);
  const [connectedAddress, setConnectedAddress] = useState('');

  useEffect(() => {
    // Check backend health on mount
    checkHealth().then(setHealthStatus);
  }, []);

  const handleQuery = async (question, target) => {
    setLoading(true);
    setNotification(null);
    try {
      const result = await queryAPI(question, target);
      setQueryResult(result);
      setNotification({
        type: 'success',
        message: 'Analysis completed successfully',
      });
    } catch (error) {
      setNotification({
        type: 'error',
        message: 'Failed to analyze query. Please try again.',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleWalletConnect = (address) => {
    setConnectedAddress(address);
    if (address) {
      // Automatically check the connected wallet
      handleQuery(`Check compliance status for wallet ${address}`, address);
    }
  };

  const handleSimulate = async () => {
    setSimulating(true);
    setNotification(null);
    try {
      const target = connectedAddress || queryResult?.target || `0xDEMO${Date.now().toString().slice(-8)}`;
      const result = await simulateIngestion(target);
      setNotification({
        type: 'success',
        message: `Simulated ingestion for ${result.target}. Re-run your query to see updated results!`,
      });
      // Clear previous results to encourage re-query
      setQueryResult(null);
    } catch (error) {
      setNotification({
        type: 'error',
        message: 'Failed to simulate ingestion. Please try again.',
      });
    } finally {
      setSimulating(false);
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
                  ReguChain Watch
                </h1>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Real-time Regulatory Compliance with AI-powered RAG
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {healthStatus && (
                <div className="flex items-center gap-2 px-3 py-1 bg-green-50 dark:bg-green-900/20 rounded-full">
                  <CheckCircle className="w-4 h-4 text-green-600 dark:text-green-400" />
                  <span className="text-sm text-green-700 dark:text-green-300">
                    System Online
                  </span>
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
            
            {/* Query Box */}
            <QueryBox onQuery={handleQuery} loading={loading} />

            {/* Simulate Button */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
              <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                <Zap className="w-5 h-5 text-yellow-500" />
                Demo: Simulate New Sanction
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                Inject a simulated sanction entry to see how the system updates in real-time.
                This will add new OFAC and news entries for the target wallet.
              </p>
              <button
                onClick={handleSimulate}
                disabled={simulating}
                className="w-full bg-yellow-500 hover:bg-yellow-600 disabled:bg-gray-400 text-white py-2 px-4 rounded-lg transition-colors duration-200 flex items-center justify-center gap-2"
              >
                {simulating ? (
                  <>
                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Simulating...
                  </>
                ) : (
                  <>
                    <Zap className="w-5 h-5" />
                    Simulate Ingestion
                  </>
                )}
              </button>
            </div>

            {/* Results */}
            {queryResult && (
              <>
                <RiskGauge
                  score={queryResult.risk_score}
                  reasons={queryResult.risk_reasons}
                  recommendations={queryResult.recommendations}
                />
                <EvidenceExplorer
                  evidence={queryResult.evidence}
                  onchainMatches={queryResult.onchain_matches}
                  answer={queryResult.answer}
                />
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
          <p className="text-center text-sm text-gray-600 dark:text-gray-400">
            © 2024 ReguChain Watch. AI-powered regulatory compliance monitoring.
          </p>
        </div>
      </footer>
    </div>
  );
}
