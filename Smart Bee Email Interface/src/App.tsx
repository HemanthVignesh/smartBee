import { Inbox } from "./components/Inbox";
import { useState } from "react";
import { ScheduledEmails } from "./components/ScheduledEmails";
import { ScheduledMeetings } from "./components/ScheduledMeetings";
import { ChatBot } from "./components/ChatBot";
import { HexagonPattern } from "./components/HexagonPattern";
import { StatsBar } from "./components/StatsBar";
import { AIInsights } from "./components/AIInsights";
import { Sidebar } from "./components/Sidebar";
import { Analytics } from "./components/Analytics";


import logo from "./assets/SmartBee_logo.png";
import bgImage from "./assets/SmartBee_bg.png";

export default function App() {
  const [currentView, setCurrentView] = useState("dashboard");

  return (
    <div className="size-full bg-slate-50 relative overflow-hidden">
      {/* Background Image */}
      <div 
        className="absolute inset-0 opacity-5 pointer-events-none mix-blend-multiply bg-repeat"
        style={{ backgroundImage: `url(${bgImage})`, backgroundSize: '400px' }}
      ></div>
      
      {/* Honeycomb background pattern */}
      <HexagonPattern />
      
      {/* Watermark at center */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-0">
      </div>
      
      {/* Main container */}
      <div className="relative z-10 size-full flex">
        {/* Sidebar */}
        <Sidebar currentView={currentView} onViewChange={setCurrentView} />

        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Header */}
          <header className="bg-white/90 backdrop-blur-md border-b border-gray-200 px-6 py-4 shadow-sm">
            <div className="flex items-center gap-4">
              <img src={logo} alt="Smart Bee Logo" className="w-10 h-10 object-contain" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Smart Bee</h1>
                <p className="text-sm text-gray-500">Intelligent Email Management</p>
              </div>
            </div>
          </header>

          {/* Main content */}
          <main className="flex-1 overflow-y-auto p-6">
            <div className="max-w-7xl mx-auto space-y-6">
              {currentView === "dashboard" && (
                <>
                  {/* Stats Bar */}
                  <StatsBar />
                  
                  {/* AI Insights - Full Width */}
                  <AIInsights />
                  
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Scheduled Emails */}
                    <div className="bg-white/90 backdrop-blur-md rounded-2xl p-6 shadow-lg border border-gray-200 hover:shadow-xl hover:border-[#FFC107]/50 transition-all duration-300">
                      <ScheduledEmails />
                    </div>

                    {/* Scheduled Meetings */}
                    <div className="bg-white/90 backdrop-blur-md rounded-2xl p-6 shadow-lg border border-gray-200 hover:shadow-xl hover:border-[#FFC107]/50 transition-all duration-300">
                      <ScheduledMeetings />
                    </div>
                  </div>
                </>
              )}

              {currentView === "analytics" && <Analytics />}
              
              {currentView === "inbox" && <Inbox />}
              
              {currentView === "scheduled" && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div className="bg-white/90 backdrop-blur-md rounded-2xl p-6 shadow-lg border border-gray-200">
                    <ScheduledEmails />
                  </div>
                  <div className="bg-white/90 backdrop-blur-md rounded-2xl p-6 shadow-lg border border-gray-200">
                    <ScheduledMeetings />
                  </div>
                </div>
              )}
              
              {currentView === "ai-assistant" && (
                <div className="bg-white/90 backdrop-blur-md rounded-2xl p-6 shadow-lg border border-gray-200">
                  <h2 className="text-2xl text-gray-900 mb-4">🤖 AI Assistant</h2>
                  <p className="text-gray-600">Use the floating bee button in the bottom-right corner to interact with the AI Assistant!</p>
                </div>
              )}
              
              {currentView === "settings" && (
                <div className="bg-white/90 backdrop-blur-md rounded-2xl p-6 shadow-lg border border-gray-200">
                  <h2 className="text-2xl text-gray-900 mb-4">⚙️ Settings</h2>
                  <p className="text-gray-600">Settings view coming soon...</p>
                </div>
              )}
            </div>
          </main>
        </div>
      </div>

      {/* Floating AI Chatbot */}
      <ChatBot />
    </div>
  );
}
