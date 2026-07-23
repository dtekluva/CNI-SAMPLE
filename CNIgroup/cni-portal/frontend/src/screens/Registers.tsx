import { useState } from "react";
import { useApi } from "../api/useApi";
import { Badge, CellTitle, EmptyState, PageHeader, Table } from "../ui";

type Entry = {
  id: number;
  entity: number;
  register_type: string;
  register_type_display: string;
  party_name: string;
  particulars: Record<string, unknown>;
  effective_from: string;
  ceased_on: string | null;
  is_active: boolean;
};
type Entity = { id: number; legal_name: string };

const TYPES: [string, string][] = [
  ["", "All registers"],
  ["members", "Members"],
  ["directors", "Directors"],
  ["secretaries", "Secretaries"],
  ["charges", "Charges"],
  ["beneficial_owners", "PSC"],
  ["debenture_holders", "Debentures"],
];

const fmtDate = (iso: string) => new Date(iso).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" });

/** Compact one-line summary of register-specific particulars. */
function particulars(p: Record<string, unknown>) {
  const bits: string[] = [];
  if (p.shares != null) bits.push(`${Number(p.shares).toLocaleString()} ${p.class ?? ""} shares`.trim());
  if (p.designation) bits.push(String(p.designation));
  if (p.control) bits.push(String(p.control));
  if (p.amount != null) bits.push(`${p.currency ?? ""} ${Number(p.amount).toLocaleString()}`.trim());
  if (p.appointment) bits.push(String(p.appointment));
  return bits.join(" · ") || "—";
}

export function RegistersScreen() {
  const [type, setType] = useState("");
  const [activeOnly, setActiveOnly] = useState(true);
  const params = new URLSearchParams();
  if (type) params.set("register_type", type);
  if (activeOnly) params.set("active", "true");
  const qs = params.toString();
  const { data, loading } = useApi<Entry[]>(`/registers/${qs ? `?${qs}` : ""}`);
  const { data: entitiesData } = useApi<Entity[]>("/entities/");
  const entries = Array.isArray(data) ? data : [];
  const entityName = new Map((Array.isArray(entitiesData) ? entitiesData : []).map((e) => [e.id, e.legal_name]));

  return (
    <div>
      <PageHeader
        title="Statutory Registers"
        sub="CAMA registers per entity — entries are ceased, never deleted, so the historical position is always provable."
        actions={
          <button className={`ns-chip${activeOnly ? " ns-chip--on" : ""}`} onClick={() => setActiveOnly(!activeOnly)}>
            Current only
          </button>
        }
      />
      <div className="ns-chiprow" style={{ marginBottom: "var(--ns-space-md)" }}>
        {TYPES.map(([value, label]) => (
          <button key={value} className={`ns-chip${type === value ? " ns-chip--on" : ""}`} onClick={() => setType(value)}>
            {label}
          </button>
        ))}
      </div>
      {entries.length > 0 && (
        <Table head={<><th>Party</th><th>Register</th><th>Entity</th><th>Particulars</th><th>From</th><th>Status</th></>}>
          {entries.map((e) => (
            <tr key={e.id}>
              <td><CellTitle title={e.party_name} /></td>
              <td><Badge tone="neutral">{e.register_type_display}</Badge></td>
              <td className="ns-muted">{entityName.get(e.entity) ?? `#${e.entity}`}</td>
              <td className="ns-muted">{particulars(e.particulars ?? {})}</td>
              <td className="ns-muted">{fmtDate(e.effective_from)}</td>
              <td>
                {e.is_active ? (
                  <Badge tone="success">Current</Badge>
                ) : (
                  <Badge tone="neutral">Ceased {e.ceased_on ? fmtDate(e.ceased_on) : ""}</Badge>
                )}
              </td>
            </tr>
          ))}
        </Table>
      )}
      {!loading && entries.length === 0 && (
        <EmptyState title="No entries in this view" hint="Adjust the register filter, or include ceased entries." />
      )}
    </div>
  );
}
