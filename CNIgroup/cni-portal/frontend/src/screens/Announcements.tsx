import { useEffect, useState, type FormEvent } from "react";
import { apiGet, apiPost } from "../api/client";
import { useApi } from "../api/useApi";
import { Badge, Button, Card, CardBody, EmptyState, Field, Overline, PageHeader } from "../ui";

type Announcement = {
  id: number;
  entity: number;
  title: string;
  body: string;
  posted_by_name: string | null;
  posted_at: string;
  read_by_me: boolean;
  read_count: number;
};
type Entity = { id: number; legal_name: string };
type Receipt = { user: number; name: string; read_at: string };

const fmtDate = (iso: string) => new Date(iso).toLocaleDateString(undefined, { day: "numeric", month: "long", year: "numeric" });

function Item({ a, entityName, canManage, onChange }: { a: Announcement; entityName: string; canManage: boolean; onChange: () => void }) {
  const [receipts, setReceipts] = useState<Receipt[] | null>(null);

  useEffect(() => {
    // opening the list marks it read for the current user
    if (!a.read_by_me) apiPost(`/announcements/${a.id}/read/`).then(onChange).catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [a.id]);

  async function showReceipts() {
    const r = await apiGet<Receipt[]>(`/announcements/${a.id}/receipts/`);
    setReceipts(Array.isArray(r) ? r : []);
  }

  return (
    <Card>
      <CardBody>
        <div style={{ display: "flex", justifyContent: "space-between", gap: "var(--ns-space-sm)", alignItems: "flex-start" }}>
          <div>
            <Overline>{entityName} · {a.posted_by_name ?? "—"} · {fmtDate(a.posted_at)}</Overline>
            <div style={{ fontFamily: "var(--ns-font-reading)", fontSize: "var(--ns-size-subheading)", fontWeight: "var(--ns-weight-semibold)", margin: "2px 0 var(--ns-space-2xs)" }}>{a.title}</div>
          </div>
          {!a.read_by_me && <Badge tone="info">New</Badge>}
        </div>
        <div style={{ fontFamily: "var(--ns-font-reading)", lineHeight: "var(--ns-lh-body-lg)", whiteSpace: "pre-wrap", maxWidth: "70ch" }}>{a.body}</div>
        {canManage && (
          <div style={{ marginTop: "var(--ns-space-md)", borderTop: "var(--ns-border-hairline) solid var(--ns-color-border-subtle)", paddingTop: "var(--ns-space-sm)" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "var(--ns-space-sm)" }}>
              <Badge tone="neutral">{a.read_count} read</Badge>
              <Button size="sm" variant="ghost" onClick={showReceipts}>Who has read?</Button>
            </div>
            {receipts && (
              <div className="ns-muted" style={{ fontSize: "var(--ns-size-caption)", marginTop: "var(--ns-space-2xs)" }}>
                {receipts.length === 0 ? "No one has opened it yet." : receipts.map((r) => `${r.name} (${fmtDate(r.read_at)})`).join(" · ")}
              </div>
            )}
          </div>
        )}
      </CardBody>
    </Card>
  );
}

export function AnnouncementsScreen() {
  const { data, loading, reload } = useApi<Announcement[]>("/announcements/");
  const { data: entitiesData } = useApi<Entity[]>("/entities/");
  const { data: opts } = useApi<{ can_manage: boolean }>("/roles/options/");
  const announcements = Array.isArray(data) ? data : [];
  const entities = Array.isArray(entitiesData) ? entitiesData : [];
  const entityName = new Map(entities.map((e) => [e.id, e.legal_name]));
  const canManage = opts?.can_manage ?? false;

  const [show, setShow] = useState(false);
  const [entity, setEntity] = useState("");
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function post(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await apiPost("/announcements/", { entity: Number(entity || entities[0]?.id), title, body });
      setTitle("");
      setBody("");
      setShow(false);
      reload();
    } catch {
      setError("Could not post (Chairman or Company Secretary only).");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <PageHeader
        title="Announcements"
        sub="Board circulars — directors' reads are receipted, so leadership knows the board is informed."
        actions={canManage ? <Button size="sm" onClick={() => setShow((v) => !v)}>{show ? "Cancel" : "New announcement"}</Button> : undefined}
      />

      {show && (
        <Card>
          <CardBody>
            <Overline>New announcement</Overline>
            <form onSubmit={post} style={{ display: "flex", flexDirection: "column", gap: "var(--ns-space-sm)", marginTop: "var(--ns-space-2xs)" }}>
              <div className="ns-field">
                <label className="ns-field__label" htmlFor="an-entity">Entity</label>
                <select id="an-entity" className="ns-input" value={entity} onChange={(e) => setEntity(e.target.value)}>
                  {entities.map((en) => <option key={en.id} value={en.id}>{en.legal_name}</option>)}
                </select>
              </div>
              <Field label="Title" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="e.g. Q3 board circular" />
              <div className="ns-field">
                <label className="ns-field__label" htmlFor="an-body">Message</label>
                <textarea id="an-body" className="ns-input" value={body} onChange={(e) => setBody(e.target.value)}
                  style={{ minHeight: 110, padding: "var(--ns-space-2xs) var(--ns-space-xs)", fontFamily: "var(--ns-font-reading)", resize: "vertical" }} />
              </div>
              {error && <span className="ns-field__error">{error}</span>}
              <Button type="submit" disabled={busy || !title || !body}>{busy ? "Posting…" : "Post to the board"}</Button>
            </form>
          </CardBody>
        </Card>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: "var(--ns-space-md)", marginTop: show ? "var(--ns-space-md)" : 0 }}>
        {announcements.map((a) => (
          <Item key={a.id} a={a} entityName={entityName.get(a.entity) ?? `#${a.entity}`} canManage={canManage} onChange={reload} />
        ))}
      </div>
      {!loading && announcements.length === 0 && <EmptyState title="No announcements" hint="Board circulars will appear here." />}
    </div>
  );
}
