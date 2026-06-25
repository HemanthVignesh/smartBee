/**
 * src/auth/LoginPage.tsx
 *
 * Full-screen sign-in page shown when no valid session exists.
 * Matches the SmartBee amber/honey visual identity.
 *
 * The only action is "Sign in with Google" — no passwords to manage.
 */

import { useAuth } from "./AuthContext";
import { HexagonPattern } from "../components/HexagonPattern";
import logo from "../assets/SmartBee_logo.png";

export function LoginPage() {
  const { login } = useAuth();

  return (
    <div className="min-h-screen bg-slate-50 relative overflow-hidden flex items-center justify-center">
      {/* Honeycomb background */}
      <HexagonPattern />

      {/* Ambient amber glow */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-amber-400/10 rounded-full blur-3xl" />
      </div>

      {/* Card */}
      <div className="relative z-10 w-full max-w-sm mx-4">
        {/* Glass card */}
        <div className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-2xl border border-gray-200/50 p-8 flex flex-col items-center gap-6">

          {/* Logo + wordmark */}
          <div className="flex flex-col items-center gap-3">
            <img
              src={logo}
              alt="Smart Bee"
              className="w-20 h-20 object-contain drop-shadow-md"
            />
            <div className="text-center">
              <h1 className="text-2xl font-bold text-gray-900 tracking-tight">
                Smart Bee
              </h1>
              <p className="text-xs text-gray-500 mt-0.5">
                Intelligent Email Management
              </p>
            </div>
          </div>

          {/* Divider */}
          <div className="w-full h-px bg-gradient-to-r from-transparent via-amber-300/60 to-transparent" />

          {/* Hero copy */}
          <div className="text-center space-y-1.5 px-2">
            <p className="text-sm font-semibold text-gray-800">
              Your inbox, automated.
            </p>
            <p className="text-xs text-gray-500 leading-relaxed">
              Sign in with Google to connect your Gmail inbox and let AI handle
              triage, replies, and scheduling.
            </p>
          </div>

          {/* Sign-in button */}
          <button
            onClick={login}
            className="w-full flex items-center justify-center gap-3 px-5 py-3 bg-white hover:bg-gray-50 active:bg-gray-100 border border-gray-300 hover:border-gray-400 text-gray-700 font-semibold rounded-2xl shadow-sm hover:shadow-md transition-all duration-200 cursor-pointer group"
          >
            {/* Google "G" logo */}
            <svg width="20" height="20" viewBox="0 0 48 48" className="shrink-0">
              <path
                fill="#EA4335"
                d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"
              />
              <path
                fill="#4285F4"
                d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"
              />
              <path
                fill="#FBBC05"
                d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"
              />
              <path
                fill="#34A853"
                d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"
              />
              <path fill="none" d="M0 0h48v48H0z" />
            </svg>
            <span>Continue with Google</span>
          </button>

          {/* Feature pills */}
          <div className="flex flex-wrap justify-center gap-2 pt-1">
            {[
              "📬 Gmail sync",
              "🧠 AI triage",
              "📅 Auto-scheduling",
              "🔒 Your data only",
            ].map((feat) => (
              <span
                key={feat}
                className="text-[10px] font-semibold text-gray-500 bg-gray-100/80 px-2.5 py-1 rounded-full border border-gray-200/60"
              >
                {feat}
              </span>
            ))}
          </div>

          {/* Privacy note */}
          <p className="text-[10px] text-gray-400 text-center leading-relaxed px-4">
            By signing in you agree to Smart Bee accessing your Gmail for
            read, send, and label management. Your data is never shared.
          </p>
        </div>

        {/* Below-card tagline */}
        <p className="text-center text-[10px] text-gray-400 mt-4 font-medium">
          Secured with Google OAuth 2.0 · JWT sessions · Per-user isolation
        </p>
      </div>
    </div>
  );
}
