'use client';

import { useState } from 'react';
import { ExternalLink, AlertTriangle, FileText, Clock, TrendingUp, Shield, ChevronDown, ChevronUp } from 'lucide-react';

export default function EnhancedQueryResults({ result, loading }) {
  const [expandedEvidence, setExpandedEvidence] = useState(false);
  const [expandedAlerts, setExpandedAlerts] = useState(false);

  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
        <div className="flex items-center gap-2 text-gray-500">
          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
          Analyzing with Mistral AI...
        </div>
      </div>
    );
  }

  if (!result) return null;

  const getRiskColor = (score) => {
    if (score >= 70) return 'text-red-600 bg-red-50 border-red-200';
    if (score >= 40) return 'text-orange-600 bg-orange-50 border-orange-200';
    return 'text-green-600 bg-green-50 border-green-200';
  };

  const getRiskIcon = (score) => {
    if (score >= 70) return <AlertTriangle className="w-5 h-5 text-red-600" />;
    if (score >= 40) return <TrendingUp className="w-5 h-5 text-orange-600" />;
    return <Shield className="w-5 h-5 text-green-600" />;
  };

  const getRiskLabel = (score) => {
    if (score >= 70) return 'HIGH RISK';
    if (score >= 40) return 'MEDIUM RISK';
    return 'LOW RISK';
  };

  return (
    <div className="space-y-6">
      {/* Main Response */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg">
            <FileText className="w-5 h-5 text-white" />
          </div>
          <h3 className="text-xl font-semibold text-gray-900 dark:text-white">AI Analysis</h3>
        </div>
        
        <div className="prose dark:prose-invert max-w-none">
          <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
            {result.answer}
          </p>
        </div>
      </div>

      {/* Risk Assessment */}
      {result.risk_score !== undefined && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            {getRiskIcon(result.risk_score)}
            Risk Assessment
          </h3>
          
          <div className="flex items-center gap-4 mb-4">
            <div className={`px-4 py-2 rounded-lg border font-semibold ${getRiskColor(result.risk_score)}`}>
              {getRiskLabel(result.risk_score)}
            </div>
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              {result.risk_score}/100
            </div>
          </div>
          
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
            <div 
              className={`h-3 rounded-full transition-all duration-500 ${
                result.risk_score >= 70 ? 'bg-red-500' : 
                result.risk_score >= 40 ? 'bg-orange-500' : 'bg-green-500'
              }`}
              style={{ width: `${Math.min(result.risk_score, 100)}%` }}
            ></div>
          </div>
        </div>
      )}

      {/* Evidence Explorer */}
      {result.evidence && result.evidence.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <FileText className="w-5 h-5 text-blue-600" />
              Evidence ({result.evidence.length})
            </h3>
            <button
              onClick={() => setExpandedEvidence(!expandedEvidence)}
              className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800"
            >
              {expandedEvidence ? 'Collapse' : 'Expand'}
              {expandedEvidence ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>
          </div>
          
          <div className={`space-y-3 ${expandedEvidence ? '' : 'max-h-48 overflow-hidden'}`}>
            {result.evidence.map((evidence, index) => (
              <div key={index} className="p-3 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-100 dark:border-gray-800">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-xs px-2 py-1 rounded-full bg-blue-100 text-blue-800 font-medium">
                        {evidence.source}
                      </span>
                      {evidence.similarity && (
                        <span className="text-xs text-gray-500">
                          {Math.round(evidence.similarity * 100)}% match
                        </span>
                      )}
                    </div>
                    
                    <p className="text-sm text-gray-700 dark:text-gray-300 mb-2">
                      {evidence.snippet}
                    </p>
                    
                    {evidence.timestamp && (
                      <div className="text-xs text-gray-500 flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {new Date(evidence.timestamp).toLocaleString()}
                      </div>
                    )}
                  </div>
                  
                  {evidence.link && (
                    <div className="ml-4 flex-shrink-0">
                      <a
                        href={evidence.link}
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
        </div>
      )}

      {/* Recent Alerts */}
      {result.alerts && result.alerts.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-red-600" />
              Recent Alerts ({result.alerts.length})
            </h3>
            <button
              onClick={() => setExpandedAlerts(!expandedAlerts)}
              className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800"
            >
              {expandedAlerts ? 'Collapse' : 'Expand'}
              {expandedAlerts ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>
          </div>
          
          <div className={`space-y-3 ${expandedAlerts ? '' : 'max-h-48 overflow-hidden'}`}>
            {result.alerts.map((alert, index) => (
              <div key={index} className="p-3 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-100 dark:border-red-800">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="w-4 h-4 text-red-600 mt-0.5 flex-shrink-0" />
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-medium text-red-800 dark:text-red-300">
                        {alert.type}
                      </span>
                      {alert.timestamp && (
                        <span className="text-xs text-red-600 dark:text-red-400">
                          {new Date(alert.timestamp).toLocaleString()}
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-red-700 dark:text-red-300">
                      {alert.detail}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Related News */}
      {result.news && result.news.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <FileText className="w-5 h-5 text-green-600" />
            Related News ({result.news.length})
          </h3>
          
          <div className="space-y-3">
            {result.news.map((newsItem, index) => (
              <div key={index} className="p-3 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-100 dark:border-green-800">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h4 className="text-sm font-medium text-green-800 dark:text-green-300 mb-1">
                      {newsItem.title}
                    </h4>
                    {newsItem.timestamp && (
                      <div className="text-xs text-green-600 dark:text-green-400 flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {new Date(newsItem.timestamp).toLocaleString()}
                      </div>
                    )}
                  </div>
                  
                  {newsItem.url && (
                    <div className="ml-4 flex-shrink-0">
                      <a
                        href={newsItem.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-green-600 hover:text-green-800 flex items-center gap-1 px-2 py-1 rounded hover:bg-green-100 transition-colors"
                      >
                        Read <ExternalLink className="w-3 h-3" />
                      </a>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
