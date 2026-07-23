import { useEffect, useState } from "react";
import { apiPost } from "../api/client";
import { useApi } from "../api/useApi";
import { useAuth } from "../auth/AuthContext";
import { Badge, Card, CardBody, Overline, PageHeader } from "../ui";

type Pref = { event_type: string; channel: string; enabled: boolean };

const EVENTS: [string, string][] = [
  ["meeting.scheduled", "Meeting scheduled"],
  ["pack.published", "Board pack published"],
  ["resolution.circulated", "Resolution circulated"],
  ["minutes.finalized", "Minutes finalized"],
  ["action.assigned", "Action assigned to me"],
];
const CHANNELS: [string, string][] = [
  ["in_portal", "In-portal"],
  ["email", "Email"],
];

export function SettingsScreen() {
  const { session } = useAuth();
  const { data } = useApi<Pref[]>("/notifications/preferences/");
  const [prefs, setPrefs] = useState<Record<string, boolean>>({});

  useEffect(() => {
    if (!data) return;
    const map: Record<string, boolean> = {};
    for (const p of data) map[`${p.event_type}|${p.channel}`] = p.enabled;
    setPrefs(map);
  }, [data]);

  function isOn(event: string, channel: string) {
    return prefs[`${event}|${channel}`] ?? true; // default-on until user opts out
  }

  async function toggle(event: string, channel: string) {
    const next = !isOn(event, channel);
    setPrefs((p) => ({ ...p, [`${event}|${channel}`]: next }));
    await apiPost("/notifications/preferences/", { event_type: event, channel, enabled: next });
  }

  return (
    <div>
      <PageHeader title="Settings" sub="Your account, security posture, and how the portal reaches you." />

      <div style={{ display: "flex", flexDirection: "column", gap: "var(--ns-space-md)" }}>
        <Card>
          <CardBody>
            <Overline>Account</Overline>
            <div style={{ marginTop: "var(--ns-space-2xs)" }}>
              <div style={{ fontWeight: 600 }}>{session?.name ?? "—"}</div>
              <div style={{ color: "var(--ns-color-text-secondary)", fontSize: "var(--ns-size-body-sm)" }}>{session?.email ?? "—"}</div>
            </div>
            <div style={{ marginTop: "var(--ns-space-sm)" }}>
              {session?.mfa_verified ? <Badge tone="success">MFA active</Badge> : <Badge tone="warning">MFA not verified</Badge>}
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardBody>
            <Overline>Notification preferences</Overline>
            <table className="ns-table" style={{ width: "100%", marginTop: "var(--ns-space-sm)" }}>
              <thead>
                <tr>
                  <th style={{ textAlign: "left" }}>Event</th>
                  {CHANNELS.map(([c, label]) => (
                    <th key={c} style={{ textAlign: "center" }}>
                      {label}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {EVENTS.map(([ev, label]) => (
                  <tr key={ev}>
                    <td>{label}</td>
                    {CHANNELS.map(([c]) => (
                      <td key={c} style={{ textAlign: "center" }}>
                        <input
                          type="checkbox"
                          aria-label={`${label} — ${c}`}
                          checked={isOn(ev, c)}
                          onChange={() => toggle(ev, c)}
                        />
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
            <p style={{ color: "var(--ns-color-text-secondary)", fontSize: "var(--ns-size-body-sm)", marginTop: "var(--ns-space-sm)" }}>
              Statutory notices are always delivered and cannot be turned off.
            </p>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
