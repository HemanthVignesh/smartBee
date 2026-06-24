/**
 * Smart BEE API Client
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Type Definitions
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

// API Client Class
export class SmartBeeAPI {
  private baseURL: string;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    
    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // Health Check
  async healthCheck(): Promise<{ status: string }> {
    return this.request('/health');
  }

  // Gmail Profile
  async getGmailProfile(): Promise<any> {
    return this.request('/api/v1/emails/gmail/profile');
  }

  // Fetch Emails from Gmail
  async fetchEmails(params?: { max_results?: number; query?: string }): Promise<FetchEmailsResponse> {
    return this.request('/api/v1/emails/fetch', {
      method: 'POST',
      body: JSON.stringify({
        max_results: params?.max_results || 10,
        query: params?.query || 'in:inbox',
      }),
    });
  }

  // Get All Emails
  async getEmails(params?: { skip?: number; limit?: number }): Promise<Email[]> {
    const queryParams = new URLSearchParams();
    if (params?.skip !== undefined) queryParams.append('skip', params.skip.toString());
    if (params?.limit !== undefined) queryParams.append('limit', params.limit.toString());
    
    const query = queryParams.toString();
    const data = await this.request<Email[]>(`/api/v1/emails/${query ? '?' + query : ''}`);
    return Array.isArray(data) ? data : [];
  }

  // Get Email by ID
  async getEmailById(emailId: string): Promise<Email> {
    return this.request(`/api/v1/emails/${emailId}`);
  }

  // Manually trigger AI analysis on an email
  async analyzeEmail(emailId: string): Promise<any> {
    return this.request(`/api/v1/emails/${emailId}/analyze`, {
      method: 'POST',
    });
  }

  // Search Emails
  async searchEmails(query: string, limit?: number): Promise<Email[]> {
    const params = new URLSearchParams({ query });
    if (limit) params.append('limit', limit.toString());
    return this.request(`/api/v1/emails/search/?${params.toString()}`);
  }

  // Get AI Insights
  async getInsights(): Promise<InsightResponse[]> {
    const data = await this.request<InsightResponse[]>('/api/v1/insights/');
    return Array.isArray(data) ? data : [];
  }

  // Submit Action Feedback
  async submitFeedback(actionId: string, feedback: FeedbackRequest): Promise<any> {
    return this.request(`/api/v1/actions/${actionId}/feedback`, {
      method: 'POST',
      body: JSON.stringify(feedback),
    });
  }

  // Delete a scheduled email suggested action
  async deleteScheduledEmail(actionId: string): Promise<any> {
    return this.request(`/api/v1/scheduled/${actionId}`, {
      method: 'DELETE',
    });
  }

  // Get Analytics Stats
  async getAnalytics(): Promise<any> {
    return this.request('/api/v1/analytics/stats');
  }

  // Sync Gmail - fetch real emails now
  async syncGmail(): Promise<{ status: string; message: string; new_emails: number }> {
    return this.request('/api/v1/bootstrap/sync', { method: 'POST' });
  }

  // Clear all data (dev reset tool)
  async clearAllData(): Promise<{ message: string }> {
    return this.request('/api/v1/bootstrap/clear', { method: 'DELETE' });
  }

  // [Deprecated] Bootstrap with mock data - kept for dev use only
  async bootstrap(): Promise<{ message: string }> {
    return this.request('/api/v1/bootstrap/', { method: 'POST' });
  }

  // Chat with AI Assistant
  async chat(message: string, sessionId = "default_session"): Promise<{ response: string; context_used: boolean }> {
    return this.request('/api/v1/chatbot/chat', {
      method: 'POST',
      body: JSON.stringify({
        message,
        session_id: sessionId,
      }),
    });
  }

  // Get Chat History
  async getChatHistory(sessionId = "default_session", limit = 50): Promise<Array<{id: string; role: string; content: string; timestamp: string}>> {
    const data = await this.request<Array<{id: string; role: string; content: string; timestamp: string}>>(`/api/v1/chatbot/history?session_id=${encodeURIComponent(sessionId)}&limit=${limit}`);
    return Array.isArray(data) ? data : [];
  }

  // Clear Chat History
  async clearChatHistory(sessionId = "default_session"): Promise<{ message: string }> {
    return this.request(`/api/v1/chatbot/history?session_id=${encodeURIComponent(sessionId)}`, {
      method: 'DELETE',
    });
  }

  // Get Scheduled Actions / Emails
  async getScheduledEmails(): Promise<any[]> {
    const data = await this.request<any[]>('/api/v1/scheduled/');
    return Array.isArray(data) ? data : [];
  }

  // Get Scheduled Meetings
  async getMeetings(): Promise<any[]> {
    const data = await this.request<any[]>('/api/v1/actions/meetings');
    return Array.isArray(data) ? data : [];
  }

  // Update Scheduled Email
  async updateScheduledEmail(actionId: string, to: string, subject: string, body: string): Promise<any> {
    return this.request(`/api/v1/scheduled/${actionId}`, {
      method: 'PUT',
      body: JSON.stringify({ to, subject, body }),
    });
  }

  // Pause Scheduled Email
  async pauseScheduledEmail(actionId: string): Promise<any> {
    return this.request(`/api/v1/scheduled/${actionId}/pause`, {
      method: 'POST',
    });
  }

  // Resume Scheduled Email
  async resumeScheduledEmail(actionId: string): Promise<any> {
    return this.request(`/api/v1/scheduled/${actionId}/resume`, {
      method: 'POST',
    });
  }

  // Rewrite Scheduled Email with AI
  async rewriteScheduledEmail(actionId: string, instruction: string): Promise<any> {
    return this.request(`/api/v1/scheduled/${actionId}/rewrite`, {
      method: 'POST',
      body: JSON.stringify({ instruction }),
    });
  }

  // Get System Settings
  async getSettings(): Promise<any> {
    return this.request('/api/v1/settings/');
  }

  // Update System Settings
  async updateSettings(settingsData: any): Promise<any> {
    return this.request('/api/v1/settings/', {
      method: 'POST',
      body: JSON.stringify(settingsData),
    });
  }
}

// Singleton Instance
export const api = new SmartBeeAPI();

// React Hooks
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