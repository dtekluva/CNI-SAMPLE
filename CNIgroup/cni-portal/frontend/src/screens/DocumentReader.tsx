import { useState, type FormEvent } from "react";
import { useParams } from "react-router-dom";
import { apiPost, api } from "../api/client";
import { useApi } from "../api/useApi";
import { Badge, Button, Card, CardBody, EmptyState, Field, Overline, PdfViewer } from "../ui";

type Doc = {
  id: number;
  title: string;
  access_mode: string;
  topic: string;
  committee: string;
  page_count: number;
  is_late: boolean;
  retention_until: string | null;
  legal_hold: boolean;
  purged: boolean;
};
type Content = {
  id: number;
  title: string;
  text: string;
  version: number;
  versions: { version_number: number; uploaded_at: string; content_hash: string }[];
  watermark: string;
};
type Annotation = { id: number; author: number; author_name: string; page: number; text: string; visibility: string; created_at: string };

const fmtDate = (iso: string) => new Date(iso).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" });

function Annotations({ docId }: { docId: string }) {
  const { data, reload } = useApi<Annotation[]>(`/annotations/?document=${docId}`);
  const notes = Array.isArray(data) ? data : [];
  const [page, setPage] = useState("1");
  const [text, setText] = useState("");
  const [shared, setShared] = useState(false);
  const [busy, setBusy] = useState(false);

  async function add(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    try {
      await apiPost("/annotations/", { document: Number(docId), page: Number(page) || 1, text, visibility: shared ? "shared" : "private" });
      setText("");
      reload();
    } finally {
      setBusy(false);
    }
  }
  async function remove(id: number) {
    await api(`/annotations/${id}/`, { method: "DELETE" });
    reload();
  }

  return (
    <Card>
      <CardBody>
        <Overline>My annotations</Overline>
        <div style={{ margin: "var(--ns-space-2xs) 0 var(--ns-space-sm)" }}>
          {notes.map((n) => (
            <div key={n.id} className={`ns-annot${n.visibility === "shared" ? " ns-annot--shared" : ""}`}>
              <div style={{ fontSize: "var(--ns-size-body-sm)" }}>{n.text}</div>
              <div className="ns-annot__meta">
                <span>
                  <span className="ns-annot__page">p{n.page}</span> · {n.visibility === "shared" ? "Shared" : "Private"} · {n.author_name}
                </span>
                <button className="ns-btn ns-btn--ghost ns-btn--sm" style={{ minHeight: 22, padding: "0 6px" }} onClick={() => remove(n.id)}>
                  Delete
                </button>
              </div>
            </div>
          ))}
          {notes.length === 0 && <span className="ns-muted" style={{ fontSize: "var(--ns-size-body-sm)" }}>No notes yet.</span>}
        </div>
        <form onSubmit={add} style={{ display: "flex", flexDirection: "column", gap: "var(--ns-space-2xs)" }}>
          <div style={{ display: "flex", gap: "var(--ns-space-2xs)", alignItems: "flex-end" }}>
            <div style={{ width: 70 }}>
              <Field label="Page" type="number" min="1" value={page} onChange={(e) => setPage(e.target.value)} />
            </div>
            <div style={{ flex: 1 }}>
              <Field label="Note" value={text} onChange={(e) => setText(e.target.value)} placeholder="Your annotation…" />
            </div>
          </div>
          <label style={{ display: "flex", alignItems: "center", gap: "var(--ns-space-2xs)", fontSize: "var(--ns-size-caption)", color: "var(--ns-color-text-secondary)" }}>
            <input type="checkbox" checked={shared} onChange={(e) => setShared(e.target.checked)} /> Share with the board (otherwise private)
          </label>
          <Button size="sm" type="submit" disabled={busy || !text}>Add note</Button>
        </form>
      </CardBody>
    </Card>
  );
}

function LifecyclePanel({ doc, reload }: { doc: Doc; reload: () => void }) {
  // controls are enforced server-side: non-cosec calls 403 and surface a message
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  async function toggleHold() {
    setBusy(true);
    try {
      await apiPost(`/documents/${doc.id}/legal-hold/`, { on: !doc.legal_hold });
      reload();
    } catch {
      setMsg("Only the Company Secretary can change legal holds.");
    } finally {
      setBusy(false);
    }
  }
  async function purge() {
    if (!window.confirm("Securely purge this document? Content is destroyed and a certificate of destruction is issued. This cannot be undone.")) return;
    setBusy(true);
    setMsg(null);
    try {
      const r = await apiPost<{ certificate: { reference: string } }>(`/documents/${doc.id}/purge/`, { reason: "End of retention" });
      setMsg(`Purged — certificate ${r.certificate.reference}`);
      reload();
    } catch (e) {
      const err = e as { status?: number; data?: { detail?: string } };
      setMsg(err.status === 409 ? err.data?.detail ?? "Cannot purge." : "Only the Company Secretary can purge.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card>
      <CardBody>
        <Overline>Lifecycle & retention</Overline>
        <div className="ns-ctxcard__row" style={{ fontSize: "var(--ns-size-body-sm)" }}>
          <span className="ns-muted">Retention until</span>
          <b>{doc.retention_until ? fmtDate(doc.retention_until) : "—"}</b>
        </div>
        <div className="ns-ctxcard__row" style={{ fontSize: "var(--ns-size-body-sm)" }}>
          <span className="ns-muted">Legal hold</span>
          {doc.legal_hold ? <Badge tone="warning">On hold</Badge> : <span>Off</span>}
        </div>
        <div className="ns-ctxcard__row" style={{ fontSize: "var(--ns-size-body-sm)" }}>
          <span className="ns-muted">Status</span>
          {doc.purged ? <Badge tone="danger">Purged</Badge> : <Badge tone="success">Retained</Badge>}
        </div>
        {!doc.purged && (
          <div style={{ display: "flex", gap: "var(--ns-space-2xs)", marginTop: "var(--ns-space-sm)", flexWrap: "wrap" }}>
            <Button size="sm" variant="secondary" disabled={busy} onClick={toggleHold}>
              {doc.legal_hold ? "Release hold" : "Place legal hold"}
            </Button>
            <Button size="sm" variant="danger" disabled={busy || doc.legal_hold} onClick={purge}>
              Purge
            </Button>
          </div>
        )}
        {msg && <p className="ns-muted" style={{ fontSize: "var(--ns-size-caption)", marginTop: "var(--ns-space-2xs)", marginBottom: 0 }}>{msg}</p>}
        <p className="ns-muted" style={{ fontSize: "var(--ns-size-caption)", marginTop: "var(--ns-space-2xs)", marginBottom: 0 }}>
          Legal hold blocks purge. Purge issues a certificate of destruction (NDPA). Cosec only.
        </p>
      </CardBody>
    </Card>
  );
}

export function DocumentReader() {
  const { id } = useParams();
  const { data: doc, reload: reloadDoc } = useApi<Doc>(`/documents/${id}/`);
  const { data: content, loading } = useApi<Content>(`/documents/${id}/content/`);
  const [showPdf, setShowPdf] = useState(false);

  return (
    <div>
      <header className="ns-page__head">
        <div>
          <Overline>Document</Overline>
          <h1 className="ns-page__title">{doc?.title ?? "…"}</h1>
          {doc && (
            <p className="ns-page__sub">
              {doc.topic || doc.committee || "General"} · {doc.page_count} pp
              {content ? ` · v${content.version}` : ""}
            </p>
          )}
        </div>
        <div className="ns-page__actions">
          {doc?.is_late && <Badge tone="warning">Late paper</Badge>}
          {doc?.legal_hold && <Badge tone="warning">Legal hold</Badge>}
          {doc?.purged && <Badge tone="danger">Purged</Badge>}
          {!doc?.purged && (
            <Button size="sm" variant="secondary" onClick={() => setShowPdf(true)}>
              Open PDF
            </Button>
          )}
        </div>
      </header>
      {showPdf && doc && (
        <PdfViewer overline="Document" title={doc.title} src={`/api/documents/${id}/pdf/`} onClose={() => setShowPdf(false)} />
      )}

      {content && content.versions.length > 1 && (
        <div className="ns-chiprow" style={{ marginBottom: "var(--ns-space-md)" }}>
          {content.versions.map((v) => (
            <span key={v.version_number} className={`ns-chip${v.version_number === content.version ? " ns-chip--on" : ""}`}>
              v{v.version_number} · {new Date(v.uploaded_at).toLocaleDateString()}
            </span>
          ))}
        </div>
      )}

      <div className="ns-twocol" style={{ gridTemplateColumns: "1fr 320px" }}>
        <div>
          {doc?.purged ? (
            <EmptyState title="This document has been purged" hint="The content was securely destroyed under the retention policy. A certificate of destruction is on record." />
          ) : content ? (
            <Card>
              <CardBody>
                <div style={{ fontFamily: "var(--ns-font-reading)", fontSize: "var(--ns-size-body)", lineHeight: "var(--ns-lh-body-lg)", whiteSpace: "pre-wrap", maxWidth: "72ch" }}>
                  {content.text || <span className="ns-muted">This version has no extracted text.</span>}
                </div>
                {content.watermark && (
                  <div className="ns-muted" style={{ marginTop: "var(--ns-space-lg)", fontSize: "var(--ns-size-caption)", borderTop: "var(--ns-border-hairline) solid var(--ns-color-border-subtle)", paddingTop: "var(--ns-space-2xs)" }}>
                    {content.watermark}
                  </div>
                )}
              </CardBody>
            </Card>
          ) : (
            !loading && <EmptyState title="Document unavailable" hint="You may not have access, or it has no readable version." />
          )}
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: "var(--ns-space-md)" }}>
          {doc && <LifecyclePanel doc={doc} reload={reloadDoc} />}
          {doc && !doc.purged && <Annotations docId={id!} />}
        </div>
      </div>
    </div>
  );
}
