import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { Button, Field, Overline } from "../ui";

export function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await login(email, password);
      navigate("/mfa"); // password OK -> MFA step
    } catch {
      setError("Invalid email or password.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="ns ns-auth">
      <div className="ns-auth__panel">
        <div>
          <div className="ns-shell__brand" style={{ padding: 0, marginBottom: "var(--ns-space-xl)" }}>
            <span className="mark">CL</span> C&I Leasing
          </div>
          <Overline>Governance Portal</Overline>
          <h1 className="ns-page__title" style={{ marginBottom: "var(--ns-space-lg)" }}>Sign in</h1>
          <form onSubmit={submit} style={{ display: "flex", flexDirection: "column", gap: "var(--ns-space-md)" }}>
            <Field label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="username" />
            <Field
              label="Password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              error={error ?? undefined}
            />
            <Button type="submit" disabled={busy}>
              {busy ? "Signing in…" : "Sign in"}
            </Button>
          </form>
          <p className="ns-muted" style={{ fontSize: "var(--ns-size-caption)", marginTop: "var(--ns-space-lg)" }}>
            Access is by invitation. Multi-factor authentication is mandatory.
          </p>
        </div>
      </div>
      <div className="ns-auth__brandside">
        <div className="ns-auth__tag">
          <h2>The group's boardroom, in one trusted place.</h2>
          <p>
            Meetings, packs, minutes, resolutions and statutory records for every C&I Leasing entity —
            scoped to your role, auditable to the last signature.
          </p>
        </div>
      </div>
    </div>
  );
}
