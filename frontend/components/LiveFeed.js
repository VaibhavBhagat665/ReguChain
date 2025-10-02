'use client';

import { useState, useEffect } from 'react';
import { Activity, Clock, ExternalLink, AlertTriangle, TrendingUp, Shield, Database } from 'lucide-react';
import { getStatus } from '../lib/api';

export default function LiveFeed() {
  const [updates, setUpdates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({});
  const [systemStatus, setSystemStatus] = useState('inactive');

  useEffect(() => {
    const loadUpdates = async () => {
      try {
        const data = await getStatus();
        setUpdates(data.last_updates || []);
        setStats(data.index_stats || {});
        setSystemStatus(data.status || 'inactive');
        setLoading(false);
      } catch (error) {
        console.error('Error loading updates:', error);
        setUpdates([]);
        setLoading(false);
      }
    };

    loadUpdates();
    // Refresh every 15 seconds for more real-time feel
    const interval = setInterval(loadUpdates, 15000);
    return () => clearInterval(interval);
  }, []);

  const getRiskColor = (level) => {
    switch (level?.toLowerCase()) {
      case 'critical': return 'text-red-600 bg-red-50 border-red-200';
      case 'high': return 'text-orange-600 bg-orange-50 border-orange-200';
      case 'medium': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      default: return 'text-green-600 bg-green-50 border-green-200';
    }
  };

  const getRiskIcon = (level) => {
    switch (level?.toLowerCase()) {
      case 'critical': return <AlertTriangle className="w-4 h-4" />;
      case 'high': return <TrendingUp className="w-4 h-4" />;
      default: return <Shield className="w-4 h-4" />;
    }
  };

  const getSourceColor = (source) => {
    if (source?.includes('OFAC')) return 'bg-red-100 text-red-800';
    if (source?.includes('NEWS')) return 'bg-blue-100 text-blue-800';
    return 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold flex items-center gap-2">
          <Activity className={`w-5 h-5 ${systemStatus === 'active' ? 'text-green-600' : 'text-gray-400'}`} />
          Live Data Feed
          <span className={`ml-2 px-2 py-1 text-xs rounded-full ${systemStatus === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'}`}>
            {systemStatus === 'active' ? 'ACTIVE' : 'INACTIVE'}
          </span>
        </h2>
        <div className="flex items-center gap-4 text-sm text-gray-500">
          <span className="flex items-center gap-1">
            <Database className="w-4 h-4" />
            {stats.documents || 0} docs
          </span>
          <span>
            {stats.alerts_generated || 0} alerts
          </span>
        </div>
      </div>

      {loading ? (
        <div className="text-sm text-gray-500 flex items-center gap-2">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
          Loading live updates...
        </div>
      ) : updates.length > 0 ? (
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {updates.map((update, index) => (
            <div key={update.id || index} className="p-3 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-100 dark:border-gray-800 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className={`text-xs px-2 py-1 rounded-full font-medium ${getSourceColor(update.source)}`}>
                      {update.source}
                    </span>
                    {update.type && (
                      <span className="text-xs px-2 py-1 rounded-full bg-purple-100 text-purple-800">
                        {update.type.replace('_', ' ').toUpperCase()}
                      </span>
                    )}
                    {update.risk_level && (
                      <span className={`text-xs px-2 py-1 rounded-full border flex items-center gap-1 ${getRiskColor(update.risk_level)}`}>
                        {getRiskIcon(update.risk_level)}
                        {update.risk_level.toUpperCase()}
                      </span>
                    )}
                  </div>

                  <div className="text-sm font-medium text-gray-900 dark:text-white mb-1 line-clamp-2">
                    {update.title || update.text || 'Document Update'}
                  </div>

                  <div className="text-xs text-gray-500 flex items-center gap-3">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {new Date(update.timestamp).toLocaleString()}
                    </span>
                    {update.id && (
                      <span className="text-gray-400">
                        ID: {update.id.substring(0, 8)}...
                      </span>
                    )}
                  </div>
                </div>

                {update.link && (
                  <div className="ml-4 flex-shrink-0">
                    <a
                      href={update.link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-blue-600 hover:text-blue-800 flex items-center gap-1 px-2 py-1 rounded hover:bg-blue-50 transition-colors"
                    >
                      View <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-sm text-gray-500 text-center py-8">
          <div className="mb-2">No recent updates available.</div>
          <div className="text-xs">
            {systemStatus === 'active' 
              ? 'Data ingestion is running. New documents will appear here in real-time.'
              : 'System is inactive. Check your API keys and restart the backend.'
            }
          </div>
        </div>
      )}
      
      <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
        <div className="text-xs text-blue-800 dark:text-blue-300">
          <strong>Live Sources:</strong> OFAC sanctions, NewsData.io regulatory news, SEC/CFTC/FINRA RSS feeds
        </div>
        <div className="text-xs text-blue-600 dark:text-blue-400 mt-1">
          Updates every 5 minutes • Click links to view original sources
        </div>
      </div>
    </div>
  );
}
