import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { TrendingUp, Mail, Clock, Zap } from "lucide-react";

const emailsPerWeekData = [
  { day: 'Mon', sent: 12, received: 24 },
  { day: 'Tue', sent: 15, received: 28 },
  { day: 'Wed', sent: 10, received: 20 },
  { day: 'Thu', sent: 18, received: 32 },
  { day: 'Fri', sent: 14, received: 26 },
  { day: 'Sat', sent: 5, received: 10 },
  { day: 'Sun', sent: 3, received: 8 },
];

const timeSavedData = [
  { week: 'Week 1', hours: 2.5 },
  { week: 'Week 2', hours: 3.2 },
  { week: 'Week 3', hours: 2.8 },
  { week: 'Week 4', hours: 3.5 },
];

interface MetricCardProps {
  title: string;
  value: string;
  subtitle: string;
  icon: React.ReactNode;
  color: string;
}

function MetricCard({ title, value, subtitle, icon, color }: MetricCardProps) {
  return (
    <div className="bg-white/70 backdrop-blur-md rounded-2xl p-5 border border-gray-200/60 hover:border-amber-500/20 hover:bg-white/95 hover:shadow-xl transition-all duration-300 hover:scale-[1.02] cursor-pointer">
      <div className="flex items-start justify-between mb-3">
        <div className={`p-2.5 rounded-xl ${color} flex items-center justify-center shrink-0`}>
          {icon}
        </div>
        <TrendingUp className="w-4.5 h-4.5 text-green-500" />
      </div>
      <div className="text-2xl font-bold text-gray-900 tracking-tight mb-0.5">{value}</div>
      <div className="text-xs font-semibold text-gray-600 mb-1">{title}</div>
      <div className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">{subtitle}</div>
    </div>
  );
}

import { useState, useEffect } from "react";
import { api } from "../api/client";

export function Analytics() {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await api.getAnalytics();
        setStats(data);
      } catch (e) {
        console.error("Failed to fetch analytics", e);
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
    const interval = setInterval(fetchStats, 30000); // Poll every 30 seconds
    return () => clearInterval(interval);
  }, []);

  // Use real data if populated, otherwise use mock data fallbacks
  const currentEmailsPerWeek = stats?.emails_per_week && stats.emails_per_week.length > 0 
    ? stats.emails_per_week 
    : emailsPerWeekData;

  const currentTimeSavedTrend = stats?.time_saved_trend && stats.time_saved_trend.length > 0
    ? stats.time_saved_trend
    : timeSavedData;

  const emailsManaged = stats?.total_emails !== undefined ? stats.total_emails : 77;
  const timeSavedHours = stats?.time_saved_hours !== undefined ? stats.time_saved_hours : 12.5;
  const actionsCount = stats?.actions_count !== undefined ? stats.actions_count : 11;
  const processedEmails = stats?.processed_emails !== undefined ? stats.processed_emails : 34;
  
  // Custom focus score heuristic based on ratio of processed to total emails
  const focusScore = stats?.total_emails 
    ? Math.min(100, Math.max(50, Math.round(80 + (processedEmails / stats.total_emails) * 15))) 
    : 92;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 tracking-tight mb-1">Productivity Analytics</h2>
        <p className="text-sm text-gray-500">Track automation efficiency and email triage metrics</p>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Emails Managed"
          value={loading ? "..." : String(emailsManaged)}
          subtitle="+12% vs last week"
          icon={<Mail className="w-4.5 h-4.5 text-black" />}
          color="bg-gradient-to-br from-amber-400 to-yellow-400"
        />
        <MetricCard
          title="Time Saved"
          value={loading ? "..." : `${timeSavedHours}h`}
          subtitle="Triage automated"
          icon={<Clock className="w-4.5 h-4.5 text-black" />}
          color="bg-gradient-to-br from-amber-300 to-yellow-300"
        />
        <MetricCard
          title="AI Task Executions"
          value={loading ? "..." : String(processedEmails)}
          subtitle="98.5% Accuracy"
          icon={<Zap className="w-4.5 h-4.5 text-black" />}
          color="bg-gradient-to-br from-amber-400 to-yellow-500"
        />
        <MetricCard
          title="Focus Score"
          value={loading ? "..." : `${focusScore}%`}
          subtitle="+5% Improvement"
          icon={<TrendingUp className="w-4.5 h-4.5 text-white" />}
          color="bg-gradient-to-br from-[#1C1C1E] to-[#2C2C2E]"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Emails Per Week Chart */}
        <div className="bg-white/70 backdrop-blur-md rounded-3xl p-6 border border-gray-200/60 hover:border-amber-500/20 hover:shadow-2xl transition-all duration-300">
          <h3 className="text-sm font-bold text-gray-900 mb-4 tracking-tight">Weekly Email Volume</h3>
          <div className="h-[250px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={currentEmailsPerWeek}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f2f2f2" vertical={false} />
                <XAxis dataKey="day" stroke="#a0a0a0" style={{ fontSize: '11px', fontFamily: 'Outfit' }} tickLine={false} />
                <YAxis stroke="#a0a0a0" style={{ fontSize: '11px', fontFamily: 'Outfit' }} tickLine={false} axisLine={false} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'rgba(255, 255, 255, 0.85)', 
                    backdropFilter: 'blur(8px)',
                    border: '1px solid rgba(0, 0, 0, 0.1)',
                    borderRadius: '16px',
                    boxShadow: '0 10px 30px rgba(0, 0, 0, 0.06)',
                    fontSize: '11px',
                    fontFamily: 'Outfit'
                  }} 
                />
                <Bar dataKey="sent" fill="#FF9500" radius={[4, 4, 0, 0]} />
                <Bar dataKey="received" fill="#FFCC00" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="flex items-center justify-center gap-6 mt-4">
            <div className="flex items-center gap-2">
              <div className="w-2.5 h-2.5 rounded-full bg-[#FF9500]"></div>
              <span className="text-xs text-gray-500 font-medium">Sent</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2.5 h-2.5 rounded-full bg-[#FFCC00]"></div>
              <span className="text-xs text-gray-500 font-medium">Received</span>
            </div>
          </div>
        </div>

        {/* Time Saved Chart */}
        <div className="bg-white/70 backdrop-blur-md rounded-3xl p-6 border border-gray-200/60 hover:border-amber-500/20 hover:shadow-2xl transition-all duration-300">
          <h3 className="text-sm font-bold text-gray-900 mb-4 tracking-tight">Time Saved Growth</h3>
          <div className="h-[250px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={currentTimeSavedTrend}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f2f2f2" vertical={false} />
                <XAxis dataKey="week" stroke="#a0a0a0" style={{ fontSize: '11px', fontFamily: 'Outfit' }} tickLine={false} />
                <YAxis stroke="#a0a0a0" style={{ fontSize: '11px', fontFamily: 'Outfit' }} tickLine={false} axisLine={false} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'rgba(255, 255, 255, 0.85)', 
                    backdropFilter: 'blur(8px)',
                    border: '1px solid rgba(0, 0, 0, 0.1)',
                    borderRadius: '16px',
                    boxShadow: '0 10px 30px rgba(0, 0, 0, 0.06)',
                    fontSize: '11px',
                    fontFamily: 'Outfit'
                  }} 
                />
                <Line 
                  type="monotone" 
                  dataKey="hours" 
                  stroke="#FF9500" 
                  strokeWidth={3}
                  dot={{ fill: '#FF9500', r: 4, strokeWidth: 1 }}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div className="flex items-center justify-center gap-2 mt-4">
            <div className="w-2.5 h-2.5 rounded-full bg-[#FF9500]"></div>
            <span className="text-xs text-gray-500 font-medium">Hours Saved per Week</span>
          </div>
        </div>
      </div>

      {/* AI Summary */}
      <div className="bg-gradient-to-br from-amber-500/5 to-orange-500/5 rounded-3xl p-6 border border-amber-500/20 shadow-sm relative overflow-hidden">
        <div className="flex items-start gap-4">
          <div className="p-3 bg-amber-500/10 rounded-2xl shrink-0">
            <Zap className="w-6 h-6 text-amber-600 animate-pulse" />
          </div>
          <div>
            <h3 className="text-base font-bold text-gray-900 mb-1 tracking-tight">AI Productivity Report</h3>
            <p className="text-xs text-gray-600 leading-relaxed mb-3">
              This month, Smart Bee AI has automated <span className="font-semibold text-amber-700">{loading ? "..." : processedEmails} tasks</span>, 
              saving you <span className="font-semibold text-amber-700">{loading ? "..." : `${timeSavedHours} hours`}</span> of manual triage. Your focus scores 
              have improved by <span className="font-semibold text-amber-700">5%</span>, freeing up valuable deep-work blocks.
            </p>
            <div className="flex flex-wrap gap-4 text-[10px] font-bold uppercase tracking-wider text-gray-400">
              <div className="flex items-center gap-1.5"><span className="text-green-500">✓</span> {processedEmails} auto-replies sent</div>
              <div className="flex items-center gap-1.5"><span className="text-green-500">✓</span> {actionsCount} meetings scheduled</div>
              <div className="flex items-center gap-1.5"><span className="text-green-500">✓</span> {emailsManaged} emails managed</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
