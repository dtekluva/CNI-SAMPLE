import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { apiGet, apiPost } from "../api/client";

export type Session = {
  authenticated: boolean;
  mfa_verified?: boolean;
  email?: string;
  name?: string;
};

type AuthValue = {
  session: Session | null;
  ready: boolean;
  refresh: () => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
};

const Ctx = createContext<AuthValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [ready, setReady] = useState(false);

  async function refresh() {
    try {
      setSession(await apiGet<Session>("/auth/session/"));
    } catch {
      setSession({ authenticated: false });
    } finally {
      setReady(true);
    }
  }

  useEffect(() => {
    apiGet("/auth/csrf/").catch(() => {});
    refresh();
  }, []);

  async function login(email: string, password: string) {
    await apiPost("/auth/login/", { email, password });
    await refresh();
  }

  async function logout() {
    await apiPost("/auth/logout/").catch(() => {});
    setSession({ authenticated: false });
  }

  return <Ctx.Provider value={{ session, ready, refresh, login, logout }}>{children}</Ctx.Provider>;
}

export function useAuth(): AuthValue {
  const v = useContext(Ctx);
  if (!v) throw new Error("useAuth must be used within AuthProvider");
  return v;
}
