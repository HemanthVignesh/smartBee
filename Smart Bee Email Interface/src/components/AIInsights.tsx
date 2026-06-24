import { Brain, AlertCircle, Clock, Zap, ChevronDown, ChevronUp, HelpCircle } from "lucide-react";
import { useState } from "react";
import { api, useInsights } from "../api/client";

interface InsightProps {
  text: string;
  type: "info" | "warning" | "success";
  confidence: number;
  explanation: string;
  beeReaction: "thinking" | "happy" | "alert";
  insight: any;
}

function Insight({ text, type, confidence, explanation, beeReaction, insight }: InsightProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  
  const iconColor = {
    info: "text-blue-500",
    warning: "text-orange-500",
    success: "text-green-500"
  }[type];

  const typeIcon = {
    info: <Clock className="w-5 h-5" />,
    warning: <AlertCircle className="w-5 h-5" />,
    success: <Zap className="w-5 h-5" />
  }[type];

  const typeLabelColor = {
    info: "bg-blue-500/10 text-blue-700 border-blue-500/20",
    warning: "bg-orange-500/10 text-orange-700 border-orange-500/20",
    success: "bg-green-500/10 text-green-700 border-green-500/20"
  }[type];
  
  const leftBorderColor = {
    info: "bg-blue-500",
    warning: "bg-orange-500",
    success: "bg-green-500"
  }[type];

  const beeEmoji = {
    thinking: "🤔",
    happy: "😊",
    alert: "⚠️"
  }[beeReaction];

  return (
    <div className="bg-white/70 backdrop-blur-md border border-gray-150 hover:border-amber-500/20 hover:bg-white/95 rounded-2xl transition-all duration-300 hover:scale-[1.01] hover:shadow-md cursor-pointer overflow-hidden relative group">
      {/* Accent left border */}
      <div className={`absolute left-0 top-0 bottom-0 w-1.5 ${leftBorderColor}`}></div>
      
      <div 
        className="p-5 pl-6"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-start gap-4">
          <div className={`${iconColor} shrink-0 mt-0.5 group-hover:scale-110 transition-transform duration-200`}>
            {typeIcon}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2 flex-wrap">
              <span className={`text-[10px] uppercase tracking-wider px-2 py-0.5 rounded-full border font-bold ${typeLabelColor}`}>
                {type === "warning" ? "High Priority" : type === "success" ? "Task Detected" : "General"}
              </span>
              <span className="text-xs text-gray-500 font-medium">Confidence: {confidence}%</span>
              {insight.category && (
                <span className="text-[10px] uppercase px-2 py-0.5 rounded-full border bg-amber-500/10 text-amber-700 border-amber-500/20 font-bold">
                  {insight.category}
                </span>
              )}
              {insight.intent && (
                <span className="text-[10px] uppercase px-2 py-0.5 rounded-full border bg-purple-500/10 text-purple-700 border-purple-500/20 font-bold">
                  {insight.intent.replace('_', ' ')}
                </span>
              )}
            </div>

            <div className="mb-2.5">
              <span className="text-sm font-bold text-gray-900 block truncate leading-tight mb-0.5">{insight.sender}</span>
              <span className="text-xs text-gray-500 font-semibold block truncate">{insight.subject || '(No Subject)'}</span>
            </div>

            <div className="bg-amber-500/[0.02] border border-amber-500/5 hover:border-amber-500/10 p-3 rounded-2xl transition duration-200">
              <p className="text-xs text-gray-700 leading-relaxed font-medium whitespace-pre-line">
                <span className="text-amber-500 font-bold text-sm leading-none select-none">“</span>
                {text}
                <span className="text-amber-500 font-bold text-sm leading-none select-none">”</span>
              </p>
            </div>
            
            {/* Confidence progress bar */}
            <div className="mt-3 w-32">
              <div className="h-1 bg-gray-100 rounded-full overflow-hidden">
                <div 
                  className={`h-full transition-all duration-500 ${
                    confidence >= 80 ? "bg-green-500" : confidence >= 60 ? "bg-yellow-500" : "bg-orange-500"
                  }`}
                  style={{ width: `${confidence}%` }}
                ></div>
              </div>
            </div>
          </div>
          
          <div className="flex items-center gap-2 shrink-0">
            <div className="text-lg leading-none">{beeEmoji}</div>
            <button className="p-1 hover:bg-gray-100 rounded-full transition-colors cursor-pointer text-gray-400 hover:text-gray-600">
              {isExpanded ? (
                <ChevronUp className="w-4 h-4" />
              ) : (
                <ChevronDown className="w-4 h-4" />
              )}
            </button>
          </div>
        </div>
      </div>
      
      {/* Expandable explanation & Action items */}
      {isExpanded && (
        <div className="px-6 pb-5 pt-2 border-t border-gray-100 bg-gray-50/50 animate-in slide-in-from-top-2 duration-200 pl-8">
          <div className="text-xs text-gray-600">
            <div className="flex items-start gap-2.5">
              <Brain className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
              <div className="flex-1">
                <div className="font-semibold text-gray-800 mb-1">AI Rationale:</div>
                <div className="leading-relaxed mb-3">{explanation}</div>
                
                {/* Actions mapping */}
                {insight.actions && insight.actions.length > 0 && (
                  <div className="mt-4 pt-4 border-t border-gray-100 w-full">
                    <div className="font-bold text-gray-700 mb-2 flex items-center gap-1.5">
                      <span>⚡</span> Suggested Actions:
                    </div>
                    
                    <div className="flex flex-wrap gap-2.5">
                      {insight.actions.map((action: any) => {
                        // 📅 Calendar pending
                        if (action.action_type === "create_calendar_event" && action.status === "pending") {
                          return (
                            <div key={action.action_id} className="flex gap-2 items-center bg-white p-3 rounded-xl border border-gray-200 shadow-sm w-full sm:w-auto">
                              <span className="text-sm">📅</span>
                              <div className="text-xs">
                                <span className="font-semibold text-gray-800">Add to Calendar:</span>{" "}
                                <span className="text-gray-500">{action.payload.title} ({action.payload.date} at {action.payload.time})</span>
                              </div>
                              <div className="flex gap-1.5 ml-auto sm:ml-4">
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    sendFeedback(action.action_id, "accepted");
                                  }}
                                  className="px-3 py-1.5 text-xs rounded-lg bg-amber-500 hover:bg-amber-600 text-black font-semibold transition cursor-pointer"
                                >
                                  Accept
                                </button>
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    sendFeedback(action.action_id, "rejected");
                                  }}
                                  className="px-3 py-1.5 text-xs rounded-lg bg-gray-100 hover:bg-gray-200 text-gray-600 transition cursor-pointer"
                                >
                                  Reject
                                </button>
                              </div>
                            </div>
                          );
                        }

                        // ✉️ Smart Reply pending
                        if (action.action_type === "generate_reply" && action.status === "pending") {
                          return (
                            <div key={action.action_id} className="mt-1 space-y-2 w-full">
                              <div className="text-[11px] font-bold text-gray-500 uppercase tracking-wider mb-1">Select a draft response to send:</div>
                              {action.payload.replies.map((reply: string, idx: number) => (
                                <div
                                  key={idx}
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    sendFeedback(action.action_id, "accepted");
                                  }}
                                  className="p-3 text-xs bg-white rounded-xl border border-gray-200 cursor-pointer hover:border-amber-500 hover:bg-amber-500/5 transition leading-relaxed shadow-sm hover:scale-[1.005]"
                                >
                                  <div className="font-semibold text-amber-800 mb-1 flex items-center gap-1">
                                    <span>✍️</span> Draft Option {idx + 1}
                                  </div>
                                  <div className="text-gray-700 italic">"{reply}"</div>
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
                              key={action.action_id}
                              href={action.execution_metadata.event_link}
                              target="_blank"
                              rel="noreferrer"
                              onClick={(e) => e.stopPropagation()}
                              className="px-3.5 py-2 text-xs rounded-xl bg-green-500 hover:bg-green-600 text-white font-semibold shadow-sm transition inline-flex items-center gap-1.5 cursor-pointer"
                            >
                              <span>📅</span> Calendar Event Created - View Details
                            </a>
                          );
                        }

                        // ✅ Executed reply
                        if (action.action_type === "generate_reply" && action.status === "executed") {
                          return (
                            <div key={action.action_id} className="mt-2 text-xs bg-green-50/50 border border-green-200/50 rounded-xl p-3 w-full">
                              <span className="font-semibold text-green-800 flex items-center gap-1 mb-1">
                                <span>✅</span> Auto-Reply Sent Successfully:
                              </span>
                              <div className="italic text-gray-600 pl-5">
                                "{action.execution_metadata.selected_reply}"
                              </div>
                            </div>
                          );
                        }

                        // ❌ Rejected
                        if (action.status === "rejected") {
                          return (
                            <div key={action.action_id} className="text-xs text-gray-400 italic">
                              Action dismissed
                            </div>
                          );
                        }

                        return null;
                      })}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function sendFeedback(actionId: string, type: "accepted" | "rejected") {
  api.submitFeedback(actionId, { feedback_type: type })
    .then(() => window.location.reload())
    .catch((err) => {
      console.error("Failed to submit feedback:", err);
      window.location.reload();
    });
}

export function AIInsights() {
  const [aiStatus, setAiStatus] = useState<"learning" | "active" | "optimizing">("active");
  const { insights, loading } = useInsights(true);

  return (
    <div className="bg-white/80 backdrop-blur-xl rounded-3xl p-6 shadow-xl border border-gray-200/50 hover:shadow-2xl transition-all duration-300">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-amber-500/10 rounded-2xl">
            <Brain className="w-5 h-5 text-amber-600" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-gray-900 tracking-tight">AI Insights</h2>
            <p className="text-xs text-gray-500">Automated reasoning and context actions</p>
          </div>
        </div>
        
        {/* Animated Bee Mascot Indicator */}
        <div className="relative w-8 h-8 bg-amber-500/10 rounded-full flex items-center justify-center">
          <span className="text-base leading-none">🐝</span>
          <div className="absolute bottom-0 right-0 w-2.5 h-2.5 bg-green-500 rounded-full border-2 border-white animate-pulse"></div>
        </div>
      </div>

      <div className="space-y-3">
        {loading && (
          <div className="flex items-center justify-center py-6 gap-2">
            <div className="animate-spin rounded-full h-5.5 w-5.5 border-b-2 border-amber-500"></div>
            <div className="text-xs text-gray-500 font-medium">Analyzing emails and generating insights...</div>
          </div>
        )}

        {!loading && insights.length === 0 && (
          <div className="text-center py-10 bg-gray-50/50 border border-dashed border-gray-200 rounded-2xl">
            <div className="text-3xl mb-3">🧠</div>
            <div className="text-sm font-semibold text-gray-800 mb-1">No AI insights yet</div>
            <div className="text-xs text-gray-500 px-4">
              Sync your Gmail inbox to have the AI analyze your emails and generate actionable insights automatically.
            </div>
          </div>
        )}

        {(() => {
          if (loading || insights.length === 0) return null;

          // Helper to format date header
          const getGroupDateHeader = (dateStr: string) => {
            const date = new Date(dateStr);
            const today = new Date();
            const yesterday = new Date();
            yesterday.setDate(today.getDate() - 1);
            
            if (date.toDateString() === today.toDateString()) {
              return "Today";
            } else if (date.toDateString() === yesterday.toDateString()) {
              return "Yesterday";
            } else {
              return date.toLocaleDateString(undefined, {
                weekday: 'long',
                month: 'long',
                day: 'numeric',
                year: 'numeric'
              });
            }
          };

          // Group insights by day-key
          const groupedInsights: Record<string, typeof insights> = {};
          insights.forEach((insight) => {
            const dayKey = new Date(insight.received_at).toDateString();
            if (!groupedInsights[dayKey]) {
              groupedInsights[dayKey] = [];
            }
            groupedInsights[dayKey].push(insight);
          });

          // Sort day keys descending (most recent first)
          const sortedDayKeys = Object.keys(groupedInsights).sort((a, b) => {
            return new Date(b).getTime() - new Date(a).getTime();
          });

          return sortedDayKeys.map((dayKey) => {
            const dayInsights = groupedInsights[dayKey];
            const header = getGroupDateHeader(dayInsights[0].received_at);
            return (
              <div key={dayKey} className="space-y-3">
                <div className="text-xs font-bold text-gray-400 uppercase tracking-wider pl-1 mt-6 mb-2">
                  {header}
                </div>
                {dayInsights.map((insight) => {
                  const priority = insight.priority || "medium";
                  const type = priority === "high" ? "warning" : priority === "low" ? "info" : "success";
                  const beeReaction = priority === "high" ? "alert" : priority === "low" ? "thinking" : "happy";
                  const explanation = insight.rationale || `Intent detected: ${insight.intent.replace('_', ' ')}. Rationale: This email contains key signals relating to scheduling, notifications, or deliverables.`;

                  return (
                    <Insight
                      key={insight.email_id}
                      text={insight.summary}
                      type={type}
                      confidence={Math.round(insight.confidence * 100)}
                      explanation={explanation}
                      beeReaction={beeReaction}
                      insight={insight}
                    />
                  );
                })}
              </div>
            );
          });
        })()}
      </div>

      {/* AI Activity Indicator */}
      <div className="mt-6 pt-5 border-t border-gray-100">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <div className="text-xs text-gray-500 font-semibold uppercase tracking-wider">AI Engine:</div>
            <div className="flex gap-1">
              {["learning", "active", "optimizing"].map((status) => (
                <button
                  key={status}
                  onClick={() => setAiStatus(status as typeof aiStatus)}
                  className={`text-[10px] font-bold px-2.5 py-1 rounded-full transition-all cursor-pointer ${
                    aiStatus === status
                      ? "bg-amber-500 text-black shadow-sm"
                      : "bg-gray-100 text-gray-500 hover:bg-gray-200"
                  }`}
                >
                  {status.toUpperCase()}
                </button>
              ))}
            </div>
          </div>
          <div className="flex items-center gap-1.5 ml-auto sm:ml-0">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-xs text-green-600 font-bold">Online</span>
          </div>
        </div>
      </div>
    </div>
  );
}