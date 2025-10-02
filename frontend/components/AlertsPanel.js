'use client';

import { useState, useEffect } from 'react';
import { AlertTriangle, Clock, ExternalLink, Shield, TrendingUp } from 'lucide-react';
import { getAlerts } from '../lib/api';

export default function AlertsPanel() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadAlerts = async () => {
      try {
        setLoading(true);
        const alertsData = await getAlerts(10);
        setAlerts(Array.isArray(alertsData) ? alertsData : []);
      } catch (error) {
        console.error('Error loading alerts:', error);
        setAlerts([]);
      } finally {
        setLoading(false);
      }
    };

    loadAlerts();
    // Refresh alerts every 30 seconds
    const interval = setInterval(loadAlerts, 30000);
    return () => clearInterval(interval);
  }, []);

  const getSeverityColor = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'critical':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'high':
        return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      default:
        return 'bg-blue-100 text-blue-800 border-blue-200';
    }
  };

  const getSeverityIcon = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'critical':
        return <AlertTriangle className="w-4 h-4 text-red-600" />;
      case 'high':
        return <TrendingUp className="w-4 h-4 text-orange-600" />;
      default:
        return <Shield className="w-4 h-4 text-blue-600" />;
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
      <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
        <AlertTriangle className="w-5 h-5 text-red-600" />
        Compliance Alerts
      </h2>

      {loading ? (
        <div className="text-sm text-gray-500">Loading alerts...</div>
      ) : alerts.length > 0 ? (
        <div className="space-y-3">
          {alerts.map((alert, index) => (
            <div
              key={alert.id || index}
              className={`p-4 rounded-lg border ${getSeverityColor(alert.severity)}`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    {getSeverityIcon(alert.severity)}
                    <span className="text-sm font-medium">
                      {alert.type || 'COMPLIANCE_ALERT'}
                    </span>
                    <span className="text-xs px-2 py-1 rounded-full bg-gray-200 text-gray-700">
                      {alert.severity || 'MEDIUM'}
                    </span>
                  </div>
                  
                  <h3 className="font-semibold text-sm mb-1">
                    {alert.title || 'Compliance Alert'}
                  </h3>
                  
                  <p className="text-sm text-gray-600 dark:text-gray-300 mb-2">
                    {alert.description || alert.detail || 'No description available'}
                  </p>
                  
                  {alert.wallet_address && (
                    <div className="text-xs text-gray-500 mb-2">
                      <strong>Wallet:</strong> {alert.wallet_address}
                    </div>
                  )}
                  
                  {alert.evidence && (
                    <div className="text-xs text-gray-500 mb-2 max-w-md">
                      <strong>Evidence:</strong> {alert.evidence.substring(0, 100)}...
                    </div>
                  )}
                  
                  <div className="flex items-center gap-4 text-xs text-gray-500">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {new Date(alert.timestamp).toLocaleString()}
                    </span>
                    {alert.risk_score && (
                      <span>Risk Score: {alert.risk_score}/100</span>
                    )}
                  </div>
                </div>
                
                {alert.source_document && (
                  <div className="ml-4">
                    <button className="text-xs text-blue-600 hover:text-blue-800 flex items-center gap-1">
                      View Source <ExternalLink className="w-3 h-3" />
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-sm text-gray-500 text-center py-8">
          No recent alerts. The system is monitoring for compliance violations.
        </div>
      )}
      
      <div className="mt-4 text-xs text-gray-500">
        Alerts are generated in real-time based on sanctions matching, high-value transactions, and regulatory enforcement actions.
      </div>
    </div>
  );
}
