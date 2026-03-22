
import { useState } from 'react';
import { api, useEmails } from '../api/client';
import { Mail, RefreshCw, Search, Clock } from 'lucide-react';

export function Inbox() {
  const { emails, loading, error, refetch } = useEmails(true);
  const [fetching, setFetching] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

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

  const filteredEmails = emails.filter(email =>
    searchTerm === '' ||
    email.subject?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    email.sender?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="bg-white/90 backdrop-blur-md rounded-2xl p-6 shadow-lg border border-gray-200">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl text-gray-900 flex items-center gap-2">
          <Mail className="w-6 h-6 text-[#FFC107]" />
          📬 Inbox
        </h2>
        <div className="flex gap-2">
          <button
            onClick={refetch}
            disabled={loading}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50 transition flex items-center gap-2"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <button
            onClick={handleFetchFromGmail}
            disabled={fetching}
            className="px-4 py-2 bg-[#FFC107] text-gray-900 rounded-lg hover:bg-[#FFB300] disabled:opacity-50 transition flex items-center gap-2 font-medium"
          >
            <Mail className="w-4 h-4" />
            {fetching ? 'Fetching...' : 'Fetch from Gmail'}
          </button>
        </div>
      </div>

      {/* Search */}
      <div className="mb-6">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search emails..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#FFC107]"
          />
        </div>
      </div>

      {/* Loading */}
      {loading && (
        <div className="flex flex-col items-center justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#FFC107] mb-4"></div>
          <p className="text-gray-600">Loading emails...</p>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          ⚠️ Error: {error.message}
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && emails.length === 0 && (
        <div className="text-center py-12">
          <div className="text-6xl mb-4">📭</div>
          <div className="text-xl font-semibold text-gray-900 mb-2">No emails yet</div>
          <div className="text-gray-600 mb-6">Fetch your emails from Gmail to get started</div>
          <button
            onClick={handleFetchFromGmail}
            disabled={fetching}
            className="px-6 py-3 bg-[#FFC107] text-gray-900 rounded-lg hover:bg-[#FFB300] transition font-medium"
          >
            {fetching ? 'Fetching...' : 'Fetch Emails from Gmail'}
          </button>
        </div>
      )}

      {/* Email List */}
      {!loading && !error && filteredEmails.length > 0 && (
        <div className="space-y-3">
          {filteredEmails.map((email) => (
            <div
              key={email.id}
              className="border border-gray-200 rounded-lg p-4 hover:border-[#FFC107] hover:shadow-md transition cursor-pointer bg-white"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-medium text-gray-900 truncate">
                      {email.sender}
                    </span>
                    <span className="text-xs text-gray-500 flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {new Date(email.received_at).toLocaleDateString()}
                    </span>
                  </div>
                  <h3 className="text-sm font-semibold text-gray-800 mb-2">
                    {email.subject || '(No Subject)'}
                  </h3>
                  <p className="text-xs text-gray-600 line-clamp-2">
                    {email.body}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Count */}
      {!loading && filteredEmails.length > 0 && (
        <div className="mt-4 text-sm text-gray-600 text-center">
          Showing {filteredEmails.length} of {emails.length} emails
        </div>
      )}
    </div>
  );
}