/**
 * src/auth/AuthContext.tsx
 *
 * Global authentication state for SmartBee.
 *
 * • Reads/writes the JWT from localStorage under the key "sb_token".
 * • Exposes useAuth() hook consumed by every protected component.
 * • On mount, validates the stored token by calling GET /api/v1/auth/me.
 *   If the token is expired or invalid the user is silently signed out.
 */

import {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  ReactNode,
} from "react";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";
const TOKEN_KEY = "sb_token";

// ── Types ─────────────────────────────────────────────────────────────────────

export interface AuthUser {
  id: string;
  email: string;
  name: string | null;
  picture: string | null;
  is_active: boolean;
  created_at: string;
}

interface AuthContextValue {
  user: AuthUser | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: () => void;         // Redirect browser to Google OAuth
  logout: () => void;        // Clear token + reset state
  setTokenAndFetch: (token: string) => Promise<void>; // Called after OAuth callback
}

// ── Context ───────────────────────────────────────────────────────────────────

const AuthContext = createContext<AuthContextValue | null>(null);

// ── Provider ──────────────────────────────────────────────────────────────────

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(
    () => localStorage.getItem(TOKEN_KEY)
  );
  const [isLoading, setIsLoading] = useState(true);

  // ── Fetch /me with a given token ────────────────────────────────────────────
  const fetchMe = useCallback(async (jwt: string): Promise<AuthUser | null> => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/auth/me`, {
        headers: { Authorization: `Bearer ${jwt}` },
      });
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  }, []);

  // ── On mount: validate any stored token ─────────────────────────────────────
  useEffect(() => {
    const stored = localStorage.getItem(TOKEN_KEY);
    if (!stored) {
      setIsLoading(false);
      return;
    }

    fetchMe(stored).then((profile) => {
      if (profile) {
        setUser(profile);
        setToken(stored);
      } else {
        // Token invalid / expired — clear it
        localStorage.removeItem(TOKEN_KEY);
        setToken(null);
      }
      setIsLoading(false);
    });
  }, [fetchMe]);

  // ── Called after the OAuth callback sets the token in the URL hash ──────────
  const setTokenAndFetch = useCallback(
    async (newToken: string) => {
      localStorage.setItem(TOKEN_KEY, newToken);
      setToken(newToken);
      const profile = await fetchMe(newToken);
      if (profile) {
        setUser(profile);
      } else {
        // Something went wrong — don't store a bad token
        localStorage.removeItem(TOKEN_KEY);
        setToken(null);
      }
    },
    [fetchMe]
  );

  // ── Redirect to Google OAuth ─────────────────────────────────────────────────
  const login = useCallback(() => {
    window.location.href = `${API_BASE}/api/v1/auth/google/login`;
  }, []);

  // ── Sign out ─────────────────────────────────────────────────────────────────
  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setUser(null);
    // Optionally notify the server (fire-and-forget)
    if (token) {
      fetch(`${API_BASE}/api/v1/auth/logout`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      }).catch(() => {});
    }
  }, [token]);

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        isAuthenticated: !!user && !!token,
        login,
        logout,
        setTokenAndFetch,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

// ── Hook ──────────────────────────────────────────────────────────────────────

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
