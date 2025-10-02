'use client';

import { useState, useEffect, useRef } from 'react';
import { ExternalLink, Clock, Newspaper } from 'lucide-react';
import { fetchRealtimeNews, getTopHeadlines, getRegulatoryNews } from '../lib/api';

export default function NewsFeed() {
  const [news, setNews] = useState([]);
  const [loading, setLoading] = useState(true);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    const controller = new AbortController();

    const load = async () => {
      try {
        setLoading(true);
        // Prefer realtime News API (no mock)
        const res = await fetchRealtimeNews('cryptocurrency OR blockchain OR DeFi OR regulatory OR compliance', 20);
        if (!mountedRef.current) return;
        const articles = Array.isArray(res?.articles) ? res.articles : [];
        let items = articles.map((a, idx) => ({
          id: a.id || `a-${idx}`,
          title: a.title,
          source: a.source?.name || a.source || 'Unknown Source',
          timestamp: a.published_at || new Date().toISOString(),
          snippet: a.description || a.content || '',
          link: a.verification_url || a.url || '#',
        }));
        // Fallback to headlines if empty
        if (items.length === 0) {
          const h = await getTopHeadlines('business', 'us', 10);
          const headlines = Array.isArray(h?.headlines) ? h.headlines : [];
          items = headlines.map((a, idx) => ({
            id: a.id || `h-${idx}`,
            title: a.title,
            source: a.source?.name || a.source || 'Unknown Source',
            timestamp: a.published_at || new Date().toISOString(),
            snippet: a.description || a.content || '',
            link: a.url || '#',
          }));
        }
        setNews(items);
      } catch (e) {
        if (e.name === 'AbortError') return;
        console.error('Error loading news/status:', e);
        setNews([]);
      } finally {
        if (mountedRef.current) setLoading(false);
      }
    };

    load();
    const id = setInterval(load, 120000); // refresh every 2 minutes

    return () => {
      mountedRef.current = false;
      try { controller.abort(); } catch (e) {}
      clearInterval(id);
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
      ) : news.length > 0 ? (
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
                  {item.link && item.link !== '#' && item.link !== '' ? (
                    <a href={item.link} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-600 hover:text-blue-800 flex items-center gap-1 bg-blue-50 hover:bg-blue-100 px-2 py-1 rounded">
                      Read <ExternalLink className="w-3 h-3" />
                    </a>
                  ) : (
                    <span className="text-xs text-gray-400 px-2 py-1">No link</span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-sm text-gray-500">No recent news available. Ensure NEWSAPI_KEY (or NewsData.io key starting with pub_) is configured on the backend.</div>
      )}

      <div className="mt-4 text-xs text-gray-500">
        Live news is sourced from configured providers (NewsAPI.org or NewsData.io). All items include verification links.
      </div>
    </div>
  );
}
