import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
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
