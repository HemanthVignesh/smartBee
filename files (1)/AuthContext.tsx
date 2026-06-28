/**
 * SmartBee — Auth context
 * ────────────────────────
 * Holds the current user + access token in React state (in-memory only).
 * The refresh token lives in an httpOnly cookie — JS never touches it.
 *
 * On every cold start (page load / refresh) we call POST /api/v1/auth/refresh.
 * If the cookie is present and valid, the server returns a new access token
 * and the user stays logged in silently.
 *
 * Usage anywhere in the component tree:
 *   const { user, token, login, logout, loading } = useAuth();
 */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

// ─── Types ────────────────────────────────────────────────────────────────────

export interface AuthUser {
  id: number;
  email: string;
  display_name: string | null;
  is_verified: boolean;
}

interface AuthState {
  user: AuthUser | null;
  token: string | null;
  loading: boolean;        // true while the initial /refresh probe runs
  login:   (email: string, password: string) => Promise<void>;
  register:(email: string, password: string, displayName?: string) => Promise<void>;
  logout:  () => Promise<void>;
  /** Refreshes the access token using the httpOnly cookie. */
  refreshToken: () => Promise<string | null>;
}

// ─── Context ─────────────────────────────────────────────────────────────────

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user,    setUser]    = useState<AuthUser | null>(null);
  const [token,   setToken]   = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Keep a ref so the interceptor in client.ts can call refresh without
  // creating a circular import
  const tokenRef = useRef<string | null>(null);
  tokenRef.current = token;

  // ── Core fetch helper (no auth header — used only for auth endpoints) ────
  const authFetch = useCallback(async (path: string, body: object) => {
    const res = await fetch(`${API}${path}`, {
      method:      "POST",
      headers:     { "Content-Type": "application/json" },
      credentials: "include",   // send/receive httpOnly cookies
      body:        JSON.stringify(body),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return res.json();
  }, []);

  // ── Refresh (silent re-login via cookie) ─────────────────────────────────
  const refreshToken = useCallback(async (): Promise<string | null> => {
    try {
      const data = await fetch(`${API}/api/v1/auth/refresh`, {
        method:      "POST",
        credentials: "include",
      });
      if (!data.ok) return null;
      const json = await data.json();
      setToken(json.access_token);
      setUser(json.user);
      return json.access_token;
    } catch {
      return null;
    }
  }, []);

  // ── On mount: probe the refresh endpoint to restore session ──────────────
  useEffect(() => {
    refreshToken().finally(() => setLoading(false));
  }, [refreshToken]);

  // ── Auto-refresh 5 minutes before expiry ─────────────────────────────────
  // ACCESS_TOKEN_EXPIRE_MINUTES is 60 in config → refresh at 55 min
  useEffect(() => {
    if (!token) return;
    const REFRESH_INTERVAL = (60 - 5) * 60 * 1000; // 55 minutes in ms
    const id = setTimeout(() => refreshToken(), REFRESH_INTERVAL);
    return () => clearTimeout(id);
  }, [token, refreshToken]);

  // ── Login ─────────────────────────────────────────────────────────────────
  const login = useCallback(async (email: string, password: string) => {
    const data = await authFetch("/api/v1/auth/login", { email, password });
    setToken(data.access_token);
    setUser(data.user);
  }, [authFetch]);

  // ── Register ──────────────────────────────────────────────────────────────
  const register = useCallback(async (
    email: string,
    password: string,
    displayName?: string,
  ) => {
    const data = await authFetch("/api/v1/auth/register", {
      email,
      password,
      display_name: displayName,
    });
    setToken(data.access_token);
    setUser(data.user);
  }, [authFetch]);

  // ── Logout ────────────────────────────────────────────────────────────────
  const logout = useCallback(async () => {
    await fetch(`${API}/api/v1/auth/logout`, {
      method:      "POST",
      credentials: "include",
    }).catch(() => {}); // best-effort
    setToken(null);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, logout, refreshToken }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
