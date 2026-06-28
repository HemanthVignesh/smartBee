import { useState, useEffect } from "react";
import { Menu, LogOut, User as UserIcon } from "lucide-react";

import { Inbox } from "./components/Inbox";
import { ScheduledEmails } from "./components/ScheduledEmails";
import { ScheduledMeetings } from "./components/ScheduledMeetings";
import { ChatBot } from "./components/ChatBot";
import { HexagonPattern } from "./components/HexagonPattern";
import { StatsBar } from "./components/StatsBar";
import { AIInsights } from "./components/AIInsights";
import { Sidebar } from "./components/Sidebar";
import { Analytics } from "./components/Analytics";
import { SettingsComponent } from "./components/Settings";
import { AIAssistantPage } from "./components/AIAssistantPage";

import { AuthProvider, useAuth } from "./auth/AuthContext";
import { LoginPage } from "./auth/LoginPage";
import { api, SmartBeeAPI } from "./api/client";

import logo from "./assets/SmartBee_logo.png";
import bgImage from "./assets/SmartBee_bg.png";

// ─── Wire auth into the API singleton ────────────────────────────────────────
// This lives outside the component so it only runs once.
// SmartBeeAPI.getToken / refreshToken are static setters set below.

function AppShell() {
  const { user, token, loading, logout, refreshToken } = useAuth();
  const [currentView, setCurrentView] = useState("dashboard");
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [syncing, setSyncing] = useState(false);

  // Keep the API singleton's token getter in sync with React state
  useEffect(() => {
    SmartBeeAPI.getToken = () => token;
    SmartBeeAPI.refreshToken = refreshToken;
  }, [token, refreshToken]);

  // ── While the initial /refresh probe is running, show a spinner ──────────
  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <img src={logo} alt="SmartBee" className="w-12 h-12 object-contain animate-pulse" />
          <p className="text-sm text-gray-400 font-medium">Loading…</p>
        </div>
      </div>
    );
  }

  // ── Not logged in → show the login / register page ───────────────────────
  if (!user) {
    return <LoginPage />;
  }

  // ── Authenticated → show the full app ────────────────────────────────────
  return (
    <div className="size-full bg-slate-50 relative overflow-hidden">
      <div
        className="absolute inset-0 opacity-5 pointer-events-none mix-blend-multiply bg-repeat"
        style={{ backgroundImage: `url(${bgImage})`, backgroundSize: "400px" }}
      />
      <HexagonPattern />

      <div className="relative z-10 size-full flex">
        <Sidebar
          currentView={currentView}
          onViewChange={(view) => {
            setCurrentView(view);
            setIsSidebarOpen(false);
          }}
          isOpen={isSidebarOpen}
          onClose={() => setIsSidebarOpen(false)}
        />

        {isSidebarOpen && (
          <div
            className="fixed inset-0 bg-black/20 backdrop-blur-sm z-40 lg:hidden transition-opacity duration-300"
            onClick={() => setIsSidebarOpen(false)}
          />
        )}

        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Header */}
          <header className="bg-white/80 backdrop-blur-md border-b border-gray-200/80 px-6 py-4 shadow-sm">
            <div className="flex items-center justify-between w-full">
              <div className="flex items-center gap-4">
                <button
                  onClick={() => setIsSidebarOpen(true)}
                  className="lg:hidden p-2 -ml-2 rounded-xl hover:bg-gray-100 active:bg-gray-200 transition duration-200 cursor-pointer"
                  aria-label="Open Menu"
                >
                  <Menu className="w-5 h-5 text-gray-700" />
                </button>
                <img src={logo} alt="Smart Bee Logo" className="w-10 h-10 object-contain" />
                <div>
                  <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Smart Bee</h1>
                  <p className="text-sm text-gray-500">Intelligent Email Management</p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                {/* Sync Gmail */}
                <button
                  onClick={async () => {
                    try {
                      setSyncing(true);
                      const res = await api.syncGmail();
                      if (res.status === "not_configured") {
                        alert(
                          "Gmail not configured yet.\n\n" +
                            "1. Go to Google Cloud Console\n" +
                            "2. Create OAuth2 credentials\n" +
                            "3. Download credentials.json\n" +
                            "4. Place it in Backend_SB/\n" +
                            "5. Restart the server\n\n" +
                            res.message
                        );
                      } else if (res.new_emails > 0) {
                        alert(`✅ Synced ${res.new_emails} new email(s) from Gmail!`);
                        window.location.reload();
                      } else {
                        alert("✅ Gmail is up to date — no new emails.");
                      }
                    } catch (err: any) {
                      alert("❌ Sync failed: " + err.message);
                    } finally {
                      setSyncing(false);
                    }
                  }}
                  disabled={syncing}
                  className="px-4 py-2 bg-gradient-to-r from-amber-500 to-yellow-500 hover:from-amber-600 hover:to-yellow-600 disabled:opacity-60 text-black font-semibold rounded-xl shadow-md hover:shadow-lg transition duration-200 flex items-center gap-2 text-sm cursor-pointer"
                >
                  <span>📬</span> {syncing ? "Syncing…" : "Sync Gmail"}
                </button>

                {/* User badge + logout */}
                <div className="flex items-center gap-2 pl-3 border-l border-gray-200">
                  <div className="flex items-center gap-2 bg-gray-100 rounded-xl px-3 py-2">
                    <UserIcon className="w-4 h-4 text-gray-500" />
                    <span className="text-xs font-semibold text-gray-700 max-w-[120px] truncate">
                      {user.display_name || user.email}
                    </span>
                  </div>
                  <button
                    onClick={logout}
                    title="Sign out"
                    className="p-2 rounded-xl hover:bg-red-50 hover:text-red-600 text-gray-400 transition cursor-pointer"
                  >
                    <LogOut className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          </header>

          {/* Main content */}
          <main className="flex-1 overflow-y-auto p-6">
            <div className="max-w-7xl mx-auto space-y-6">
              {currentView === "dashboard" && (
                <>
                  <StatsBar />
                  <AIInsights />
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div className="bg-white/80 backdrop-blur-xl rounded-3xl p-6 shadow-xl border border-gray-200/50 hover:shadow-2xl transition-all duration-300">
                      <ScheduledEmails />
                    </div>
                    <div className="bg-white/80 backdrop-blur-xl rounded-3xl p-6 shadow-xl border border-gray-200/50 hover:shadow-2xl transition-all duration-300">
                      <ScheduledMeetings />
                    </div>
                  </div>
                </>
              )}
              {currentView === "analytics"   && <Analytics />}
              {currentView === "inbox"        && <Inbox />}
              {currentView === "scheduled"    && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div className="bg-white/80 backdrop-blur-xl rounded-3xl p-6 shadow-xl border border-gray-200/50 hover:shadow-2xl transition-all duration-300">
                    <ScheduledEmails />
                  </div>
                  <div className="bg-white/80 backdrop-blur-xl rounded-3xl p-6 shadow-xl border border-gray-200/50 hover:shadow-2xl transition-all duration-300">
                    <ScheduledMeetings />
                  </div>
                </div>
              )}
              {currentView === "ai-assistant" && <AIAssistantPage />}
              {currentView === "settings"     && <SettingsComponent />}
            </div>
          </main>
        </div>
      </div>

      <ChatBot />
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppShell />
    </AuthProvider>
  );
}
