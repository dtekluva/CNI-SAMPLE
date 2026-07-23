import { useApi } from "../api/useApi";
import { Badge, EmptyState, Icon, PageHeader } from "../ui";

type Entity = {
  id: number;
  parent: number | null;
  legal_name: string;
  cac_rc_number: string;
  company_secretary?: string;
  regulators?: string[];
  is_complete: boolean;
};

function Node({ e, childrenOf }: { e: Entity; childrenOf: Map<number | null, Entity[]> }) {
  const kids = childrenOf.get(e.id) ?? [];
  return (
    <li>
      <div className="ns-treecard">
        <div style={{ display: "flex", alignItems: "center", gap: "var(--ns-space-sm)" }}>
          <span className="ns-avatar" style={{ borderRadius: "var(--ns-radius-medium)" }}>
            <Icon name="building" />
          </span>
          <div>
            <div className="ns-treecard__name">{e.legal_name}</div>
            <div className="ns-treecard__meta ns-mono">
              {e.cac_rc_number || "RC —"}
              {e.regulators && e.regulators.length > 0 ? ` · ${e.regulators.join(" · ")}` : ""}
            </div>
          </div>
        </div>
        <Badge tone={e.is_complete ? "success" : "warning"}>{e.is_complete ? "Complete" : "Incomplete"}</Badge>
      </div>
      {kids.length > 0 && (
        <ul className="ns-tree">
          {kids.map((k) => (
            <Node key={k.id} e={k} childrenOf={childrenOf} />
          ))}
        </ul>
      )}
    </li>
  );
}

export function EntitiesScreen() {
  const { data, loading, error } = useApi<Entity[]>("/entities/");
  const entities = Array.isArray(data) ? data : [];

  const ids = new Set(entities.map((e) => e.id));
  const childrenOf = new Map<number | null, Entity[]>();
  for (const e of entities) {
    // Treat entities whose parent is outside my visibility as roots (scoped view).
    const key = e.parent !== null && ids.has(e.parent) ? e.parent : null;
    childrenOf.set(key, [...(childrenOf.get(key) ?? []), e]);
  }
  const roots = childrenOf.get(null) ?? [];

  return (
    <div>
      <PageHeader
        title="Entities"
        sub="The group structure — every company, its statutory particulars, and its place in the tree."
      />
      {error && <Badge tone="danger">{error}</Badge>}
      <ul className="ns-tree">
        {roots.map((e) => (
          <Node key={e.id} e={e} childrenOf={childrenOf} />
        ))}
      </ul>
      {!loading && entities.length === 0 && (
        <EmptyState title="No entities visible" hint="You'll see the companies your roles grant access to." />
      )}
    </div>
  );
}
