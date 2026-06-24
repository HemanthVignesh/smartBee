import { useState } from 'react';
import { api, useEmails } from '../api/client';
import { Mail, RefreshCw, Search, Clock, Tag, Users, Bell, MessageSquare, X, Brain, Inbox as InboxIcon } from 'lucide-react';

export function Inbox() {
  const { emails, loading, error, refetch } = useEmails(true);
  const [fetching, setFetching] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [activeTab, setActiveTab] = useState('all');
  const [selectedEmail, setSelectedEmail] = useState<any | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [editedActions, setEditedActions] = useState<Record<string, any>>({});

  const handleRequestInsight = async (emailId: string) => {
    try {
      setAnalyzing(true);
      await api.analyzeEmail(emailId);
      
      // Fetch updated email with analysis
      const updatedEmail = await api.getEmailById(emailId);
      setSelectedEmail(updatedEmail);
      
      refetch();
    } catch (err: any) {
      alert(`❌ AI Analysis failed: ${err.message}`);
    } finally {
      setAnalyzing(false);
    }
  };

  const handleActionFeedback = async (actionId: string, type: 'accepted' | 'rejected', customPayload?: any) => {
    try {
      await api.submitFeedback(actionId, { feedback_type: type, custom_payload: customPayload });
      if (selectedEmail) {
        const updatedEmail = await api.getEmailById(selectedEmail.id);
        setSelectedEmail(updatedEmail);
      }
      refetch();
    } catch (err: any) {
      alert(`❌ Action failed: ${err.message}`);
    }
  };

  const updateActionPayload = (actionId: string, field: string, value: any) => {
    setEditedActions(prev => {
      const currentAction = prev[actionId] || {};
      return {
        ...prev,
        [actionId]: {
          ...currentAction,
          [field]: value
        }
      };
    });
  };

  const tabs = [
    { id: 'all', label: 'All Mail', icon: InboxIcon },
    { id: 'primary', label: 'Primary', icon: Mail },
    { id: 'promotions', label: 'Promotions', icon: Tag },
    { id: 'social', label: 'Social', icon: Users },
    { id: 'updates', label: 'Updates', icon: Bell },
    { id: 'forums', label: 'Forums', icon: MessageSquare }
  ];

  const handleFetchFromGmail = async () => {
    try {
      setFetching(true);
      const result = await api.fetchEmails({ max_results: 20 });
      alert(`✅ Fetched ${result.new_count} new emails!`);
      refetch();
    } catch (err: any) {
      alert(`❌ Failed: ${err.message}\n\nMake sure Gmail is configured!`);
    } finally {
      setFetching(false);
    }
  };

  const filteredEmails = emails.filter(email => {
    if (activeTab !== 'all') {
      const cat = (email.category || 'primary').toLowerCase();
      if (cat !== activeTab) return false;
    }
    
    return (
      searchTerm === '' ||
      email.subject?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      email.sender?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      email.body?.toLowerCase().includes(searchTerm.toLowerCase())
    );
  });

  return (
    <div className="bg-white/80 backdrop-blur-xl rounded-3xl p-6 shadow-xl border border-gray-200/50 hover:shadow-2xl transition-all duration-300">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h2 className="text-xl font-bold text-gray-900 tracking-tight flex items-center gap-2">
            <Mail className="w-5 h-5 text-amber-600" />
            📬 Mailbox
          </h2>
          <p className="text-xs text-gray-500 mt-0.5">Manage and process synced messages</p>
        </div>
        
        <div className="flex gap-2 shrink-0">
          <button
            onClick={refetch}
            disabled={loading}
            className="px-4 py-2 bg-gray-100 hover:bg-gray-200/80 disabled:opacity-50 text-gray-700 font-semibold rounded-xl text-xs transition duration-200 flex items-center gap-1.5 cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <button
            onClick={handleFetchFromGmail}
            disabled={fetching}
            className="px-4 py-2 bg-amber-500 hover:bg-amber-600 disabled:opacity-50 text-black font-semibold rounded-xl text-xs transition duration-200 flex items-center gap-1.5 cursor-pointer shadow-sm shadow-amber-500/10"
          >
            <Mail className="w-3.5 h-3.5" />
            {fetching ? 'Fetching...' : 'Fetch from Gmail'}
          </button>
        </div>
      </div>

      {/* Search Bar */}
      <div className="mb-6">
        <div className="relative">
          <Search className="absolute left-3.5 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search senders, subjects, contents..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 border border-gray-200/80 rounded-2xl focus:outline-none focus:ring-1 focus:ring-amber-500 focus:border-transparent text-sm bg-white/70"
          />
        </div>
      </div>

      {/* Category Tabs */}
      {!loading && !error && emails.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-6 border-b border-gray-200/50 pb-3">
          {tabs.map((tab) => {
            const TabIcon = tab.icon;
            const count = tab.id === 'all'
              ? emails.length
              : emails.filter(email => (email.category || 'primary').toLowerCase() === tab.id).length;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold transition-all duration-200 border cursor-pointer ${
                  isActive
                    ? 'bg-amber-500/10 text-amber-600 border-amber-500/20 shadow-sm'
                    : 'bg-white hover:bg-gray-50 text-gray-500 hover:text-gray-800 border-gray-200/60'
                }`}
              >
                <TabIcon className={`w-3.5 h-3.5 ${isActive ? 'text-amber-600' : 'text-gray-400'}`} />
                <span>{tab.label}</span>
                {count > 0 && (
                  <span className={`px-1.5 py-0.5 rounded-full text-[10px] font-bold ${
                    isActive ? 'bg-amber-500/20 text-amber-700' : 'bg-gray-100 text-gray-500'
                  }`}>
                    {count}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex flex-col items-center justify-center py-16 gap-3">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-500"></div>
          <p className="text-xs text-gray-500 font-medium">Loading inbox messages...</p>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="bg-red-50/50 border border-red-200/50 rounded-2xl p-4 text-xs text-red-700 leading-normal flex items-start gap-2.5">
          <span>⚠️</span>
          <div>
            <div className="font-semibold mb-0.5">Connection Error:</div>
            <div>{error.message}</div>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && emails.length === 0 && (
        <div className="text-center py-16 bg-gray-50/50 border border-dashed border-gray-200 rounded-3xl">
          <div className="text-5xl mb-4 leading-none">📭</div>
          <div className="text-sm font-bold text-gray-900 mb-1">Your inbox is empty</div>
          <div className="text-xs text-gray-500 mb-3 px-6">
            Connect your Gmail account to start seeing and managing real emails with AI.
          </div>
          <div className="text-xs text-gray-400 mb-6 px-8 leading-relaxed">
            <strong>To set up Gmail:</strong> Download your OAuth2 credentials from Google Cloud Console,
            save as <code className="bg-gray-100 px-1 rounded">credentials.json</code> in the backend folder, then restart the server.
          </div>
          <button
            onClick={handleFetchFromGmail}
            disabled={fetching}
            className="px-5 py-2.5 bg-amber-500 hover:bg-amber-600 disabled:opacity-50 text-black font-semibold rounded-xl text-xs shadow-md shadow-amber-500/10 cursor-pointer transition duration-200"
          >
            {fetching ? 'Syncing...' : '📬 Sync Gmail Now'}
          </button>
        </div>
      )}

      {/* Empty Category State */}
      {!loading && !error && emails.length > 0 && filteredEmails.length === 0 && (
        <div className="text-center py-12 bg-gray-50/30 border border-dashed border-gray-200/60 rounded-2xl">
          <div className="text-3xl mb-3">📁</div>
          <div className="text-xs font-semibold text-gray-700 mb-1">No emails in {tabs.find(t => t.id === activeTab)?.label}</div>
          <p className="text-[11px] text-gray-400 max-w-xs mx-auto">
            {searchTerm ? "No messages match your search term in this tab." : `Emails categorized as '${activeTab}' will appear here.`}
          </p>
        </div>
      )}

      {/* Email List */}
      {!loading && !error && filteredEmails.length > 0 && (
        <div className="space-y-2.5">
          {filteredEmails.map((email) => (
            <div
              key={email.id}
              onClick={() => setSelectedEmail(email)}
              className="border border-gray-150 rounded-2xl p-4.5 hover:border-amber-500/30 hover:shadow-md hover:scale-[1.005] transition-all duration-300 cursor-pointer bg-white/60 relative group"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2 mb-1.5">
                    <span className="text-sm font-bold text-gray-900 truncate group-hover:text-amber-600 transition-colors">
                      {email.sender}
                    </span>
                    <span className="text-[10px] text-gray-400 font-semibold shrink-0 flex items-center gap-1">
                      <Clock className="w-3 h-3 text-gray-400" />
                      {new Date(email.received_at).toLocaleDateString(undefined, {
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </span>
                  </div>
                  <h3 className="text-xs font-semibold text-gray-700 mb-1.5 truncate">
                    {email.subject || '(No Subject)'}
                  </h3>
                  <p className="text-xs text-gray-500 line-clamp-2 leading-relaxed">
                    {email.body}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Email Detail Modal */}
      {selectedEmail && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm animate-in fade-in duration-200">
          <div 
            className="bg-white rounded-3xl w-full max-w-2xl max-h-[85vh] flex flex-col shadow-2xl border border-gray-200/50 animate-in zoom-in-95 duration-200"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="px-6 py-4 border-b border-gray-150 flex items-center justify-between bg-gray-50/50 rounded-t-3xl shrink-0">
              <div className="min-w-0">
                <span className="text-[10px] uppercase font-extrabold tracking-wider bg-amber-500/10 text-amber-700 px-2 py-0.5 rounded-full border border-amber-500/20">
                  {selectedEmail.category || "primary"}
                </span>
                <h3 className="text-sm font-bold text-gray-900 truncate mt-1">
                  {selectedEmail.subject || "(No Subject)"}
                </h3>
              </div>
              <button 
                onClick={() => setSelectedEmail(null)}
                className="p-1.5 hover:bg-gray-200 rounded-full transition-colors cursor-pointer text-gray-500"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {/* Metadata */}
              <div className="text-xs text-gray-500 space-y-1">
                <div><strong>From:</strong> {selectedEmail.sender}</div>
                <div>
                  <strong>Received:</strong> {new Date(selectedEmail.received_at).toLocaleString(undefined, {
                    weekday: 'long',
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                  })}
                </div>
              </div>

              {/* Email Body */}
              <div className="bg-gray-50 border border-gray-150/80 rounded-2xl p-4 max-h-48 overflow-y-auto text-xs text-gray-700 whitespace-pre-wrap leading-relaxed">
                {selectedEmail.body || "(Empty Body)"}
              </div>

              {/* AI Insights Section */}
              <div className="border-t border-gray-100 pt-5">
                <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
                  <Brain className="w-3.5 h-3.5 text-amber-500" />
                  AI Insights & Suggested Actions
                </h4>

                {selectedEmail.analysis ? (
                  <div className="space-y-4">
                    {/* Summary Card */}
                    <div className="bg-amber-500/[0.02] border border-amber-500/10 rounded-2xl p-4">
                      <div className="flex items-center justify-between gap-2 mb-2 flex-wrap">
                        <span className="text-xs font-bold text-amber-800">AI Summary</span>
                        <div className="flex items-center gap-2">
                          {selectedEmail.analysis.intent && (
                            <span className="text-[10px] uppercase px-2 py-0.5 rounded-full border bg-purple-500/10 text-purple-700 border-purple-500/20 font-bold">
                              {selectedEmail.analysis.intent.replace('_', ' ')}
                            </span>
                          )}
                          <span className="text-[10px] font-semibold text-gray-500">
                            Priority: <span className="font-bold uppercase text-amber-700">{selectedEmail.analysis.priority}</span>
                          </span>
                        </div>
                      </div>
                      <p className="text-xs text-gray-700 leading-relaxed font-medium italic whitespace-pre-line">
                        “ {selectedEmail.analysis.summary} ”
                      </p>
                    </div>

                    {/* Suggested Actions */}
                    {selectedEmail.decisions && selectedEmail.decisions.length > 0 && selectedEmail.decisions[0].actions?.length > 0 && (
                      <div className="space-y-2">
                        <div className="text-[10px] font-bold text-gray-500 uppercase tracking-wider">Suggested Actions:</div>
                        <div className="space-y-2">
                          {selectedEmail.decisions[0].actions.map((action: any) => {
                            // Calendar pending
                            if (action.action_type === "create_calendar_event" && action.status === "pending") {
                              return (
                                <div key={action.action_id} className="bg-gray-50 p-4 rounded-2xl border border-gray-200/80 shadow-sm space-y-3">
                                  <div className="flex items-center gap-1.5 text-xs font-bold text-amber-800 uppercase tracking-wider">
                                    <span>📅</span> Customize Calendar Event
                                  </div>
                                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                    <div className="sm:col-span-2">
                                      <label className="block text-[10px] font-bold text-gray-400 uppercase mb-1">Event Title:</label>
                                      <input
                                        type="text"
                                        value={editedActions[action.action_id]?.title ?? action.payload.title ?? ""}
                                        onChange={(e) => updateActionPayload(action.action_id, 'title', e.target.value)}
                                        className="w-full px-3 py-1.5 border border-gray-200 rounded-xl focus:outline-none focus:ring-1 focus:ring-amber-500 text-xs bg-white"
                                      />
                                    </div>
                                    <div>
                                      <label className="block text-[10px] font-bold text-gray-400 uppercase mb-1">Date:</label>
                                      <input
                                        type="date"
                                        value={editedActions[action.action_id]?.date ?? action.payload.date ?? ""}
                                        onChange={(e) => updateActionPayload(action.action_id, 'date', e.target.value)}
                                        className="w-full px-3 py-1.5 border border-gray-200 rounded-xl focus:outline-none focus:ring-1 focus:ring-amber-500 text-xs bg-white"
                                      />
                                    </div>
                                    <div>
                                      <label className="block text-[10px] font-bold text-gray-400 uppercase mb-1">Time:</label>
                                      <input
                                        type="text"
                                        value={editedActions[action.action_id]?.time ?? action.payload.time ?? ""}
                                        onChange={(e) => updateActionPayload(action.action_id, 'time', e.target.value)}
                                        className="w-full px-3 py-1.5 border border-gray-200 rounded-xl focus:outline-none focus:ring-1 focus:ring-amber-500 text-xs bg-white"
                                        placeholder="e.g. 10:00 AM"
                                      />
                                    </div>
                                    <div>
                                      <label className="block text-[10px] font-bold text-gray-400 uppercase mb-1">Duration:</label>
                                      <input
                                        type="text"
                                        value={editedActions[action.action_id]?.duration ?? action.payload.duration ?? ""}
                                        onChange={(e) => updateActionPayload(action.action_id, 'duration', e.target.value)}
                                        className="w-full px-3 py-1.5 border border-gray-200 rounded-xl focus:outline-none focus:ring-1 focus:ring-amber-500 text-xs bg-white"
                                        placeholder="e.g. 30m"
                                      />
                                    </div>
                                  </div>
                                  <div className="flex gap-2 justify-end pt-1">
                                    <button
                                      onClick={() => handleActionFeedback(action.action_id, "accepted", editedActions[action.action_id])}
                                      className="px-3.5 py-1.5 text-[11px] rounded-xl bg-amber-500 hover:bg-amber-600 text-black font-semibold transition cursor-pointer shadow-sm"
                                    >
                                      Schedule Event
                                    </button>
                                    <button
                                      onClick={() => handleActionFeedback(action.action_id, "rejected")}
                                      className="px-3.5 py-1.5 text-[11px] rounded-xl bg-white border border-gray-200 text-gray-500 hover:bg-gray-50 transition cursor-pointer"
                                    >
                                      Dismiss
                                    </button>
                                  </div>
                                </div>
                              );
                            }

                            // Smart Reply pending
                            if (action.action_type === "generate_reply" && action.status === "pending") {
                              const activeDraftText = editedActions[action.action_id]?.reply_text ?? action.payload.replies?.[0] ?? "";
                              return (
                                <div key={action.action_id} className="bg-gray-50 p-4 rounded-2xl border border-gray-200/80 shadow-sm space-y-3">
                                  <div className="flex items-center gap-1.5 text-xs font-bold text-amber-800 uppercase tracking-wider">
                                    <span>✍️</span> Edit Draft Response
                                  </div>
                                  
                                  {action.payload.replies && action.payload.replies.length > 1 && (
                                    <div className="space-y-1.5">
                                      <label className="block text-[10px] font-bold text-gray-400 uppercase">Draft Options:</label>
                                      <div className="flex gap-2 overflow-x-auto pb-1 max-w-full">
                                        {action.payload.replies.map((reply: string, idx: number) => {
                                          const isSelected = activeDraftText === reply;
                                          return (
                                            <button
                                              key={idx}
                                              type="button"
                                              onClick={() => updateActionPayload(action.action_id, 'reply_text', reply)}
                                              className={`px-3 py-1 rounded-xl text-[10px] font-bold whitespace-nowrap border transition cursor-pointer shrink-0 ${
                                                isSelected
                                                  ? "bg-amber-500/10 text-amber-700 border-amber-500"
                                                  : "bg-white text-gray-500 border-gray-200 hover:bg-gray-50"
                                              }`}
                                            >
                                              Option {idx + 1}
                                            </button>
                                          );
                                        })}
                                      </div>
                                    </div>
                                  )}
                                  
                                  <div>
                                    <label className="block text-[10px] font-bold text-gray-400 uppercase mb-1">Response Body:</label>
                                    <textarea
                                      value={activeDraftText}
                                      onChange={(e) => updateActionPayload(action.action_id, 'reply_text', e.target.value)}
                                      rows={5}
                                      className="w-full px-3 py-2 border border-gray-200 rounded-xl focus:outline-none focus:ring-1 focus:ring-amber-500 text-xs bg-white leading-relaxed font-medium"
                                    />
                                  </div>
                                  
                                  <div className="flex gap-2 justify-end pt-1">
                                    <button
                                      onClick={() => handleActionFeedback(action.action_id, "accepted", { 
                                        reply_text: activeDraftText 
                                      })}
                                      className="px-3.5 py-1.5 text-[11px] rounded-xl bg-amber-500 hover:bg-amber-600 text-black font-semibold transition cursor-pointer shadow-sm"
                                    >
                                      Approve & Send
                                    </button>
                                    <button
                                      onClick={() => handleActionFeedback(action.action_id, "rejected")}
                                      className="px-3.5 py-1.5 text-[11px] rounded-xl bg-white border border-gray-200 text-gray-500 hover:bg-gray-50 transition cursor-pointer"
                                    >
                                      Dismiss
                                    </button>
                                  </div>
                                </div>
                              );
                            }

                            // Calendar Executed
                            if (action.action_type === "create_calendar_event" && action.status === "executed" && action.execution_metadata?.event_link) {
                              return (
                                <a
                                  key={action.action_id}
                                  href={action.execution_metadata.event_link}
                                  target="_blank"
                                  rel="noreferrer"
                                  className="px-3 py-2 text-xs rounded-xl bg-green-500 hover:bg-green-600 text-white font-semibold shadow-sm transition inline-flex items-center gap-1.5 cursor-pointer"
                                >
                                  <span>📅</span> Calendar Event Created - View Details
                                </a>
                              );
                            }

                            // Reply Executed
                            if (action.action_type === "generate_reply" && action.status === "executed") {
                              return (
                                <div key={action.action_id} className="text-[11px] bg-green-50/50 border border-green-200/50 rounded-xl p-3 w-full">
                                  <span className="font-semibold text-green-800 flex items-center gap-1 mb-1">
                                    <span>✅</span> Auto-Reply Sent Successfully:
                                  </span>
                                  <div className="italic text-gray-600 pl-5">
                                    "{action.execution_metadata.selected_reply}"
                                  </div>
                                </div>
                              );
                            }

                            if (action.status === "rejected") {
                              return (
                                <div key={action.action_id} className="text-xs text-gray-400 italic">
                                  Action dismissed
                                </div>
                              );
                            }

                            return null;
                          })}
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-6 bg-gray-50 border border-dashed border-gray-200 rounded-2xl">
                    <div className="text-xl mb-1">🧠</div>
                    <div className="text-xs font-bold text-gray-800 mb-0.5">No AI Insight Requested Yet</div>
                    <p className="text-[10px] text-gray-500 max-w-xs mx-auto mb-4 leading-normal">
                      Promotions, social, and updates emails are not automatically summarized or analyzed to conserve system resources.
                    </p>
                    <button
                      onClick={() => handleRequestInsight(selectedEmail.id)}
                      disabled={analyzing}
                      className="px-4 py-2 bg-amber-500 hover:bg-amber-600 disabled:opacity-50 text-black font-semibold rounded-xl text-xs shadow-md shadow-amber-500/10 cursor-pointer transition flex items-center gap-1.5 mx-auto"
                    >
                      {analyzing ? (
                        <>
                          <div className="animate-spin rounded-full h-3.5 w-3.5 border-b-2 border-black"></div>
                          Analyzing Email...
                        </>
                      ) : (
                        <>
                          <Brain className="w-3.5 h-3.5" />
                          ✨ Request AI Insight
                        </>
                      )}
                    </button>
                  </div>
                )}
              </div>
            </div>

            {/* Modal Footer */}
            <div className="px-6 py-4 border-t border-gray-150 bg-gray-50/30 rounded-b-3xl shrink-0 flex justify-end">
              <button
                onClick={() => setSelectedEmail(null)}
                className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 font-semibold rounded-xl text-xs transition cursor-pointer"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Count Indicator */}
      {!loading && filteredEmails.length > 0 && (
        <div className="mt-5 text-[11px] text-gray-400 font-bold uppercase tracking-wider text-center">
          Showing {filteredEmails.length} of {activeTab === 'all' ? emails.length : emails.filter(email => (email.category || 'primary').toLowerCase() === activeTab).length} messages in {tabs.find(t => t.id === activeTab)?.label}
        </div>
      )}
    </div>
  );
}