'use client';

import { useState } from 'react';
import { ChevronDown, ChevronRight, FileText, Link, Clock, DollarSign } from 'lucide-react';

export default function EvidenceExplorer({ evidence = [], onchainMatches = [], answer = '' }) {
  const [expandedItems, setExpandedItems] = useState(new Set());

  const toggleExpand = (index) => {
    const newExpanded = new Set(expandedItems);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedItems(newExpanded);
  };

  const formatAmount = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(amount);
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
      <h2 className="text-xl font-semibold mb-4">Analysis Results</h2>
      
      {answer && (
        <div className="mb-6 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">AI Analysis</h3>
          <div className="prose prose-sm dark:prose-invert max-w-none">
            <div className="whitespace-pre-wrap text-gray-700 dark:text-gray-300">
              {answer}
            </div>
          </div>
        </div>
      )}
      
      {evidence.length > 0 && (
        <div className="mb-6">
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
            Evidence Sources ({evidence.length})
          </h3>
          <div className="space-y-2">
            {evidence.map((item, index) => (
              <div
                key={index}
                className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden"
              >
                <button
                  onClick={() => toggleExpand(index)}
                  className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    {expandedItems.has(index) ? (
                      <ChevronDown className="w-4 h-4 text-gray-500" />
                    ) : (
                      <ChevronRight className="w-4 h-4 text-gray-500" />
                    )}
                    <FileText className="w-4 h-4 text-primary-600" />
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      {item.source || 'Unknown Source'}
                    </span>
                    {item.title && (
                      <span className="text-xs text-gray-500 ml-2">
                        - {item.title}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2 text-xs text-gray-500">
                    <Clock className="w-3 h-3" />
                    {new Date(item.timestamp).toLocaleString()}
                  </div>
                </button>
                
                {expandedItems.has(index) && (
                  <div className="px-4 py-3 bg-gray-50 dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700">
                    {item.title && (
                      <h4 className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-2">
                        {item.title}
                      </h4>
                    )}
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                      {item.content || item.snippet || 'No content available'}
                    </p>
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-gray-500">
                        Source: {item.source || 'Unknown Source'}
                      </span>
                      {item.link && (
                        <a
                          href={item.link}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 text-xs text-primary-500 hover:text-primary-600 font-medium"
                        >
                          <Link className="w-3 h-3" />
                          Read Full Article
                        </a>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
      
      {onchainMatches.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
            On-chain Matches ({onchainMatches.length})
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 dark:border-gray-700">
                  <th className="text-left py-2 px-3 font-medium text-gray-700 dark:text-gray-300">Transaction</th>
                  <th className="text-right py-2 px-3 font-medium text-gray-700 dark:text-gray-300">Amount</th>
                  <th className="text-left py-2 px-3 font-medium text-gray-700 dark:text-gray-300">Time</th>
                </tr>
              </thead>
              <tbody>
                {onchainMatches.map((match, index) => (
                  <tr key={index} className="border-b border-gray-100 dark:border-gray-700">
                    <td className="py-2 px-3">
                      <code className="text-xs bg-gray-100 dark:bg-gray-700 px-1 py-0.5 rounded">
                        {match.tx ? `${match.tx.substring(0, 10)}...` : 'N/A'}
                      </code>
                    </td>
                    <td className="text-right py-2 px-3">
                      <span className="flex items-center justify-end gap-1">
                        <DollarSign className="w-3 h-3" />
                        {formatAmount(match.amount)}
                      </span>
                    </td>
                    <td className="py-2 px-3 text-gray-500 dark:text-gray-400">
                      {new Date(match.timestamp).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
