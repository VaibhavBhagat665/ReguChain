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
export const queryAPI = async (question, target = null) => {
  try {
    const response = await api.post('/api/query', {
      question,
      target,
    });
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

export const simulateIngestion = async (target = null) => {
  try {
    const response = await api.post('/api/ingest/simulate', {
      target,
    });
    return response.data;
  } catch (error) {
    console.error('Simulate API error:', error);
    throw error;
  }
};

export const checkHealth = async () => {
  try {
    const response = await api.get('/health');
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
