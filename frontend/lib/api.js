// API configuration
// In production, set NEXT_PUBLIC_API_URL to your Render backend URL
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const API_ENDPOINTS = {
  alerts: `${API_BASE_URL}/api/alerts`,
  walletAnalyze: `${API_BASE_URL}/api/wallet/analyze`,
  chat: `${API_BASE_URL}/api/agent/chat`,
  complianceSearch: `${API_BASE_URL}/api/compliance/search`,
  health: `${API_BASE_URL}/api/health`,
  status: `${API_BASE_URL}/api/status`,
};

// Helper functions for API calls
export async function getStatus() {
  try {
    const res = await fetch(API_ENDPOINTS.status);
    if (!res.ok) throw new Error('Failed to fetch status');
    return await res.json();
  } catch (error) {
    console.error('getStatus error:', error);
    return { status: 'inactive', last_updates: [], index_stats: {} };
  }
}

export async function getAlerts(limit = 10) {
  try {
    const res = await fetch(`${API_ENDPOINTS.alerts}?limit=${limit}`);
    if (!res.ok) throw new Error('Failed to fetch alerts');
    return await res.json();
  } catch (error) {
    console.error('getAlerts error:', error);
    return [];
  }
}

// Chat API function - used by AIAgentChat
export async function queryAPI(message, walletAddress, conversationId) {
  try {
    const res = await fetch(API_ENDPOINTS.chat, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: message,
        wallet_address: walletAddress || null,
        conversation_id: conversationId || null,
      }),
    });
    if (!res.ok) throw new Error('Request failed');
    return await res.json();
  } catch (error) {
    console.error('queryAPI error:', error);
    throw error;
  }
}
