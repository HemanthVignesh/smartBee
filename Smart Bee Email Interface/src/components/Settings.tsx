import { useState, useEffect } from "react";
import { Settings, Brain, Key, Sliders, Mail, Loader2, Save, Trash2, CheckCircle, XCircle } from "lucide-react";
import { api } from "../api/client";

// ─── Types ────────────────────────────────────────────────────────────────────

interface KeyStatus {
  configured: boolean;
  source: "env" | "database" | "none";
  masked: string;   // e.g.  ••••••••abcd
}

interface SettingsData {
  ai_model_mode: string;
  gemini_key_status: KeyStatus;
  openai_key_status: KeyStatus;
  auto_process: boolean;
  confidence_threshold: number;
  max_daily_automations: number;
}

// ─── Small key-row component ─────────────────────────────────────────────────

function KeyRow({
  label,
  placeholder,
  status,
  value,
  onChange,
  onRemove,
  disabled,
}: {
  label: string;
  placeholder: string;
  status: KeyStatus;
  value: string;
  onChange: (v: string) => void;
  onRemove: () => void;
  disabled?: boolean;
}) {
  const fromEnv = status.source === "env";
  const inDB    = status.source === "database";

  return (
    <div className="space-y-2">
      {/* Label row */}
      <div className="flex items-center justify-between">
        <label className="text-xs font-bold text-gray-500 uppercase tracking-wider">{label}</label>
        {fromEnv && (
          <span className="text-[9px] font-bold px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-700 border border-blue-500/20 animate-pulse">
            ⚙️ Set in .env — read-only
          </span>
        )}
        {inDB && !fromEnv && (
          <span className="text-[9px] font-bold px-2 py-0.5 rounded-full bg-green-500/10 text-green-700 border border-green-500/20 flex items-center gap-1">
            <CheckCircle className="w-2.5 h-2.5" /> Configured
          </span>
        )}
        {!status.configured && (
          <span className="text-[9px] font-bold px-2 py-0.5 rounded-full bg-red-500/10 text-red-600 border border-red-500/20 flex items-center gap-1">
            <XCircle className="w-2.5 h-2.5" /> Not set
          </span>
        )}
      </div>

      {/* Input row */}
      <div className="flex gap-2">
        <input
          type="password"
          value={fromEnv ? status.masked : value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={fromEnv ? "Managed in .env file" : status.masked || placeholder}
          disabled={fromEnv || disabled}
          className={`flex-1 px-4 py-2.5 border border-gray-200 rounded-xl focus:outline-none focus:ring-1 focus:ring-amber-500 text-sm bg-white font-mono ${
            fromEnv ? "text-gray-400 bg-gray-50 cursor-not-allowed" : ""
          }`}
        />
        {/* Remove button — only shown when key is stored in DB (not env) */}
        {inDB && !fromEnv && (
          <button
            type="button"
            onClick={onRemove}
            title="Remove stored key"
            className="p-2.5 border border-red-200 text-red-500 hover:bg-red-50 rounded-xl transition cursor-pointer"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Helper text */}
      {!fromEnv && !status.configured && (
        <p className="text-[10px] text-gray-400">
          Enter your key above and click Save. It will be encrypted before storage — never stored in plain text.
        </p>
      )}
      {!fromEnv && inDB && (
        <p className="text-[10px] text-gray-400">
          Showing {status.masked}. Enter a new value to replace, or click the trash icon to remove.
        </p>
      )}
    </div>
  );
}

// ─── Main component ──────────────────────────────────────────────────────────

export function SettingsComponent() {
  const [loading, setLoading]   = useState(true);
  const [saving, setSaving]     = useState(false);
  const [testingGmail, setTestingGmail] = useState(false);
  const [gmailMsg, setGmailMsg] = useState("");
  const [gmailOk, setGmailOk]   = useState(false);
  const [saveMsg, setSaveMsg]   = useState<{ ok: boolean; text: string } | null>(null);

  // Non-secret settings
  const [modelMode, setModelMode]   = useState("local");
  const [autoProcess, setAutoProcess] = useState(true);
  const [confidence, setConfidence] = useState(80);
  const [maxDaily, setMaxDaily]     = useState(50);

  // Key input values (what the user is typing right now)
  const [geminiInput, setGeminiInput] = useState("");
  const [openaiInput, setOpenaiInput] = useState("");

  // Key status from the server (masked + source)
  const [geminiStatus, setGeminiStatus] = useState<KeyStatus>({ configured: false, source: "none", masked: "" });
  const [openaiStatus, setOpenaiStatus] = useState<KeyStatus>({ configured: false, source: "none", masked: "" });

  // ─── Load ────────────────────────────────────────────────────────────────
  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        const data: SettingsData = await api.getSettings();
        setModelMode(data.ai_model_mode || "local");
        setAutoProcess(data.auto_process !== false);
        setConfidence(Math.round((data.confidence_threshold || 0.8) * 100));
        setMaxDaily(data.max_daily_automations || 50);
        setGeminiStatus(data.gemini_key_status || { configured: false, source: "none", masked: "" });
        setOpenaiStatus(data.openai_key_status || { configured: false, source: "none", masked: "" });
      } catch (err: any) {
        console.error("Failed to load settings:", err);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  // ─── Save ─────────────────────────────────────────────────────────────────
  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSaving(true);
      setSaveMsg(null);

      const payload: Record<string, unknown> = {
        ai_model_mode: modelMode,
        auto_process: autoProcess,
        confidence_threshold: confidence / 100,
        max_daily_automations: maxDaily,
      };

      // Only send key if the user actually typed something new
      if (geminiInput) payload.gemini_api_key = geminiInput;
      if (openaiInput) payload.openai_api_key = openaiInput;

      const res = await api.updateSettings(payload);

      // Refresh key status from server response
      if (res.gemini_key_status) setGeminiStatus(res.gemini_key_status);
      if (res.openai_key_status) setOpenaiStatus(res.openai_key_status);

      // Clear the input boxes — key is now stored
      setGeminiInput("");
      setOpenaiInput("");

      setSaveMsg({ ok: true, text: "Settings saved. Keys encrypted and stored securely." });
    } catch (err: any) {
      setSaveMsg({ ok: false, text: `Save failed: ${err.message}` });
    } finally {
      setSaving(false);
    }
  };

  // ─── Remove key ──────────────────────────────────────────────────────────
  const handleRemoveKey = async (provider: "gemini" | "openai") => {
    if (!confirm(`Remove the stored ${provider} key?`)) return;
    try {
      await fetch(`/api/v1/settings/keys/${provider}`, { method: "DELETE" });
      const freshStatus: KeyStatus = { configured: false, source: "none", masked: "" };
      if (provider === "gemini") setGeminiStatus(freshStatus);
      else setOpenaiStatus(freshStatus);
      setSaveMsg({ ok: true, text: `${provider} key removed.` });
    } catch (err: any) {
      setSaveMsg({ ok: false, text: `Remove failed: ${err.message}` });
    }
  };

  // ─── Test Gmail ──────────────────────────────────────────────────────────
  const handleTestGmail = async () => {
    try {
      setTestingGmail(true);
      setGmailMsg("");
      const res = await api.getGmailProfile();
      setGmailOk(true);
      setGmailMsg(`Connected: ${res.message || "OAuth handshake successful"}`);
    } catch (err: any) {
      setGmailOk(false);
      setGmailMsg(`Error: ${err.message || "credentials.json not found."}`);
    } finally {
      setTestingGmail(false);
    }
  };

  // ─── Loading screen ───────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 gap-3 bg-white/80 backdrop-blur-xl rounded-3xl p-6 border border-gray-200/50 shadow-xl">
        <Loader2 className="w-8 h-8 text-amber-500 animate-spin" />
        <p className="text-xs text-gray-500 font-semibold">Loading settings...</p>
      </div>
    );
  }

  // ─── Render ───────────────────────────────────────────────────────────────
  return (
    <div className="bg-white/80 backdrop-blur-xl rounded-3xl p-6 shadow-xl border border-gray-200/50 hover:shadow-2xl transition-all duration-300 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-3 mb-8 border-b border-gray-150 pb-5">
        <div className="p-2.5 bg-amber-500/10 rounded-2xl">
          <Settings className="w-5 h-5 text-amber-600" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-gray-900 tracking-tight">System Settings</h2>
          <p className="text-xs text-gray-500">API keys are encrypted at rest — never stored or returned in plain text</p>
        </div>
      </div>

      <form onSubmit={handleSave} className="space-y-8">

        {/* ── AI Model Mode ─────────────────────────────────────────────── */}
        <div className="space-y-4">
          <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider flex items-center gap-2">
            <Brain className="w-4 h-4 text-gray-400" /> AI Inference Engine
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {(["local", "gemini", "openai"] as const).map((mode) => (
              <div
                key={mode}
                onClick={() => setModelMode(mode)}
                className={`p-5 rounded-2xl border cursor-pointer flex flex-col justify-between transition-all ${
                  modelMode === mode
                    ? "bg-amber-500/5 border-amber-500 shadow-sm"
                    : "bg-white/40 border-gray-200 hover:border-gray-300"
                }`}
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-bold text-gray-900">
                      {mode === "local" ? "Local Transformer" : mode === "gemini" ? "Google Gemini" : "OpenAI GPT"}
                    </span>
                    <span className={`text-[9px] font-bold px-2 py-0.5 rounded-full border ${
                      mode === "local" ? "bg-green-500/10 text-green-700 border-green-500/20"
                      : mode === "gemini" ? "bg-blue-500/10 text-blue-700 border-blue-500/20"
                      : "bg-purple-500/10 text-purple-700 border-purple-500/20"
                    }`}>
                      {mode === "local" ? "Offline T5" : mode === "gemini" ? "Cloud Flash" : "Cloud GPT"}
                    </span>
                  </div>
                  <p className="text-[11px] text-gray-500 leading-relaxed">
                    {mode === "local"
                      ? "Runs locally. No API keys needed."
                      : mode === "gemini"
                      ? "Gemini 2.5 Flash — fast, accurate, cheap."
                      : "GPT-3.5 Turbo — great for drafting replies."}
                  </p>
                </div>
                <div className="mt-4 flex items-center gap-1.5">
                  <input type="radio" checked={modelMode === mode} onChange={() => setModelMode(mode)} className="accent-amber-500" />
                  <span className="text-xs font-semibold text-gray-800">Use {mode === "local" ? "Local" : mode === "gemini" ? "Gemini" : "OpenAI"}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* ── API Keys ──────────────────────────────────────────────────── */}
        {(modelMode === "gemini" || modelMode === "openai") && (
          <div className="space-y-4 animate-in slide-in-from-top-3 duration-250">
            <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider flex items-center gap-2">
              <Key className="w-4 h-4 text-gray-400" /> API Key Configuration
            </h3>
            <div className="bg-amber-50/50 border border-amber-200/50 rounded-xl px-4 py-3 text-[11px] text-amber-800">
              🔒 Keys are encrypted with AES-128 before being stored. The backend never returns the full key value — only a masked preview.
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {modelMode === "gemini" && (
                <KeyRow
                  label="Google Gemini API Key"
                  placeholder="AIzaSy..."
                  status={geminiStatus}
                  value={geminiInput}
                  onChange={setGeminiInput}
                  onRemove={() => handleRemoveKey("gemini")}
                />
              )}
              {modelMode === "openai" && (
                <KeyRow
                  label="OpenAI API Key"
                  placeholder="sk-proj-..."
                  status={openaiStatus}
                  value={openaiInput}
                  onChange={setOpenaiInput}
                  onRemove={() => handleRemoveKey("openai")}
                />
              )}
            </div>
          </div>
        )}

        {/* ── Triage Parameters ─────────────────────────────────────────── */}
        <div className="space-y-5">
          <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider flex items-center gap-2">
            <Sliders className="w-4 h-4 text-gray-400" /> Email Triage Control
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 bg-gray-50/50 p-5 rounded-2xl border border-gray-150">
            <div className="flex items-center justify-between gap-4">
              <div>
                <div className="text-xs font-bold text-gray-800 mb-0.5">Auto-Triage incoming mail</div>
                <p className="text-[10px] text-gray-500">Automatically run new messages through the AI intent engine.</p>
              </div>
              <button type="button" onClick={() => setAutoProcess(!autoProcess)}
                className={`relative inline-flex h-6 w-11 shrink-0 rounded-full border-2 border-transparent transition-colors cursor-pointer ${autoProcess ? "bg-amber-500" : "bg-gray-200"}`}>
                <span className={`inline-block h-5 w-5 transform rounded-full bg-white shadow transition ${autoProcess ? "translate-x-5" : "translate-x-0"}`} />
              </button>
            </div>
            <div className="flex items-center justify-between gap-4">
              <div>
                <div className="text-xs font-bold text-gray-800 mb-0.5">Max daily automations</div>
                <p className="text-[10px] text-gray-500">Safeguard against runaway AI spend.</p>
              </div>
              <input type="number" value={maxDaily} onChange={(e) => setMaxDaily(parseInt(e.target.value) || 0)}
                className="w-20 px-3 py-1.5 border border-gray-200 rounded-xl text-sm text-center bg-white focus:outline-none focus:ring-1 focus:ring-amber-500"
                min={1} max={500} />
            </div>
            <div className="md:col-span-2 pt-2 border-t border-gray-200/50">
              <div className="flex items-center justify-between text-xs font-bold text-gray-800 mb-2">
                <span>AI Confidence Threshold</span>
                <span className="text-amber-600 bg-amber-500/10 px-2 py-0.5 rounded-full">{confidence}%</span>
              </div>
              <input type="range" min="50" max="95" step="5" value={confidence}
                onChange={(e) => setConfidence(parseInt(e.target.value))}
                className="w-full h-1.5 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-amber-500" />
              <div className="flex justify-between text-[9px] text-gray-400 font-bold uppercase mt-1">
                <span>Fast (50%)</span><span>Accurate (95%)</span>
              </div>
            </div>
          </div>
        </div>

        {/* ── Gmail Diagnostics ─────────────────────────────────────────── */}
        <div className="space-y-4">
          <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider flex items-center gap-2">
            <Mail className="w-4 h-4 text-gray-400" /> Gmail Integration
          </h3>
          <div className="bg-white/40 border border-gray-150 p-5 rounded-2xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className={`w-3.5 h-3.5 rounded-full shrink-0 ${gmailOk ? "bg-green-500 animate-pulse" : "bg-red-400"}`} />
              <div>
                <div className="text-xs font-bold text-gray-900">Gmail OAuth Status</div>
                <div className="text-[10px] text-gray-500 mt-0.5">
                  {gmailOk ? "Token handshake successful" : "Offline — credentials.json not found"}
                </div>
              </div>
            </div>
            <button type="button" onClick={handleTestGmail} disabled={testingGmail}
              className="px-4 py-2 border border-gray-200 hover:bg-gray-50 font-semibold text-gray-700 rounded-full text-xs transition disabled:opacity-50 cursor-pointer flex items-center gap-1.5">
              {testingGmail && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
              Run Diagnostics
            </button>
          </div>
          {gmailMsg && (
            <div className={`p-4 rounded-xl text-xs font-mono whitespace-pre-wrap leading-relaxed ${
              gmailOk ? "bg-green-50/50 text-green-700 border border-green-200/50" : "bg-red-50/50 text-red-700 border border-red-200/50"}`}>
              {gmailMsg}
            </div>
          )}
        </div>

        {/* ── Save feedback ─────────────────────────────────────────────── */}
        {saveMsg && (
          <div className={`px-4 py-3 rounded-xl text-xs font-semibold flex items-center gap-2 ${
            saveMsg.ok ? "bg-green-50 text-green-700 border border-green-200" : "bg-red-50 text-red-700 border border-red-200"}`}>
            {saveMsg.ok ? <CheckCircle className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
            {saveMsg.text}
          </div>
        )}

        {/* ── Save button ────────────────────────────────────────────────── */}
        <div className="flex justify-end pt-5 border-t border-gray-100">
          <button type="submit" disabled={saving}
            className="px-6 py-3 bg-amber-500 hover:bg-amber-600 text-black font-semibold rounded-full shadow-md shadow-amber-500/15 transition flex items-center gap-2 text-xs cursor-pointer disabled:opacity-50">
            {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
            Save Configuration
          </button>
        </div>
      </form>
    </div>
  );
}
