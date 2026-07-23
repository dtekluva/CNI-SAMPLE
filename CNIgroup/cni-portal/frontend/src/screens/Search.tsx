import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useApi } from "../api/useApi";
import { Button, Card, CardBody, EmptyState, Icon, Overline, PageHeader, SearchBox } from "../ui";

type Result = { kind: string; id: number; title: string; subtitle: string; link: string };
type Entity = { id: number; legal_name: string };

const KIND_LABEL: Record<string, string> = {
  meeting: "Meetings", document: "Documents", resolution: "Resolutions", action: "Actions",
  register: "Registers", committee: "Committees", announcement: "Announcements",
};
const KIND_ICON: Record<string, string> = {
  meeting: "calendar", document: "folder", resolution: "gavel", action: "checks",
  register: "registers", committee: "people", announcement: "bell",
};

const EXPORTS: [string, string, string][] = [
  ["minute-book", "Minute Book", "Every signed minute, sealed and chronological"],
  ["resolution-register", "Resolution Register", "All resolutions with class and outcome"],
  ["attendance-register", "Attendance Register", "Attendance per meeting, per member"],
  ["audit-extract", "Audit Log Extract", "Latest 300 events from the tamper-evident log"],
];

export function SearchScreen() {
  const [q, setQ] = useState("");
  const [debounced, setDebounced] = useState("");
  useEffect(() => {
    const t = setTimeout(() => setDebounced(q.trim()), 250);
    return () => clearTimeout(t);
  }, [q]);

  const { data, loading } = useApi<{ q: string; results: Result[] }>(
    debounced.length >= 2 ? `/search/?q=${encodeURIComponent(debounced)}` : "/search/?q=",
  );
  const { data: entitiesData } = useApi<Entity[]>("/entities/");
  const { data: opts } = useApi<{ can_manage: boolean }>("/roles/options/");
  const entities = Array.isArray(entitiesData) ? entitiesData : [];
  const canExport = opts?.can_manage ?? false;
  const [exportEntity, setExportEntity] = useState("");

  const results = data?.results ?? [];
  const byKind = new Map<string, Result[]>();
  for (const r of results) byKind.set(r.kind, [...(byKind.get(r.kind) ?? []), r]);
  const entityForExport = exportEntity || String(entities[0]?.id ?? "");

  return (
    <div>
      <PageHeader
        title="Search & Reports"
        sub="One search across every record you can see — and one-click statutory exports for regulators and auditors."
      />
      <div className="ns-toolbar">
        <SearchBox value={q} onChange={setQ} placeholder="Search meetings, papers, resolutions, registers, people…" />
        <span className="ns-count">
          {loading && debounced ? "Searching…" : debounced ? `${results.length} result${results.length === 1 ? "" : "s"}` : ""}
        </span>
      </div>

      {debounced.length >= 2 && results.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: "var(--ns-space-lg)", marginBottom: "var(--ns-space-xl)" }}>
          {[...byKind.entries()].map(([kind, rs]) => (
            <section key={kind}>
              <Overline>{KIND_LABEL[kind] ?? kind}</Overline>
              <div className="ns-tablewrap" style={{ marginTop: "var(--ns-space-xs)" }}>
                {rs.map((r) => (
                  <Link key={`${r.kind}-${r.id}`} to={r.link} className="ns-mini">
                    <div style={{ display: "flex", alignItems: "center", gap: "var(--ns-space-sm)", minWidth: 0 }}>
                      <span className="ns-kpi__icon" style={{ width: 30, height: 30 }}>
                        <Icon name={KIND_ICON[kind] ?? "folder"} />
                      </span>
                      <div className="ns-mini__main">
                        <div className="ns-mini__title">{r.title}</div>
                        <div className="ns-mini__meta">{r.subtitle}</div>
                      </div>
                    </div>
                    <span className="ns-muted" style={{ fontSize: "var(--ns-size-caption)", flex: "none" }}>Open →</span>
                  </Link>
                ))}
              </div>
            </section>
          ))}
        </div>
      )}
      {debounced.length >= 2 && !loading && results.length === 0 && (
        <div style={{ marginBottom: "var(--ns-space-xl)" }}>
          <EmptyState title={`Nothing matches “${debounced}”`} hint="Search covers titles, numbers, paper text and register parties — scoped to your access." />
        </div>
      )}

      {canExport && (
        <Card>
          <CardBody>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "var(--ns-space-md)", flexWrap: "wrap" }}>
              <Overline>Regulator-ready exports</Overline>
              <select className="ns-input" style={{ width: 280 }} value={entityForExport} onChange={(e) => setExportEntity(e.target.value)} aria-label="Export entity">
                {entities.map((en) => <option key={en.id} value={en.id}>{en.legal_name}</option>)}
              </select>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))", gap: "var(--ns-space-sm)", marginTop: "var(--ns-space-md)" }}>
              {EXPORTS.map(([kind, label, desc]) => (
                <div key={kind} className="ns-ctxcard">
                  <b style={{ fontSize: "var(--ns-size-body-sm)" }}>{label}</b>
                  <p className="ns-muted" style={{ fontSize: "var(--ns-size-caption)", margin: "4px 0 var(--ns-space-sm)" }}>{desc}</p>
                  <a href={`/api/exports/${kind}/?entity=${entityForExport}`} target="_blank" rel="noopener noreferrer" style={{ textDecoration: "none" }}>
                    <Button size="sm" variant="secondary">Export PDF</Button>
                  </a>
                </div>
              ))}
            </div>
            <p className="ns-muted" style={{ fontSize: "var(--ns-size-caption)", marginTop: "var(--ns-space-sm)", marginBottom: 0 }}>
              Exports are dated, entity-branded, and every generation is written to the audit log.
            </p>
          </CardBody>
        </Card>
      )}
      {!debounced && !canExport && (
        <EmptyState title="Type at least two characters to search" hint="Results span meetings, documents, resolutions, actions, registers, committees and announcements." />
      )}
    </div>
  );
}
