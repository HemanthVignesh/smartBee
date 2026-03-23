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
  summary: string;
  intent: string;
  priority: 'high' | 'medium' | 'low';
  confidence: number;
  entities: Record<string, any>;
  actions: SuggestedAction[];
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

  // Get Analytics Stats
  async getAnalytics(): Promise<any> {
    return this.request('/api/v1/analytics/stats');
  }

  // Bootstrap Test Data
  async bootstrap(): Promise<{ message: string }> {
    return this.request('/api/v1/bootstrap/', { method: 'POST' });
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

export default api;