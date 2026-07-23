import { useNavigate, useParams } from "react-router-dom";
import { apiPost } from "../api/client";
import { useApi } from "../api/useApi";
import { Badge, Button, Card, CardBody, EmptyState, Overline } from "../ui";

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
  created_at: string;
};
type Entity = { id: number; legal_name: string };

const fmtDate = (iso: string) =>
  new Date(iso).toLocaleDateString(undefined, { weekday: "long", day: "numeric", month: "long", year: "numeric" });

function Row({ label, value }: { label: string; value?: string | null }) {
  return (
    <div className="ns-ctxcard__row" style={{ fontSize: "var(--ns-size-body-sm)" }}>
      <span className="ns-muted">{label}</span>
      <b style={{ textAlign: "right" }}>{value ?? "—"}</b>
    </div>
  );
}

export function InterestDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { data: i, loading, reload } = useApi<Interest>(`/interests/${id}/`);
  const { data: entitiesData } = useApi<Entity[]>("/entities/");
  const entityName = new Map((Array.isArray(entitiesData) ? entitiesData : []).map((e) => [e.id, e.legal_name]));

  if (!i || !i.id) {
    return (
      <div>
        {loading ? (
          <Badge tone="neutral">Loading…</Badge>
        ) : (
          <EmptyState title="Declaration unavailable" hint="You may not have access to this interest." />
        )}
      </div>
    );
  }

  async function withdraw() {
    await apiPost(`/interests/${id}/withdraw/`);
    reload();
  }

  return (
    <div>
      <header className="ns-page__head">
        <div>
          <Overline>Declaration of Interest</Overline>
          <h1 className="ns-page__title">{i.party}</h1>
          <p className="ns-page__sub">
            {i.kind_display} · declared by {i.director_name || "—"} · {entityName.get(i.entity) ?? `entity #${i.entity}`}
          </p>
        </div>
        <div className="ns-page__actions">
          {i.is_active ? <Badge tone="success">Active</Badge> : <Badge tone="neutral">Withdrawn</Badge>}
          {i.is_active && (
            <Button size="sm" variant="secondary" onClick={withdraw}>
              Withdraw
            </Button>
          )}
          <Button size="sm" variant="ghost" onClick={() => navigate("/interests")}>
            ← All interests
          </Button>
        </div>
      </header>

      <div className="ns-twocol">
        <Card>
          <CardBody>
            <Overline>The interest</Overline>
            <div
              style={{
                fontFamily: "var(--ns-font-reading)",
                fontSize: "var(--ns-size-body)",
                lineHeight: "var(--ns-lh-body-lg)",
                whiteSpace: "pre-wrap",
                marginTop: "var(--ns-space-2xs)",
                maxWidth: "62ch",
              }}
            >
              {i.details || <span className="ns-muted">No further particulars were given beyond the declaration itself.</span>}
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardBody>
            <Overline>Record</Overline>
            <Row label="Nature of interest" value={i.kind_display} />
            <Row label="Company / counterparty" value={i.party} />
            <Row label="Board" value={entityName.get(i.entity) ?? `#${i.entity}`} />
            <Row label="Declared by" value={i.director_name} />
            <Row label="Declared on" value={fmtDate(i.declared_on)} />
            <Row label="Status" value={i.is_active ? "Active" : `Withdrawn ${i.withdrawn_on ? fmtDate(i.withdrawn_on) : ""}`} />
            <p className="ns-muted" style={{ fontSize: "var(--ns-size-caption)", marginTop: "var(--ns-space-sm)", marginBottom: 0 }}>
              CAMA ss.303–306 declaration. Withdrawal end-dates the record — it is never deleted, and every change is audited.
            </p>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
