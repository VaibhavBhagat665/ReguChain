'use client';

import { useState } from 'react';
import { Search, AlertCircle, Loader2 } from 'lucide-react';

export default function QueryBox({ onQuery, loading }) {
  const [question, setQuestion] = useState('');
  const [target, setTarget] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (question.trim()) {
      onQuery(question, target || null);
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
      <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
        <Search className="w-5 h-5 text-primary-600" />
        Compliance Query
      </h2>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="question" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Question
          </label>
          <textarea
            id="question"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="e.g., Is wallet 0xABC123 sanctioned? What are the latest OFAC updates?"
            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
            rows="3"
            required
          />
        </div>
        
        <div>
          <label htmlFor="target" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Target (Optional)
          </label>
          <input
            id="target"
            type="text"
            value={target}
            onChange={(e) => setTarget(e.target.value)}
            placeholder="e.g., 0xDEMO123456 or entity name"
            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
          />
        </div>
        
        <button
          type="submit"
          disabled={loading || !question.trim()}
          className="w-full bg-primary-600 text-white py-2 px-4 rounded-lg hover:bg-primary-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors duration-200 flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Analyzing...
            </>
          ) : (
            <>
              <Search className="w-5 h-5" />
              Analyze
            </>
          )}
        </button>
      </form>
      
      <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg flex items-start gap-2">
        <AlertCircle className="w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5" />
        <p className="text-sm text-blue-800 dark:text-blue-300">
          This system uses AI-powered analysis of regulatory sources. Always verify critical compliance decisions.
        </p>
      </div>
    </div>
  );
}
