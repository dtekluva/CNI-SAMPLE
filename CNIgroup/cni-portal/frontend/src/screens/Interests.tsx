import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { apiPost } from "../api/client";
import { useApi } from "../api/useApi";
import { Badge, Button, Card, CardBody, EmptyState, Field, Overline, PageHeader, Table } from "../ui";

type Interest = {
  id: number;
  entity: number;
  director_name: string;
  kind: string;
  kind_display: string;
  party: string;
  details: string;
  declared_on: string;
  withdrawn_on: string | null;
  is_active: boolean;
};
type Entity = { id: number; legal_name: string };

const KINDS: [string, string][] = [
  ["directorship", "Directorship elsewhere"],
  ["shareholding", "Shareholding"],
  ["contract", "Interest in a contract"],
  ["other", "Other"],
];

const fmtDate = (iso: string) => new Date(iso).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" });

export function InterestsScreen() {
  const navigate = useNavigate();
  const { data, loading, reload } = useApi<Interest[]>("/interests/");
  const { data: entitiesData } = useApi<Entity[]>("/entities/");
  const interests = Array.isArray(data) ? data : [];
  const entities = Array.isArray(entitiesData) ? entitiesData : [];
  const entityName = new Map(entities.map((e) => [e.id, e.legal_name]));

  const [entity, setEntity] = useState("");
  const [kind, setKind] = useState("directorship");
  const [party, setParty] = useState("");
  const [details, setDetails] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function declare(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await apiPost("/interests/", {
        entity: Number(entity || entities[0]?.id),
        kind,
        party,
        details,
        declared_on: new Date().toISOString().slice(0, 10),
      });
      setParty("");
      setDetails("");
      reload();
    } catch {
      setError("Could not record the declaration.");
    } finally {
      setBusy(false);
    }
  }

  async function withdraw(id: number) {
    await apiPost(`/interests/${id}/withdraw/`);
    reload();
  }

  return (
    <div>
      <PageHeader
        title="Directors' Interests"
        sub="Standing declarations under CAMA ss.303–306 — declared to each board, withdrawn but never deleted."
      />

      <div className="ns-twocol">
        <div>
          {interests.length > 0 ? (
            <Table head={<><th>Interest</th><th>Declared by</th><th>Declared</th><th>Status</th><th /></>}>
              {interests.map((i) => (
                <tr key={i.id} style={{ cursor: "pointer" }} onClick={() => navigate(`/interests/${i.id}`)}>
                  <td className="ns-cell-max">
                    <div className="ns-table__primary ns-clamp1">{i.party}</div>
                    <div className="ns-table__meta ns-clamp2">
                      {i.kind_display} · {entityName.get(i.entity) ?? `#${i.entity}`}
                      {i.details ? ` — ${i.details}` : ""}
                    </div>
                  </td>
                  <td className="ns-muted">{i.director_name || "—"}</td>
                  <td className="ns-muted" style={{ whiteSpace: "nowrap" }}>{fmtDate(i.declared_on)}</td>
                  <td>
                    {i.is_active ? (
                      <Badge tone="success">Active</Badge>
                    ) : (
                      <Badge tone="neutral">Withdrawn {i.withdrawn_on ? fmtDate(i.withdrawn_on) : ""}</Badge>
                    )}
                  </td>
                  <td className="is-num" style={{ whiteSpace: "nowrap" }}>
                    {i.is_active && (
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={(e) => {
                          e.stopPropagation();
                          withdraw(i.id);
                        }}
                      >
                        Withdraw
                      </Button>
                    )}
                    <span className="ns-muted" style={{ fontSize: "var(--ns-size-caption)", marginLeft: "var(--ns-space-2xs)" }}>
                      View →
                    </span>
                  </td>
                </tr>
              ))}
            </Table>
          ) : (
            !loading && <EmptyState title="No interests declared" hint="Standing declarations you make appear here and inform per-meeting conflicts." />
          )}
        </div>

        <Card>
          <CardBody>
            <Overline>Declare an interest</Overline>
            <form onSubmit={declare} style={{ display: "flex", flexDirection: "column", gap: "var(--ns-space-sm)", marginTop: "var(--ns-space-2xs)" }}>
              <div className="ns-field">
                <label className="ns-field__label" htmlFor="int-entity">Entity</label>
                <select id="int-entity" className="ns-input" value={entity} onChange={(e) => setEntity(e.target.value)}>
                  {entities.map((en) => (
                    <option key={en.id} value={en.id}>{en.legal_name}</option>
                  ))}
                </select>
              </div>
              <div className="ns-field">
                <label className="ns-field__label" htmlFor="int-kind">Nature of interest</label>
                <select id="int-kind" className="ns-input" value={kind} onChange={(e) => setKind(e.target.value)}>
                  {KINDS.map(([v, l]) => (
                    <option key={v} value={v}>{l}</option>
                  ))}
                </select>
              </div>
              <Field label="Company / counterparty" value={party} onChange={(e) => setParty(e.target.value)} placeholder="e.g. Sable Capital Partners" />
              <Field label="Details (optional)" value={details} onChange={(e) => setDetails(e.target.value)} error={error ?? undefined} />
              <Button type="submit" disabled={busy || !party}>
                {busy ? "Recording…" : "Declare interest"}
              </Button>
              <p className="ns-muted" style={{ fontSize: "var(--ns-size-caption)", margin: 0 }}>
                Declarations are recorded in your name and written to the audit log.
              </p>
            </form>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
