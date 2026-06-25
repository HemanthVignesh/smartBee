/**
 * src/api/client.ts — UPDATED for JWT authentication
 *
 * Changes:
 *  1. getToken() reads the JWT from localStorage (set by AuthContext).
 *  2. Every request() call automatically injects  Authorization: Bearer <token>.
 *  3. 401 responses trigger a client-side logout (token cleared, page reloaded).
 *  4. New auth helpers: getMe(), exchangeGoogleCode().
 */

import { RateLimitError } from './RateLimitError';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const TOKEN_KEY = 'sb_token';

// ── Auth helpers ──────────────────────────────────────────────────────────────

function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

function handleUnauthorized() {
  // Clear stale token and hard-reload so AuthProvider re-evaluates
  localStorage.removeItem(TOKEN_KEY);
  window.location.replace('/');
}

// ── Type Definitions ──────────────────────────────────────────────────────────

export interface Email {
  id: string;
  sender: string;
  subject: string;
  body: string;
  received_at: string;
  source: string;
  created_at: string;
  category?: string;
  analysis?: any;
  decisions?: any[];
}

export interface SuggestedAction {
  action_id: string;
  action_type: 'create_calendar_event' | 'generate_reply' | 'create_task';
  payload: Record<string, any>;
  status: 'pending' | 'accepted' | 'rejected' | 'executed';
  execution_metadata?: Record<string, any>;
}

export interface InsightResponse {
  email_id: string;
  sender: string;
  subject?: string;
  received_at: string;
  category?: string;
  summary: string;
  intent: string;
  priority: 'high' | 'medium' | 'low';
  confidence: number;
  entities: Record<string, any>;
  actions: SuggestedAction[];
  rationale?: string;
}

export interface FetchEmailsResponse {
  message: string;
  fetched_count: number;
  new_count: number;
  emails: string[];
}

export interface FeedbackRequest {
  feedback_type: 'accepted' | 'rejected';
  notes?: string;
  custom_payload?: Record<string, any>;
}

export interface AuthUser {
  id: string;
  email: string;
  name: string | null;
  picture: string | null;
  is_active: boolean;
  created_at: string;
}

// ── API Client Class ──────────────────────────────────────────────────────────

export class SmartBeeAPI {
  private baseURL: string;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    const token = getToken();

    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          // ── Inject JWT on every request ────────────────────────────────────
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
          ...options?.headers,
        },
      });

      // ── 401 → force logout ────────────────────────────────────────────────
      if (response.status === 401) {
        handleUnauthorized();
        throw new Error('Session expired — please sign in again.');
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));

        if (response.status === 429) {
          const retryAfter = response.headers.get('Retry-After') ?? '60';
          const tier = errorData.tier ?? 'general';
          const limit = errorData.limit ?? '?';
          const window = errorData.window_seconds ?? 60;
          throw new RateLimitError(
            `Too many requests (${tier} tier: ${limit} per ${window}s). ` +
              `Please wait ${retryAfter}s and try again.`,
            parseInt(retryAfter, 10),
          );
        }

        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // ── Auth ──────────────────────────────────────────────────────────────────

  /** Fetch the current user's profile (validates the stored JWT). */
  async getMe(): Promise<AuthUser> {
    return this.request('/api/v1/auth/me');
  }

  /**
   * Exchange a Google authorisation code for a SmartBee JWT.
   * Used when the SPA handles the OAuth redirect itself.
   */
  async exchangeGoogleCode(code: string, redirectUri: string): Promise<{ access_token: string; user: AuthUser }> {
    return this.request('/api/v1/auth/google/token', {
      method: 'POST',
      body: JSON.stringify({ code, redirect_uri: redirectUri }),
    });
  }

  // ── Health ─────────────────────────────────────────────────────────────────

  async healthCheck(): Promise<{ status: string }> {
    return this.request('/health');
  }

  // ── Gmail ──────────────────────────────────────────────────────────────────

  async getGmailProfile(): Promise<any> {
    return this.request('/api/v1/emails/gmail/profile');
  }

  async fetchEmails(params?: { max_results?: number; query?: string }): Promise<FetchEmailsResponse> {
    return this.request('/api/v1/emails/fetch', {
      method: 'POST',
      body: JSON.stringify({
        max_results: params?.max_results || 10,
        query: params?.query || 'in:inbox',
      }),
    });
  }

  // ── Emails ─────────────────────────────────────────────────────────────────

  async getEmails(params?: { skip?: number; limit?: number }): Promise<Email[]> {
    const queryParams = new URLSearchParams();
    if (params?.skip !== undefined) queryParams.append('skip', params.skip.toString());
    if (params?.limit !== undefined) queryParams.append('limit', params.limit.toString());
    const query = queryParams.toString();
    const data = await this.request<Email[]>(`/api/v1/emails/${query ? '?' + query : ''}`);
    return Array.isArray(data) ? data : [];
  }

  async getEmailById(emailId: string): Promise<Email> {
    return this.request(`/api/v1/emails/${emailId}`);
  }

  async analyzeEmail(emailId: string): Promise<any> {
    return this.request(`/api/v1/emails/${emailId}/analyze`, { method: 'POST' });
  }

  async searchEmails(query: string, limit?: number): Promise<Email[]> {
    const params = new URLSearchParams({ query });
    if (limit) params.append('limit', limit.toString());
    return this.request(`/api/v1/emails/search/?${params.toString()}`);
  }

  // ── Insights ───────────────────────────────────────────────────────────────

  async getInsights(): Promise<InsightResponse[]> {
    const data = await this.request<InsightResponse[]>('/api/v1/insights/');
    return Array.isArray(data) ? data : [];
  }

  // ── Actions ────────────────────────────────────────────────────────────────

  async submitFeedback(actionId: string, feedback: FeedbackRequest): Promise<any> {
    return this.request(`/api/v1/actions/${actionId}/feedback`, {
      method: 'POST',
      body: JSON.stringify(feedback),
    });
  }

  async deleteScheduledEmail(actionId: string): Promise<any> {
    return this.request(`/api/v1/scheduled/${actionId}`, { method: 'DELETE' });
  }

  // ── Analytics ──────────────────────────────────────────────────────────────

  async getAnalytics(): Promise<any> {
    return this.request('/api/v1/analytics/stats');
  }

  // ── Bootstrap ──────────────────────────────────────────────────────────────

  async syncGmail(): Promise<{ status: string; message: string; new_emails: number }> {
    return this.request('/api/v1/bootstrap/sync', { method: 'POST' });
  }

  async clearAllData(): Promise<{ message: string }> {
    return this.request('/api/v1/bootstrap/clear', { method: 'DELETE' });
  }

  async bootstrap(): Promise<{ message: string }> {
    return this.request('/api/v1/bootstrap/', { method: 'POST' });
  }

  // ── Chatbot ────────────────────────────────────────────────────────────────

  async chat(message: string, sessionId = 'default_session'): Promise<{ response: string; context_used: boolean }> {
    return this.request('/api/v1/chatbot/chat', {
      method: 'POST',
      body: JSON.stringify({ message, session_id: sessionId }),
    });
  }

  async getChatHistory(
    sessionId = 'default_session',
    limit = 50,
  ): Promise<Array<{ id: string; role: string; content: string; timestamp: string }>> {
    const data = await this.request<Array<{ id: string; role: string; content: string; timestamp: string }>>(
      `/api/v1/chatbot/history?session_id=${encodeURIComponent(sessionId)}&limit=${limit}`,
    );
    return Array.isArray(data) ? data : [];
  }

  async clearChatHistory(sessionId = 'default_session'): Promise<{ message: string }> {
    return this.request(`/api/v1/chatbot/history?session_id=${encodeURIComponent(sessionId)}`, {
      method: 'DELETE',
    });
  }

  // ── Scheduled emails ───────────────────────────────────────────────────────

  async getScheduledEmails(): Promise<any[]> {
    const data = await this.request<any[]>('/api/v1/scheduled/');
    return Array.isArray(data) ? data : [];
  }

  async getMeetings(): Promise<any[]> {
    const data = await this.request<any[]>('/api/v1/actions/meetings');
    return Array.isArray(data) ? data : [];
  }

  async updateScheduledEmail(actionId: string, to: string, subject: string, body: string): Promise<any> {
    return this.request(`/api/v1/scheduled/${actionId}`, {
      method: 'PUT',
      body: JSON.stringify({ to, subject, body }),
    });
  }

  async pauseScheduledEmail(actionId: string): Promise<any> {
    return this.request(`/api/v1/scheduled/${actionId}/pause`, { method: 'POST' });
  }

  async resumeScheduledEmail(actionId: string): Promise<any> {
    return this.request(`/api/v1/scheduled/${actionId}/resume`, { method: 'POST' });
  }

  async rewriteScheduledEmail(actionId: string, instruction: string): Promise<any> {
    return this.request(`/api/v1/scheduled/${actionId}/rewrite`, {
      method: 'POST',
      body: JSON.stringify({ instruction }),
    });
  }

  // ── Settings ───────────────────────────────────────────────────────────────

  async getSettings(): Promise<any> {
    return this.request('/api/v1/settings/');
  }

  async updateSettings(settingsData: any): Promise<any> {
    return this.request('/api/v1/settings/', {
      method: 'POST',
      body: JSON.stringify(settingsData),
    });
  }
}

// ── Singleton ─────────────────────────────────────────────────────────────────

export const api = new SmartBeeAPI();

// ── React Hooks ───────────────────────────────────────────────────────────────

import { useState, useEffect } from 'react';

export function useEmails(autoFetch = true) {
  const [emails, setEmails] = useState<Email[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchEmails = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getEmails();
      setEmails(data);
    } catch (err) {
      setError(err as Error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (autoFetch) fetchEmails();
  }, [autoFetch]);

  return { emails, loading, error, refetch: fetchEmails };
}

export function useInsights(autoFetch = true) {
  const [insights, setInsights] = useState<InsightResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchInsights = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getInsights();
      setInsights(data);
    } catch (err) {
      setError(err as Error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (autoFetch) fetchInsights();
  }, [autoFetch]);

  return { insights, loading, error, refetch: fetchInsights };
}

export function useScheduledEmails(autoFetch = true) {
  const [scheduledEmails, setScheduledEmails] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchScheduled = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getScheduledEmails();
      setScheduledEmails(data);
    } catch (err) {
      setError(err as Error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (autoFetch) fetchScheduled();
  }, [autoFetch]);

  return { scheduledEmails, loading, error, refetch: fetchScheduled };
}

export function useMeetings(autoFetch = true) {
  const [meetings, setMeetings] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchMeetings = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getMeetings();
      setMeetings(data);
    } catch (err) {
      setError(err as Error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (autoFetch) fetchMeetings();
  }, [autoFetch]);

  return { meetings, loading, error, refetch: fetchMeetings };
}

export default api;
