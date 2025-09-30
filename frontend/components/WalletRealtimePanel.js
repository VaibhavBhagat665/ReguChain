'use client';

import { useEffect, useState, useMemo } from 'react';
import { AlertTriangle, Activity, Clock, Link, Play, Square, Wallet } from 'lucide-react';
import {
  startRealtime,
  stopRealtime,
  connectWalletRealtime,
  getWalletRealtimeStatus,
  getStreamRecords,
} from '../lib/api';

export default function WalletRealtimePanel({ walletAddress }) {
  const [status, setStatus] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [txs, setTxs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const isConnected = useMemo(() => !!walletAddress, [walletAddress]);

  const fetchData = async (addr) => {
    if (!addr) return;
    try {
      setError('');
      const [stRes, alRes, txRes] = await Promise.all([
        getWalletRealtimeStatus(addr).catch(() => null),
        getStreamRecords('wallet_alerts', { limit: 10, walletAddress: addr }).catch(() => ({ records: [] })),
        getStreamRecords('wallet_transactions_processed', { limit: 10, walletAddress: addr }).catch(() => ({ records: [] })),
      ]);
      if (stRes) setStatus(stRes);
      setAlerts(alRes?.records || []);
      setTxs(txRes?.records || []);
    } catch (e) {
      console.error('Realtime wallet fetch error:', e);
      setError('Failed to load realtime wallet data');
    }
  };

  useEffect(() => {
    let intervalId;
    (async () => {
      if (!isConnected) return;
      try {
        setLoading(true);
        // Start realtime (idempotent) and connect wallet realtime
        await startRealtime().catch(() => {});
        await connectWalletRealtime(walletAddress).catch(() => {});
        await fetchData(walletAddress);
      } finally {
        setLoading(false);
      }
      // Poll every 30s
      intervalId = setInterval(() => fetchData(walletAddress), 30000);
    })();
    return () => intervalId && clearInterval(intervalId);
  }, [walletAddress, isConnected]);

  const onStart = async () => {
    try {
      setLoading(true);
      await startRealtime();
      if (walletAddress) await connectWalletRealtime(walletAddress);
      await fetchData(walletAddress);
    } catch (e) {
      setError('Failed to start realtime');
    } finally {
      setLoading(false);
    }
  };

  const onStop = async () => {
    try {
      setLoading(true);
      await stopRealtime();
      await fetchData(walletAddress);
    } catch (e) {
      setError('Failed to stop realtime');
    } finally {
      setLoading(false);
    }
  };

  if (!isConnected) {
    return (
      <div className="bg-white/50 dark:bg-gray-800/50 backdrop-blur-xl rounded-3xl shadow-lg border border-gray-200/30 dark:border-gray-700/30 p-6">
        <div className="flex items-center gap-2 mb-3">
          <Wallet className="w-5 h-5 text-purple-600" />
          <h3 className="text-lg font-semibold">Wallet Realtime</h3>
        </div>
        <p className="text-sm text-gray-600 dark:text-gray-400">Connect a wallet to see live transactions and compliance alerts.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="bg-white/50 dark:bg-gray-800/50 backdrop-blur-xl rounded-3xl shadow-lg border border-gray-200/30 dark:border-gray-700/30 p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Activity className="w-5 h-5 text-emerald-600" />
            <h3 className="text-lg font-semibold">Wallet Realtime</h3>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={onStart} disabled={loading} className="px-2 py-1.5 text-xs rounded-lg bg-emerald-600 text-white hover:bg-emerald-700 disabled:opacity-50 flex items-center gap-1">
              <Play className="w-3 h-3" /> Start
            </button>
            <button onClick={onStop} disabled={loading} className="px-2 py-1.5 text-xs rounded-lg bg-red-600 text-white hover:bg-red-700 disabled:opacity-50 flex items-center gap-1">
              <Square className="w-3 h-3" /> Stop
            </button>
          </div>
        </div>
        {error && (
          <div className="p-2 rounded bg-red-50 dark:bg-red-900/20 text-xs text-red-700 dark:text-red-300 mb-3">{error}</div>
        )}
        <div className="grid grid-cols-3 gap-3">
          <div className="p-3 rounded-xl bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200/50 dark:border-emerald-800/50">
            <div className="text-xs text-emerald-700 dark:text-emerald-300">Alerts</div>
            <div className="text-xl font-bold">{alerts.length}</div>
          </div>
          <div className="p-3 rounded-xl bg-blue-50 dark:bg-blue-900/20 border border-blue-200/50 dark:border-blue-800/50">
            <div className="text-xs text-blue-700 dark:text-blue-300">Recent TX</div>
            <div className="text-xl font-bold">{txs.length}</div>
          </div>
          <div className="p-3 rounded-xl bg-purple-50 dark:bg-purple-900/20 border border-purple-200/50 dark:border-purple-800/50">
            <div className="text-xs text-purple-700 dark:text-purple-300">Status</div>
            <div className="text-xs">{status?.status || 'pending'}</div>
          </div>
        </div>
      </div>

      {/* Alerts list */}
      <div className="bg-white/50 dark:bg-gray-800/50 backdrop-blur-xl rounded-3xl shadow-lg border border-gray-200/30 dark:border-gray-700/30 p-6">
        <div className="flex items-center gap-2 mb-4">
          <AlertTriangle className="w-5 h-5 text-amber-600" />
          <h4 className="font-semibold">Recent Alerts</h4>
        </div>
        {alerts.length === 0 ? (
          <p className="text-sm text-gray-500">No alerts yet.</p>
        ) : (
          <div className="space-y-3">
            {alerts.map((a, idx) => (
              <div key={idx} className="p-3 rounded-xl border border-amber-200/40 dark:border-amber-800/40 bg-amber-50/40 dark:bg-amber-900/10">
                <div className="flex items-center justify-between">
                  <div className="text-sm font-medium">{a.hash ? `${a.hash.slice(0, 10)}...` : 'Transaction'}</div>
                  <span className="text-xs px-2 py-0.5 rounded-full bg-amber-600 text-white">{a.tx_alert || 'alert'}</span>
                </div>
                <div className="mt-1 text-xs text-gray-600 dark:text-gray-400 flex items-center gap-2">
                  <Clock className="w-3 h-3" /> {a.timestamp}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Recent transactions */}
      <div className="bg-white/50 dark:bg-gray-800/50 backdrop-blur-xl rounded-3xl shadow-lg border border-gray-200/30 dark:border-gray-700/30 p-6">
        <div className="flex items-center gap-2 mb-4">
          <Link className="w-5 h-5 text-blue-600" />
          <h4 className="font-semibold">Recent Transactions</h4>
        </div>
        {txs.length === 0 ? (
          <p className="text-sm text-gray-500">No transactions yet.</p>
        ) : (
          <div className="space-y-3">
            {txs.map((t, idx) => (
              <div key={idx} className="p-3 rounded-xl border border-blue-200/40 dark:border-blue-800/40 bg-blue-50/40 dark:bg-blue-900/10">
                <div className="flex items-center justify-between">
                  <div className="text-sm font-medium">{t.hash ? `${t.hash.slice(0, 10)}...` : 'Tx'}</div>
                  <span className="text-xs px-2 py-0.5 rounded-full bg-blue-600 text-white">{Number(t.value || 0).toFixed(4)} ETH</span>
                </div>
                <div className="mt-1 text-xs text-gray-600 dark:text-gray-400 flex items-center gap-2">
                  <Clock className="w-3 h-3" /> {t.timestamp}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
