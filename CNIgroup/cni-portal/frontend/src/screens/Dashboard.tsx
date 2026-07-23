import type { ReactNode } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useApi } from "../api/useApi";
import { useAuth } from "../auth/AuthContext";
import { Badge, Button, EmptyState, Icon, Overline } from "../ui";

type Summary = { upcoming_meetings: number; my_open_actions: number; overdue_actions: number; awaiting_my_signature: number };
type Meeting = { id: number; title: string; meeting_type: string; starts_at: string; is_virtual: boolean; location: string; quorum: number };
type Action = { id: number; title: string; owner_name: string; due_date: string | null; status: string };
type Res = { id: number; number: string; title: string; outcome: string; kind: string };
type AuditEvent = { id: number; action: string; timestamp: string };
type Director = { id: number; active: boolean };
type Entity = { id: number };
type Doc = { id: number };
type Obligation = { id: number; rag: "red" | "amber" | "green" };

const fmtDay = (iso: string) => new Date(iso).toLocaleDateString(undefined, { weekday: "short", day: "numeric", month: "short" });

function auditTone(action: string) {
  if (/denied|failed|break_glass|deleted|blocked|purged/.test(action)) return " ns-timeline__dot--danger";
  if (/signed|adopted|passed|verified|published|created|added|filed/.test(action)) return " ns-timeline__dot--success";
  return " ns-timeline__dot--info";
}
const fmtAgo = (iso: string) => {
  const mins = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 60000));
  if (mins < 60) return `${mins}m ago`;
  if (mins < 1440) return `${Math.round(mins / 60)}h ago`;
  return `${Math.round(mins / 1440)}d ago`;
};
const prettyAction = (a: string) => a.replace(/[._]/g, " ");

function Kpi({ icon, value, label, foot, tone }: { icon: string; value: number | string; label: string; foot?: string; tone?: "danger" | "warning" | "success" }) {
  return (
    <div className={`ns-kpi${tone ? ` ns-kpi--${tone}` : ""}`}>
      <div className="ns-kpi__top">
        <span className="ns-kpi__icon"><Icon name={icon} /></span>
      </div>
      <div className="ns-kpi__value">{value}</div>
      <div className="ns-kpi__label">{label}</div>
      {foot && <div className="ns-kpi__foot">{foot}</div>}
    </div>
  );
}

function Panel({ icon, title, link, linkTo, empty, children }: { icon: string; title: string; link?: string; linkTo?: string; empty?: boolean; children: ReactNode }) {
  return (
    <div className="ns-panel">
      <div className="ns-panel__head">
        <span className="ns-panel__title"><Icon name={icon} /> {title}</span>
        {link && linkTo && <Link to={linkTo} className="ns-panel__link">{link}</Link>}
      </div>
      {empty ? <div className="ns-panel__empty">{children}</div> : <div className="ns-panel__body">{children}</div>}
    </div>
  );
}

export function DashboardScreen() {
  const { session } = useAuth();
  const navigate = useNavigate();
  const { data: s } = useApi<Summary>("/dashboard/");
  const { data: meetings } = useApi<Meeting[]>("/meetings/");
  const { data: overdue } = useApi<Action[]>("/actions/?overdue=true");
  const { data: resData } = useApi<Res[]>("/resolutions/");
  const { data: auditData } = useApi<AuditEvent[]>("/audit/");
  const { data: dirData } = useApi<Director[]>("/registers/directors/");
  const { data: entData } = useApi<Entity[]>("/entities/");
  const { data: docData } = useApi<Doc[]>("/documents/");
  const { data: compData } = useApi<Obligation[]>("/compliance/");

  const who = (session?.name || session?.email || "").split(" ")[0];
  const upcoming = (Array.isArray(meetings) ? meetings : [])
    .filter((m) => new Date(m.starts_at) > new Date())
    .sort((a, b) => a.starts_at.localeCompare(b.starts_at));
  const next = upcoming[0];
  const late = (Array.isArray(overdue) ? overdue : []).filter((a) => a.status === "open").slice(0, 5);
  const openVotes = (Array.isArray(resData) ? resData : []).filter((r) => r.outcome === "pending").slice(0, 5);
  const recent = (Array.isArray(auditData) ? auditData : []).slice(0, 8);
  const nEntities = Array.isArray(entData) ? entData.length : null;
  const nDirectors = Array.isArray(dirData) ? dirData.filter((d) => d.active).length : null;
  const nDocs = Array.isArray(docData) ? docData.length : null;
  const comp = Array.isArray(compData) ? compData : [];
  const rag = { red: comp.filter((o) => o.rag === "red").length, amber: comp.filter((o) => o.rag === "amber").length, green: comp.filter((o) => o.rag === "green").length };

  const glance = [
    nEntities != null ? `${nEntities} entities` : null,
    nDirectors != null ? `${nDirectors} active directors` : null,
    nDocs != null ? `${nDocs} documents` : null,
  ].filter(Boolean);

  const daysTo = next ? Math.ceil((new Date(next.starts_at).getTime() - Date.now()) / 86_400_000) : null;

  return (
    <div className="ns-dash">
      <header className="ns-page__head" style={{ marginBottom: 0 }}>
        <div>
          <Overline>CNI Group</Overline>
          <h1 className="ns-page__title">{who ? `Good day, ${who}` : "Dashboard"}</h1>
          <p className="ns-page__sub">{glance.length > 0 ? glance.join(" · ") : "Here is where the group stands today."}</p>
        </div>
      </header>

      {/* KPI tiles */}
      <div className="ns-kpis">
        <Kpi icon="calendar" value={s?.upcoming_meetings ?? "—"} label="Upcoming meetings" foot={next ? `next ${fmtDay(next.starts_at)}` : undefined} />
        <Kpi icon="checks" value={s?.my_open_actions ?? "—"} label="My open actions" tone={s && s.my_open_actions > 0 ? "warning" : undefined} />
        <Kpi icon="bell" value={s?.overdue_actions ?? "—"} label="Overdue actions" tone={s && s.overdue_actions > 0 ? "danger" : "success"} foot={s && s.overdue_actions === 0 ? "all clear" : undefined} />
        <Kpi icon="gavel" value={s?.awaiting_my_signature ?? "—"} label="Awaiting my signature" tone={s && s.awaiting_my_signature > 0 ? "warning" : undefined} />
      </div>

      {/* Up-next hero */}
      {next && (
        <div className="ns-uxt">
          <div className="ns-uxt__k">Up next</div>
          <div className="ns-uxt__title">{next.title}</div>
          <div className="ns-uxt__facts">
            <div className="ns-uxt__fact"><b>{new Date(next.starts_at).toLocaleDateString(undefined, { day: "numeric", month: "short" })}</b><span>{new Date(next.starts_at).toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" })}{daysTo != null ? ` · in ${daysTo}d` : ""}</span></div>
            <div className="ns-uxt__fact"><b>{next.is_virtual ? "Virtual" : (next.location || "TBC")}</b><span>{next.meeting_type}</span></div>
            <div className="ns-uxt__fact"><b>{next.quorum}</b><span>quorum required</span></div>
          </div>
          <div className="ns-uxt__cta">
            <Button size="sm" variant="secondary" onClick={() => navigate(`/meetings/${next.id}`)}>Open workspace →</Button>
          </div>
        </div>
      )}

      {/* Two-column body */}
      <div className="ns-dashgrid">
        <div style={{ display: "flex", flexDirection: "column", gap: "var(--ns-space-md)" }}>
          <Panel icon="bell" title="Needs attention" link="All actions" linkTo="/actions" empty={late.length === 0}>
            {late.length === 0 ? "Nothing overdue — all clear." : late.map((a) => (
              <div key={a.id} className="ns-mini">
                <div className="ns-mini__main">
                  <div className="ns-mini__title">{a.title}</div>
                  <div className="ns-mini__meta">{a.owner_name || "Unassigned"}</div>
                </div>
                <div className="ns-mini__side">
                  {a.due_date && <span className="ns-due--over" style={{ fontSize: "var(--ns-size-caption)" }}>due {fmtDay(a.due_date)}</span>}
                </div>
              </div>
            ))}
          </Panel>

          <Panel icon="gavel" title="Open votes" link="All resolutions" linkTo="/resolutions" empty={openVotes.length === 0}>
            {openVotes.length === 0 ? "No resolutions awaiting a vote." : openVotes.map((r) => (
              <Link key={r.id} to="/resolutions" className="ns-mini">
                <div className="ns-mini__main">
                  <div className="ns-mini__title">{r.title}</div>
                  <div className="ns-mini__meta ns-mono">{r.number}</div>
                </div>
                <div className="ns-mini__side"><Badge tone="warning">pending</Badge></div>
              </Link>
            ))}
          </Panel>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "var(--ns-space-md)" }}>
          {comp.length > 0 && (
            <Panel icon="clipboard" title="Compliance" link="Calendar" linkTo="/compliance">
              <div className="ns-rag">
                <div className="ns-rag__cell ns-rag--red"><div className="ns-rag__n">{rag.red}</div><div className="ns-rag__l">Overdue</div></div>
                <div className="ns-rag__cell ns-rag--amber"><div className="ns-rag__n">{rag.amber}</div><div className="ns-rag__l">Due soon</div></div>
                <div className="ns-rag__cell ns-rag--green"><div className="ns-rag__n">{rag.green}</div><div className="ns-rag__l">On track</div></div>
              </div>
            </Panel>
          )}

          <Panel icon="shield" title="Recent activity" link="Audit log" linkTo="/audit" empty={recent.length === 0}>
            {recent.length === 0 ? "No recent events in your scope." : (
              <ul className="ns-timeline" style={{ margin: 0, padding: "var(--ns-space-2xs) var(--ns-space-md)" }}>
                {recent.map((e) => (
                  <li key={e.id} className="ns-timeline__item" style={{ paddingBottom: "var(--ns-space-sm)" }}>
                    <span className={`ns-timeline__dot${auditTone(e.action)}`} />
                    <div className="ns-timeline__row">
                      <div className="ns-timeline__who" style={{ fontSize: "var(--ns-size-body-sm)" }}>{prettyAction(e.action)}</div>
                      <div className="ns-muted" style={{ fontSize: "var(--ns-size-caption)", whiteSpace: "nowrap" }}>{fmtAgo(e.timestamp)}</div>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </Panel>
        </div>
      </div>

      {!s && !meetings && <EmptyState title="Loading your governance world…" />}
    </div>
  );
}
