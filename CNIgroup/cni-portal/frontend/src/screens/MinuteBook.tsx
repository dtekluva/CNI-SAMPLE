import { useState } from "react";
import { apiGet } from "../api/client";
import { useApi } from "../api/useApi";
import { Button, EmptyState, Icon, PageHeader, PdfViewer } from "../ui";

type Entry = {
  id: number;
  state: string;
  content_hash: string;
  signed_at: string | null;
  signed_by_name: string | null;
  meeting_title: string;
  meeting_date: string;
  entity: number;
  entity_name: string;
};
type Integrity = {
  audit_chain: { intact: boolean; events: number };
  sealed_minutes: { id: number; intact: boolean }[];
  all_intact: boolean;
};
type Entity = { id: number; legal_name: string };

const MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"];

function IntegrityBand() {
  const { data, reload } = useApi<Integrity>("/integrity/");
  const [busy, setBusy] = useState(false);
  if (!data || !data.audit_chain) return null; // non-admins (403) see no band
  const ok = data.all_intact;

  async function rerun() {
    setBusy(true);
    try {
      reload();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className={`ns-hero${ok ? "" : " ns-hero--bad"}`} style={{ marginBottom: "var(--ns-space-lg)" }}>
      <Icon name="shield" />
      <div>
        <div className="ns-hero__title">{ok ? "Record integrity verified" : "Integrity check FAILED"}</div>
        <div className="ns-hero__sub">
          Audit chain {data.audit_chain.intact ? "intact" : "BROKEN"} · {data.audit_chain.events.toLocaleString()} events ·{" "}
          {data.sealed_minutes.length} sealed minute{data.sealed_minutes.length === 1 ? "" : "s"}
          {ok ? " · every seal holds" : " · investigate immediately"}
        </div>
      </div>
      <div className="ns-hero__actions">
        <Button size="sm" variant="secondary" onClick={rerun} disabled={busy}>
          {busy ? "Verifying…" : "Re-verify"}
        </Button>
      </div>
    </div>
  );
}

function Entry({ e }: { e: Entry }) {
  const [seal, setSeal] = useState<"unknown" | "ok" | "bad">("unknown");
  const [showPdf, setShowPdf] = useState(false);
  const d = new Date(e.meeting_date);

  async function verify() {
    try {
      const r = await apiGet<{ intact: boolean }>(`/minute-book/${e.id}/verify/`);
      setSeal(r.intact ? "ok" : "bad");
    } catch {
      setSeal("bad");
    }
  }

  return (
    <div className="ns-book__entry">
      <div className="ns-book__date">
        <div className="ns-book__day">{d.getDate()}</div>
        <div className="ns-book__mon">
          {MONTHS[d.getMonth()]} {d.getFullYear()}
        </div>
      </div>
      <div>
        <div className="ns-overline">{e.entity_name}</div>
        <div className="ns-book__title">{e.meeting_title}</div>
        <div className="ns-book__meta">
          Signed by {e.signed_by_name ?? "—"}
          {e.signed_at
            ? ` on ${new Date(e.signed_at).toLocaleDateString(undefined, { day: "numeric", month: "long", year: "numeric" })}`
            : ""}
        </div>
      </div>
      <div className="ns-book__side">
        {seal === "unknown" && <span className="ns-seal ns-seal--quiet">⌘ {e.content_hash ? e.content_hash.slice(0, 12) : "unsealed"}</span>}
        {seal === "ok" && <span className="ns-seal">✓ seal intact</span>}
        {seal === "bad" && <span className="ns-seal ns-seal--bad">✗ TAMPERED</span>}
        <div style={{ display: "flex", gap: "var(--ns-space-2xs)" }}>
          <Button size="sm" variant="secondary" onClick={() => setShowPdf(true)}>
            Open PDF
          </Button>
          <Button size="sm" variant="ghost" onClick={verify}>
            Verify seal
          </Button>
        </div>
      </div>
      {showPdf && (
        <PdfViewer
          overline="Minute Book"
          title={e.meeting_title}
          src={`/api/minute-book/${e.id}/pdf/`}
          onClose={() => setShowPdf(false)}
        />
      )}
    </div>
  );
}

export function MinuteBookScreen() {
  const [entity, setEntity] = useState("");
  const { data, loading } = useApi<Entry[]>(`/minute-book/${entity ? `?entity=${entity}` : ""}`);
  const { data: entitiesData } = useApi<Entity[]>("/entities/");
  const entries = Array.isArray(data) ? data : [];
  const entities = Array.isArray(entitiesData) ? entitiesData : [];

  return (
    <div>
      <PageHeader
        title="Minute Book"
        sub="The statutory record — every signed minute, sealed with a content hash and compiled chronologically per entity."
      />
      <IntegrityBand />
      {entities.length > 1 && (
        <div className="ns-chiprow" style={{ marginBottom: "var(--ns-space-md)" }}>
          <button className={`ns-chip${entity === "" ? " ns-chip--on" : ""}`} onClick={() => setEntity("")}>
            All entities
          </button>
          {entities.map((en) => (
            <button
              key={en.id}
              className={`ns-chip${entity === String(en.id) ? " ns-chip--on" : ""}`}
              onClick={() => setEntity(String(en.id))}
            >
              {en.legal_name}
            </button>
          ))}
        </div>
      )}
      <div className="ns-book">
        {entries.map((e) => (
          <Entry key={e.id} e={e} />
        ))}
      </div>
      {!loading && entries.length === 0 && (
        <EmptyState
          title="No signed minutes yet"
          hint="Minutes enter the book the moment they are signed — locked, hashed and exportable."
        />
      )}
      {entries.length > 0 && (
        <p className="ns-muted" style={{ fontSize: "var(--ns-size-caption)", marginTop: "var(--ns-space-md)" }}>
          Signed minutes are immutable. A correction is a fresh minute at a later meeting — the book is never rewritten.
        </p>
      )}
    </div>
  );
}
