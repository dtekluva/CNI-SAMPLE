import { useState, type FormEvent } from "react";
import { apiPost } from "../api/client";
import { useApi } from "../api/useApi";
import { Badge, Button, Card, CardBody, EmptyState, Field, Overline, PageHeader, Table } from "../ui";

type Membership = {
  id: number;
  user: number;
  user_name: string;
  role: string;
  term_start: string;
  term_end: string | null;
  ended_on: string | null;
  is_active: boolean;
  expires_soon: boolean;
};
type Committee = {
  id: number;
  entity: number;
  entity_name: string;
  name: string;
  charter: string;
  charter_adopted_on: string | null;
  memberships: Membership[];
  reports_count: number;
};
type Report = {
  id: number;
  title: string;
  summary: string;
  status: string;
  submitted_by_name: string | null;
  submitted_at: string;
  noted_at: string | null;
};

const fmtDate = (iso: string) => new Date(iso).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" });

function initials(name: string) {
  const parts = name.split(/\s+/).filter((p) => /^[A-Za-z]/.test(p));
  return ((parts[0]?.[0] ?? "?") + (parts[parts.length - 1]?.[0] ?? "")).toUpperCase();
}

function CommitteeDetail({ committee, reloadAll }: { committee: Committee; reloadAll: () => void }) {
  const { data: reportsData, reload: reloadReports } = useApi<Report[]>(`/committees/${committee.id}/reports/`);
  const reports = Array.isArray(reportsData) ? reportsData : [];
  const [title, setTitle] = useState("");
  const [summary, setSummary] = useState("");
  const [busy, setBusy] = useState(false);

  async function submitReport(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    try {
      await apiPost(`/committees/${committee.id}/reports/`, { title, summary });
      setTitle("");
      setSummary("");
      reloadReports();
      reloadAll();
    } finally {
      setBusy(false);
    }
  }

  async function rotate(membershipId: number) {
    await apiPost(`/committees/${committee.id}/end-membership/`, { membership: membershipId });
    reloadAll();
  }

  async function note(reportId: number) {
    await apiPost(`/committees/${committee.id}/note-report/`, { report: reportId });
    reloadReports();
  }

  return (
    <div className="ns-twocol ns-section">
      <div style={{ display: "flex", flexDirection: "column", gap: "var(--ns-space-md)" }}>
        <Card>
          <CardBody>
            <Overline>Charter — terms of reference</Overline>
            <div
              style={{
                fontFamily: "var(--ns-font-reading)", fontSize: "var(--ns-size-body)",
                lineHeight: "var(--ns-lh-body-lg)", whiteSpace: "pre-wrap",
                marginTop: "var(--ns-space-2xs)", maxWidth: "62ch",
              }}
            >
              {committee.charter || <span className="ns-muted">No charter recorded yet.</span>}
            </div>
            {committee.charter_adopted_on && (
              <p className="ns-muted" style={{ fontSize: "var(--ns-size-caption)", marginTop: "var(--ns-space-sm)", marginBottom: 0 }}>
                Adopted {fmtDate(committee.charter_adopted_on)}
              </p>
            )}
          </CardBody>
        </Card>

        <div>
          <Overline>Members & terms</Overline>
          <div style={{ marginTop: "var(--ns-space-xs)" }}>
            <Table head={<><th>Member</th><th>Role</th><th>Term</th><th>Status</th><th /></>}>
              {committee.memberships.map((m) => (
                <tr key={m.id}>
                  <td>
                    <div style={{ display: "flex", alignItems: "center", gap: "var(--ns-space-xs)" }}>
                      <span className="ns-avatar">{initials(m.user_name)}</span>
                      <span className="ns-table__primary">{m.user_name}</span>
                    </div>
                  </td>
                  <td>{m.role === "chair" ? <Badge tone="info">Chair</Badge> : <span className="ns-muted">Member</span>}</td>
                  <td className="ns-muted" style={{ whiteSpace: "nowrap" }}>
                    {fmtDate(m.term_start)} → {m.term_end ? fmtDate(m.term_end) : "open"}
                  </td>
                  <td>
                    {!m.is_active ? (
                      <Badge tone="neutral">Rotated off</Badge>
                    ) : m.expires_soon ? (
                      <Badge tone="warning">Term expiring</Badge>
                    ) : (
                      <Badge tone="success">Active</Badge>
                    )}
                  </td>
                  <td className="is-num">
                    {m.is_active && (
                      <Button size="sm" variant="ghost" onClick={() => rotate(m.id)}>
                        Rotate off
                      </Button>
                    )}
                  </td>
                </tr>
              ))}
            </Table>
          </div>
          {committee.memberships.length === 0 && <EmptyState title="No members appointed" />}
        </div>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "var(--ns-space-md)" }}>
        <Card>
          <CardBody>
            <Overline>Reports to the board</Overline>
            <div style={{ display: "flex", flexDirection: "column", marginTop: "var(--ns-space-2xs)" }}>
              {reports.map((r) => (
                <div key={r.id} className="ns-listrow" style={{ paddingLeft: 0, paddingRight: 0 }}>
                  <div>
                    <div className="ns-table__primary ns-clamp1">{r.title}</div>
                    <div className="ns-table__meta ns-clamp2">{r.summary}</div>
                    <div className="ns-table__meta">
                      {r.submitted_by_name ?? "—"} · {fmtDate(r.submitted_at)}
                    </div>
                  </div>
                  <div style={{ flex: "none" }}>
                    {r.status === "noted" ? (
                      <Badge tone="success">Noted</Badge>
                    ) : (
                      <span style={{ display: "inline-flex", gap: "var(--ns-space-2xs)", alignItems: "center" }}>
                        <Badge tone="warning">Submitted</Badge>
                        <Button size="sm" variant="ghost" onClick={() => note(r.id)}>
                          Note
                        </Button>
                      </span>
                    )}
                  </div>
                </div>
              ))}
              {reports.length === 0 && <span className="ns-muted" style={{ fontSize: "var(--ns-size-body-sm)" }}>No reports yet.</span>}
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardBody>
            <Overline>Submit a report</Overline>
            <form onSubmit={submitReport} style={{ display: "flex", flexDirection: "column", gap: "var(--ns-space-sm)", marginTop: "var(--ns-space-2xs)" }}>
              <Field label="Report title" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="e.g. Q3 Audit Committee Report" />
              <div className="ns-field">
                <label className="ns-field__label" htmlFor="rep-sum">Summary for the board</label>
                <textarea
                  id="rep-sum"
                  className="ns-input"
                  value={summary}
                  onChange={(e) => setSummary(e.target.value)}
                  style={{ minHeight: 88, padding: "var(--ns-space-2xs) var(--ns-space-xs)", resize: "vertical" }}
                />
              </div>
              <Button type="submit" disabled={busy || !title || !summary}>
                {busy ? "Submitting…" : "Submit to board"}
              </Button>
            </form>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}

export function CommitteesScreen() {
  const { data, loading, reload } = useApi<Committee[]>("/committees/");
  const committees = Array.isArray(data) ? data : [];
  const [selected, setSelected] = useState<number | null>(null);
  const current = committees.find((c) => c.id === selected) ?? null;

  return (
    <div>
      <PageHeader
        title="Committees"
        sub="Board committees with charters, membership terms and rotation, reporting up to the board."
      />
      <div className="ns-comgrid">
        {committees.map((c) => {
          const active = c.memberships.filter((m) => m.is_active);
          const chair = active.find((m) => m.role === "chair");
          const expiring = active.filter((m) => m.expires_soon).length;
          return (
            <button
              key={c.id}
              className={`ns-comcard${selected === c.id ? " ns-comcard--on" : ""}`}
              onClick={() => setSelected(selected === c.id ? null : c.id)}
            >
              <Overline>{c.entity_name}</Overline>
              <div className="ns-comcard__name">{c.name}</div>
              <div className="ns-comcard__meta">
                <span className="ns-avlist">
                  {active.slice(0, 5).map((m) => (
                    <span key={m.id} className="ns-avatar" title={m.user_name}>
                      {initials(m.user_name)}
                    </span>
                  ))}
                </span>
                <span className="ns-muted" style={{ fontSize: "var(--ns-size-caption)" }}>
                  {chair ? `Chair: ${chair.user_name}` : "No chair"} · {active.length} member{active.length === 1 ? "" : "s"}
                </span>
              </div>
              <div style={{ display: "flex", gap: "var(--ns-space-2xs)", marginTop: "var(--ns-space-sm)" }}>
                {expiring > 0 && <Badge tone="warning">{expiring} term{expiring === 1 ? "" : "s"} expiring</Badge>}
                <Badge tone="neutral">{c.reports_count} report{c.reports_count === 1 ? "" : "s"}</Badge>
              </div>
            </button>
          );
        })}
      </div>
      {!loading && committees.length === 0 && (
        <EmptyState title="No committees yet" hint="The Company Secretary can constitute committees per entity." />
      )}
      {current && <CommitteeDetail committee={current} reloadAll={reload} />}
    </div>
  );
}
