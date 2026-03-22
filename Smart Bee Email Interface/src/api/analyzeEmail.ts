export interface AnalyzeResponse {
    intent: string;
    priority: string;
    entities: {
      dates?: string[];
      times?: string[];
    };
    suggested_reply: string;
  }
  
  export async function analyzeEmail(emailBody: string): Promise<AnalyzeResponse> {
    const response = await fetch("http://127.0.0.1:8000/analyze-email", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        email_body: emailBody,
      }),
    });
  
    if (!response.ok) {
      throw new Error("Failed to analyze email");
    }
  
    return response.json();
  }
  