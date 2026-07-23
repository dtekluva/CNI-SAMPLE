import { useEffect, useState, type FormEvent } from "react";
import { apiPost } from "../api/client";
import { useApi } from "../api/useApi";
import { Badge, Button, Card, CardBody, CellTitle, EmptyState, Field, Overline, PageHeader, Table } from "../ui";

type Res = {
  id: number;
  entity: number;
  number: string;
  title: string;
  text: string;
  outcome: string;
  kind: string;
  voting_mode: string;
  resolution_class: string;
  amount: string | null;
  category: string;
  threshold: number;
  effective_date: string | null;
  created_at: string;
};
type Authority = { applicable: boolean; in_authority?: boolean; approver?: string; amount?: string; category?: string };
type Entity = { id: number; legal_name: string };
type Results = {
  mode: string;
  tally: Record<string, number>;
  total_votes: number;
  recused?: number[];
  weighted?: Record<string, number>;
  ballots: unknown[] | null;
};

function tone(o: string): "success" | "danger" | "warning" {
  return o === "passed" ? "success" : o === "failed" || o === "lapsed" ? "danger" : "warning";
}

const MODE_LABEL: Record<string, string> = { open: "Open", secret: "Secret ballot", poll: "Poll" };

const fmtDate = (iso: string) => new Date(iso).toLocaleDateString(undefined, { day: "numeric", month: "long", year: "numeric" });

function TallyBar({ label, value, max, color }: { label: string; value: number; max: number; color: string }) {
  return (
    <div className="ns-tally__row">
      <span className="ns-muted">{label}</span>
      <div className="ns-tally__bar">
        <div className="ns-tally__fill" style={{ width: `${max > 0 ? (value / max) * 100 : 0}%`, background: color }} />
      </div>
      <b className="is-num ns-mono" style={{ textAlign: "right" }}>{value}</b>
    </div>
  );
}

function ResolutionModal({
  r,
  entityName,
  onClose,
  onVote,
  onConclude,
}: {
  r: Res;
  entityName: string;
  onClose: () => void;
  onVote: (id: number, choice: string) => Promise<void>;
  onConclude: (id: number) => Promise<void>;
}) {
  const { data: results, reload } = useApi<Results>(`/resolutions/${r.id}/results/`);
  const { data: authority } = useApi<Authority>(`/resolutions/${r.id}/authority/`);
  const tally = results?.tally ?? {};
  const max = Math.max(tally.for ?? 0, tally.against ?? 0, tally.abstain ?? 0, 1);
  const naira = (v: string) => `₦${Number(v).toLocaleString()}`;

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div className="ns-modal" onClick={onClose} role="dialog" aria-modal="true" aria-label={r.title}>
      <div className="ns-modal__card" onClick={(e) => e.stopPropagation()}>
        <div className="ns-modal__head">
          <div>
            <Overline>
              <span className="ns-mono">{r.number}</span> · {entityName}
            </Overline>
            <h2 className="ns-modal__title">{r.title}</h2>
            <div style={{ display: "flex", gap: "var(--ns-space-2xs)", marginTop: "var(--ns-space-2xs)", flexWrap: "wrap" }}>
              <Badge tone={tone(r.outcome)}>{r.outcome}</Badge>
              <Badge tone="neutral">{r.kind === "circular" ? "Circular" : "Board"}</Badge>
              <Badge tone="neutral">{MODE_LABEL[r.voting_mode] ?? "Open"}</Badge>
              {r.resolution_class === "special" && <Badge tone="info">Special · ≥75%</Badge>}
            </div>
          </div>
          <button className="ns-modal__close" onClick={onClose} aria-label="Close">
            ✕
          </button>
        </div>
        <div className="ns-modal__body">
          <div className="ns-resolution-text">{r.text || "(No resolution text.)"}</div>

          <div className="ns-section" style={{ marginTop: "var(--ns-space-lg)" }}>
            <Overline>Voting</Overline>
            <div className="ns-tally" style={{ marginTop: "var(--ns-space-xs)" }}>
              <TallyBar label="For" value={tally.for ?? 0} max={max} color="var(--ns-color-success-fill)" />
              <TallyBar label="Against" value={tally.against ?? 0} max={max} color="var(--ns-color-danger-fill)" />
              <TallyBar label="Abstain" value={tally.abstain ?? 0} max={max} color="var(--ns-color-border-strong)" />
            </div>
            <p className="ns-muted" style={{ fontSize: "var(--ns-size-caption)", marginTop: "var(--ns-space-sm)", marginBottom: 0 }}>
              {results?.total_votes ?? 0} vote{(results?.total_votes ?? 0) === 1 ? "" : "s"} cast
              {r.voting_mode === "secret" ? " · individual ballots are sealed" : ""}
              {r.voting_mode === "poll" && results?.weighted ? ` · weighted: ${results.weighted.for ?? 0} for / ${results.weighted.against ?? 0} against` : ""}
              {results?.recused && results.recused.length > 0 ? ` · ${results.recused.length} director${results.recused.length === 1 ? "" : "s"} recused` : ""}
            </p>
          </div>

          {authority?.applicable && (
            <div
              className={`ns-hero${authority.in_authority ? "" : " ns-hero--bad"}`}
              style={{ marginTop: "var(--ns-space-lg)", padding: "var(--ns-space-sm) var(--ns-space-md)" }}
            >
              <span style={{ fontSize: "var(--ns-size-heading)" }}>{authority.in_authority ? "✓" : "⚠"}</span>
              <div>
                <div className="ns-hero__title" style={{ fontSize: "var(--ns-size-body)" }}>
                  {authority.in_authority ? "Within delegated authority" : "Exceeds delegated authority"}
                </div>
                <div className="ns-hero__sub">
                  {naira(authority.amount ?? "0")} · {authority.category} · requires <b>{authority.approver}</b>
                </div>
              </div>
            </div>
          )}

          <div className="ns-ctxcard" style={{ marginTop: "var(--ns-space-lg)" }}>
            <div className="ns-ctxcard__row"><span className="ns-muted">Class</span><b>{r.resolution_class === "special" ? "Special (≥75%)" : "Ordinary"}</b></div>
            {r.amount && <div className="ns-ctxcard__row"><span className="ns-muted">Amount</span><b className="ns-mono">{naira(r.amount)}</b></div>}
            <div className="ns-ctxcard__row"><span className="ns-muted">Effective date</span><b>{r.effective_date ? fmtDate(r.effective_date) : "—"}</b></div>
            <div className="ns-ctxcard__row"><span className="ns-muted">Created</span><b>{r.created_at ? fmtDate(r.created_at) : "—"}</b></div>
            {r.kind === "circular" && (
              <div className="ns-ctxcard__row"><span className="ns-muted">Signature threshold</span><b>{r.threshold}</b></div>
            )}
          </div>
        </div>
        {r.outcome === "pending" && (
          <div className="ns-modal__foot">
            <Button size="sm" onClick={async () => { await onVote(r.id, "for"); reload(); }}>
              Vote for
            </Button>
            <Button size="sm" variant="secondary" onClick={async () => { await onVote(r.id, "against"); reload(); }}>
              Vote against
            </Button>
            <Button size="sm" variant="ghost" onClick={async () => { await onConclude(r.id); onClose(); }}>
              Conclude
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}

export function ResolutionsScreen() {
  const { data, loading, error, reload } = useApi<Res[]>("/resolutions/");
  const { data: entitiesData } = useApi<Entity[]>("/entities/");
  const resolutions = Array.isArray(data) ? data : [];
  const entities = Array.isArray(entitiesData) ? entitiesData : [];
  const entityName = new Map(entities.map((e) => [e.id, e.legal_name]));
  const [openId, setOpenId] = useState<number | null>(null);
  const openRes = resolutions.find((r) => r.id === openId) ?? null;
  const [voteId, setVoteId] = useState<number | null>(null);
  const voteRes = resolutions.find((r) => r.id === voteId) ?? null;

  const [showForm, setShowForm] = useState(false);
  const [entity, setEntity] = useState("");
  const [title, setTitle] = useState("");
  const [text, setText] = useState("");
  const [mode, setMode] = useState("open");
  const [resClass, setResClass] = useState("ordinary");
  const [amount, setAmount] = useState("");
  const [category, setCategory] = useState("");
  const [busy, setBusy] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [voteNote, setVoteNote] = useState<string | null>(null);

  async function vote(id: number, choice: string) {
    setVoteNote(null);
    try {
      await apiPost(`/resolutions/${id}/vote/`, { choice });
      setVoteId(null);
      reload();
    } catch (err) {
      const e = err as { status?: number; data?: { detail?: string } };
      setVoteId(null);
      setVoteNote(e.status === 409 ? e.data?.detail ?? "You are recused from this vote." : "Could not record the vote.");
    }
  }
  async function conclude(id: number) {
    await apiPost(`/resolutions/${id}/conclude/`);
    reload();
  }

  async function createResolution(e: FormEvent) {
    e.preventDefault();
    setFormError(null);
    setBusy(true);
    try {
      await apiPost("/resolutions/", {
        entity: Number(entity || entities[0]?.id),
        title,
        text,
        voting_mode: mode,
        resolution_class: resClass,
        amount: amount ? Number(amount) : null,
        category: category.trim(),
      });
      setTitle("");
      setText("");
      setAmount("");
      setCategory("");
      setShowForm(false);
      reload();
    } catch {
      setFormError("Could not create the resolution.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <PageHeader
        title="Resolutions"
        sub="Board and circular resolutions — moved, voted, concluded, certified."
        actions={
          <Button size="sm" onClick={() => setShowForm((v) => !v)}>
            {showForm ? "Cancel" : "New resolution"}
          </Button>
        }
      />

      {showForm && (
        <Card>
          <CardBody>
            <Overline>New resolution</Overline>
            <form onSubmit={createResolution} style={{ display: "flex", flexDirection: "column", gap: "var(--ns-space-sm)", marginTop: "var(--ns-space-2xs)" }}>
              <div className="ns-field">
                <label className="ns-field__label" htmlFor="res-entity">Entity</label>
                <select id="res-entity" className="ns-input" value={entity} onChange={(e) => setEntity(e.target.value)}>
                  {entities.map((en) => (
                    <option key={en.id} value={en.id}>{en.legal_name}</option>
                  ))}
                </select>
              </div>
              <Field label="Title" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="e.g. Approval of 2027 Group Budget" />
              <div className="ns-twocol" style={{ gap: "var(--ns-space-sm)" }}>
                <div className="ns-field">
                  <label className="ns-field__label" htmlFor="res-mode">Voting mode</label>
                  <select id="res-mode" className="ns-input" value={mode} onChange={(e) => setMode(e.target.value)}>
                    <option value="open">Open (show of hands)</option>
                    <option value="secret">Secret ballot</option>
                    <option value="poll">Poll (weighted)</option>
                  </select>
                </div>
                <div className="ns-field">
                  <label className="ns-field__label" htmlFor="res-class">Class</label>
                  <select id="res-class" className="ns-input" value={resClass} onChange={(e) => setResClass(e.target.value)}>
                    <option value="ordinary">Ordinary (simple majority)</option>
                    <option value="special">Special (≥75%)</option>
                  </select>
                </div>
              </div>
              <div className="ns-twocol" style={{ gap: "var(--ns-space-sm)" }}>
                <Field label="Amount (₦, optional)" type="number" min="0" value={amount} onChange={(e) => setAmount(e.target.value)} placeholder="e.g. 120000000" />
                <Field label="DoA category (optional)" value={category} onChange={(e) => setCategory(e.target.value)} placeholder="e.g. Capital expenditure" />
              </div>
              <div className="ns-field">
                <label className="ns-field__label" htmlFor="res-text">Resolution text</label>
                <textarea
                  id="res-text"
                  className="ns-input"
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  placeholder="THAT the … be and is hereby approved."
                  style={{ minHeight: 96, padding: "var(--ns-space-2xs) var(--ns-space-xs)", fontFamily: "var(--ns-font-reading)", lineHeight: "var(--ns-lh-body)", resize: "vertical" }}
                />
              </div>
              {formError && <span className="ns-field__error">{formError}</span>}
              <div style={{ display: "flex", gap: "var(--ns-space-2xs)" }}>
                <Button type="submit" disabled={busy || !title || !text}>
                  {busy ? "Creating…" : "Create for voting"}
                </Button>
                <span className="ns-muted" style={{ fontSize: "var(--ns-size-caption)", alignSelf: "center" }}>
                  It's auto-numbered and opens as pending, ready for votes.
                </span>
              </div>
            </form>
          </CardBody>
        </Card>
      )}

      {error && <Badge tone="danger">{error}</Badge>}
      {voteNote && (
        <div style={{ marginTop: "var(--ns-space-sm)" }}>
          <Badge tone="warning">{voteNote}</Badge>
        </div>
      )}
      {resolutions.length > 0 && (
        <div style={{ marginTop: showForm || voteNote ? "var(--ns-space-md)" : 0 }}>
          <Table head={<><th>Resolution</th><th>Kind</th><th>Mode</th><th>Effective</th><th>Outcome</th><th /></>}>
            {resolutions.map((r) => (
              <tr key={r.id} style={{ cursor: "pointer" }} onClick={() => setOpenId(r.id)}>
                <td>
                  <CellTitle title={r.title} meta={<span className="ns-mono">{r.number}</span>} />
                </td>
                <td>
                  <Badge tone="neutral">{r.kind === "circular" ? "Circular" : "Board"}</Badge>
                </td>
                <td className="ns-muted">{MODE_LABEL[r.voting_mode] ?? "Open"}</td>
                <td className="ns-muted">
                  {r.effective_date
                    ? new Date(r.effective_date).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" })
                    : "—"}
                </td>
                <td><Badge tone={tone(r.outcome)}>{r.outcome}</Badge></td>
                <td className="is-num" onClick={(e) => e.stopPropagation()}>
                  <span style={{ display: "inline-flex", gap: "var(--ns-space-2xs)" }}>
                    {r.outcome === "pending" && (
                      <Button size="sm" onClick={() => setVoteId(r.id)}>
                        Vote
                      </Button>
                    )}
                    <Button size="sm" variant={r.outcome === "pending" ? "ghost" : "secondary"} onClick={() => setOpenId(r.id)}>
                      View
                    </Button>
                  </span>
                </td>
              </tr>
            ))}
          </Table>
        </div>
      )}
      {!loading && resolutions.length === 0 && (
        <EmptyState title="No resolutions yet" hint="Create the first one with “New resolution” above." />
      )}
      {voteRes && (
        <div className="ns-modal" onClick={() => setVoteId(null)} role="dialog" aria-modal="true" aria-label="Cast your vote">
          <div className="ns-modal__card" style={{ width: "min(420px, 100%)" }} onClick={(e) => e.stopPropagation()}>
            <div className="ns-modal__head">
              <div>
                <Overline><span className="ns-mono">{voteRes.number}</span></Overline>
                <h2 className="ns-modal__title" style={{ fontSize: "var(--ns-size-subheading)" }}>{voteRes.title}</h2>
              </div>
              <button className="ns-modal__close" onClick={() => setVoteId(null)} aria-label="Close">✕</button>
            </div>
            <div className="ns-modal__body" style={{ paddingTop: "var(--ns-space-2xs)" }}>
              <p className="ns-muted" style={{ fontSize: "var(--ns-size-body-sm)", margin: "0 0 var(--ns-space-md)" }}>
                How do you vote on this resolution?
              </p>
              <div style={{ display: "flex", flexDirection: "column", gap: "var(--ns-space-2xs)" }}>
                <Button variant="primary" onClick={() => vote(voteRes.id, "for")}>Vote for</Button>
                <Button variant="danger" onClick={() => vote(voteRes.id, "against")}>Vote against</Button>
                <Button variant="ghost" onClick={() => vote(voteRes.id, "abstain")}>Abstain</Button>
              </div>
            </div>
          </div>
        </div>
      )}
      {openRes && (
        <ResolutionModal
          r={openRes}
          entityName={entityName.get(openRes.entity) ?? `Entity #${openRes.entity}`}
          onClose={() => setOpenId(null)}
          onVote={vote}
          onConclude={conclude}
        />
      )}
    </div>
  );
}
