import { useParams } from "react-router-dom";
import { useApi } from "../api/useApi";
import { Badge, Card, CardBody, EmptyState, Overline } from "../ui";

type Profile = {
  id: number;
  entity_name: string;
  name: string;
  designation: string;
  appointed: string;
  ceased_on: string | null;
  active: boolean;
  date_of_birth: string | null;
  nationality: string | null;
  occupation: string | null;
  bvn: string | null;
  document_type: string | null;
  document_number: string | null;
  document_expiry: string | null;
  residential_address: string | null;
  email: string | null;
  phone: string | null;
  other_directorships: string[];
  shares: number | null;
  share_class: string | null;
};

function initials(name: string) {
  const parts = name.split(/\s+/).filter((p) => /^[A-Za-z]/.test(p));
  return ((parts[0]?.[0] ?? "?") + (parts[parts.length - 1]?.[0] ?? "")).toUpperCase();
}
const fmtDate = (iso: string) => new Date(iso).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" });

function Row({ label, value, mono }: { label: string; value?: string | number | null; mono?: boolean }) {
  return (
    <div className="ns-ctxcard__row" style={{ fontSize: "var(--ns-size-body-sm)" }}>
      <span className="ns-muted">{label}</span>
      <b className={mono ? "ns-mono" : undefined} style={{ textAlign: "right" }}>{value ?? "—"}</b>
    </div>
  );
}

export function DirectorProfile() {
  const { id } = useParams();
  const { data: d, loading, error } = useApi<Profile>(`/registers/${id}/director/`);

  if (!d) {
    return (
      <div>
        {loading && <Badge tone="neutral">Loading…</Badge>}
        {!loading && <EmptyState title={error ? "Profile unavailable" : "Director not found"} hint="You may not have access to this register entry." />}
      </div>
    );
  }

  return (
    <div>
      <header className="ns-page__head">
        <div style={{ display: "flex", alignItems: "center", gap: "var(--ns-space-md)" }}>
          <span className="ns-avatar" style={{ width: 64, height: 64, fontSize: "var(--ns-size-subheading)" }}>
            {initials(d.name)}
          </span>
          <div>
            <Overline>{d.entity_name}</Overline>
            <h1 className="ns-page__title">{d.name}</h1>
            <p className="ns-page__sub">
              {d.designation} · appointed {fmtDate(d.appointed)}
            </p>
          </div>
        </div>
        <div className="ns-page__actions">
          {d.active ? <Badge tone="success">Active</Badge> : <Badge tone="neutral">Ceased {d.ceased_on ? fmtDate(d.ceased_on) : ""}</Badge>}
        </div>
      </header>

      <div className="ns-twocol">
        <Card>
          <CardBody>
            <Overline>Identity</Overline>
            <Row label="Full name" value={d.name} />
            <Row label="Date of birth" value={d.date_of_birth ? fmtDate(d.date_of_birth) : null} />
            <Row label="Nationality" value={d.nationality} />
            <Row label="Occupation" value={d.occupation} />
            <Row label="BVN" value={d.bvn} mono />
          </CardBody>
        </Card>

        <Card>
          <CardBody>
            <Overline>Identification document</Overline>
            <Row label="Document type" value={d.document_type} />
            <Row label="Document number" value={d.document_number} mono />
            <Row label="Expiry" value={d.document_expiry ? fmtDate(d.document_expiry) : null} />
          </CardBody>
        </Card>

        <Card>
          <CardBody>
            <Overline>Contact</Overline>
            <Row label="Residential address" value={d.residential_address} />
            <Row label="Email" value={d.email} />
            <Row label="Phone" value={d.phone} mono />
          </CardBody>
        </Card>

        <Card>
          <CardBody>
            <Overline>Governance</Overline>
            <Row label="Shareholding" value={d.shares != null ? `${d.shares.toLocaleString()} ${d.share_class ?? ""}`.trim() : null} mono />
            <Row label="Status" value={d.active ? "Active" : "Ceased"} />
            <div className="ns-ctxcard__row" style={{ fontSize: "var(--ns-size-body-sm)" }}>
              <span className="ns-muted">Other directorships</span>
              <span style={{ textAlign: "right" }}>
                {d.other_directorships.length > 0
                  ? d.other_directorships.map((o) => (
                      <div key={o}><b>{o}</b></div>
                    ))
                  : "—"}
              </span>
            </div>
          </CardBody>
        </Card>
      </div>

      <p className="ns-muted" style={{ fontSize: "var(--ns-size-caption)", marginTop: "var(--ns-space-md)" }}>
        Access to this profile is recorded in the audit log. BVN is shown in full to group administrators only.
      </p>
    </div>
  );
}
