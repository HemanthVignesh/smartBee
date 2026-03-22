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
    <div className="bg-white/90 backdrop-blur-sm rounded-xl p-5 border border-gray-200 hover:border-[#FFC107] transition-all hover:shadow-lg hover:-translate-y-1">
      <div className="flex items-start justify-between mb-3">
        <div className={`p-3 rounded-lg ${color}`}>
          {icon}
        </div>
        <TrendingUp className="w-5 h-5 text-green-500" />
      </div>
      <div className="text-2xl text-gray-900 mb-1">{value}</div>
      <div className="text-sm text-gray-600 mb-1">{title}</div>
      <div className="text-xs text-gray-500">{subtitle}</div>
    </div>
  );
}

export function Analytics() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl text-gray-900 mb-2">📊 Analytics Dashboard</h2>
        <p className="text-sm text-gray-600">Track your productivity and email management insights</p>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Emails Sent This Week"
          value="77"
          subtitle="+12% from last week"
          icon={<Mail className="w-5 h-5 text-white" />}
          color="bg-gradient-to-br from-[#FFC107] to-[#FFB300]"
        />
        <MetricCard
          title="Time Saved"
          value="12.5h"
          subtitle="This month"
          icon={<Clock className="w-5 h-5 text-white" />}
          color="bg-gradient-to-br from-[#FFCA28] to-[#FFD54F]"
        />
        <MetricCard
          title="AI Automation Count"
          value="45"
          subtitle="Tasks automated"
          icon={<Zap className="w-5 h-5 text-white" />}
          color="bg-gradient-to-br from-[#FFB300] to-[#FFC107]"
        />
        <MetricCard
          title="Productivity Score"
          value="92%"
          subtitle="+5% improvement"
          icon={<TrendingUp className="w-5 h-5 text-white" />}
          color="bg-gradient-to-br from-[#1E1E1E] to-[#424242]"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Emails Per Week Chart */}
        <div className="bg-white/90 backdrop-blur-sm rounded-xl p-6 border border-gray-200 hover:border-[#FFC107] transition-all">
          <h3 className="text-lg text-gray-900 mb-4">Emails Per Week</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={emailsPerWeekData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="day" stroke="#666" style={{ fontSize: '12px' }} />
              <YAxis stroke="#666" style={{ fontSize: '12px' }} />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#fff', 
                  border: '1px solid #FFC107',
                  borderRadius: '8px',
                  fontSize: '12px'
                }} 
              />
              <Bar dataKey="sent" fill="#FFC107" radius={[8, 8, 0, 0]} />
              <Bar dataKey="received" fill="#FFB300" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
          <div className="flex items-center justify-center gap-6 mt-4">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-[#FFC107]"></div>
              <span className="text-xs text-gray-600">Sent</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-[#FFB300]"></div>
              <span className="text-xs text-gray-600">Received</span>
            </div>
          </div>
        </div>

        {/* Time Saved Chart */}
        <div className="bg-white/90 backdrop-blur-sm rounded-xl p-6 border border-gray-200 hover:border-[#FFC107] transition-all">
          <h3 className="text-lg text-gray-900 mb-4">Time Saved (Hours)</h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={timeSavedData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="week" stroke="#666" style={{ fontSize: '12px' }} />
              <YAxis stroke="#666" style={{ fontSize: '12px' }} />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#fff', 
                  border: '1px solid #FFC107',
                  borderRadius: '8px',
                  fontSize: '12px'
                }} 
              />
              <Line 
                type="monotone" 
                dataKey="hours" 
                stroke="#FFC107" 
                strokeWidth={3}
                dot={{ fill: '#FFC107', r: 5 }}
                activeDot={{ r: 7 }}
              />
            </LineChart>
          </ResponsiveContainer>
          <div className="flex items-center justify-center gap-2 mt-4">
            <div className="w-3 h-3 rounded-full bg-[#FFC107]"></div>
            <span className="text-xs text-gray-600">Hours Saved</span>
          </div>
        </div>
      </div>

      {/* AI Summary */}
      <div className="bg-gradient-to-br from-[#FFF8E1] to-white rounded-xl p-6 border-2 border-[#FFC107]/30">
        <div className="flex items-start gap-4">
          <div className="p-3 bg-[#FFC107] rounded-full">
            <Zap className="w-6 h-6 text-black" />
          </div>
          <div>
            <h3 className="text-lg text-gray-900 mb-2">AI Productivity Summary</h3>
            <p className="text-sm text-gray-700 mb-3">
              This month, Smart Bee AI has automated <span className="text-[#FFC107]">45 tasks</span>, 
              saving you <span className="text-[#FFC107]">12.5 hours</span> of work time. Your productivity score 
              is <span className="text-[#FFC107]">92%</span>, which is excellent!
            </p>
            <div className="flex gap-4 text-xs text-gray-600">
              <div>✅ 34 auto-replies sent</div>
              <div>📅 11 meetings scheduled</div>
              <div>📧 77 emails managed</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
