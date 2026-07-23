import { useState } from "react";
import { useApi } from "../api/useApi";
import { Badge, EmptyState, Overline, PageHeader } from "../ui";

type Rule = {
  id: number;
  entity: number;
  entity_name: string;
  category: string;
  approver: string;
  max_amount: string;
  tier: number;
};
type Entity = { id: number; legal_name: string };

const naira = (v: string) => {
  const n = Number(v);
  if (n >= 1_000_000_000) return `₦${(n / 1_000_000_000).toFixed(n % 1_000_000_000 ? 1 : 0)}bn`;
  if (n >= 1_000_000) return `₦${(n / 1_000_000).toFixed(n % 1_000_000 ? 1 : 0)}m`;
  return `₦${n.toLocaleString()}`;
};

export function DelegationMatrixScreen() {
  const { data: rulesData, loading } = useApi<Rule[]>("/doa/");
  const { data: entitiesData } = useApi<Entity[]>("/entities/");
  const rules = Array.isArray(rulesData) ? rulesData : [];
  const entities = Array.isArray(entitiesData) ? entitiesData : [];
  const [entity, setEntity] = useState<string>("");

  const scoped = entity ? rules.filter((r) => String(r.entity) === entity) : rules;

  // group: entity -> category -> tiers
  const byEntity = new Map<string, Map<string, Rule[]>>();
  for (const r of scoped) {
    const eKey = r.entity_name;
    if (!byEntity.has(eKey)) byEntity.set(eKey, new Map());
    const cats = byEntity.get(eKey)!;
    cats.set(r.category, [...(cats.get(r.category) ?? []), r].sort((a, b) => a.tier - b.tier));
  }

  return (
    <div>
      <PageHeader
        title="Delegation of Authority"
        sub="Who may approve what, up to which limit. Resolutions above the top tier are flagged as exceeding delegated authority (CAMA)."
      />
      {entities.length > 1 && (
        <div className="ns-chiprow" style={{ marginBottom: "var(--ns-space-lg)" }}>
          <button className={`ns-chip${entity === "" ? " ns-chip--on" : ""}`} onClick={() => setEntity("")}>
            All entities
          </button>
          {entities.map((e) => (
            <button
              key={e.id}
              className={`ns-chip${entity === String(e.id) ? " ns-chip--on" : ""}`}
              onClick={() => setEntity(String(e.id))}
            >
              {e.legal_name}
            </button>
          ))}
        </div>
      )}

      {[...byEntity.entries()].map(([entityName, cats]) => (
        <section key={entityName} className="ns-section" style={{ marginTop: 0, marginBottom: "var(--ns-space-xl)" }}>
          {byEntity.size > 1 && <Overline>{entityName}</Overline>}
          <div className="ns-doa" style={{ marginTop: "var(--ns-space-xs)" }}>
            {[...cats.entries()].map(([category, tiers]) => (
              <div key={category} className="ns-doa__cat">
                <div className="ns-doa__head">
                  <span className="ns-doa__cat-name">{category}</span>
                  <Badge tone="neutral">{tiers.length} tier{tiers.length === 1 ? "" : "s"}</Badge>
                </div>
                {tiers.map((r, i) => (
                  <div key={r.id} className="ns-doa__tier">
                    <span className="ns-doa__tiernum">{r.tier}</span>
                    <div>
                      <div className="ns-doa__approver">{r.approver}</div>
                      <div className="ns-muted" style={{ fontSize: "var(--ns-size-caption)" }}>
                        {i === 0 ? "up to" : `above ${naira(tiers[i - 1].max_amount)}, up to`} the limit
                      </div>
                    </div>
                    <div className="ns-doa__limit">
                      {naira(r.max_amount)}
                      <small>≤ {Number(r.max_amount).toLocaleString()}</small>
                    </div>
                  </div>
                ))}
                <div className="ns-doa__tier" style={{ background: "var(--ns-color-surface-subtle)" }}>
                  <span className="ns-doa__tiernum" style={{ background: "var(--ns-color-danger-subtle)", color: "var(--ns-color-danger-text)" }}>
                    !
                  </span>
                  <div>
                    <div className="ns-doa__approver">Shareholders</div>
                    <div className="ns-muted" style={{ fontSize: "var(--ns-size-caption)" }}>
                      above {naira(tiers[tiers.length - 1].max_amount)} — exceeds delegated authority
                    </div>
                  </div>
                  <Badge tone="danger">out of authority</Badge>
                </div>
              </div>
            ))}
          </div>
        </section>
      ))}
      {!loading && scoped.length === 0 && (
        <EmptyState title="No delegation rules yet" hint="The Company Secretary can define approval tiers per category." />
      )}
    </div>
  );
}
