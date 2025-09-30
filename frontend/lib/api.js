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

// API functions
export const queryAPI = async (question, target = null, conversationId = null) => {
  try {
    const payload = {
      message: question,
    };
    if (conversationId) payload.conversation_id = conversationId;
    if (target) payload.wallet_address = target;

    const response = await api.post('/api/agent/chat', payload);
    return response.data;
  } catch (error) {
    console.error('Query API error:', error);
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
    const response = await api.get('/api/realtime/health');
    return response.data;
  } catch (error) {
    console.error('Health check error:', error);
    return { status: 'error', services: {} };
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
