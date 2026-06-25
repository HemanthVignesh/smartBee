/**
 * src/auth/AuthCallback.tsx
 *
 * The backend redirects here after a successful Google OAuth flow:
 *   http://localhost:5173/auth/callback#token=eyJ...
 *
 * This component reads the token from the URL hash (never visible to the
 * server), stores it via AuthContext, and sends the user to the dashboard.
 *
 * Mount this at the route  /auth/callback  in your router.
 */

import { useEffect, useState } from "react";
import { useAuth } from "./AuthContext";

export function AuthCallback() {
  const { setTokenAndFetch } = useAuth();
  const [status, setStatus] = useState<"loading" | "success" | "error">(
    "loading"
  );
  const [errorMsg, setErrorMsg] = useState("");

  useEffect(() => {
    // The token lives in the URL fragment (#token=…) — window.location.hash
    const hash = window.location.hash.slice(1); // remove leading '#'
    const params = new URLSearchParams(hash);
    const token = params.get("token");

    if (!token) {
      setErrorMsg(
        "No token in callback URL. The sign-in may have been cancelled."
      );
      setStatus("error");
      return;
    }

    setTokenAndFetch(token)
      .then(() => {
        setStatus("success");
        // Clear the token from the URL bar so it doesn't appear in history
        window.history.replaceState(null, "", "/auth/callback");
        // Navigate to dashboard
        setTimeout(() => {
          window.location.replace("/");
        }, 800);
      })
      .catch(() => {
        setErrorMsg("Failed to verify your session. Please try again.");
        setStatus("error");
      });
  }, [setTokenAndFetch]);

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center">
      <div className="text-center space-y-4">
        {status === "loading" && (
          <>
            <div className="w-12 h-12 border-4 border-amber-500 border-t-transparent rounded-full animate-spin mx-auto" />
            <p className="text-sm font-semibold text-gray-600">
              Signing you in…
            </p>
          </>
        )}
        {status === "success" && (
          <>
            <div className="text-4xl">✅</div>
            <p className="text-sm font-semibold text-gray-600">
              Signed in! Redirecting to your inbox…
            </p>
          </>
        )}
        {status === "error" && (
          <>
            <div className="text-4xl">❌</div>
            <p className="text-sm font-semibold text-red-600">{errorMsg}</p>
            <a
              href="/"
              className="inline-block px-4 py-2 bg-amber-500 hover:bg-amber-600 text-black font-semibold rounded-xl text-sm transition"
            >
              Back to Sign In
            </a>
          </>
        )}
      </div>
    </div>
  );
}
