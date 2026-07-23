import { useEffect, useState, type FormEvent } from "react";
import { apiPost } from "../api/client";
import { useApi } from "../api/useApi";
import { Badge, Button, CellTitle, EmptyState, Field, Overline, PageHeader, Stat, Table } from "../ui";

type Filing = { id: number; period_label: string; filed_on: string; evidence: string; filed_by_name: string | null };
type Obligation = {
  id: number;
  entity: number;
  entity_name: string;
  title: string;
  regulator: string;
  frequency: string;
  due_date: string;
  description: string;
  rag: "red" | "amber" | "green";
  last_filing: Filing | null;
};

const fmtDate = (iso: string) => new Date(iso).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" });
const FREQ: Record<string, string> = { annual: "Annual", quarterly: "Quarterly", monthly: "Monthly", once: "One-off" };

function ragBadge(rag: Obligation["rag"], due: string) {
  const days = Math.ceil((new Date(due).getTime() - Date.now()) / 86_400_000);
  if (rag === "red") return <Badge tone="danger">{Math.abs(days)}d overdue</Badge>;
  if (rag === "amber") return <Badge tone="warning">due in {days}d</Badge>;
  return <Badge tone="success">on track</Badge>;
}

function FilingModal({ ob, onClose, onFiled }: { ob: Obligation; onClose: () => void; onFiled: () => void }) {
  const { data: history } = useApi<Filing[]>(`/compliance/${ob.id}/filings/`);
  const filings = Array.isArray(history) ? history : [];
  const [period, setPeriod] = useState("");
  const [filedOn, setFiledOn] = useState(new Date().toISOString().slice(0, 10));
  const [evidence, setEvidence] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  async function file(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await apiPost(`/compliance/${ob.id}/filings/`, { period_label: period, filed_on: filedOn, evidence });
      onFiled();
      onClose();
    } catch {
      setError("Could not record the filing (cosec only).");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="ns-modal" onClick={onClose} role="dialog" aria-modal="true" aria-label={ob.title}>
      <div className="ns-modal__card" onClick={(e) => e.stopPropagation()}>
        <div className="ns-modal__head">
          <div>
            <Overline>{ob.regulator} · {ob.entity_name}</Overline>
            <h2 className="ns-modal__title">{ob.title}</h2>
            <div style={{ display: "flex", gap: "var(--ns-space-2xs)", marginTop: "var(--ns-space-2xs)" }}>
              {ragBadge(ob.rag, ob.due_date)}
              <Badge tone="neutral">{FREQ[ob.frequency] ?? ob.frequency}</Badge>
              <Badge tone="neutral">next due {fmtDate(ob.due_date)}</Badge>
            </div>
          </div>
          <button className="ns-modal__close" onClick={onClose} aria-label="Close">✕</button>
        </div>
        <div className="ns-modal__body">
          {ob.description && (
            <p className="ns-muted" style={{ fontSize: "var(--ns-size-body-sm)", marginTop: 0 }}>{ob.description}</p>
          )}

          <Overline>Filing history</Overline>
          <div style={{ margin: "var(--ns-space-2xs) 0 var(--ns-space-lg)" }}>
            {filings.map((f) => (
              <div key={f.id} className="ns-listrow" style={{ paddingLeft: 0, paddingRight: 0 }}>
                <div>
                  <div className="ns-table__primary">{f.period_label}</div>
                  <div className="ns-table__meta">
                    filed {fmtDate(f.filed_on)}{f.filed_by_name ? ` by ${f.filed_by_name}` : ""}
                  </div>
                </div>
                <span className="ns-mono ns-muted" style={{ fontSize: "var(--ns-size-caption)" }}>{f.evidence || "—"}</span>
              </div>
            ))}
            {filings.length === 0 && <span className="ns-muted" style={{ fontSize: "var(--ns-size-body-sm)" }}>No filings recorded yet.</span>}
          </div>

          <Overline>Record a filing</Overline>
          <form onSubmit={file} style={{ display: "flex", flexDirection: "column", gap: "var(--ns-space-sm)", marginTop: "var(--ns-space-2xs)" }}>
            <div className="ns-twocol" style={{ gap: "var(--ns-space-sm)" }}>
              <Field label="Period" value={period} onChange={(e) => setPeriod(e.target.value)} placeholder="e.g. FY2025" />
              <Field label="Filed on" type="date" value={filedOn} onChange={(e) => setFiledOn(e.target.value)} />
            </div>
            <Field
              label="Evidence reference"
              value={evidence}
              onChange={(e) => setEvidence(e.target.value)}
              placeholder="Receipt no., acknowledgement ref., document link"
              error={error ?? undefined}
            />
            <Button type="submit" disabled={busy || !period}>
              {busy ? "Recording…" : "Record filing — rolls the due date forward"}
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
}

export function ComplianceScreen() {
  const { data, loading, reload } = useApi<Obligation[]>("/compliance/");
  const obligations = Array.isArray(data) ? data : [];
  const [openId, setOpenId] = useState<number | null>(null);
  const open = obligations.find((o) => o.id === openId) ?? null;

  const overdue = obligations.filter((o) => o.rag === "red").length;
  const soon = obligations.filter((o) => o.rag === "amber").length;
  const onTrack = obligations.filter((o) => o.rag === "green").length;

  return (
    <div>
      <PageHeader
        title="Compliance Calendar"
        sub="Statutory obligations per entity — CAC, CBN, FIRS, NDPC — with filings, evidence and self-rolling due dates."
      />
      <div className="ns-statgrid" style={{ marginBottom: "var(--ns-space-lg)" }}>
        <Stat label="Overdue" value={overdue} tone={overdue > 0 ? "danger" : undefined} />
        <Stat label="Due within 30 days" value={soon} tone={soon > 0 ? "accent" : undefined} />
        <Stat label="On track" value={onTrack} />
      </div>

      {obligations.length > 0 && (
        <Table head={<><th>Obligation</th><th>Regulator</th><th>Frequency</th><th>Next due</th><th>Last filed</th><th /></>}>
          {obligations.map((o) => (
            <tr key={o.id} style={{ cursor: "pointer" }} onClick={() => setOpenId(o.id)}>
              <td className="ns-cell-max">
                <CellTitle title={<span className="ns-clamp1">{o.title}</span>} meta={o.entity_name} />
              </td>
              <td><Badge tone="info">{o.regulator}</Badge></td>
              <td className="ns-muted">{FREQ[o.frequency] ?? o.frequency}</td>
              <td style={{ whiteSpace: "nowrap" }}>
                <span style={{ display: "inline-flex", gap: "var(--ns-space-2xs)", alignItems: "center" }}>
                  <span className="ns-muted">{fmtDate(o.due_date)}</span>
                  {ragBadge(o.rag, o.due_date)}
                </span>
              </td>
              <td className="ns-muted">
                {o.last_filing ? `${o.last_filing.period_label} · ${fmtDate(o.last_filing.filed_on)}` : "—"}
              </td>
              <td className="is-num" onClick={(e) => e.stopPropagation()}>
                <Button size="sm" variant="secondary" onClick={() => setOpenId(o.id)}>
                  View
                </Button>
              </td>
            </tr>
          ))}
        </Table>
      )}
      {!loading && obligations.length === 0 && (
        <EmptyState title="No obligations on the calendar" hint="The Company Secretary can add each entity's statutory obligations." />
      )}
      {open && <FilingModal ob={open} onClose={() => setOpenId(null)} onFiled={reload} />}
    </div>
  );
}
