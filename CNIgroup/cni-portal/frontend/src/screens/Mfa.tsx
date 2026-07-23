import { useEffect, useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { QRCodeSVG } from "qrcode.react";
import { apiPost } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { Button, Card, CardBody, Field, Overline } from "../ui";

type EnrollResponse = { config_url?: string; enrolled?: boolean };

/** Pull the base32 secret out of an otpauth:// URI for manual entry. */
function secretOf(configUrl: string): string | null {
  const q = configUrl.split("?")[1];
  return q ? new URLSearchParams(q).get("secret") : null;
}

export function Mfa() {
  const { refresh } = useAuth();
  const navigate = useNavigate();
  const [configUrl, setConfigUrl] = useState<string | null>(null);
  const [enrolled, setEnrolled] = useState<boolean>(false);
  const [token, setToken] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    apiPost<EnrollResponse>("/auth/mfa/enroll/")
      .then((r) => {
        if (r.enrolled) setEnrolled(true);
        else if (r.config_url) setConfigUrl(r.config_url);
      })
      .catch(() => {});
  }, []);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await apiPost("/auth/mfa/verify/", { token });
      await refresh();
      navigate("/");
    } catch {
      setError("Invalid code. Try again.");
    } finally {
      setBusy(false);
    }
  }

  const secret = configUrl ? secretOf(configUrl) : null;

  return (
    <div className="ns" style={{ minHeight: "100vh", display: "grid", placeItems: "center", background: "var(--ns-color-bg-secondary)" }}>
      <Card>
        <CardBody>
          <div className="ns-shell__brand" style={{ padding: 0, marginBottom: "var(--ns-space-md)" }}>
            <span className="mark">CG</span> CNI Group
          </div>
          <Overline>Security step</Overline>
          <h1 style={{ fontSize: "var(--ns-size-heading)", margin: "4px 0 var(--ns-space-sm)", letterSpacing: "-0.02em" }}>Multi-factor authentication</h1>

          {enrolled ? (
            <p style={{ color: "var(--ns-color-text-secondary)", fontSize: "var(--ns-size-body-sm)", maxWidth: 340 }}>
              Enter the 6-digit code from your authenticator app.
            </p>
          ) : (
            <>
              <p style={{ color: "var(--ns-color-text-secondary)", fontSize: "var(--ns-size-body-sm)", maxWidth: 340 }}>
                Scan this QR code with your authenticator app (Google Authenticator, Microsoft Authenticator, 1Password…), then
                enter the 6-digit code it shows.
              </p>
              {configUrl && (
                <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "var(--ns-space-2xs)", margin: "var(--ns-space-sm) 0" }}>
                  <div style={{ background: "#fff", padding: 12, borderRadius: "var(--ns-radius-small)" }}>
                    <QRCodeSVG value={configUrl} size={176} aria-label="MFA enrolment QR code" />
                  </div>
                  {secret && (
                    <div style={{ textAlign: "center" }}>
                      <div style={{ color: "var(--ns-color-text-secondary)", fontSize: "var(--ns-size-caption)" }}>
                        Can't scan? Enter this key manually:
                      </div>
                      <code className="ns-mono" style={{ fontSize: "var(--ns-size-caption)", wordBreak: "break-all", userSelect: "all" }}>
                        {secret}
                      </code>
                    </div>
                  )}
                </div>
              )}
            </>
          )}

          <form onSubmit={submit} style={{ display: "flex", flexDirection: "column", gap: "var(--ns-space-sm)", width: 320, marginTop: "var(--ns-space-sm)" }}>
            <Field
              label="Authentication code"
              inputMode="numeric"
              autoComplete="one-time-code"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              error={error ?? undefined}
            />
            <Button type="submit" disabled={busy}>
              {busy ? "Verifying…" : "Verify"}
            </Button>
          </form>
        </CardBody>
      </Card>
    </div>
  );
}
