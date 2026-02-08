// API configuration
// In production, set NEXT_PUBLIC_API_URL to your Render backend URL
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const API_ENDPOINTS = {
  alerts: `${API_BASE_URL}/api/alerts`,
  walletAnalyze: `${API_BASE_URL}/api/wallet/analyze`,
  chat: `${API_BASE_URL}/api/agent/chat`,
  complianceSearch: `${API_BASE_URL}/api/compliance/search`,
  health: `${API_BASE_URL}/api/health`,
};
