import { Mail, Clock, Eye, Edit, Sparkles, Pause, ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";

interface ScheduledEmail {
  id: string;
  to: string;
  subject: string;
  scheduledTime: string;
  date: string;
  status: "ready" | "draft" | "auto-send" | "pending";
  preview?: string;
  fullContent?: string;
  isAIGenerated?: boolean;
  priority?: "low" | "medium" | "high" | "urgent";
}

const mockEmails: ScheduledEmail[] = [
  {
    id: "1",
    to: "john.doe@example.com",
    subject: "Quarterly Report Review",
    scheduledTime: "09:00 AM",
    date: "Dec 17, 2025",
    status: "ready",
    preview: "Hi John, I wanted to share the quarterly report for your review. Please let me know if you have any questions.",
    fullContent: "Hi John,\n\nI wanted to share the quarterly report for your review. The numbers look great this quarter - we've exceeded our targets by 15%.\n\nKey highlights:\n• Revenue up 18%\n• Customer satisfaction at 94%\n• New clients: 23\n\nPlease let me know if you have any questions or would like to discuss further.\n\nBest regards",
    isAIGenerated: true,
    priority: "high"
  },
  {
    id: "2",
    to: "team@company.com",
    subject: "Weekly Team Update",
    scheduledTime: "02:30 PM",
    date: "Dec 17, 2025",
    status: "auto-send",
    preview: "Team, here's our weekly update covering project progress, upcoming milestones, and important announcements.",
    fullContent: "Team,\n\nHere's our weekly update:\n\nCompleted:\n• Feature X deployment\n• Bug fixes for Issue #234\n• Client presentation\n\nUpcoming:\n• Sprint planning Thursday\n• Product demo Friday\n\nGreat work everyone!",
    isAIGenerated: true,
    priority: "medium"
  },
  {
    id: "3",
    to: "client@business.com",
    subject: "Project Milestone Delivery",
    scheduledTime: "11:00 AM",
    date: "Dec 18, 2025",
    status: "pending",
    preview: "Dear Client, I'm pleased to inform you that we've reached an important milestone in your project.",
    fullContent: "Dear Client,\n\nI'm pleased to inform you that we've reached an important milestone in your project.\n\nWe've completed Phase 2 ahead of schedule and are ready to move to final testing.\n\nWould you be available for a demo next week?\n\nBest regards",
    priority: "urgent"
  },
  {
    id: "4",
    to: "sarah.wilson@example.com",
    subject: "Follow-up on Proposal",
    scheduledTime: "03:45 PM",
    date: "Dec 19, 2025",
    status: "draft",
    preview: "Hi Sarah, following up on the proposal we discussed last week. Would love to get your thoughts.",
    fullContent: "Hi Sarah,\n\nFollowing up on the proposal we discussed last week.\n\nI've attached the updated version with the changes we talked about.\n\nWould love to get your thoughts when you have a chance.\n\nThanks!",
    priority: "low"
  }
];

const statusConfig = {
  ready: { label: "Ready", icon: "✅", color: "bg-green-100 text-green-700 border-green-200" },
  draft: { label: "Draft", icon: "🟡", color: "bg-yellow-100 text-yellow-700 border-yellow-200" },
  "auto-send": { label: "Auto-Send", icon: "🔁", color: "bg-blue-100 text-blue-700 border-blue-200" },
  pending: { label: "Pending Approval", icon: "⏳", color: "bg-orange-100 text-orange-700 border-orange-200" }
};

const priorityColors = {
  low: "bg-gray-400",
  medium: "bg-blue-400",
  high: "bg-orange-400",
  urgent: "bg-red-500"
};

export function ScheduledEmails() {
  const [expandedEmail, setExpandedEmail] = useState<string | null>(null);

  const toggleExpand = (id: string) => {
    setExpandedEmail(expandedEmail === id ? null : id);
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 mb-4">
        <Mail className="w-5 h-5" />
        <h2>Scheduled Emails</h2>
      </div>
      <div className="space-y-3">
        {mockEmails.map((email) => (
          <div
            key={email.id}
            className="bg-white border border-gray-200 rounded-xl hover:border-[#FFC107] hover:shadow-lg transition-all duration-300 hover:-translate-y-1 relative group overflow-hidden"
          >
            {/* Priority color line */}
            {email.priority && (
              <div className={`absolute left-0 top-0 bottom-0 w-1 ${priorityColors[email.priority]}`}></div>
            )}
            
            <div className="p-4 pl-5">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-2 flex-wrap">
                    <div className="text-gray-900 truncate">{email.subject}</div>
                    <span className={`text-xs px-2 py-0.5 rounded-full border ${statusConfig[email.status].color} shrink-0`}>
                      {statusConfig[email.status].icon} {statusConfig[email.status].label}
                    </span>
                    {email.isAIGenerated && (
                      <span className="text-xs px-2 py-0.5 rounded-full bg-purple-100 text-purple-700 border border-purple-200 shrink-0 flex items-center gap-1">
                        <Sparkles className="w-3 h-3" />
                        AI Generated
                      </span>
                    )}
                  </div>
                  <div className="text-sm text-gray-500 mt-1">To: {email.to}</div>
                  
                  {/* Preview */}
                  {!expandedEmail && email.preview && (
                    <div className="mt-2 text-sm text-gray-600 line-clamp-2">
                      {email.preview}
                    </div>
                  )}
                  
                  {/* Full content when expanded */}
                  {expandedEmail === email.id && email.fullContent && (
                    <div className="mt-3 p-3 bg-gray-50 rounded-lg text-sm text-gray-700 border border-gray-200 whitespace-pre-line">
                      {email.fullContent}
                    </div>
                  )}
                </div>
                
                <div className="flex flex-col items-end gap-2">
                  <div className="flex items-center gap-2 text-sm text-gray-600 shrink-0">
                    <Clock className="w-4 h-4 text-[#FFC107]" />
                    <div className="text-right">
                      <div>{email.scheduledTime}</div>
                      <div className="text-xs text-gray-400">{email.date}</div>
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Action buttons */}
              <div className="mt-3 pt-3 border-t border-gray-100 flex items-center gap-2 flex-wrap">
                <button
                  onClick={() => toggleExpand(email.id)}
                  className="text-xs px-3 py-1.5 bg-gray-100 hover:bg-gray-200 rounded-lg flex items-center gap-1 text-gray-700 transition-all hover:scale-105"
                >
                  {expandedEmail === email.id ? (
                    <>
                      <ChevronUp className="w-3 h-3" />
                      Collapse
                    </>
                  ) : (
                    <>
                      <Eye className="w-3 h-3" />
                      Expand
                    </>
                  )}
                </button>
                <button className="text-xs px-3 py-1.5 bg-blue-100 hover:bg-blue-200 rounded-lg flex items-center gap-1 text-blue-700 transition-all hover:scale-105">
                  <Edit className="w-3 h-3" />
                  Edit
                </button>
                <button className="text-xs px-3 py-1.5 bg-purple-100 hover:bg-purple-200 rounded-lg flex items-center gap-1 text-purple-700 transition-all hover:scale-105">
                  <Sparkles className="w-3 h-3" />
                  Rewrite with AI
                </button>
                <button className="text-xs px-3 py-1.5 bg-orange-100 hover:bg-orange-200 rounded-lg flex items-center gap-1 text-orange-700 transition-all hover:scale-105">
                  <Pause className="w-3 h-3" />
                  Pause
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}