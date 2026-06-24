import { useState, useEffect } from "react";
import { Settings, Brain, Key, Sliders, Mail, HelpCircle, Loader2, Save } from "lucide-react";
import { api } from "../api/client";

export function SettingsComponent() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testingGmail, setTestingGmail] = useState(false);
  
  // Settings State
  const [modelMode, setModelMode] = useState("local");
  const [geminiKey, setGeminiKey] = useState("");
  const [openaiKey, setOpenaiKey] = useState("");
  const [geminiFromEnv, setGeminiFromEnv] = useState(false);
  const [openaiFromEnv, setOpenaiFromEnv] = useState(false);
  const [autoProcess, setAutoProcess] = useState(true);
  const [confidence, setConfidence] = useState(80);
  const [maxDaily, setMaxDaily] = useState(50);
  
  // Diagnostics State
  const [gmailConnected, setGmailConnected] = useState(false);
  const [gmailProfileMsg, setGmailProfileMsg] = useState("");

  // Load Settings on Mount
  useEffect(() => {
    const fetchSettings = async () => {
      try {
        setLoading(true);
        const data = await api.getSettings();
        setModelMode(data.ai_model_mode || "local");
        setGeminiKey(data.gemini_api_key || "");
        setOpenaiKey(data.openai_api_key || "");
        setGeminiFromEnv(data.gemini_api_key_from_env || false);
        setOpenaiFromEnv(data.openai_api_key_from_env || false);
        setAutoProcess(data.auto_process !== false);
        setConfidence(Math.round((data.confidence_threshold || 0.8) * 100));
        setMaxDaily(data.max_daily_automations || 50);
        setGmailConnected(data.gmail_connected || false);
      } catch (err: any) {
        console.error("Failed to load settings:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchSettings();
  }, []);

  // Save Settings
  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSaving(true);
      const payload = {
        ai_model_mode: modelMode,
        gemini_api_key: geminiKey,
        openai_api_key: openaiKey,
        auto_process: autoProcess,
        confidence_threshold: confidence / 100,
        max_daily_automations: maxDaily
      };
      await api.updateSettings(payload);
      alert("✅ Settings saved successfully and synced to engine!");
    } catch (err: any) {
      alert("❌ Failed to save settings: " + err.message);
    } finally {
      setSaving(false);
    }
  };

  // Test Gmail Connection
  const handleTestGmail = async () => {
    try {
      setTestingGmail(true);
      setGmailProfileMsg("");
      const res = await api.getGmailProfile();
      setGmailConnected(true);
      setGmailProfileMsg(`Success: ${res.message || "Connected"}`);
    } catch (err: any) {
      setGmailConnected(false);
      setGmailProfileMsg(`Error: ${err.message || "OAuth files credentials.json not found."}`);
    } finally {
      setTestingGmail(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 gap-3 bg-white/80 backdrop-blur-xl rounded-3xl p-6 border border-gray-200/50 shadow-xl">
        <Loader2 className="w-8 h-8 text-amber-500 animate-spin" />
        <p className="text-xs text-gray-500 font-semibold">Loading system settings...</p>
      </div>
    );
  }

  return (
    <div className="bg-white/80 backdrop-blur-xl rounded-3xl p-6 shadow-xl border border-gray-200/50 hover:shadow-2xl transition-all duration-300 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-3 mb-8 border-b border-gray-150 pb-5">
        <div className="p-2.5 bg-amber-500/10 rounded-2xl">
          <Settings className="w-5 h-5 text-amber-600" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-gray-900 tracking-tight">System Settings</h2>
          <p className="text-xs text-gray-500">Configure AI models, API integrations, and email triage parameters</p>
        </div>
      </div>

      <form onSubmit={handleSave} className="space-y-8">
        
        {/* SECTION 1: AI Model Mode selection */}
        <div className="space-y-4">
          <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider flex items-center gap-2">
            <Brain className="w-4.5 h-4.5 text-gray-400" /> AI Inference Engine
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Option 1: Local Transformer */}
            <div 
              onClick={() => setModelMode("local")}
              className={`p-5 rounded-2xl border transition-all cursor-pointer relative flex flex-col justify-between ${
                modelMode === "local" 
                  ? "bg-amber-500/5 border-amber-500 shadow-sm" 
                  : "bg-white/40 border-gray-200 hover:border-gray-300"
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-gray-900">Local Transformer</span>
                  <span className="text-[9px] font-bold px-2 py-0.5 rounded-full bg-green-500/10 text-green-700 border border-green-500/20">Offline T5</span>
                </div>
                <p className="text-[11px] text-gray-500 leading-relaxed">
                  Runs locally on your CPU/MPS. Fully offline, private, and does not require credit cards or cloud API keys.
                </p>
              </div>
              <div className="mt-4 flex items-center gap-1.5">
                <input 
                  type="radio" 
                  checked={modelMode === "local"} 
                  onChange={() => setModelMode("local")} 
                  className="accent-amber-500 cursor-pointer"
                />
                <span className="text-xs font-semibold text-gray-800">Use Local T5 Model</span>
              </div>
            </div>

            {/* Option 2: Google Gemini */}
            <div 
              onClick={() => setModelMode("gemini")}
              className={`p-5 rounded-2xl border transition-all cursor-pointer relative flex flex-col justify-between ${
                modelMode === "gemini" 
                  ? "bg-amber-500/5 border-amber-500 shadow-sm" 
                  : "bg-white/40 border-gray-200 hover:border-gray-300"
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-gray-900">Google Gemini</span>
                  <span className="text-[9px] font-bold px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-700 border border-blue-500/20">Cloud Flash</span>
                </div>
                <p className="text-[11px] text-gray-500 leading-relaxed">
                  Uses the Google Gemini API (gemini-2.5-flash) for state-of-the-art accuracy, summaries, and action extraction.
                </p>
              </div>
              <div className="mt-4 flex items-center gap-1.5">
                <input 
                  type="radio" 
                  checked={modelMode === "gemini"} 
                  onChange={() => setModelMode("gemini")} 
                  className="accent-amber-500 cursor-pointer"
                />
                <span className="text-xs font-semibold text-gray-800">Use Gemini API</span>
              </div>
            </div>

            {/* Option 3: OpenAI */}
            <div 
              onClick={() => setModelMode("openai")}
              className={`p-5 rounded-2xl border transition-all cursor-pointer relative flex flex-col justify-between ${
                modelMode === "openai" 
                  ? "bg-amber-500/5 border-amber-500 shadow-sm" 
                  : "bg-white/40 border-gray-200 hover:border-gray-300"
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-gray-900">OpenAI GPT</span>
                  <span className="text-[9px] font-bold px-2 py-0.5 rounded-full bg-purple-500/10 text-purple-700 border border-purple-500/20">Cloud Turbo</span>
                </div>
                <p className="text-[11px] text-gray-500 leading-relaxed">
                  Uses OpenAI completions (gpt-3.5-turbo) to process intent, draft templates, and support chat conversations.
                </p>
              </div>
              <div className="mt-4 flex items-center gap-1.5">
                <input 
                  type="radio" 
                  checked={modelMode === "openai"} 
                  onChange={() => setModelMode("openai")} 
                  className="accent-amber-500 cursor-pointer"
                />
                <span className="text-xs font-semibold text-gray-800">Use OpenAI GPT</span>
              </div>
            </div>
          </div>
        </div>

        {/* SECTION 2: API Keys Configuration */}
        {(modelMode === "gemini" || modelMode === "openai") && (
          <div className="space-y-4 animate-in slide-in-from-top-3 duration-250">
            <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider flex items-center gap-2">
              <Key className="w-4.5 h-4.5 text-gray-400" /> API Keys Credentials
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {modelMode === "gemini" && (
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider">Google Gemini API Key:</label>
                    {geminiFromEnv ? (
                      <span className="text-[9px] font-bold px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-700 border border-blue-500/20 flex items-center gap-1 animate-pulse">
                        ⚙️ Loaded from backend .env
                      </span>
                    ) : geminiKey === "••••••••" ? (
                      <span className="text-[9px] font-bold px-2 py-0.5 rounded-full bg-green-500/10 text-green-700 border border-green-500/20 flex items-center gap-1">
                        🔒 Configured & Secured
                      </span>
                    ) : null}
                  </div>
                  <input
                    type="password"
                    value={geminiKey}
                    onChange={(e) => setGeminiKey(e.target.value)}
                    placeholder={geminiFromEnv ? "Configured in backend .env file" : "AIzaSy..."}
                    className={`w-full px-4 py-2.5 border border-gray-200 rounded-xl focus:outline-none focus:ring-1 focus:ring-amber-500 focus:border-transparent text-sm bg-white ${
                      geminiFromEnv ? "text-gray-400 font-mono bg-gray-50 cursor-not-allowed" : ""
                    }`}
                    disabled={geminiFromEnv}
                    required={!geminiFromEnv}
                  />
                </div>
              )}
              
              {modelMode === "openai" && (
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider">OpenAI API Key:</label>
                    {openaiFromEnv ? (
                      <span className="text-[9px] font-bold px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-700 border border-blue-500/20 flex items-center gap-1 animate-pulse">
                        ⚙️ Loaded from backend .env
                      </span>
                    ) : openaiKey === "••••••••" ? (
                      <span className="text-[9px] font-bold px-2 py-0.5 rounded-full bg-green-500/10 text-green-700 border border-green-500/20 flex items-center gap-1">
                        🔒 Configured & Secured
                      </span>
                    ) : null}
                  </div>
                  <input
                    type="password"
                    value={openaiKey}
                    onChange={(e) => setOpenaiKey(e.target.value)}
                    placeholder={openaiFromEnv ? "Configured in backend .env file" : "sk-proj-..."}
                    className={`w-full px-4 py-2.5 border border-gray-200 rounded-xl focus:outline-none focus:ring-1 focus:ring-amber-500 focus:border-transparent text-sm bg-white ${
                      openaiFromEnv ? "text-gray-400 font-mono bg-gray-50 cursor-not-allowed" : ""
                    }`}
                    disabled={openaiFromEnv}
                    required={!openaiFromEnv}
                  />
                </div>
              )}
            </div>
          </div>
        )}

        {/* SECTION 3: Tuning Parameters */}
        <div className="space-y-5">
          <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider flex items-center gap-2">
            <Sliders className="w-4.5 h-4.5 text-gray-400" /> Email Triage Control
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 bg-gray-50/50 p-5 rounded-2xl border border-gray-150">
            {/* Auto process toggle */}
            <div className="flex items-center justify-between gap-4">
              <div>
                <div className="text-xs font-bold text-gray-800 mb-0.5">Auto-Triage incoming mail</div>
                <p className="text-[10px] text-gray-500 leading-normal">
                  Automatically process incoming messages through the intent engine upon ingestion.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setAutoProcess(!autoProcess)}
                className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                  autoProcess ? "bg-amber-500" : "bg-gray-200"
                }`}
              >
                <span className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                  autoProcess ? "translate-x-5" : "translate-x-0"
                }`} />
              </button>
            </div>

            {/* Daily limit */}
            <div className="flex items-center justify-between gap-4">
              <div>
                <div className="text-xs font-bold text-gray-800 mb-0.5">Max daily automations</div>
                <p className="text-[10px] text-gray-500 leading-normal">
                  Safeguard threshold of AI-processed triage requests per 24 hour window.
                </p>
              </div>
              <input
                type="number"
                value={maxDaily}
                onChange={(e) => setMaxDaily(parseInt(e.target.value) || 0)}
                className="w-20 px-3 py-1.5 border border-gray-200 rounded-xl focus:outline-none focus:ring-1 focus:ring-amber-500 focus:border-transparent text-sm text-center bg-white"
                min={1}
                max={500}
              />
            </div>
            
            {/* Slider threshold - span cols */}
            <div className="md:col-span-2 pt-2 border-t border-gray-200/50">
              <div className="flex items-center justify-between text-xs font-bold text-gray-800 mb-2">
                <span>AI Confidence Threshold:</span>
                <span className="text-amber-600 bg-amber-500/10 px-2 py-0.5 rounded-full">{confidence}%</span>
              </div>
              <input
                type="range"
                min="50"
                max="95"
                step="5"
                value={confidence}
                onChange={(e) => setConfidence(parseInt(e.target.value))}
                className="w-full h-1.5 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-amber-500 focus:outline-none"
              />
              <div className="flex justify-between text-[9px] text-gray-400 font-bold uppercase mt-1">
                <span>Fast & Dynamic (50%)</span>
                <span>Highly Accurate (95%)</span>
              </div>
            </div>
          </div>
        </div>

        {/* SECTION 4: Integration Diagnostics */}
        <div className="space-y-4">
          <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider flex items-center gap-2">
            <Mail className="w-4.5 h-4.5 text-gray-400" /> API Integration Diagnostics
          </h3>
          
          <div className="bg-white/40 border border-gray-150 p-5 rounded-2xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className={`w-3.5 h-3.5 rounded-full shrink-0 ${gmailConnected ? "bg-green-500 animate-pulse" : "bg-red-400"}`}></div>
              <div>
                <div className="text-xs font-bold text-gray-900">Gmail OAuth Link Status</div>
                <div className="text-[10px] text-gray-500 mt-0.5">
                  {gmailConnected ? "Dynamic API token handshake successful" : "Handshake offline. credentials.json file check failed."}
                </div>
              </div>
            </div>
            
            <div className="flex items-center gap-2.5 ml-auto md:ml-0">
              <button
                type="button"
                onClick={handleTestGmail}
                disabled={testingGmail}
                className="px-4 py-2 border border-gray-200 hover:bg-gray-50 font-semibold text-gray-700 rounded-full text-xs transition disabled:opacity-50 cursor-pointer flex items-center gap-1.5"
              >
                {testingGmail && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                Run Diagnostics
              </button>
            </div>
          </div>
          {gmailProfileMsg && (
            <div className={`p-4 rounded-xl text-xs font-mono whitespace-pre-wrap leading-relaxed ${
              gmailConnected ? "bg-green-50/50 text-green-700 border border-green-200/50" : "bg-red-50/50 text-red-700 border border-red-200/50"
            }`}>
              {gmailProfileMsg}
            </div>
          )}
        </div>

        {/* Save button panel */}
        <div className="flex justify-end pt-5 border-t border-gray-100">
          <button
            type="submit"
            disabled={saving}
            className="px-6 py-3 bg-amber-500 hover:bg-amber-600 text-black font-semibold rounded-full shadow-md shadow-amber-500/15 transition duration-200 flex items-center gap-2 text-xs cursor-pointer disabled:opacity-50"
          >
            {saving ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Save className="w-3.5 h-3.5" />
            )}
            Save Configuration
          </button>
        </div>
      </form>
    </div>
  );
}
