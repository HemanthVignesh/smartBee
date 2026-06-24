import { useState, useRef, useEffect, useCallback } from "react";
import {
  Send, Bot, User, Sparkles, RotateCcw, Zap, Copy, ThumbsUp, ThumbsDown,
  Mail, Calendar, Clock, FileText, Search, ChevronRight
} from "lucide-react";
import { api } from "../api/client";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  isError?: boolean;
  isStreaming?: boolean;
}

/** Lightweight Markdown renderer */
function renderMarkdown(text: string): React.ReactNode[] {
  const lines = text.split("\n");
  const result: React.ReactNode[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    if (/^---+$/.test(line.trim())) {
      result.push(<hr key={i} style={{ border: "none", borderTop: "1px solid rgba(245,158,11,0.2)", margin: "8px 0" }} />);
      i++;
      continue;
    }

    if (line.startsWith("```")) {
      const codeLines: string[] = [];
      i++;
      while (i < lines.length && !lines[i].startsWith("```")) {
        codeLines.push(lines[i]);
        i++;
      }
      result.push(
        <pre key={i} style={{
          background: "#1a1a2e",
          color: "#e2e8f0",
          borderRadius: 10,
          padding: "12px 16px",
          overflowX: "auto",
          fontSize: 12,
          margin: "8px 0",
          fontFamily: "monospace",
          border: "1px solid rgba(245,158,11,0.15)"
        }}>
          {codeLines.join("\n")}
        </pre>
      );
      i++;
      continue;
    }

    if (/^#{1,3}\s/.test(line)) {
      const level = line.match(/^(#{1,3})/)?.[1].length || 1;
      const headingText = line.replace(/^#{1,3}\s/, "");
      const sizes = ["1.1em", "1em", "0.95em"];
      result.push(
        <p key={i} style={{ fontWeight: 700, fontSize: sizes[level - 1], margin: "8px 0 4px", color: "#f59e0b" }}>
          {inlineMarkdown(headingText)}
        </p>
      );
      i++;
      continue;
    }

    if (/^[*\-•]\s/.test(line.trim())) {
      const listItems: string[] = [];
      while (i < lines.length && /^[*\-•]\s/.test(lines[i].trim())) {
        listItems.push(lines[i].trim().replace(/^[*\-•]\s/, ""));
        i++;
      }
      result.push(
        <ul key={i} style={{ paddingLeft: 18, margin: "6px 0", listStyleType: "disc" }}>
          {listItems.map((item, idx) => (
            <li key={idx} style={{ marginBottom: 4, lineHeight: 1.6 }}>
              {inlineMarkdown(item)}
            </li>
          ))}
        </ul>
      );
      continue;
    }

    if (/^\d+\.\s/.test(line.trim())) {
      const listItems: string[] = [];
      while (i < lines.length && /^\d+\.\s/.test(lines[i].trim())) {
        listItems.push(lines[i].trim().replace(/^\d+\.\s/, ""));
        i++;
      }
      result.push(
        <ol key={i} style={{ paddingLeft: 18, margin: "6px 0" }}>
          {listItems.map((item, idx) => (
            <li key={idx} style={{ marginBottom: 4, lineHeight: 1.6 }}>
              {inlineMarkdown(item)}
            </li>
          ))}
        </ol>
      );
      continue;
    }

    if (line.trim() === "") {
      result.push(<div key={i} style={{ height: 8 }} />);
      i++;
      continue;
    }

    result.push(
      <p key={i} style={{ margin: "3px 0", lineHeight: 1.7 }}>
        {inlineMarkdown(line)}
      </p>
    );
    i++;
  }

  return result;
}

function inlineMarkdown(text: string): React.ReactNode {
  const parts: React.ReactNode[] = [];
  const regex = /(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|\[([^\]]+)\]\(([^)]+)\))/g;
  let lastIndex = 0;
  let match;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }
    const full = match[0];
    if (full.startsWith("**")) {
      parts.push(<strong key={match.index} style={{ fontWeight: 700 }}>{full.slice(2, -2)}</strong>);
    } else if (full.startsWith("*")) {
      parts.push(<em key={match.index}>{full.slice(1, -1)}</em>);
    } else if (full.startsWith("`")) {
      parts.push(
        <code key={match.index} style={{
          background: "rgba(245,158,11,0.15)",
          borderRadius: 4,
          padding: "1px 6px",
          fontSize: "0.85em",
          fontFamily: "monospace",
          color: "#f59e0b"
        }}>
          {full.slice(1, -1)}
        </code>
      );
    } else if (full.startsWith("[")) {
      parts.push(
        <a key={match.index} href={match[3]} target="_blank" rel="noopener noreferrer" style={{
          color: "#f59e0b",
          textDecoration: "underline",
          fontWeight: 500
        }}>
          {match[2]}
        </a>
      );
    }
    lastIndex = match.index + full.length;
  }

  if (lastIndex < text.length) parts.push(text.slice(lastIndex));
  return parts.length > 0 ? <>{parts}</> : text;
}

const WELCOME_MESSAGE: Message = {
  id: "welcome-1",
  role: "assistant",
  content: `Hi! I'm **Smart Bee AI** 🐝 — your intelligent email & calendar assistant.

Here's what I can do for you:
- 📥 **Summarize your inbox** — *"Summarize my emails"*
- 🔍 **Find unread emails** — *"Show me unread emails"*
- ✍️ **Draft smart replies** — *"Draft a reply to the latest email"*
- 📅 **Schedule meetings** — *"Book a meeting tomorrow at 3pm"*
- ⏰ **Set follow-ups** — *"Follow up with my client in 2 days"*
- 🗓️ **Today's schedule** — *"What's on my calendar today?"*

> 💡 **Tip:** I only analyze your **Primary** emails for AI insights. Promotions, Social, and Spam are shown in your inbox but not summarized unless you ask.

Just ask me anything naturally!`,
  timestamp: new Date(),
};

const QUICK_ACTIONS = [
  { emoji: "📥", label: "Summarize inbox", query: "Summarize my inbox", color: "from-amber-400/20 to-amber-600/10 border-amber-400/30 hover:border-amber-400/60" },
  { emoji: "🔍", label: "Unread emails", query: "Find all unread emails", color: "from-blue-400/20 to-blue-600/10 border-blue-400/30 hover:border-blue-400/60" },
  { emoji: "📅", label: "Today's schedule", query: "Show today's schedule", color: "from-purple-400/20 to-purple-600/10 border-purple-400/30 hover:border-purple-400/60" },
  { emoji: "✍️", label: "Draft a reply", query: "Draft a reply to the latest email", color: "from-green-400/20 to-green-600/10 border-green-400/30 hover:border-green-400/60" },
  { emoji: "⏰", label: "Schedule follow-up", query: "Schedule a follow-up email for tomorrow", color: "from-rose-400/20 to-rose-600/10 border-rose-400/30 hover:border-rose-400/60" },
  { emoji: "🗓️", label: "Book a meeting", query: "Schedule a meeting tomorrow at 11am", color: "from-teal-400/20 to-teal-600/10 border-teal-400/30 hover:border-teal-400/60" },
];

const CAPABILITIES = [
  { icon: Mail, label: "Email Management", desc: "Summarize & draft replies" },
  { icon: Calendar, label: "Calendar & Meetings", desc: "Schedule Google Meet" },
  { icon: Search, label: "Smart Search", desc: "Find emails by context" },
  { icon: FileText, label: "AI Summaries", desc: "Primary emails only" },
  { icon: Clock, label: "Follow-ups", desc: "Schedule future sends" },
  { icon: Sparkles, label: "Smart Insights", desc: "Priority detection" },
];

export function AIAssistantPage() {
  const [messages, setMessages] = useState<Message[]>([WELCOME_MESSAGE]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [copied, setCopied] = useState<string | null>(null);
  const [showCapabilities, setShowCapabilities] = useState(false);
  const [isHistoryLoaded, setIsHistoryLoaded] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Load chat history from backend on mount
  useEffect(() => {
    if (isHistoryLoaded) return;
    setIsHistoryLoaded(true);
    api.getChatHistory("ai_assistant_page", 30).then((history) => {
      if (history.length > 0) {
        const loaded: Message[] = history.map((h) => ({
          id: h.id,
          role: h.role as "user" | "assistant",
          content: h.content,
          timestamp: h.timestamp ? new Date(h.timestamp) : new Date(),
        }));
        setMessages([WELCOME_MESSAGE, ...loaded]);
      }
    }).catch(() => {
      // silently ignore - history not critical
    });
    inputRef.current?.focus();
  }, [isHistoryLoaded]);

  const sendMessage = async (text: string) => {
    if (!text.trim() || isTyping) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: "user",
      content: text,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsTyping(true);

    // Add a streaming placeholder
    const streamId = `ai-${Date.now()}`;
    setMessages((prev) => [...prev, {
      id: streamId,
      role: "assistant",
      content: "",
      timestamp: new Date(),
      isStreaming: true,
    }]);

    try {
      const data = await api.chat(text, "ai_assistant_page");
      setMessages((prev) => prev.map(m =>
        m.id === streamId
          ? { ...m, content: data.response, isStreaming: false }
          : m
      ));
    } catch {
      setMessages((prev) => prev.map(m =>
        m.id === streamId
          ? {
              ...m,
              content: "⚠️ Couldn't reach the AI engine. Please check if the backend is running on **port 8000**.",
              isError: true,
              isStreaming: false
            }
          : m
      ));
    } finally {
      setIsTyping(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(input);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  };

  const handleClear = async () => {
    setMessages([WELCOME_MESSAGE]);
    setInput("");
    inputRef.current?.focus();
    // Also clear server-side history
    try {
      await api.clearChatHistory("ai_assistant_page");
    } catch {
      // silently ignore
    }
  };

  const handleCopy = (content: string, id: string) => {
    navigator.clipboard.writeText(content).then(() => {
      setCopied(id);
      setTimeout(() => setCopied(null), 2000);
    });
  };

  const formatTime = (date: Date) =>
    date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

  const showSuggestions = messages.length <= 1 && !isTyping;

  return (
    <div className="flex gap-5 h-[calc(100vh-160px)] min-h-[600px]">
      {/* Left Panel: Chat */}
      <div className="flex-1 flex flex-col bg-white/80 backdrop-blur-xl rounded-3xl shadow-xl border border-gray-200/50 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100/80 bg-gradient-to-r from-amber-50/60 to-white shrink-0">
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="w-11 h-11 bg-gradient-to-br from-amber-400 to-amber-600 rounded-2xl flex items-center justify-center shadow-lg shadow-amber-500/30">
                <Bot className="w-5.5 h-5.5 text-white" />
              </div>
              <span className="absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 bg-green-500 rounded-full border-2 border-white animate-pulse" />
            </div>
            <div>
              <div className="font-bold text-gray-900 text-base">Smart Bee AI</div>
              <div className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 bg-green-500 rounded-full inline-block" />
                <span className="text-[11px] text-gray-500 font-medium">
                  {isTyping ? "Analyzing your request..." : "Online · Primary emails only"}
                </span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowCapabilities(!showCapabilities)}
              className="px-3 py-1.5 bg-amber-50 hover:bg-amber-100 text-amber-700 rounded-full text-xs font-semibold transition-all flex items-center gap-1 cursor-pointer border border-amber-200/60"
            >
              <Sparkles className="w-3 h-3" />
              Capabilities
            </button>
            <button
              onClick={handleClear}
              className="p-2 hover:bg-gray-100 rounded-full transition-colors cursor-pointer group"
              title="Clear chat"
            >
              <RotateCcw className="w-4 h-4 text-gray-400 group-hover:text-gray-600 transition-colors" />
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-5 py-5 space-y-5 scroll-smooth" style={{ scrollbarWidth: "thin", scrollbarColor: "#f59e0b20 transparent" }}>
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-3 ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              style={{ animation: "fadeSlideIn 0.25s ease-out" }}
            >
              {msg.role === "assistant" && (
                <div className="w-8 h-8 bg-gradient-to-br from-amber-400 to-amber-600 rounded-xl flex items-center justify-center shrink-0 mt-0.5 shadow-md shadow-amber-400/30">
                  <Bot className="w-4 h-4 text-white" />
                </div>
              )}
              <div className={`group max-w-[80%] flex flex-col gap-1.5 ${msg.role === "user" ? "items-end" : "items-start"}`}>
                <div
                  className={`rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-sm ${
                    msg.role === "user"
                      ? "bg-gradient-to-br from-[#1C1C1E] to-[#2d2d2f] text-white rounded-tr-sm"
                      : msg.isError
                      ? "bg-red-50 text-red-700 border border-red-100 rounded-tl-sm"
                      : "bg-gray-50/80 border border-gray-100 text-gray-800 rounded-tl-sm"
                  }`}
                >
                  {msg.isStreaming ? (
                    <div className="flex gap-1.5 items-center h-5">
                      {[0, 150, 300].map((delay) => (
                        <span
                          key={delay}
                          className="w-2 h-2 bg-amber-400 rounded-full animate-bounce"
                          style={{ animationDelay: `${delay}ms`, animationDuration: "1s" }}
                        />
                      ))}
                    </div>
                  ) : msg.role === "user" ? (
                    <span className="whitespace-pre-wrap">{msg.content}</span>
                  ) : (
                    <div className="prose-sm">{renderMarkdown(msg.content)}</div>
                  )}
                </div>
                <div className="flex items-center gap-2 px-1">
                  <span className="text-[10px] text-gray-400">{formatTime(msg.timestamp)}</span>
                  {msg.role === "assistant" && !msg.isStreaming && msg.content && (
                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button
                        onClick={() => handleCopy(msg.content, msg.id)}
                        className="p-1 hover:bg-gray-100 rounded-full cursor-pointer transition-colors"
                        title="Copy"
                      >
                        <Copy className="w-3 h-3 text-gray-400 hover:text-gray-600" />
                      </button>
                      {copied === msg.id && (
                        <span className="text-[10px] text-green-500 font-medium">Copied!</span>
                      )}
                      <button className="p-1 hover:bg-gray-100 rounded-full cursor-pointer transition-colors" title="Good response">
                        <ThumbsUp className="w-3 h-3 text-gray-400 hover:text-green-500" />
                      </button>
                      <button className="p-1 hover:bg-gray-100 rounded-full cursor-pointer transition-colors" title="Bad response">
                        <ThumbsDown className="w-3 h-3 text-gray-400 hover:text-red-500" />
                      </button>
                    </div>
                  )}
                </div>
              </div>
              {msg.role === "user" && (
                <div className="w-8 h-8 bg-gray-200 rounded-xl flex items-center justify-center shrink-0 mt-0.5">
                  <User className="w-4 h-4 text-gray-600" />
                </div>
              )}
            </div>
          ))}

          {/* Quick Action Suggestions */}
          {showSuggestions && (
            <div className="pt-2" style={{ animation: "fadeSlideIn 0.3s ease-out 0.2s both" }}>
              <div className="flex items-center gap-2 mb-3">
                <Zap className="w-3.5 h-3.5 text-amber-500" />
                <span className="text-[11px] text-gray-500 font-bold uppercase tracking-widest">Quick Actions</span>
              </div>
              <div className="grid grid-cols-2 gap-2">
                {QUICK_ACTIONS.map((action, idx) => (
                  <button
                    key={idx}
                    onClick={() => sendMessage(action.query)}
                    className={`flex items-center gap-2.5 px-3.5 py-3 bg-gradient-to-br ${action.color} text-gray-700 hover:text-gray-900 rounded-2xl border transition-all text-xs font-semibold shadow-sm hover:shadow-md cursor-pointer text-left`}
                  >
                    <span className="text-lg shrink-0">{action.emoji}</span>
                    <span className="truncate">{action.label}</span>
                    <ChevronRight className="w-3 h-3 text-gray-400 ml-auto shrink-0" />
                  </button>
                ))}
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <form
          onSubmit={handleSubmit}
          className="px-5 py-4 border-t border-gray-100/80 bg-white/95 backdrop-blur shrink-0"
        >
          <div className="flex gap-3 items-end bg-gray-50/80 border border-gray-200/80 rounded-2xl px-4 py-3 focus-within:border-amber-400/60 focus-within:ring-2 focus-within:ring-amber-400/20 transition-all">
            <textarea
              id="ai-assistant-input"
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask anything about your emails, calendar, or meetings..."
              className="flex-1 bg-transparent text-sm text-gray-800 placeholder:text-gray-400 resize-none focus:outline-none leading-relaxed"
              rows={1}
              disabled={isTyping}
              style={{ maxHeight: "120px", overflowY: "auto" }}
            />
            <button
              id="ai-assistant-send-btn"
              type="submit"
              disabled={!input.trim() || isTyping}
              className="w-9 h-9 bg-amber-500 hover:bg-amber-600 active:scale-95 rounded-xl flex items-center justify-center transition-all shrink-0 disabled:opacity-40 disabled:cursor-not-allowed shadow-md shadow-amber-500/30 cursor-pointer"
              aria-label="Send"
            >
              <Send className="w-4 h-4 text-white" />
            </button>
          </div>
          <div className="flex items-center justify-between mt-2 px-1">
            <p className="text-[10px] text-gray-400">
              Press <kbd className="bg-gray-100 px-1.5 py-0.5 rounded text-[9px] font-mono">Enter</kbd> to send · <kbd className="bg-gray-100 px-1.5 py-0.5 rounded text-[9px] font-mono">Shift+Enter</kbd> for new line
            </p>
            <p className="text-[10px] text-gray-400">Smart Bee AI · Only primary emails analyzed</p>
          </div>
        </form>
      </div>

      {/* Right Panel: Capabilities & Info */}
      <div className="w-72 flex flex-col gap-4 shrink-0">
        {/* Capabilities Card */}
        <div className="bg-white/80 backdrop-blur-xl rounded-3xl p-5 shadow-xl border border-gray-200/50">
          <div className="flex items-center gap-2 mb-4">
            <div className="w-7 h-7 bg-amber-500/10 rounded-lg flex items-center justify-center">
              <Sparkles className="w-3.5 h-3.5 text-amber-600" />
            </div>
            <h3 className="font-bold text-gray-900 text-sm">AI Capabilities</h3>
          </div>
          <div className="space-y-2.5">
            {CAPABILITIES.map((cap, idx) => {
              const CapIcon = cap.icon;
              return (
                <div key={idx} className="flex items-center gap-3 p-2 rounded-xl hover:bg-gray-50/80 transition-colors">
                  <div className="w-7 h-7 bg-gradient-to-br from-amber-100 to-amber-50 rounded-lg flex items-center justify-center shrink-0">
                    <CapIcon className="w-3.5 h-3.5 text-amber-600" />
                  </div>
                  <div>
                    <div className="text-xs font-semibold text-gray-800">{cap.label}</div>
                    <div className="text-[10px] text-gray-500">{cap.desc}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Tips Card */}
        <div className="bg-gradient-to-br from-amber-50 to-yellow-50 rounded-3xl p-5 border border-amber-200/40 shadow-lg">
          <div className="flex items-center gap-2 mb-3">
            <span className="text-base">💡</span>
            <h3 className="font-bold text-amber-800 text-sm">Pro Tips</h3>
          </div>
          <div className="space-y-2">
            {[
              "Say \"draft a reply\" to auto-write professional email responses",
              "Ask \"schedule a meeting with [email] tomorrow at 2pm\" to create Google Meet events",
              "Only primary emails are analyzed by AI — promotions/social are excluded",
              "Use natural language like \"what emails did I get today?\"",
            ].map((tip, idx) => (
              <div key={idx} className="flex items-start gap-2">
                <span className="text-amber-500 font-bold text-xs shrink-0 mt-0.5">→</span>
                <p className="text-[11px] text-amber-800/80 leading-relaxed">{tip}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Stats Card */}
        <div className="bg-white/80 backdrop-blur-xl rounded-3xl p-5 shadow-xl border border-gray-200/50">
          <div className="flex items-center gap-2 mb-3">
            <span className="text-base">📊</span>
            <h3 className="font-bold text-gray-900 text-sm">Session Stats</h3>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-gray-50 rounded-2xl p-3 text-center">
              <div className="text-xl font-bold text-amber-600">{messages.filter(m => m.role === "user").length}</div>
              <div className="text-[10px] text-gray-500 font-medium">Messages</div>
            </div>
            <div className="bg-gray-50 rounded-2xl p-3 text-center">
              <div className="text-xl font-bold text-green-600">{messages.filter(m => m.role === "assistant" && !m.isError && !m.isStreaming && m.content.length > 50).length}</div>
              <div className="text-[10px] text-gray-500 font-medium">AI Responses</div>
            </div>
          </div>
        </div>
      </div>

      {/* Global animations */}
      <style>{`
        @keyframes fadeSlideIn {
          from { opacity: 0; transform: translateY(10px); }
          to   { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
}
