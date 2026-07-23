import { useNavigate } from "react-router-dom";
import { useApi } from "../api/useApi";
import { Badge, EmptyState, PageHeader, Table } from "../ui";

type Director = {
  id: number;
  entity: number;
  entity_name: string;
  name: string;
  designation: string;
  appointed: string;
  ceased_on: string | null;
  active: boolean;
  shares: number | null;
  share_class: string | null;
};

function initials(name: string) {
  const parts = name.split(/\s+/).filter((p) => /^[A-Za-z]/.test(p));
  return ((parts[0]?.[0] ?? "?") + (parts[parts.length - 1]?.[0] ?? "")).toUpperCase();
}

const fmtShares = (n: number) => n.toLocaleString();
const fmtDate = (iso: string) => new Date(iso).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" });

export function DirectorsScreen() {
  const { data, loading } = useApi<Director[]>("/registers/directors/");
  const roster = Array.isArray(data) ? data : [];
  const navigate = useNavigate();

  const byEntity = new Map<string, Director[]>();
  for (const d of roster) byEntity.set(d.entity_name, [...(byEntity.get(d.entity_name) ?? []), d]);

  return (
    <div>
      <PageHeader
        title="Directors"
        sub="Every board, from the statutory register of directors — designation, tenure and shareholding."
      />
      {[...byEntity.entries()].map(([entityName, directors]) => (
        <section key={entityName} className="ns-section" style={{ marginTop: byEntity.size > 0 ? undefined : 0 }}>
          <div className="ns-overline" style={{ marginBottom: "var(--ns-space-xs)" }}>{entityName}</div>
          <Table head={<><th>Director</th><th>Designation</th><th>Appointed</th><th className="is-num">Shareholding</th><th>Status</th><th /></>}>
            {directors.map((d) => (
              <tr key={d.id} style={{ cursor: "pointer" }} onClick={() => navigate(`/directors/${d.id}`)}>
                <td>
                  <div style={{ display: "flex", alignItems: "center", gap: "var(--ns-space-xs)" }}>
                    <span className="ns-avatar">{initials(d.name)}</span>
                    <span className="ns-table__primary">{d.name}</span>
                  </div>
                </td>
                <td className="ns-muted">{d.designation}</td>
                <td className="ns-muted">{fmtDate(d.appointed)}</td>
                <td className="is-num">
                  {d.shares != null ? (
                    <span>
                      <span className="ns-mono">{fmtShares(d.shares)}</span>
                      <span className="ns-table__meta"> {d.share_class ?? ""}</span>
                    </span>
                  ) : (
                    <span className="ns-muted">—</span>
                  )}
                </td>
                <td>
                  {d.active ? (
                    <Badge tone="success">Active</Badge>
                  ) : (
                    <Badge tone="neutral">Ceased {d.ceased_on ? fmtDate(d.ceased_on) : ""}</Badge>
                  )}
                </td>
                <td className="is-num">
                  <span className="ns-muted" style={{ fontSize: "var(--ns-size-caption)" }}>View →</span>
                </td>
              </tr>
            ))}
          </Table>
        </section>
      ))}
      {!loading && roster.length === 0 && (
        <EmptyState title="No directors on the register" hint="Directors recorded in each entity's statutory register appear here." />
      )}
    </div>
  );
}
