"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { apiFetch, authHeaders, ApiError } from "@/lib/api";

const TOKEN_KEY = "pdf_qna_token";

export interface CurrentUser {
  id: number;
  username: string;
}

interface AuthContextValue {
  user: CurrentUser | null;
  token: string | null;
  loading: boolean;
  login: (token: string) => Promise<void>;
  logout: (options?: { expired?: boolean }) => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  const logout = useCallback(
    (options?: { expired?: boolean }) => {
      localStorage.removeItem(TOKEN_KEY);
      setToken(null);
      setUser(null);
      if (options?.expired) {
        toast.error("Session expired", { description: "Please log in again." });
      }
      router.push("/login");
    },
    [router]
  );

  const fetchMe = useCallback(
    async (activeToken: string) => {
      try {
        const me = await apiFetch<CurrentUser>("/api/auth/me", {
          headers: authHeaders(activeToken),
        });
        setUser(me);
      } catch (err) {
        if (err instanceof ApiError && err.status === 401) {
          logout({ expired: true });
        }
      }
    },
    [logout]
  );

  useEffect(() => {
    const stored = localStorage.getItem(TOKEN_KEY);
    if (stored) {
      // Reading a browser-only API (localStorage) on mount and syncing it into
      // state is exactly what this effect is for — not derivable during render.
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setToken(stored);
      fetchMe(stored).finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const login = useCallback(
    async (newToken: string) => {
      localStorage.setItem(TOKEN_KEY, newToken);
      setToken(newToken);
      await fetchMe(newToken);
    },
    [fetchMe]
  );

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
