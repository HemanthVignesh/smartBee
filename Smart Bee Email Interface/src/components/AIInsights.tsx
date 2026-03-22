import { Brain, TrendingUp, AlertCircle, Clock, Zap, ChevronDown, ChevronUp, HelpCircle } from "lucide-react";
import { useEffect, useState } from "react";


interface InsightProps {
  icon: React.ReactNode;
  text: string;
  type?: "info" | "warning" | "success";
  confidence: number;
  explanation: string;
  beeReaction: "thinking" | "happy" | "alert";
  insight: any;
}

function Insight({ icon, text, type, confidence, explanation, beeReaction, insight }: InsightProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  
  const bgColor = {
    info: "bg-blue-50 border-blue-200 hover:bg-blue-100",
    warning: "bg-orange-50 border-orange-200 hover:bg-orange-100",
    success: "bg-green-50 border-green-200 hover:bg-green-100"
  }[type || "info"];

  const iconColor = {
    info: "text-blue-600",
    warning: "text-orange-600",
    success: "text-green-600"
  }[type || "info"];
  
  const beeEmoji = {
    thinking: "🤔",
    happy: "😊",
    alert: "⚠️"
  }[beeReaction];

  return (
    <div className={`${bgColor} border rounded-xl transition-all duration-300 hover:scale-[1.02] hover:shadow-md cursor-pointer overflow-hidden`}>
      <div 
        className="p-4"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-start gap-3">
          <div className={`${iconColor} shrink-0 mt-0.5 group-hover:scale-110 transition-transform`}>
            {icon}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm text-gray-800">{text}</p>
            
            {/* Confidence meter */}
            <div className="mt-2 flex items-center gap-2">
              <div className="flex-1">
                <div className="h-1 bg-white/50 rounded-full overflow-hidden">
                  <div 
                    className={`h-full transition-all duration-500 ${
                      confidence >= 80 ? "bg-green-500" : confidence >= 60 ? "bg-yellow-500" : "bg-orange-500"
                    }`}
                    style={{ width: `${confidence}%` }}
                  ></div>
                </div>
              </div>
              <span className="text-xs text-gray-600">{confidence}%</span>
            </div>
          </div>
          
          <div className="flex items-center gap-2 shrink-0">
            <div className="text-lg">{beeEmoji}</div>
            <button className="p-1 hover:bg-white/50 rounded-full transition-colors">
              {isExpanded ? (
                <ChevronUp className="w-4 h-4 text-gray-600" />
              ) : (
                <HelpCircle className="w-4 h-4 text-gray-600" />
              )}
            </button>
          </div>
        </div>
      </div>
      
      {/* Expandable explanation */}
      {isExpanded && (
        <div className="px-4 pb-4 pt-2 border-t border-white/50 animate-in slide-in-from-top-2">
          <div className="text-xs text-gray-700 bg-white/50 rounded-lg p-3">
            <div className="flex items-start gap-2">
              <Brain className="w-4 h-4 text-[#FFC107] shrink-0 mt-0.5" />
              <div>
                <div className="text-gray-900 mb-1">Why this matters:</div>
                <div>{explanation}</div>
                <div className="mt-3 flex gap-2">
                {insight.actions?.map((action: any) => {

                  // 📅 Calendar pending
                  if (action.action_type === "create_calendar_event" && action.status === "pending") {
                    return (
                      <>
                        <button
                          onClick={() => sendFeedback(action.action_id, "accepted")}
                          className="px-3 py-1 text-xs rounded bg-green-600 text-white"
                        >
                          Accept
                        </button>
                        <button
                          onClick={() => sendFeedback(action.action_id, "rejected")}
                          className="px-3 py-1 text-xs rounded bg-gray-400 text-white"
                        >
                          Reject
                        </button>
                      </>
                    );
                  }

                  // ✉️ Smart Reply pending
                  if (action.action_type === "generate_reply" && action.status === "pending") {
                    return (
                      <div className="mt-2 space-y-2 w-full">
                        {action.payload.replies.map((reply: string, idx: number) => (
                          <div
                            key={idx}
                            onClick={() => sendFeedback(action.action_id, "accepted")}
                            className="p-2 text-xs bg-white rounded border cursor-pointer hover:bg-gray-50"
                          >
                            {reply}
                          </div>
                        ))}
                      </div>
                    );
                  }

                  // 🔵 Executed calendar
                  if (
                    action.action_type === "create_calendar_event" &&
                    action.status === "executed" &&
                    action.execution_metadata?.event_link
                  ) {
                    return (
                      <a
                        href={action.execution_metadata.event_link}
                        target="_blank"
                        className="px-3 py-1 text-xs rounded bg-blue-600 text-white"
                      >
                        Join Meet
                      </a>
                    );
                  }

                  // ✅ Executed reply
                  if (action.action_type === "generate_reply" && action.status === "executed") {
                    return (
                      <div className="mt-2 text-xs bg-green-50 border rounded p-2">
                        ✨ Reply ready:
                        <div className="italic mt-1">
                          {action.execution_metadata.selected_reply}
                        </div>
                      </div>
                    );
                  }

                  // ❌ Rejected
                  if (action.status === "rejected") {
                    return <span className="text-xs text-gray-500">Dismissed</span>;
                  }

                  return null;
                  })}

                </div>

              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
function sendFeedback(actionId: string, type: "accepted" | "rejected") {
  fetch(`http://127.0.0.1:8000/api/v1/actions/${actionId}/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ feedback_type: type })
  }).then(() => window.location.reload());
}


export function AIInsights() {
  const [aiStatus, setAiStatus] = useState<"learning" | "active" | "optimizing">("active");
  const [insights, setInsights] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("http://127.0.0.1:8000/api/v1/insights")
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data)) {
          setInsights(data);
        } else {
          console.error("Insights data is not an array:", data);
          setInsights([]);
        }
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to fetch insights:", err);
        setInsights([]);
        setLoading(false);
      });
  }, []);

  
  return (
    <div className="bg-gradient-to-br from-white/90 to-[#FFF8E1]/50 backdrop-blur-sm rounded-2xl p-6 shadow-lg border border-[#FFC107]/20 hover:shadow-xl transition-all duration-300">
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-2">
          <div className="p-2 bg-gradient-to-br from-[#FFC107] to-[#FFB300] rounded-lg animate-pulse">
            <Brain className="w-5 h-5 text-black" />
          </div>
          <h2 className="text-gray-900">🔍 AI Insights</h2>
        </div>
        
        {/* Animated Bee Mascot */}
        <div className="relative">
        <span className="text-xl">🐝</span>

          <div className="absolute -bottom-1 -right-1 w-3 h-3 bg-green-500 rounded-full border-2 border-white animate-pulse"></div>
        </div>
      </div>

      <div className="space-y-3">
        {loading && <div className="text-sm text-gray-500">Analyzing emails...</div>}

        {!loading && insights.length === 0 && (
          <div className="text-sm text-gray-500">
            No AI insights right now
          </div>
        )}

        {insights.map((insight, idx) => (
          <Insight
            icon={<Brain className="w-5 h-5" />}
            text={insight.summary}
            confidence={Math.round(insight.confidence * 100)}
            explanation={`Intent detected: ${insight.intent}`}
            beeReaction="alert"
            insight={insight}
          />
        
        ))}
      </div>


      {/* AI Activity Indicator */}
      <div className="mt-5 pt-5 border-t border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="text-xs text-gray-600">AI Status:</div>
            <div className="flex gap-1">
              {["learning", "active", "optimizing"].map((status) => (
                <button
                  key={status}
                  onClick={() => setAiStatus(status as typeof aiStatus)}
                  className={`text-xs px-2 py-1 rounded-full transition-all ${
                    aiStatus === status
                      ? "bg-gradient-to-r from-[#FFC107] to-[#FFB300] text-black"
                      : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                  }`}
                >
                  {status.charAt(0).toUpperCase() + status.slice(1)}
                </button>
              ))}
            </div>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-xs text-green-600">Online</span>
          </div>
        </div>
      </div>
    </div>
  );
  
}