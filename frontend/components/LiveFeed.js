'use client';

import { useEffect, useState } from 'react';
import { Activity, RefreshCw, Database } from 'lucide-react';
import { getStatus } from '../lib/api';

export default function LiveFeed() {
  const [updates, setUpdates] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);

  const fetchStatus = async () => {
    try {
      const data = await getStatus();
      setUpdates(data.last_updates || []);
      setStats(data.index_stats || {});
    } catch (error) {
      console.error('Error fetching status:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 3000); // Poll every 3 seconds
    return () => clearInterval(interval);
  }, []);

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold flex items-center gap-2">
          <Activity className="w-5 h-5 text-primary-600" />
          Live Feed
          <span className="relative flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
          </span>
        </h2>
        <button
          onClick={fetchStatus}
          className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          title="Refresh"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      <div className="mb-4 flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
        <div className="flex items-center gap-1">
          <Database className="w-4 h-4" />
          <span>{stats.documents || 0} documents</span>
        </div>
        <div>
          <span>{stats.total_vectors || 0} vectors</span>
        </div>
        <div>
          <span className="capitalize">{stats.backend || 'unknown'} backend</span>
        </div>
      </div>

      <div className="space-y-2 max-h-96 overflow-y-auto">
        {loading && updates.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            Loading updates...
          </div>
        ) : updates.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No recent updates
          </div>
        ) : (
          updates.map((update, index) => (
            <div
              key={update.id || index}
              className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg animate-slide-in"
            >
              <div className="flex items-start justify-between mb-1">
                <span className="text-xs font-semibold text-primary-600 dark:text-primary-400">
                  {update.source}
                </span>
                <span className="text-xs text-gray-500 dark:text-gray-400">
                  {formatTimestamp(update.timestamp)}
                </span>
              </div>
              <p className="text-sm text-gray-700 dark:text-gray-300 line-clamp-2">
                {update.text}
              </p>
              {update.link && (
                <a
                  href={update.link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-primary-500 hover:text-primary-600 mt-1 inline-block"
                >
                  View source →
                </a>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
