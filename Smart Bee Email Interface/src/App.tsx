/**
 * src/App.tsx — UPDATED with authentication
 *
 * Changes:
 *  • Wrapped in <AuthProvider>
 *  • /auth/callback route renders <AuthCallback>
 *  • Unauthenticated users see <LoginPage> (no redirect loop — simple conditional)
 *  • Header gains user avatar + name + logout button
 */

import { useState } from "react";
import { Menu, LogOut } from "lucide-react";

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

// ── Auth ──────────────────────────────────────────────────────────────────────
import { AuthProvider, useAuth } from "./auth/AuthContext";
import { LoginPage } from "./auth/LoginPage";
import { AuthCallback } from "./auth/AuthCallback";

import logo from "./assets/SmartBee_logo.png";
import api from "./api/client";

// ── Inner app (requires auth) ─────────────────────────────────────────────────

function AppContent() {
  const { user, isLoading, isAuthenticated, logout } = useAuth();
  const [currentView, setCurrentView] = useState("dashboard");
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  // ── Handle /auth/callback regardless of auth state ────────────────────────
  if (window.location.pathname === "/auth/callback") {
    return <AuthCallback />;
  }

  // ── While validating stored token ─────────────────────────────────────────
  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 border-4 border-amber-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-xs font-semibold text-gray-500">Loading Smart Bee…</p>
        </div>
      </div>
    );
  }

  // ── Not signed in ─────────────────────────────────────────────────────────
  if (!isAuthenticated) {
    return <LoginPage />;
  }

  // ── Authenticated app ─────────────────────────────────────────────────────
  return (
    <div className="size-full bg-slate-50 relative overflow-hidden">
      {/* Background */}
      <HexagonPattern />

      <div className="relative z-10 size-full flex">
        {/* Sidebar */}
        <Sidebar
          currentView={currentView}
          onViewChange={(view) => {
            setCurrentView(view);
            setIsSidebarOpen(false);
          }}
          isOpen={isSidebarOpen}
          onClose={() => setIsSidebarOpen(false)}
        />

        {/* Mobile backdrop */}
        {isSidebarOpen && (
          <div
            className="fixed inset-0 bg-black/20 backdrop-blur-sm z-40 lg:hidden"
            onClick={() => setIsSidebarOpen(false)}
          />
        )}

        <div className="flex-1 flex flex-col overflow-hidden">
          {/* ── Header ─────────────────────────────────────────────────────── */}
          <header className="bg-white/80 backdrop-blur-md border-b border-gray-200/80 px-6 py-4 shadow-sm">
            <div className="flex items-center justify-between w-full">
              {/* Left: hamburger + logo */}
              <div className="flex items-center gap-4">
                <button
                  onClick={() => setIsSidebarOpen(true)}
                  className="lg:hidden p-2 -ml-2 rounded-xl hover:bg-gray-100 transition cursor-pointer"
                  aria-label="Open Menu"
                >
                  <Menu className="w-5 h-5 text-gray-700" />
                </button>
                <img src={logo} alt="Smart Bee" className="w-10 h-10 object-contain" />
                <div>
                  <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Smart Bee</h1>
                  <p className="text-sm text-gray-500">Intelligent Email Management</p>
                </div>
              </div>

              {/* Right: Sync + User avatar */}
              <div className="flex items-center gap-3">
                {/* Sync Gmail */}
                <button
                  onClick={async () => {
                    try {
                      const res = await api.syncGmail();
                      if (res.status === "not_configured") {
                        alert("⚙️ Gmail not configured.\n\n" + res.message);
                      } else if (res.new_emails > 0) {
                        alert(`✅ Synced ${res.new_emails} new email(s)!`);
                        window.location.reload();
                      } else {
                        alert("✅ Gmail is up to date — no new emails.");
                      }
                    } catch (err: any) {
                      alert("❌ Sync failed: " + err.message);
                    }
                  }}
                  className="px-4 py-2 bg-gradient-to-r from-amber-500 to-yellow-500 hover:from-amber-600 hover:to-yellow-600 text-black font-semibold rounded-xl shadow-md hover:shadow-lg transition duration-200 flex items-center gap-2 text-sm cursor-pointer"
                >
                  <span>📬</span> Sync Gmail
                </button>

                {/* User avatar + logout */}
                <div className="flex items-center gap-2 pl-2 border-l border-gray-200">
                  {user?.picture ? (
                    <img
                      src={user.picture}
                      alt={user.name || user.email}
                      className="w-8 h-8 rounded-full border-2 border-amber-400/50 object-cover"
                      referrerPolicy="no-referrer"
                    />
                  ) : (
                    <div className="w-8 h-8 rounded-full bg-amber-500 flex items-center justify-center text-black font-bold text-xs">
                      {(user?.name || user?.email || "U")[0].toUpperCase()}
                    </div>
                  )}
                  <div className="hidden sm:block">
                    <p className="text-xs font-semibold text-gray-800 leading-none">
                      {user?.name || "User"}
                    </p>
                    <p className="text-[10px] text-gray-400 mt-0.5 truncate max-w-[120px]">
                      {user?.email}
                    </p>
                  </div>
                  <button
                    onClick={logout}
                    title="Sign out"
                    className="p-1.5 rounded-xl hover:bg-gray-100 text-gray-500 hover:text-gray-800 transition cursor-pointer ml-1"
                  >
                    <LogOut className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          </header>

          {/* ── Main content ─────────────────────────────────────────────── */}
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
              {currentView === "analytics" && <Analytics />}
              {currentView === "inbox" && <Inbox />}
              {currentView === "scheduled" && (
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
              {currentView === "settings" && <SettingsComponent />}
            </div>
          </main>
        </div>
      </div>

      {/* Floating AI chatbot */}
      <ChatBot />
    </div>
  );
}

// ── Root export — wraps everything in AuthProvider ────────────────────────────

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
