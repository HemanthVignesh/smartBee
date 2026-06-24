import { Mail, Brain, Clock, Inbox, TrendingUp, TrendingDown } from "lucide-react";

interface StatCardProps {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  color: string;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  progress?: number;
}

function StatCard({ icon, label, value, color, trend, progress }: StatCardProps) {
  return (
    <div className="bg-white/70 backdrop-blur-md rounded-3xl p-5 shadow-sm border border-gray-200/60 hover:border-amber-500/20 hover:shadow-xl hover:scale-[1.02] hover:-translate-y-1 transition-all duration-300 relative overflow-hidden group cursor-pointer">
      {/* Honey glow effect */}
      <div className="absolute inset-0 bg-gradient-to-br from-amber-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
      
      {/* Shimmer effect */}
      <div className="absolute inset-0 animate-shimmer opacity-0 group-hover:opacity-100"></div>
      
      <div className="relative z-10">
        <div className="flex items-start justify-between mb-3.5">
          <div className={`w-11 h-11 rounded-xl ${color} flex items-center justify-center shrink-0 group-hover:scale-110 transition-transform duration-300 shadow-sm`}>
            {icon}
          </div>
          {trend && (
            <div className={`flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full ${
              trend.isPositive ? "bg-green-500/10 text-green-700 border border-green-500/20" : "bg-red-500/10 text-red-700 border border-red-500/20"
            }`}>
              {trend.isPositive ? (
                <TrendingUp className="w-3 h-3" />
              ) : (
                <TrendingDown className="w-3 h-3" />
              )}
              <span>{trend.isPositive ? "+" : ""}{trend.value}%</span>
            </div>
          )}
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="text-3xl font-bold text-gray-900 tracking-tight mb-1">{value}</div>
          <div className="text-xs font-semibold text-gray-500">{label}</div>
          
          {progress !== undefined && (
            <div className="mt-3.5">
              <div className="flex items-center justify-between text-[10px] font-bold text-gray-400 mb-1 uppercase tracking-wider">
                <span>Weekly Goal</span>
                <span>{progress}%</span>
              </div>
              <div className="h-1 bg-gray-150 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-amber-500 to-yellow-500 rounded-full transition-all duration-500"
                  style={{ width: `${progress}%` }}
                ></div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

import { useState, useEffect } from "react";
import { api } from "../api/client";

export function StatsBar() {
  const [stats, setStats] = useState<any>(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await api.getAnalytics();
        setStats(data);
      } catch (e) {
        console.error("Failed to fetch analytics", e);
      }
    };
    fetchStats();
    const interval = setInterval(fetchStats, 30000); // 30s refresh
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <StatCard
        icon={<Mail className="w-6 h-6 text-white" />}
        label="Emails Scheduled"
        value={stats?.actions_count || 0}
        color="bg-gradient-to-br from-[#FFC107] to-[#FFB300]"
        trend={{ value: 2, isPositive: true }}
      />
      <StatCard
        icon={<Brain className="w-6 h-6 text-white" />}
        label="AI Processed"
        value={stats?.processed_emails || 0}
        color="bg-gradient-to-br from-[#FFB300] to-[#FFC107]"
      />
      <StatCard
        icon={<Clock className="w-6 h-6 text-white" />}
        label="Time Saved"
        value={`${stats?.time_saved_hours || 0}h`}
        color="bg-gradient-to-br from-[#FFCA28] to-[#FFD54F]"
        progress={70}
      />
      <StatCard
        icon={<Inbox className="w-6 h-6 text-white" />}
        label="Total Emails"
        value={stats?.total_emails || 0}
        color="bg-gradient-to-br from-[#1E1E1E] to-[#424242]"
        trend={{ value: 12, isPositive: true }}
      />
    </div>
  );
}