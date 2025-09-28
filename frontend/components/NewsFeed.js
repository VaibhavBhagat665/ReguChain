'use client';

import { useState, useEffect, useRef } from 'react';
import { ExternalLink, Clock, Newspaper } from 'lucide-react';
import { getStatus } from '../lib/api';

export default function NewsFeed() {
  const [news, setNews] = useState([]);
  const [loading, setLoading] = useState(true);
  const mountedRef = useRef(true);

  const SAMPLE_NEWS = [
    {
      id: 'n1',
      title: 'Regulators increase crypto enforcement actions in Q3',
      source: 'Industry News',
      timestamp: new Date().toISOString(),
      snippet: 'Several enforcement actions were announced targeting mixing services and sanctioned addresses. This increases the importance of continuous monitoring.',
      link: '#'
    },
    {
      id: 'n2',
      title: 'OFAC updates sanctions guidance for virtual assets',
      source: 'OFAC',
      timestamp: new Date().toISOString(),
      snippet: 'New guidance clarifies obligations for service providers interacting with sanctioned entities.',
      link: '#'
    },
  ];

  useEffect(() => {
    mountedRef.current = true;
    const controller = new AbortController();

    const load = async () => {
      try {
        setLoading(true);
        const status = await getStatus();
        if (!mountedRef.current) return;
        if (status && status.last_updates && status.last_updates.length > 0) {
          // Map to UI-friendly shape
          const items = status.last_updates.map((u, idx) => ({
            id: u.id || `s-${idx}`,
            title: u.source || 'News',
            source: u.source || 'Unknown',
            timestamp: u.timestamp || new Date().toISOString(),
            snippet: u.text || '',
            link: u.link || '#'
          }));
          setNews(items);
        } else {
          setNews(SAMPLE_NEWS);
        }
      } catch (e) {
        if (e.name === 'AbortError') return;
        console.error('Error loading news/status:', e);
        setNews(SAMPLE_NEWS);
      } finally {
        if (mountedRef.current) setLoading(false);
      }
    };

    load();

    return () => {
      mountedRef.current = false;
      try { controller.abort(); } catch (e) {}
    };
  }, []);

  return (
    <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-sm rounded-2xl shadow-xl border border-gray-200/50 dark:border-gray-700/50 p-6">
      <div className="flex items-center gap-3 mb-4">
        <div className="p-2 bg-gradient-to-br from-yellow-400 to-orange-500 rounded-lg">
          <Newspaper className="w-5 h-5 text-white" />
        </div>
        <h3 className="text-xl font-semibold text-gray-900 dark:text-white">News & External Signals</h3>
      </div>

      {loading ? (
        <div className="text-sm text-gray-500">Loading news...</div>
      ) : (
        <div className="space-y-3">
          {news.map((item) => (
            <div key={item.id} className="p-3 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-100 dark:border-gray-800">
              <div className="flex items-start justify-between">
                <div>
                  <div className="text-sm font-semibold text-gray-900 dark:text-white">{item.title}</div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">{item.source} • <span className="inline-flex items-center gap-1"><Clock className="w-3 h-3" /> {new Date(item.timestamp).toLocaleString()}</span></div>
                  <p className="text-sm text-gray-600 dark:text-gray-300 mt-2">{item.snippet}</p>
                </div>
                <div className="ml-4 flex-shrink-0">
                  <a href={item.link} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-600 hover:text-blue-800 flex items-center gap-1">
                    Read <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="mt-4 text-xs text-gray-500">
        These news items are used to enrich AI responses and can be connected to live feeds (OFAC, SEC, NewsAPI) in production.
      </div>
    </div>
  );
}
