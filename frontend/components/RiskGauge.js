'use client';

import { useMemo } from 'react';
import { AlertTriangle, CheckCircle, XCircle } from 'lucide-react';

export default function RiskGauge({ score, reasons = [], recommendations = [] }) {
  const { color, label, icon: Icon } = useMemo(() => {
    if (score >= 70) {
      return { color: 'text-risk-high', label: 'HIGH RISK', icon: XCircle };
    } else if (score >= 40) {
      return { color: 'text-risk-medium', label: 'MEDIUM RISK', icon: AlertTriangle };
    } else {
      return { color: 'text-risk-low', label: 'LOW RISK', icon: CheckCircle };
    }
  }, [score]);

  const circumference = 2 * Math.PI * 45;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
      <h2 className="text-xl font-semibold mb-4">Risk Assessment</h2>
      
      <div className="flex items-center justify-center mb-6">
        <div className="relative">
          <svg className="w-32 h-32 transform -rotate-90">
            <circle
              cx="64"
              cy="64"
              r="45"
              stroke="currentColor"
              strokeWidth="8"
              fill="none"
              className="text-gray-200 dark:text-gray-700"
            />
            <circle
              cx="64"
              cy="64"
              r="45"
              stroke="currentColor"
              strokeWidth="8"
              fill="none"
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              className={`${color} risk-gauge-fill`}
              strokeLinecap="round"
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <Icon className={`w-8 h-8 ${color}`} />
            <span className={`text-2xl font-bold ${color}`}>{score}</span>
            <span className="text-xs text-gray-500 dark:text-gray-400">/ 100</span>
          </div>
        </div>
      </div>
      
      <div className={`text-center mb-4 ${color}`}>
        <span className="text-lg font-semibold">{label}</span>
      </div>
      
      {reasons.length > 0 && (
        <div className="mb-4">
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Risk Factors</h3>
          <ul className="space-y-1">
            {reasons.slice(0, 5).map((reason, index) => (
              <li key={index} className="text-sm text-gray-600 dark:text-gray-400 flex items-start gap-2">
                <span className="text-gray-400">•</span>
                <span>{reason}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
      
      {recommendations.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Recommended Actions</h3>
          <ul className="space-y-1">
            {recommendations.map((rec, index) => (
              <li key={index} className="text-sm text-gray-600 dark:text-gray-400 flex items-start gap-2">
                <span className="text-primary-500">→</span>
                <span>{rec}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
