import { useEffect, useState } from "react";
import { EntitySwitcher, type Selection } from "./components/EntitySwitcher";

type Health = { status: string; service: string; version: string };

export default function App() {
  const [health, setHealth] = useState<Health | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [scope, setScope] = useState<Selection>({ id: "group", legal_name: "Group" });

  useEffect(() => {
    fetch("/api/health/")
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then(setHealth)
      .catch((e) => setError(String(e)));
  }, []);

  const inGroupView = scope.id === "group";

  return (
    <div className="ns" style={{ padding: "var(--ns-space-lg)", maxWidth: 720, margin: "0 auto" }}>
      <div className="ns-overline">CNI Group</div>
      <h1 style={{ fontSize: "var(--ns-size-display)", lineHeight: "var(--ns-lh-display)", margin: "4px 0 var(--ns-space-2xs)" }}>
        Governance Portal
      </h1>

      <div style={{ maxWidth: 320, marginTop: "var(--ns-space-md)" }}>
        <EntitySwitcher onSelect={setScope} />
      </div>

      <h2 style={{ fontSize: "var(--ns-size-heading)", marginTop: "var(--ns-space-md)" }}>
        {inGroupView ? "Group view — all entities" : `Entity view — ${scope.legal_name}`}
      </h2>

      <div className="ns-card" style={{ marginTop: "var(--ns-space-md)" }}>
        <div className="ns-card__body" style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <span>API health</span>
          {health ? (
            <span className="ns-badge ns-badge--success"><span className="ns-badge__dot" /> {health.status}</span>
          ) : error ? (
            <span className="ns-badge ns-badge--danger"><span className="ns-badge__dot" /> unreachable ({error})</span>
          ) : (
            <span className="ns-badge ns-badge--neutral"><span className="ns-badge__dot" /> checking…</span>
          )}
        </div>
      </div>
    </div>
  );
}
