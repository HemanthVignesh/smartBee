import { Home, Inbox, Calendar, Brain, BarChart3, Settings, ChevronRight, X } from "lucide-react";
import logo from "../assets/SmartBee_logo.png";

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
      className={`w-full flex items-center justify-between gap-3 px-4 py-3 rounded-2xl transition-all duration-300 group cursor-pointer ${
        isActive
          ? "bg-amber-500 text-black font-semibold shadow-[0_4px_20px_-2px_rgba(245,158,11,0.25)] scale-[1.02]"
          : "text-gray-600 hover:bg-gray-100/85 hover:text-gray-900 hover:translate-x-0.5"
      }`}
    >
      <div className="flex items-center gap-3">
        <div className={`transition-transform duration-200 ${isActive ? "" : "group-hover:scale-110"}`}>
          {icon}
        </div>
        <span className="text-sm font-medium">{label}</span>
      </div>
      
      <div className="flex items-center gap-1.5">
        {badge !== undefined && badge > 0 && (
          <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${
            isActive ? "bg-black/10 text-black" : "bg-amber-100 text-amber-800"
          }`}>
            {badge}
          </span>
        )}
        {isActive && (
          <ChevronRight className="w-4 h-4 shrink-0" />
        )}
      </div>
    </button>
  );
}

interface SidebarProps {
  currentView: string;
  onViewChange: (view: string) => void;
  isOpen: boolean;
  onClose: () => void;
}

export function Sidebar({ currentView, onViewChange, isOpen, onClose }: SidebarProps) {
  return (
    <aside 
      className={`fixed inset-y-0 left-0 z-50 w-64 bg-white/80 backdrop-blur-xl border-r border-gray-200/50 p-6 flex flex-col shadow-2xl lg:shadow-none transform transition-transform duration-300 ease-out lg:relative lg:translate-x-0 ${
        isOpen ? "translate-x-0" : "-translate-x-full"
      }`}
    >
      {/* Mobile close button */}
      <div className="lg:hidden flex justify-end mb-2">
        <button 
          onClick={onClose}
          className="p-1.5 rounded-full hover:bg-gray-100 text-gray-500 transition-colors cursor-pointer"
          aria-label="Close menu"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Logo section */}
      <div className="mb-8 flex flex-col items-center">
        <img src={logo} alt="Smart Bee Logo" className="w-16 h-16 object-contain mb-2 hover:rotate-12 transition-transform duration-300" />
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
          <span className="text-xs text-gray-500 font-medium">Live & Secured</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="space-y-1.5 flex-1">
        <NavItem
          icon={<Home className="w-4.5 h-4.5" />}
          label="Dashboard"
          isActive={currentView === "dashboard"}
          onClick={() => onViewChange("dashboard")}
        />
        <NavItem
          icon={<Inbox className="w-4.5 h-4.5" />}
          label="Inbox"
          isActive={currentView === "inbox"}
          badge={12}
          onClick={() => onViewChange("inbox")}
        />
        <NavItem
          icon={<Calendar className="w-4.5 h-4.5" />}
          label="Scheduled"
          isActive={currentView === "scheduled"}
          badge={4}
          onClick={() => onViewChange("scheduled")}
        />
        <NavItem
          icon={<Brain className="w-4.5 h-4.5" />}
          label="AI Assistant"
          isActive={currentView === "ai-assistant"}
          badge={2}
          onClick={() => onViewChange("ai-assistant")}
        />
        <NavItem
          icon={<BarChart3 className="w-4.5 h-4.5" />}
          label="Analytics"
          isActive={currentView === "analytics"}
          onClick={() => onViewChange("analytics")}
        />
        <NavItem
          icon={<Settings className="w-4.5 h-4.5" />}
          label="Settings"
          isActive={currentView === "settings"}
          onClick={() => onViewChange("settings")}
        />
      </nav>

      {/* Footer */}
      <div className="mt-6 pt-6 border-t border-gray-100">
        <div className="bg-gradient-to-br from-amber-50/60 to-orange-50/60 rounded-2xl p-4 border border-amber-200/30">
          <div className="flex items-start gap-2.5">
            <div className="text-xl leading-none">✨</div>
            <div>
              <div className="text-xs font-semibold text-gray-900 mb-0.5">Pro Tip</div>
              <p className="text-[11px] text-gray-500 leading-normal">
                Use AI Assistant to auto-draft responses in seconds!
              </p>
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
}
