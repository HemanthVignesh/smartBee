export interface SuggestedAction {
    action_id: string;
    action_type: string;
    payload: Record<string, any>;
    status: string;
  }
  
  export interface Insight {
    email_id: string;
    summary: string;
    intent: string;
    priority: string;
    confidence: number;
    actions: SuggestedAction[];
  }

  