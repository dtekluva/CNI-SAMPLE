import { useState } from "react";
import { apiPost } from "../api/client";
import { useApi } from "../api/useApi";
import { Badge, Button, CellTitle, EmptyState, Overline, PageHeader, Table } from "../ui";

type Action = { id: number; title: string; owner_name: string; due_date: string | null; status: string };
type Group = { entity: number; entity_name: string; items: { id: number; title: string; owner: string; due_date: string | null; overdue_days: number | null }[] };

function dueClass(due: string | null, status: string) {
  if (!due || status === "done") return "ns-muted";
  const days = (new Date(due).getTime() - Date.now()) / 86_400_000;
  if (days < 0) return "ns-due--over";
  if (days < 7) return "ns-due--soon";
  return "ns-muted";
}
const fmt = (iso: string) => new Date(iso).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" });

export function ActionsScreen() {
  const [filter, setFilter] = useState("");
  const grouped = filter === "grouped";
  const { data, loading, reload } = useApi<Action[]>(grouped ? "/actions/" : `/actions/${filter}`);
  const { data: groupData } = useApi<Group[]>("/actions/overdue-dashboard/");
  const actions = Array.isArray(data) ? data : [];
  const groups = Array.isArray(groupData) ? groupData : [];
  const [note, setNote] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function complete(id: number) {
    await apiPost(`/actions/${id}/complete/`, { evidence: "Done" });
    reload();
  }
  async function remind() {
    setBusy(true);
    setNote(null);
    try {
      const r = await apiPost<{ reminded: number; escalated: number }>("/actions/run-reminders/");
      setNote(`Reminded ${r.reminded} owner(s); escalated ${r.escalated} overdue item(s) to the Company Secretary.`);
    } catch {
      setNote("Could not run reminders.");
    } finally {
      setBusy(false);
    }
  }

  const chip = (label: string, value: string) => (
    <button key={value} className={`ns-chip${filter === value ? " ns-chip--on" : ""}`} onClick={() => setFilter(value)}>
      {label}
    </button>
  );

  return (
    <div>
      <PageHeader
        title="Actions"
        sub="Everything the board asked for — owned, dated, and chased to completion."
        actions={
          <div style={{ display: "flex", gap: "var(--ns-space-sm)", alignItems: "center", flexWrap: "wrap" }}>
            <div className="ns-chiprow">{[chip("All", ""), chip("Mine", "?mine=true"), chip("Overdue", "?overdue=true"), chip("By entity", "grouped")]}</div>
            <Button size="sm" variant="secondary" onClick={remind} disabled={busy}>{busy ? "Sending…" : "Remind owners"}</Button>
          </div>
        }
      />
      {note && <div style={{ marginBottom: "var(--ns-space-md)" }}><Badge tone="info">{note}</Badge></div>}

      {grouped ? (
        <div style={{ display: "flex", flexDirection: "column", gap: "var(--ns-space-lg)" }}>
          {groups.map((g) => (
            <section key={g.entity}>
              <Overline>{g.entity_name}</Overline>
              <div style={{ marginTop: "var(--ns-space-xs)" }}>
                <Table head={<><th>Action</th><th>Owner</th><th>Due</th><th>Age</th></>}>
                  {g.items.map((it) => (
                    <tr key={it.id}>
                      <td><CellTitle title={it.title} /></td>
                      <td className="ns-muted">{it.owner}</td>
                      <td className={it.overdue_days != null ? "ns-due--over" : "ns-muted"}>{it.due_date ? fmt(it.due_date) : "—"}</td>
                      <td>{it.overdue_days != null ? <Badge tone="danger">{it.overdue_days}d overdue</Badge> : <Badge tone="neutral">on track</Badge>}</td>
                    </tr>
                  ))}
                </Table>
              </div>
            </section>
          ))}
          {groups.length === 0 && <EmptyState title="No open actions" hint="Nothing outstanding across your entities." />}
        </div>
      ) : (
        <>
          {actions.length > 0 && (
            <Table head={<><th>Action</th><th>Owner</th><th>Due</th><th>Status</th><th /></>}>
              {actions.map((a) => (
                <tr key={a.id}>
                  <td><CellTitle title={a.title} /></td>
                  <td className="ns-muted">{a.owner_name || "—"}</td>
                  <td className={dueClass(a.due_date, a.status)}>{a.due_date ? fmt(a.due_date) : "—"}</td>
                  <td><Badge tone={a.status === "done" ? "success" : "warning"}>{a.status}</Badge></td>
                  <td className="is-num">
                    {a.status === "open" && (
                      <Button size="sm" variant="secondary" onClick={() => complete(a.id)}>Complete</Button>
                    )}
                  </td>
                </tr>
              ))}
            </Table>
          )}
          {!loading && actions.length === 0 && (
            <EmptyState title="No actions here" hint="Try a different filter, or relax — nothing is waiting on you." />
          )}
        </>
      )}
    </div>
  );
}
