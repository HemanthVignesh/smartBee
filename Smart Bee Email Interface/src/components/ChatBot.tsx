import { useState, useRef, useEffect } from "react";
import { Send, Bot, User, X, Sparkles } from "lucide-react";
import { analyzeEmail } from "../api/analyzeEmail";



interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

const initialMessages: Message[] = [
  {
    id: "1",
    role: "assistant",
    content: "Hi! I'm your Smart Bee assistant. I can help you schedule emails and meetings. Just tell me what you need!",
    timestamp: new Date()
  }
];

const quickSuggestions = [
  "✉️ Summarize my inbox",
  "📅 Schedule a follow-up",
  "✍️ Draft reply to John",
  "🔍 Find unread emails",
  "⏰ Show today's schedule"
];

export function ChatBot() {
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [input, setInput] = useState("");
  const [isOpen, setIsOpen] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
  
    const userText = input;
  
    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: userText,
      timestamp: new Date(),
    };
  
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsTyping(true);
    setShowSuggestions(false);
  
    try {
      const aiResult = await analyzeEmail(userText);
  
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: 
          `🧠 Intent: ${aiResult.intent}\n` +
          `⚡ Priority: ${aiResult.priority}\n\n` +
          `${aiResult.suggested_reply}`,
        timestamp: new Date(),
      };
  
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 2).toString(),
        role: "assistant",
        content: "⚠️ Sorry, I couldn't reach the AI engine. Please try again.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    setInput(suggestion.substring(2).trim()); // Remove emoji
    setShowSuggestions(false);
  };

  return (
    <>
      {/* Floating Bee Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 w-16 h-16 bg-gradient-to-br from-[#FFC107] to-[#FFB300] rounded-full shadow-2xl hover:shadow-[#FFC107]/50 hover:scale-110 transition-all duration-300 flex items-center justify-center group animate-bounce"
          style={{ animationDuration: "3s" }}
        >
          <Bot className="w-5 h-5 text-yellow-500" />

          <div className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full flex items-center justify-center">
            <Sparkles className="w-2.5 h-2.5 text-white" />
          </div>
        </button>
      )}

      {/* Expanded Chat Panel */}
      {isOpen && (
        <div className="fixed bottom-6 right-6 w-[420px] h-[650px] bg-white/95 backdrop-blur-xl border-2 border-[#FFC107] rounded-3xl shadow-2xl flex flex-col animate-in slide-in-from-bottom-4 duration-300">
          {/* Header */}
          <div className="flex items-center justify-between p-5 border-b border-gray-200 bg-gradient-to-r from-[#FFC107] to-[#FFB300] rounded-t-3xl">
            <div className="flex items-center gap-3">
              <div className="relative">
              <Bot className="w-5 h-5 text-yellow-500" />

                <div className="absolute -bottom-1 -right-1 w-3 h-3 bg-green-500 rounded-full border-2 border-white"></div>
              </div>
              <div>
                <div className="text-black">Smart Bee AI</div>
                <div className="text-xs text-black/70">Your intelligent assistant</div>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="p-2 hover:bg-black/10 rounded-full transition-colors"
            >
              <X className="w-5 h-5 text-black" />
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-5 space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex gap-3 ${message.role === "user" ? "justify-end" : "justify-start"}`}
              >
                {message.role === "assistant" && (
                  <div className="w-8 h-8 bg-gradient-to-br from-[#FFC107] to-[#FFB300] rounded-full flex items-center justify-center shrink-0">
                    <Bot className="w-5 h-5 text-black" />
                  </div>
                )}
                <div
                  className={`max-w-[75%] rounded-2xl px-4 py-3 ${
                    message.role === "user"
                      ? "bg-gradient-to-br from-[#1E1E1E] to-[#424242] text-white"
                      : "bg-gray-100 text-gray-900"
                  }`}
                >
                  <div className="text-sm whitespace-pre-line">{message.content}</div>
                </div>
                {message.role === "user" && (
                  <div className="w-8 h-8 bg-gradient-to-br from-gray-700 to-gray-900 rounded-full flex items-center justify-center shrink-0">
                    <User className="w-5 h-5 text-white" />
                  </div>
                )}
              </div>
            ))}
            {isTyping && (
              <div className="flex gap-3 justify-start">
                <div className="w-8 h-8 bg-gradient-to-br from-[#FFC107] to-[#FFB300] rounded-full flex items-center justify-center shrink-0">
                  <Bot className="w-5 h-5 text-black" />
                </div>
                <div className="bg-gray-100 rounded-2xl px-4 py-3">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }}></div>
                  </div>
                </div>
              </div>
            )}
            
            {/* Quick Suggestions */}
            {showSuggestions && messages.length <= 1 && (
              <div className="space-y-2">
                <div className="text-xs text-gray-500 text-center mb-2">Quick actions:</div>
                <div className="flex flex-wrap gap-2 justify-center">
                  {quickSuggestions.map((suggestion, index) => (
                    <button
                      key={index}
                      onClick={() => handleSuggestionClick(suggestion)}
                      className="text-xs px-3 py-2 bg-gradient-to-r from-[#FFF8E1] to-[#FFECB3] hover:from-[#FFC107] hover:to-[#FFB300] text-gray-800 hover:text-black rounded-full border border-[#FFC107]/30 transition-all hover:scale-105"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <form onSubmit={handleSubmit} className="p-5 border-t border-gray-200 bg-white/80 backdrop-blur rounded-b-3xl">
            <div className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask me anything..."
                className="flex-1 px-4 py-3 border-2 border-gray-200 rounded-full focus:outline-none focus:ring-2 focus:ring-[#FFC107] focus:border-transparent text-sm bg-white"
              />
              <button
                type="submit"
                className="w-12 h-12 bg-gradient-to-br from-[#FFC107] to-[#FFB300] hover:from-[#FFB300] hover:to-[#FFC107] rounded-full flex items-center justify-center transition-all shrink-0 disabled:opacity-50 disabled:cursor-not-allowed hover:scale-110 shadow-lg"
                disabled={!input.trim()}
              >
                <Send className="w-5 h-5 text-black" />
              </button>
            </div>
          </form>
        </div>
      )}
    </>
  );
}