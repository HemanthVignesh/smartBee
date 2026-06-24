import { Mail, Clock, Eye, Edit, Sparkles, Pause, Play, ChevronDown, ChevronUp, X, Loader2, Trash2 } from "lucide-react";
import { useState } from "react";
import { api, useScheduledEmails } from "../api/client";

const statusConfig: Record<string, { label: string; icon: string; color: string }> = {
  ready: { label: "Ready", icon: "✅", color: "bg-green-500/10 text-green-700 border-green-500/20" },
  pending: { label: "Pending Approval", icon: "⏳", color: "bg-orange-500/10 text-orange-700 border-orange-500/20" },
  draft: { label: "Paused", icon: "🟡", color: "bg-yellow-500/10 text-yellow-700 border-yellow-500/20" },
  executed: { label: "Sent", icon: "📤", color: "bg-blue-500/10 text-blue-700 border-blue-500/20" }
};

const priorityColors: Record<string, string> = {
  low: "bg-gray-400",
  medium: "bg-blue-500",
  high: "bg-orange-500",
  urgent: "bg-red-500"
};

export function ScheduledEmails() {
  const { scheduledEmails, loading, error, refetch } = useScheduledEmails(true);
  const [expandedEmail, setExpandedEmail] = useState<string | null>(null);
  
  // Modals / Editing States
  const [editingEmail, setEditingEmail] = useState<any | null>(null);
  const [rewritingEmail, setRewritingEmail] = useState<any | null>(null);
  const [rewriteInstruction, setRewriteInstruction] = useState("");
  const [actionLoading, setActionLoading] = useState<string | null>(null); // holds actionId of currently running operation

  const toggleExpand = (id: string) => {
    setExpandedEmail(expandedEmail === id ? null : id);
  };

  // Pause Action
  const handlePause = async (e: React.MouseEvent, email: any) => {
    e.stopPropagation();
    try {
      setActionLoading(email.id);
      await api.pauseScheduledEmail(email.id);
      refetch();
    } catch (err: any) {
      alert("Failed to pause: " + err.message);
    } finally {
      setActionLoading(null);
    }
  };

  // Resume Action
  const handleResume = async (e: React.MouseEvent, email: any) => {
    e.stopPropagation();
    try {
      setActionLoading(email.id);
      await api.resumeScheduledEmail(email.id);
      refetch();
    } catch (err: any) {
      alert("Failed to resume: " + err.message);
    } finally {
      setActionLoading(null);
    }
  };

  // Delete Action
  const handleDelete = async (e: React.MouseEvent, email: any) => {
    e.stopPropagation();
    if (!window.confirm("Are you sure you want to delete this scheduled/suggested email?")) {
      return;
    }
    try {
      setActionLoading(email.id);
      await api.deleteScheduledEmail(email.id);
      refetch();
    } catch (err: any) {
      alert("Failed to delete: " + err.message);
    } finally {
      setActionLoading(null);
    }
  };

  // Edit Action Submit
  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingEmail) return;
    try {
      setActionLoading(editingEmail.id);
      await api.updateScheduledEmail(
        editingEmail.id,
        editingEmail.to,
        editingEmail.subject,
        editingEmail.fullContent
      );
      setEditingEmail(null);
      refetch();
    } catch (err: any) {
      alert("Failed to update: " + err.message);
    } finally {
      setActionLoading(null);
    }
  };

  // Rewrite Action Submit
  const handleRewriteSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!rewritingEmail || !rewriteInstruction.trim()) return;
    try {
      setActionLoading(rewritingEmail.id);
      const res = await api.rewriteScheduledEmail(rewritingEmail.id, rewriteInstruction);
      setRewritingEmail(null);
      setRewriteInstruction("");
      refetch();
      alert("AI Rewrite suggestion updated successfully!");
    } catch (err: any) {
      alert("Failed to rewrite with AI: " + err.message);
    } finally {
      setActionLoading(null);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2.5">
          <div className="p-2 bg-amber-500/10 rounded-xl">
            <Mail className="w-4.5 h-4.5 text-amber-600" />
          </div>
          <div>
            <h3 className="text-base font-bold text-gray-900 tracking-tight">Scheduled Emails</h3>
            <p className="text-[11px] text-gray-500">Outgoing automated drafts queue</p>
          </div>
        </div>
      </div>
      
      {loading && (
        <div className="flex items-center justify-center py-12 gap-2">
          <Loader2 className="w-5 h-5 text-amber-500 animate-spin" />
          <span className="text-xs text-gray-500 font-medium">Loading scheduled drafts...</span>
        </div>
      )}

      {error && (
        <div className="p-4 text-xs text-red-700 bg-red-50 rounded-2xl border border-red-200">
          ⚠️ Connection error: {error.message}
        </div>
      )}

      {!loading && !error && scheduledEmails.length === 0 && (
        <div className="text-center py-12 text-gray-500 text-xs font-medium bg-gray-50/50 border border-dashed border-gray-200 rounded-2xl">
          No scheduled emails in queue. Run email process flow.
        </div>
      )}

      {!loading && !error && scheduledEmails.length > 0 && (
        <div className="space-y-3">
          {scheduledEmails.map((email) => (
            <div
              key={email.id}
              className="bg-white/70 backdrop-blur-md border border-gray-150 hover:border-amber-500/20 hover:bg-white/95 rounded-2xl transition-all duration-300 hover:scale-[1.01] hover:shadow-md cursor-pointer overflow-hidden relative group"
            >
              {/* Priority color accent line */}
              {email.priority && (
                <div className={`absolute left-0 top-0 bottom-0 w-1.5 ${priorityColors[email.priority] || "bg-gray-300"}`}></div>
              )}
              
              <div className="p-5 pl-6">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2.5 mb-1.5 flex-wrap">
                      <span className="text-sm font-bold text-gray-900 truncate group-hover:text-amber-600 transition-colors">
                        {email.subject}
                      </span>
                      <span className={`text-[10px] uppercase tracking-wider px-2 py-0.5 rounded-full border font-bold ${statusConfig[email.status]?.color || "bg-gray-100"}`}>
                        {statusConfig[email.status]?.icon} {statusConfig[email.status]?.label || email.status}
                      </span>
                      {email.isAIGenerated && (
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-purple-500/10 text-purple-700 border border-purple-500/20 shrink-0 flex items-center gap-1">
                          <Sparkles className="w-2.5 h-2.5" />
                          AI Generated
                        </span>
                      )}
                    </div>
                    <div className="text-xs text-gray-500 font-medium">To: {email.to}</div>
                    
                    {/* Preview snippet */}
                    {!expandedEmail && email.preview && (
                      <div className="mt-2.5 text-xs text-gray-600 leading-relaxed line-clamp-2">
                        {email.preview}
                      </div>
                    )}
                    
                    {/* Full content */}
                    {expandedEmail === email.id && email.fullContent && (
                      <div className="mt-3 p-4 bg-gray-50/50 rounded-xl text-xs text-gray-700 border border-gray-200/50 whitespace-pre-line leading-relaxed animate-in fade-in duration-200">
                        {email.fullContent}
                      </div>
                    )}
                  </div>
                  
                  <div className="flex flex-col items-end gap-2 shrink-0">
                    <div className="flex items-center gap-1.5 text-xs text-gray-500 font-medium">
                      <Clock className="w-3.5 h-3.5 text-amber-500" />
                      <div className="text-right leading-tight">
                        <div className="font-semibold text-gray-700">{email.scheduledTime}</div>
                        <div className="text-[10px] text-gray-400">{email.date}</div>
                      </div>
                    </div>
                  </div>
                </div>
                
                {/* Premium rounded action buttons */}
                <div className="mt-4 pt-3.5 border-t border-gray-100/80 flex items-center gap-2 flex-wrap">
                  <button
                    onClick={() => toggleExpand(email.id)}
                    className="text-[11px] font-semibold px-3 py-1.5 bg-gray-100 hover:bg-gray-200/80 text-gray-700 rounded-full flex items-center gap-1 transition active:scale-95 cursor-pointer"
                  >
                    {expandedEmail === email.id ? (
                      <>
                        <ChevronUp className="w-3 h-3" />
                        Collapse
                      </>
                    ) : (
                      <>
                        <Eye className="w-3 h-3" />
                        Expand Preview
                      </>
                    )}
                  </button>
                  
                  {email.status !== "executed" && (
                    <>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setEditingEmail(email);
                        }}
                        className="text-[11px] font-semibold px-3 py-1.5 bg-blue-50 hover:bg-blue-100 text-blue-700 border border-blue-200/30 rounded-full flex items-center gap-1 transition active:scale-95 cursor-pointer"
                      >
                        <Edit className="w-3 h-3" />
                        Edit
                      </button>
                      
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setRewritingEmail(email);
                        }}
                        className="text-[11px] font-semibold px-3 py-1.5 bg-purple-50 hover:bg-purple-100 text-purple-700 border border-purple-200/30 rounded-full flex items-center gap-1 transition active:scale-95 cursor-pointer"
                      >
                        <Sparkles className="w-3 h-3" />
                        Rewrite
                      </button>

                      {email.status === "ready" || email.status === "pending" ? (
                        <button
                          onClick={(e) => handlePause(e, email)}
                          disabled={actionLoading === email.id}
                          className="text-[11px] font-semibold px-3 py-1.5 bg-orange-50 hover:bg-orange-100 text-orange-700 border border-orange-200/30 rounded-full flex items-center gap-1 transition active:scale-95 cursor-pointer disabled:opacity-50"
                        >
                          {actionLoading === email.id ? (
                            <Loader2 className="w-3 h-3 animate-spin" />
                          ) : (
                            <Pause className="w-3 h-3" />
                          )}
                          Pause
                        </button>
                      ) : (
                        <button
                          onClick={(e) => handleResume(e, email)}
                          disabled={actionLoading === email.id}
                          className="text-[11px] font-semibold px-3 py-1.5 bg-green-50 hover:bg-green-150 text-green-700 border border-green-200/30 rounded-full flex items-center gap-1 transition active:scale-95 cursor-pointer disabled:opacity-50"
                        >
                          {actionLoading === email.id ? (
                            <Loader2 className="w-3 h-3 animate-spin" />
                          ) : (
                            <Play className="w-3 h-3" />
                          )}
                          Resume
                        </button>
                      )}

                      <button
                        onClick={(e) => handleDelete(e, email)}
                        disabled={actionLoading === email.id}
                        className="text-[11px] font-semibold px-3 py-1.5 bg-red-50 hover:bg-red-100 text-red-700 border border-red-200/30 rounded-full flex items-center gap-1 transition active:scale-95 cursor-pointer disabled:opacity-50 ml-auto"
                      >
                        {actionLoading === email.id ? (
                          <Loader2 className="w-3 h-3 animate-spin" />
                        ) : (
                          <Trash2 className="w-3 h-3" />
                        )}
                        Delete
                      </button>
                    </>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Edit Email Glassmorphic Modal */}
      {editingEmail && (
        <div className="fixed inset-0 bg-black/30 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white/95 backdrop-blur-xl border border-gray-200 rounded-3xl p-6 w-full max-w-xl shadow-2xl animate-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between mb-4 border-b border-gray-100 pb-3">
              <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                <Edit className="w-5 h-5 text-blue-500" /> Edit Scheduled Email
              </h3>
              <button
                onClick={() => setEditingEmail(null)}
                className="p-1 rounded-full hover:bg-gray-100 text-gray-500 cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <form onSubmit={handleEditSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1.5">Recipient (To):</label>
                <input
                  type="email"
                  value={editingEmail.to}
                  onChange={(e) => setEditingEmail({ ...editingEmail, to: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-200 rounded-xl focus:outline-none focus:ring-1 focus:ring-amber-500 focus:border-transparent text-sm bg-white"
                  required
                />
              </div>
              
              <div>
                <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1.5">Subject:</label>
                <input
                  type="text"
                  value={editingEmail.subject}
                  onChange={(e) => setEditingEmail({ ...editingEmail, subject: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-200 rounded-xl focus:outline-none focus:ring-1 focus:ring-amber-500 focus:border-transparent text-sm bg-white"
                  required
                />
              </div>
              
              <div>
                <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1.5">Email Content:</label>
                <textarea
                  value={editingEmail.fullContent}
                  onChange={(e) => setEditingEmail({ ...editingEmail, fullContent: e.target.value })}
                  rows={8}
                  className="w-full px-4 py-3 border border-gray-200 rounded-2xl focus:outline-none focus:ring-1 focus:ring-amber-500 focus:border-transparent text-sm bg-white font-sans leading-relaxed"
                  required
                />
              </div>

              <div className="flex gap-2 justify-end pt-2">
                <button
                  type="button"
                  onClick={() => setEditingEmail(null)}
                  className="px-4 py-2 text-xs font-semibold bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-full cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading === editingEmail.id}
                  className="px-5 py-2 text-xs font-semibold bg-blue-500 hover:bg-blue-600 text-white rounded-full cursor-pointer flex items-center gap-1.5 disabled:opacity-50"
                >
                  {actionLoading === editingEmail.id && (
                    <Loader2 className="w-3 h-3 animate-spin" />
                  )}
                  Save Changes
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* AI Rewrite Instructions Modal */}
      {rewritingEmail && (
        <div className="fixed inset-0 bg-black/30 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white/95 backdrop-blur-xl border border-gray-200 rounded-3xl p-6 w-full max-w-md shadow-2xl animate-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between mb-4 border-b border-gray-100 pb-3">
              <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-purple-500" /> Rewrite with Smart Bee AI
              </h3>
              <button
                onClick={() => {
                  setRewritingEmail(null);
                  setRewriteInstruction("");
                }}
                className="p-1 rounded-full hover:bg-gray-100 text-gray-500 cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <form onSubmit={handleRewriteSubmit} className="space-y-4">
              <div className="text-xs text-gray-500 bg-purple-500/5 p-3.5 rounded-xl border border-purple-500/10 leading-relaxed">
                Provide instructions to rewrite the email: e.g. <span className="italic font-medium text-purple-800">"make it short and friendly"</span> or <span className="italic font-medium text-purple-800">"change tone to formal, ask client to reply by Friday"</span>.
              </div>
              
              <div>
                <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1.5">Rewrite Instructions:</label>
                <textarea
                  value={rewriteInstruction}
                  onChange={(e) => setRewriteInstruction(e.target.value)}
                  placeholder="Enter editing instruction..."
                  rows={3}
                  className="w-full px-4 py-2.5 border border-gray-200 rounded-xl focus:outline-none focus:ring-1 focus:ring-amber-500 focus:border-transparent text-sm bg-white"
                  required
                />
              </div>

              <div className="flex gap-2 justify-end pt-2">
                <button
                  type="button"
                  onClick={() => {
                    setRewritingEmail(null);
                    setRewriteInstruction("");
                  }}
                  className="px-4 py-2 text-xs font-semibold bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-full cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading === rewritingEmail.id || !rewriteInstruction.trim()}
                  className="px-5 py-2 text-xs font-semibold bg-purple-600 hover:bg-purple-700 text-white rounded-full cursor-pointer flex items-center gap-1.5 disabled:opacity-50"
                >
                  {actionLoading === rewritingEmail.id && (
                    <Loader2 className="w-3 h-3 animate-spin" />
                  )}
                  Generate with AI
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}