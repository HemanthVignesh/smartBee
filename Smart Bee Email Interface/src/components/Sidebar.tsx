import { Home, Inbox, Calendar, Brain, BarChart3, Settings, ChevronRight } from "lucide-react";
import { useState } from "react";

interface NavItemProps {
  icon: React.ReactNode;
  label: string;
  isActive: boolean;
  badge?: number;
  onClick: () => void;
}

function NavItem({ icon, label, isActive, badge, onClick }: NavItemProps) {
  return (
    <button
      onClick={onClick}
      className={`w-full flex items-center justify-between gap-3 px-4 py-3 rounded-xl transition-all duration-300 group ${
        isActive
          ? "bg-gradient-to-r from-[#FFC107] to-[#FFB300] text-black shadow-lg"
          : "text-gray-700 hover:bg-gray-100 hover:translate-x-1"
      }`}
    >
      <div className="flex items-center gap-3">
        <div className={`transition-transform ${isActive ? "" : "group-hover:scale-110"}`}>
          {icon}
        </div>
        <span className={isActive ? "" : ""}>{label}</span>
      </div>
      {badge !== undefined && badge > 0 && (
        <span className={`px-2 py-0.5 rounded-full text-xs ${
          isActive ? "bg-black/20 text-black" : "bg-[#FFC107] text-black"
        }`}>
          {badge}
        </span>
      )}
      {isActive && (
        <ChevronRight className="w-4 h-4" />
      )}
    </button>
  );
}

interface SidebarProps {
  currentView: string;
  onViewChange: (view: string) => void;
}

export function Sidebar({ currentView, onViewChange }: SidebarProps) {
  return (
    <aside className="w-64 bg-white/90 backdrop-blur-md border-r border-gray-200 p-6 flex flex-col shadow-lg">
      {/* Logo section */}
      <div className="mb-8">
        <div className="flex items-center gap-2 mb-2">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
          <span className="text-xs text-gray-500">All systems active</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="space-y-2 flex-1">
        <NavItem
          icon={<Home className="w-5 h-5" />}
          label="Dashboard"
          isActive={currentView === "dashboard"}
          onClick={() => onViewChange("dashboard")}
        />
        <NavItem
          icon={<Inbox className="w-5 h-5" />}
          label="Inbox"
          isActive={currentView === "inbox"}
          badge={12}
          onClick={() => onViewChange("inbox")}
        />
        <NavItem
          icon={<Calendar className="w-5 h-5" />}
          label="Scheduled"
          isActive={currentView === "scheduled"}
          badge={4}
          onClick={() => onViewChange("scheduled")}
        />
        <NavItem
          icon={<Brain className="w-5 h-5" />}
          label="AI Assistant"
          isActive={currentView === "ai-assistant"}
          badge={2}
          onClick={() => onViewChange("ai-assistant")}
        />
        <NavItem
          icon={<BarChart3 className="w-5 h-5" />}
          label="Analytics"
          isActive={currentView === "analytics"}
          onClick={() => onViewChange("analytics")}
        />
        <NavItem
          icon={<Settings className="w-5 h-5" />}
          label="Settings"
          isActive={currentView === "settings"}
          onClick={() => onViewChange("settings")}
        />
      </nav>

      {/* Footer */}
      <div className="mt-6 pt-6 border-t border-gray-200">
        <div className="bg-gradient-to-br from-[#FFF8E1] to-[#FFECB3] rounded-xl p-4 border border-[#FFC107]/30">
          <div className="flex items-start gap-2 mb-2">
            <div className="text-2xl">✨</div>
            <div>
              <div className="text-sm text-gray-900">Pro Tip</div>
              <p className="text-xs text-gray-600 mt-1">
                Use AI Assistant to auto-draft responses in seconds!
              </p>
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
}
