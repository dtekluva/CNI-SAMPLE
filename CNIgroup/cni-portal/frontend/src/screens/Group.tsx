import { useApi } from "../api/useApi";
import { EmptyState, PageHeader, Stat, Table } from "../ui";

type Row = {
  entity: number;
  entity_name: string;
  meetings: number;
  upcoming: number;
  open_actions: number;
  overdue_actions: number;
  pending_resolutions: number;
  compliance_red: number;
};
type Summary = { entities: Row[]; totals: Omit<Row, "entity" | "entity_name"> };

function num(v: number, tone?: "warn" | "bad") {
  const cls = v > 0 && tone === "bad" ? " ns-grp__num--bad" : v > 0 && tone === "warn" ? " ns-grp__num--warn" : "";
  return <td className={`ns-grp__num${cls}`}>{v}</td>;
}

export function GroupScreen() {
  const { data, loading } = useApi<Summary>("/meetings/group-summary/");
  const rows = data?.entities ?? [];
  const t = data?.totals;

  return (
    <div>
      <PageHeader title="Group Overview" sub="Every entity you oversee, side by side — meetings, actions, resolutions and compliance at a glance." />

      {t && (
        <div className="ns-statgrid" style={{ marginBottom: "var(--ns-space-lg)" }}>
          <Stat label="Entities" value={rows.length} tone="accent" />
          <Stat label="Open actions" value={t.open_actions} />
          <Stat label="Overdue actions" value={t.overdue_actions} tone={t.overdue_actions > 0 ? "danger" : undefined} />
          <Stat label="Pending resolutions" value={t.pending_resolutions} />
        </div>
      )}

      {rows.length > 0 && (
        <Table
          head={<><th>Entity</th><th className="is-num">Meetings</th><th className="is-num">Upcoming</th><th className="is-num">Open actions</th><th className="is-num">Overdue</th><th className="is-num">Pending votes</th><th className="is-num">Compliance red</th></>}
        >
          {rows.map((r) => (
            <tr key={r.entity}>
              <td className="ns-table__primary">{r.entity_name}</td>
              {num(r.meetings)}
              {num(r.upcoming)}
              {num(r.open_actions)}
              {num(r.overdue_actions, "bad")}
              {num(r.pending_resolutions, "warn")}
              {num(r.compliance_red, "bad")}
            </tr>
          ))}
          {t && (
            <tr style={{ background: "var(--ns-color-surface-subtle)" }}>
              <td className="ns-table__primary">Group total</td>
              {num(t.meetings)}
              {num(t.upcoming)}
              {num(t.open_actions)}
              {num(t.overdue_actions, "bad")}
              {num(t.pending_resolutions, "warn")}
              {num(t.compliance_red, "bad")}
            </tr>
          )}
        </Table>
      )}
      {!loading && rows.length === 0 && <EmptyState title="No entities in scope" hint="Group rollup appears once you can access more than one entity." />}
    </div>
  );
}
