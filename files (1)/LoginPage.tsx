/**
 * SmartBee — Login / Register page
 * Shown whenever the user is not authenticated.
 */

import { useState } from "react";
import { Loader2, Mail, Lock, User, AlertCircle, Eye, EyeOff } from "lucide-react";
import { useAuth } from "./AuthContext";
import logo from "../assets/SmartBee_logo.png";

type Mode = "login" | "register";

export function LoginPage() {
  const { login, register } = useAuth();

  const [mode,        setMode]        = useState<Mode>("login");
  const [email,       setEmail]       = useState("");
  const [password,    setPassword]    = useState("");
  const [displayName, setDisplayName] = useState("");
  const [showPass,    setShowPass]    = useState(false);
  const [loading,     setLoading]     = useState(false);
  const [error,       setError]       = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      if (mode === "login") {
        await login(email, password);
      } else {
        await register(email, password, displayName || undefined);
      }
    } catch (err: any) {
      setError(err.message || "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
      {/* Card */}
      <div className="w-full max-w-md">
        {/* Logo + title */}
        <div className="text-center mb-8">
          <img src={logo} alt="SmartBee" className="w-16 h-16 mx-auto mb-4 object-contain" />
          <h1 className="text-3xl font-bold text-gray-900 tracking-tight">Smart Bee</h1>
          <p className="text-sm text-gray-500 mt-1">Intelligent Email Management</p>
        </div>

        <div className="bg-white rounded-3xl shadow-xl border border-gray-200/50 p-8">
          {/* Mode switcher */}
          <div className="flex bg-gray-100 rounded-2xl p-1 mb-6 gap-1">
            {(["login", "register"] as const).map((m) => (
              <button
                key={m}
                type="button"
                onClick={() => { setMode(m); setError(null); }}
                className={`flex-1 py-2 rounded-xl text-sm font-semibold transition-all cursor-pointer ${
                  mode === m
                    ? "bg-white text-gray-900 shadow-sm"
                    : "text-gray-500 hover:text-gray-700"
                }`}
              >
                {m === "login" ? "Sign In" : "Create Account"}
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Display name — register only */}
            {mode === "register" && (
              <div>
                <label className="text-xs font-bold text-gray-500 uppercase tracking-wider block mb-1.5">
                  Display Name
                </label>
                <div className="relative">
                  <User className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    type="text"
                    value={displayName}
                    onChange={(e) => setDisplayName(e.target.value)}
                    placeholder="Your name (optional)"
                    className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-amber-400 bg-gray-50 focus:bg-white transition"
                  />
                </div>
              </div>
            )}

            {/* Email */}
            <div>
              <label className="text-xs font-bold text-gray-500 uppercase tracking-wider block mb-1.5">
                Email
              </label>
              <div className="relative">
                <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  required
                  autoComplete="email"
                  className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-amber-400 bg-gray-50 focus:bg-white transition"
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <label className="text-xs font-bold text-gray-500 uppercase tracking-wider block mb-1.5">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type={showPass ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder={mode === "register" ? "Min 8 chars, must include a number" : "Your password"}
                  required
                  autoComplete={mode === "login" ? "current-password" : "new-password"}
                  className="w-full pl-10 pr-11 py-3 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-amber-400 bg-gray-50 focus:bg-white transition"
                />
                <button
                  type="button"
                  onClick={() => setShowPass(!showPass)}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 cursor-pointer"
                >
                  {showPass ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Error */}
            {error && (
              <div className="flex items-start gap-2.5 p-3.5 bg-red-50 border border-red-200 rounded-xl">
                <AlertCircle className="w-4 h-4 text-red-500 shrink-0 mt-0.5" />
                <p className="text-sm text-red-700">{error}</p>
              </div>
            )}

            {/* Submit */}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-amber-500 hover:bg-amber-600 disabled:opacity-60 text-black font-bold rounded-xl shadow-md shadow-amber-500/20 transition flex items-center justify-center gap-2 cursor-pointer mt-2"
            >
              {loading && <Loader2 className="w-4 h-4 animate-spin" />}
              {mode === "login" ? "Sign In" : "Create Account"}
            </button>
          </form>

          {/* Footer hint */}
          <p className="text-center text-xs text-gray-400 mt-6">
            {mode === "login" ? (
              <>Don't have an account?{" "}
                <button onClick={() => { setMode("register"); setError(null); }} className="text-amber-600 font-semibold hover:underline cursor-pointer">
                  Create one
                </button>
              </>
            ) : (
              <>Already have an account?{" "}
                <button onClick={() => { setMode("login"); setError(null); }} className="text-amber-600 font-semibold hover:underline cursor-pointer">
                  Sign in
                </button>
              </>
            )}
          </p>
        </div>

        <p className="text-center text-[11px] text-gray-400 mt-6">
          Your data is encrypted at rest. Passwords are hashed with bcrypt.
        </p>
      </div>
    </div>
  );
}
