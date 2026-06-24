import { useState, useRef, useEffect, useCallback } from "react";
import { Send, Bot, User, X, Sparkles, RotateCcw, ChevronDown, Zap } from "lucide-react";
import { api } from "../api/client";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  isError?: boolean;
}

/** Lightweight inline Markdown renderer — no extra dependencies */
function renderMarkdown(text: string): React.ReactNode[] {
  const lines = text.split("\n");
  const result: React.ReactNode[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    // Horizontal rule
    if (/^---+$/.test(line.trim())) {
      result.push(<hr key={i} style={{ border: "none", borderTop: "1px solid #e5e7eb", margin: "6px 0" }} />);
      i++;
      continue;
    }

    // Code block
    if (line.startsWith("```")) {
      const codeLines: string[] = [];
      i++;
      while (i < lines.length && !lines[i].startsWith("```")) {
        codeLines.push(lines[i]);
        i++;
      }
      result.push(
        <pre key={i} style={{
          background: "#1c1c1e",
          color: "#f8f8f2",
          borderRadius: 8,
          padding: "10px 14px",
          overflowX: "auto",
          fontSize: 12,
          margin: "6px 0",
          fontFamily: "monospace"
        }}>
          {codeLines.join("\n")}
        </pre>
      );
      i++;
      continue;
    }

    // Unordered list
    if (/^[*\-•]\s/.test(line.trim())) {
      const listItems: string[] = [];
      while (i < lines.length && /^[*\-•]\s/.test(lines[i].trim())) {
        listItems.push(lines[i].trim().replace(/^[*\-•]\s/, ""));
        i++;
      }
      result.push(
        <ul key={i} style={{ paddingLeft: 18, margin: "4px 0", listStyleType: "disc" }}>
          {listItems.map((item, idx) => (
            <li key={idx} style={{ marginBottom: 3, lineHeight: 1.5 }}>
              {inlineMarkdown(item)}
            </li>
          ))}
        </ul>
      );
      continue;
    }

    // Ordered list
    if (/^\d+\.\s/.test(line.trim())) {
      const listItems: string[] = [];
      while (i < lines.length && /^\d+\.\s/.test(lines[i].trim())) {
        listItems.push(lines[i].trim().replace(/^\d+\.\s/, ""));
        i++;
      }
      result.push(
        <ol key={i} style={{ paddingLeft: 18, margin: "4px 0" }}>
          {listItems.map((item, idx) => (
            <li key={idx} style={{ marginBottom: 3, lineHeight: 1.5 }}>
              {inlineMarkdown(item)}
            </li>
          ))}
        </ol>
      );
      continue;
    }

    // Empty line
    if (line.trim() === "") {
      result.push(<div key={i} style={{ height: 6 }} />);
      i++;
      continue;
    }

    // Normal paragraph
    result.push(
      <p key={i} style={{ margin: "2px 0", lineHeight: 1.6 }}>
        {inlineMarkdown(line)}
      </p>
    );
    i++;
  }

  return result;
}

/** Process inline markdown: bold, italic, code, links, emojis */
function inlineMarkdown(text: string): React.ReactNode {
  // Split on bold (**text**), italic (*text*), code (`text`), links [text](url)
  const parts: React.ReactNode[] = [];
  const regex = /(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|\[([^\]]+)\]\(([^)]+)\))/g;
  let lastIndex = 0;
  let match;

  while ((match = regex.exec(text)) !== null) {
    // Plain text before
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }

    const full = match[0];
    if (full.startsWith("**")) {
      parts.push(<strong key={match.index} style={{ fontWeight: 600 }}>{full.slice(2, -2)}</strong>);
    } else if (full.startsWith("*")) {
      parts.push(<em key={match.index}>{full.slice(1, -1)}</em>);
    } else if (full.startsWith("`")) {
      parts.push(
        <code key={match.index} style={{
          background: "rgba(0,0,0,0.08)",
          borderRadius: 4,
          padding: "1px 5px",
          fontSize: "0.85em",
          fontFamily: "monospace",
          color: "#d63384"
        }}>
          {full.slice(1, -1)}
        </code>
      );
    } else if (full.startsWith("[")) {
      // Link
      const linkText = match[2];
      const linkUrl = match[3];
      parts.push(
        <a key={match.index} href={linkUrl} target="_blank" rel="noopener noreferrer" style={{
          color: "#f59e0b",
          textDecoration: "underline",
          fontWeight: 500
        }}>
          {linkText}
        </a>
      );
    }

    lastIndex = match.index + full.length;
  }

  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }

  return parts.length > 0 ? <>{parts}</> : text;
}

const WELCOME_MESSAGE: Message = {
  id: "welcome-1",
  role: "assistant",
  content: "Hi! I'm **Smart Bee AI** 🐝\n\nI can help you manage your inbox intelligently:\n- 📥 Find and summarize your emails\n- ✍️ Draft smart replies\n- 📅 Schedule meetings & follow-ups\n- 🎯 Show today's calendar\n\nJust ask me anything naturally!",
  timestamp: new Date(),
};

const QUICK_ACTIONS = [
  { emoji: "📥", label: "Summarize inbox", query: "Summarize my inbox" },
  { emoji: "🔍", label: "Unread emails", query: "Find all unread emails" },
  { emoji: "📅", label: "Today's schedule", query: "Show today's schedule" },
  { emoji: "✍️", label: "Draft a reply", query: "Draft a reply to the latest email" },
  { emoji: "⏰", label: "Schedule follow-up", query: "Schedule a follow up email" },
  { emoji: "🗓️", label: "Book a meeting", query: "Schedule a meeting tomorrow at 11am" },
];

export function ChatBot() {
  const [messages, setMessages] = useState<Message[]>([WELCOME_MESSAGE]);
  const [input, setInput] = useState("");
  const [isOpen, setIsOpen] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Load conversation history on mount
  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const history = await api.getChatHistory("user_session_1");
        if (history && history.length > 0) {
          const formatted = history.map((msg: any) => ({
            id: msg.id,
            role: msg.role as "user" | "assistant",
            content: msg.content,
            timestamp: msg.timestamp ? new Date(msg.timestamp) : new Date()
          }));
          setMessages([WELCOME_MESSAGE, ...formatted]);
        }
      } catch (err) {
        console.error("Failed to load chat history:", err);
      }
    };
    fetchHistory();
  }, []);

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 100);
      setUnreadCount(0);
    }
  }, [isOpen]);

  const sendMessage = async (text: string) => {
    if (!text.trim()) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: "user",
      content: text,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsTyping(true);

    try {
      const data = await api.chat(text, "user_session_1");
      const assistantMessage: Message = {
        id: `ai-${Date.now()}`,
        role: "assistant",
        content: data.response,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
      if (!isOpen) setUnreadCount((c) => c + 1);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          role: "assistant",
          content: "⚠️ Couldn't reach the AI engine. Please check if the backend is running.",
          timestamp: new Date(),
          isError: true,
        },
      ]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(input);
  };

  const handleClearChat = async () => {
    try {
      await api.clearChatHistory("user_session_1");
    } catch (err) {
      console.error("Failed to clear chat history on server:", err);
    }
    setMessages([WELCOME_MESSAGE]);
    setInput("");
  };

  const formatTime = (date: Date) =>
    date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

  const showSuggestions = messages.length <= 1 && !isTyping;

  return (
    <>
      {/* Floating Trigger Button */}
      {!isOpen && (
        <button
          id="chatbot-trigger-btn"
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 w-14 h-14 bg-amber-500 rounded-full shadow-[0_8px_32px_rgba(245,158,11,0.45)] hover:shadow-[0_8px_40px_rgba(245,158,11,0.65)] hover:scale-110 active:scale-95 transition-all duration-300 flex items-center justify-center z-50 cursor-pointer"
          aria-label="Open Smart Bee AI Chat"
          title="Smart Bee AI"
          style={{ animation: "subtlePulse 3s ease-in-out infinite" }}
        >
          <Bot className="w-6 h-6 text-black" />
          {/* Online indicator */}
          <span className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-green-500 rounded-full border-2 border-white flex items-center justify-center">
            <Sparkles className="w-2 h-2 text-white" />
          </span>
          {/* Unread badge */}
          {unreadCount > 0 && (
            <span className="absolute -top-1 -left-1 min-w-5 h-5 bg-red-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center px-1">
              {unreadCount}
            </span>
          )}
        </button>
      )}

      {/* Chat Panel */}
      {isOpen && (
        <div
          id="chatbot-panel"
          className="fixed bottom-4 right-4 left-4 sm:left-auto sm:right-6 sm:bottom-6 sm:w-[440px] bg-white border border-gray-200/60 rounded-3xl shadow-[0_24px_80px_rgba(0,0,0,0.18)] flex flex-col z-50 overflow-hidden"
          style={{
            height: "clamp(500px, 80vh, 680px)",
            animation: "slideUpFade 0.25s cubic-bezier(0.22,1,0.36,1)"
          }}
        >
          {/* Header */}
          <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100 bg-gradient-to-r from-amber-50/80 to-white shrink-0">
            <div className="flex items-center gap-3">
              <div className="relative">
                <div className="w-10 h-10 bg-amber-500 rounded-2xl flex items-center justify-center shadow-md shadow-amber-500/30">
                  <Bot className="w-5 h-5 text-black" />
                </div>
                <span className="absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 bg-green-500 rounded-full border-2 border-white" />
              </div>
              <div>
                <div className="font-semibold text-gray-900 text-sm leading-tight">Smart Bee AI</div>
                <div className="flex items-center gap-1.5 mt-0.5">
                  <span className="w-1.5 h-1.5 bg-green-500 rounded-full inline-block animate-pulse" />
                  <span className="text-[11px] text-gray-500 font-medium">
                    {isTyping ? "Thinking..." : "Online · Ready to help"}
                  </span>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-1">
              <button
                onClick={handleClearChat}
                className="p-2 hover:bg-gray-100 rounded-full transition-colors cursor-pointer"
                title="Clear chat"
                aria-label="Clear chat history"
              >
                <RotateCcw className="w-4 h-4 text-gray-400" />
              </button>
              <button
                onClick={() => setIsOpen(false)}
                className="p-2 hover:bg-gray-100 rounded-full transition-colors cursor-pointer"
                aria-label="Close chat"
              >
                <X className="w-4.5 h-4.5 text-gray-500" />
              </button>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4 scroll-smooth">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex gap-2.5 ${msg.role === "user" ? "justify-end" : "justify-start"} animate-in fade-in-0 slide-in-from-bottom-2 duration-200`}
              >
                {msg.role === "assistant" && (
                  <div className="w-7 h-7 bg-amber-500/10 rounded-full flex items-center justify-center shrink-0 mt-0.5">
                    <Bot className="w-3.5 h-3.5 text-amber-600" />
                  </div>
                )}
                <div className={`group max-w-[82%] flex flex-col gap-1 ${msg.role === "user" ? "items-end" : "items-start"}`}>
                  <div
                    className={`rounded-2xl px-4 py-2.5 text-sm leading-relaxed shadow-sm ${
                      msg.role === "user"
                        ? "bg-[#1C1C1E] text-white rounded-tr-sm"
                        : msg.isError
                        ? "bg-red-50 text-red-700 border border-red-100 rounded-tl-sm"
                        : "bg-[#F5F5F7] text-gray-900 rounded-tl-sm"
                    }`}
                  >
                    {msg.role === "user" ? (
                      <span className="whitespace-pre-wrap">{msg.content}</span>
                    ) : (
                      <div className="prose-sm">{renderMarkdown(msg.content)}</div>
                    )}
                  </div>
                  <span className="text-[10px] text-gray-400 px-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    {formatTime(msg.timestamp)}
                  </span>
                </div>
                {msg.role === "user" && (
                  <div className="w-7 h-7 bg-gray-200 rounded-full flex items-center justify-center shrink-0 mt-0.5">
                    <User className="w-3.5 h-3.5 text-gray-600" />
                  </div>
                )}
              </div>
            ))}

            {/* Typing indicator */}
            {isTyping && (
              <div className="flex gap-2.5 justify-start animate-in fade-in-0 slide-in-from-bottom-2">
                <div className="w-7 h-7 bg-amber-500/10 rounded-full flex items-center justify-center shrink-0">
                  <Bot className="w-3.5 h-3.5 text-amber-600" />
                </div>
                <div className="bg-[#F5F5F7] rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
                  <div className="flex gap-1.5 items-center h-3">
                    {[0, 150, 300].map((delay) => (
                      <span
                        key={delay}
                        className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                        style={{ animationDelay: `${delay}ms`, animationDuration: "1s" }}
                      />
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Quick Action Suggestions */}
            {showSuggestions && (
              <div className="pt-2 animate-in fade-in-0 duration-300">
                <div className="flex items-center gap-2 mb-3">
                  <Zap className="w-3 h-3 text-amber-500" />
                  <span className="text-[11px] text-gray-400 font-semibold uppercase tracking-wide">Quick Actions</span>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  {QUICK_ACTIONS.map((action, idx) => (
                    <button
                      key={idx}
                      onClick={() => sendMessage(action.query)}
                      className="flex items-center gap-2 px-3 py-2.5 bg-white hover:bg-amber-50 text-gray-700 hover:text-amber-900 rounded-xl border border-gray-200 hover:border-amber-300 transition-all text-xs font-medium shadow-sm hover:shadow-md cursor-pointer text-left"
                    >
                      <span className="text-base shrink-0">{action.emoji}</span>
                      <span className="truncate">{action.label}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Scroll to bottom hint (shows when scrolled up) */}

          {/* Input Area */}
          <form
            onSubmit={handleSubmit}
            className="px-4 py-3 border-t border-gray-100 bg-white/90 backdrop-blur shrink-0"
          >
            <div className="flex gap-2 items-end">
              <input
                id="chatbot-input"
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask anything about your emails..."
                className="flex-1 px-4 py-2.5 border border-gray-200 rounded-full focus:outline-none focus:ring-2 focus:ring-amber-400/50 focus:border-amber-400 text-sm bg-gray-50 focus:bg-white transition-all text-gray-900 placeholder:text-gray-400"
                disabled={isTyping}
                autoComplete="off"
              />
              <button
                id="chatbot-send-btn"
                type="submit"
                disabled={!input.trim() || isTyping}
                className="w-10 h-10 bg-amber-500 hover:bg-amber-600 active:scale-95 rounded-full flex items-center justify-center transition-all shrink-0 disabled:opacity-40 disabled:cursor-not-allowed shadow-md shadow-amber-500/20 cursor-pointer"
                aria-label="Send message"
              >
                <Send className="w-4 h-4 text-black" />
              </button>
            </div>
            <p className="text-[10px] text-gray-400 text-center mt-2">
              Smart Bee AI · Only primary emails are analyzed
            </p>
          </form>
        </div>
      )}

      {/* Global animations */}
      <style>{`
        @keyframes subtlePulse {
          0%, 100% { box-shadow: 0 8px 32px rgba(245,158,11,0.45); }
          50% { box-shadow: 0 8px 48px rgba(245,158,11,0.7); }
        }
        @keyframes slideUpFade {
          from { opacity: 0; transform: translateY(20px) scale(0.97); }
          to   { opacity: 1; transform: translateY(0) scale(1); }
        }
      `}</style>
    </>
  );
}