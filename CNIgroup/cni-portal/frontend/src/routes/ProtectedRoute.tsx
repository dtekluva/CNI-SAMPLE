import type { ReactElement } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export function ProtectedRoute({ children }: { children: ReactElement }) {
  const { session, ready } = useAuth();
  if (!ready) return <div className="ns" style={{ padding: "var(--ns-space-lg)" }}>Loading…</div>;
  if (!session?.authenticated) return <Navigate to="/login" replace />;
  if (!session.mfa_verified) return <Navigate to="/mfa" replace />;
  return children;
}
