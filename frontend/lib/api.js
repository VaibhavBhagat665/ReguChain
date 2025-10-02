import axios from 'axios';

// Normalize NEXT_PUBLIC_API_URL to always be the backend root (no trailing slash)
const raw = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const stripTrailingSlash = (u) => u.replace(/\/$/, '');
// If env already includes "/api" at the end, treat that as base root
const API_ROOT = stripTrailingSlash(raw.endsWith('/api') ? raw.slice(0, -4) : raw);

// Create axios instance pointed to backend root; endpoints will prefix with /api
const api = axios.create({
  baseURL: API_ROOT,
  headers: {
    'Content-Type': 'application/json',
  },
});

// API functions - Updated for new backend endpoints
export const queryAPI = async (question, target = null, conversationId = null) => {
  try {
    // Use the proper agent chat endpoint
    const payload = {
      message: question,
      conversation_id: conversationId || 'default',
      wallet_address: target,
      context: {}
    };

    const response = await api.post('/api/agent/chat', payload);
    
    // Transform response to match expected format
    const data = response.data;
    
    // Get evidence from context documents if available
    const evidence = [];
    const news = [];
    
    // Extract evidence from the response metadata if available
    if (data.context_documents) {
      data.context_documents.forEach(doc => {
        const evidenceItem = {
          source: doc.source || 'Unknown',
          snippet: doc.content || doc.text || '',
          link: doc.link || '',
          timestamp: doc.timestamp || '',
          title: doc.title || '',
          similarity: doc.similarity || 1.0
        };
        
        if (doc.source && doc.source.includes('NEWS')) {
          news.push({
            title: doc.title || 'News Update',
            url: doc.link || '',
            timestamp: doc.timestamp || '',
            source: doc.source || ''
          });
        }
        
        evidence.push(evidenceItem);
      });
    }
    
    return {
      answer: data.message,
      risk_score: data.risk_assessment?.score || 0,
      evidence: evidence,
      alerts: [], // Will be populated from alerts endpoint
      news: news,
      conversation_id: data.conversation_id,
      confidence: data.confidence,
      suggested_actions: data.suggested_actions || [],
      follow_up_questions: data.follow_up_questions || [],
      risk_assessment: data.risk_assessment,
      blockchain_data: data.blockchain_data,
      capabilities_used: data.capabilities_used || []
    };
  } catch (error) {
    console.error('Query API error:', error);
    throw error;
  }
};

// Legacy chat endpoint for compatibility
export const chatAPI = async (question, target = null, conversationId = null) => {
  try {
    const payload = {
      message: question,
    };
    if (conversationId) payload.conversation_id = conversationId;
    if (target) payload.wallet_address = target;

    const response = await api.post('/api/agent/chat', payload);
    return response.data;
  } catch (error) {
    console.error('Chat API error:', error);
    throw error;
  }
};

export const getStatus = async () => {
  try {
    const response = await api.get('/api/status');
    return response.data;
  } catch (error) {
    console.error('Status API error:', error);
    throw error;
  }
};

// simulateIngestion removed: system uses real data only

export const checkHealth = async () => {
  try {
    const response = await api.get('/api/health');
    return response.data;
  } catch (error) {
    console.error('Health check error:', error);
    return { status: 'error', services: {} };
  }
};

// Get recent alerts
export const getAlerts = async (limit = 10) => {
  try {
    const response = await api.get(`/api/alerts?limit=${limit}`);
    return response.data;
  } catch (error) {
    console.error('Get alerts error:', error);
    throw error;
  }
};

// Add wallet to monitoring
export const addWalletMonitoring = async (walletAddress) => {
  try {
    const response = await api.post('/api/wallet/monitor', {
      wallet_address: walletAddress
    });
    return response.data;
  } catch (error) {
    console.error('Add wallet monitoring error:', error);
    throw error;
  }
};

// Analyze wallet
export const analyzeWallet = async (walletAddress) => {
  try {
    const response = await api.post('/api/wallet/analyze', {
      address: walletAddress
    });
    return response.data;
  } catch (error) {
    console.error('Analyze wallet error:', error);
    throw error;
  }
};

// Get RAG system status
export const getRagStatus = async () => {
  try {
    const response = await api.get('/api/rag/status');
    return response.data;
  } catch (error) {
    console.error('Get RAG status error:', error);
    throw error;
  }
};

export const refreshData = async () => {
  try {
    const response = await api.post('/api/ingest/refresh');
    return response.data;
  } catch (error) {
    console.error('Refresh API error:', error);
    throw error;
  }
};

// Realtime controls
export const startRealtime = async () => {
  try {
    const res = await api.post('/api/realtime/start');
    return res.data;
  } catch (e) {
    console.error('Start realtime error:', e);
    throw e;
  }
};

export const stopRealtime = async () => {
  try {
    const res = await api.post('/api/realtime/stop');
    return res.data;
  } catch (e) {
    console.error('Stop realtime error:', e);
    throw e;
  }
};

// Wallet realtime helpers
export const connectWalletRealtime = async (walletAddress) => {
  try {
    const res = await api.post('/api/realtime/wallet/connect', null, {
      params: { wallet_address: walletAddress },
    });
    return res.data;
  } catch (e) {
    console.error('Connect wallet realtime error:', e);
    throw e;
  }
};

export const getWalletRealtimeStatus = async (walletAddress) => {
  try {
    const res = await api.get(`/api/realtime/wallet/${walletAddress}/status`);
    return res.data;
  } catch (e) {
    console.error('Get wallet realtime status error:', e);
    throw e;
  }
};

export const getWalletCompliance = async (walletAddress) => {
  try {
    const res = await api.get(`/api/realtime/wallet/${walletAddress}/compliance`);
    return res.data;
  } catch (e) {
    console.error('Get wallet compliance error:', e);
    throw e;
  }
};

export const getWalletReport = async (walletAddress) => {
  try {
    const res = await api.get(`/api/realtime/wallet/${walletAddress}/report`);
    return res.data;
  } catch (e) {
    console.error('Get wallet report error:', e);
    throw e;
  }
};

export const listTrackedWallets = async () => {
  try {
    const res = await api.get('/api/realtime/wallet/tracked');
    return res.data;
  } catch (e) {
    console.error('List tracked wallets error:', e);
    throw e;
  }
};

export const getStreamRecords = async (streamName, { limit = 10, walletAddress = null } = {}) => {
  try {
    const params = { limit };
    if (walletAddress) params.wallet_address = walletAddress;
    const res = await api.get(`/api/realtime/streams/${streamName}`, { params });
    return res.data;
  } catch (e) {
    console.error('Get stream records error:', e);
    throw e;
  }
};

// News and status helpers - Updated to use new endpoints
export const fetchRealtimeNews = async (query = 'cryptocurrency OR blockchain OR regulatory', pageSize = 20) => {
  try {
    // Use the status endpoint to get recent news documents
    const res = await api.get('/api/status');
    const lastUpdates = res.data.last_updates || [];
    
    // Filter for news items
    const newsItems = lastUpdates
      .filter(item => item.type === 'regulatory_news' || item.source?.includes('Reuters') || item.source?.includes('Bloomberg') || item.source?.includes('Commission'))
      .map(item => ({
        id: item.id,
        title: item.title,
        source: item.source,
        published_at: item.timestamp,
        description: item.title,
        url: item.link,
        verification_url: item.link
      }));
    
    return { count: newsItems.length, articles: newsItems };
  } catch (e) {
    console.error('Fetch realtime news error:', e);
    throw e;
  }
};

export const getTopHeadlines = async (category = 'business', country = 'us', pageSize = 20) => {
  try {
    // Fallback to status endpoint for headlines
    const res = await api.get('/api/status');
    const lastUpdates = res.data.last_updates || [];
    
    const headlines = lastUpdates
      .filter(item => item.source.includes('RSS') || item.type === 'regulatory_update')
      .map(item => ({
        id: item.id,
        title: item.title,
        source: item.source,
        published_at: item.timestamp,
        description: item.title,
        url: item.link
      }));
    
    return { count: headlines.length, headlines: headlines };
  } catch (e) {
    console.error('Get top headlines error:', e);
    throw e;
  }
};

export const getRegulatoryNews = async () => {
  try {
    const res = await api.get('/api/status');
    const lastUpdates = res.data.last_updates || [];
    
    const articles = lastUpdates
      .filter(item => item.risk_level === 'high' || item.risk_level === 'critical')
      .map(item => ({
        id: item.id,
        title: item.title,
        source: item.source,
        published_at: item.timestamp,
        description: item.title,
        url: item.link
      }));
    
    return { count: articles.length, articles: articles };
  } catch (e) {
    console.error('Get regulatory news error:', e);
    throw e;
  }
};

// PDF upload helper
export const uploadPdf = async (file) => {
  try {
    const formData = new FormData();
    formData.append('file', file);
    const res = await api.post('/api/ingest/pdf', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return res.data; // { message, title, chunks }
  } catch (e) {
    console.error('Upload PDF error:', e);
    throw e;
  }
};
