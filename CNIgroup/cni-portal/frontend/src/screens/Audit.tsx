import { useState } from "react";
import { useApi } from "../api/useApi";
import { Badge, Card, CardBody, EmptyState, Field, PageHeader } from "../ui";

type Event = { id: number; action: string; actor: number | null; timestamp: string };
type Group = { action: string; events: Event[] };

function dotTone(action: string) {
  if (/denied|failed|break_glass|deleted|blocked|purged/.test(action)) return " ns-timeline__dot--danger";
  if (/signed|adopted|passed|verified|published|created|added|filed/.test(action)) return " ns-timeline__dot--success";
  return " ns-timeline__dot--info";
}

const fmtFull = (iso: string) =>
  new Date(iso).toLocaleString(undefined, { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit", second: "2-digit" });
const fmtTime = (iso: string) =>
  new Date(iso).toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit", second: "2-digit" });

/** Fold consecutive runs of the same action into one group (timeline order preserved). */
function aggregate(events: Event[]): Group[] {
  const groups: Group[] = [];
  for (const e of events) {
    const last = groups[groups.length - 1];
    if (last && last.action === e.action) last.events.push(e);
    else groups.push({ action: e.action, events: [e] });
  }
  return groups;
}

function span(events: Event[]) {
  // events arrive newest-first; show oldest -> newest
  const newest = events[0].timestamp;
  const oldest = events[events.length - 1].timestamp;
  const sameDay = new Date(newest).toDateString() === new Date(oldest).toDateString();
  if (events.length === 1) return fmtFull(newest);
  return sameDay ? `${fmtFull(oldest)} – ${fmtTime(newest)}` : `${fmtFull(oldest)} – ${fmtFull(newest)}`;
}

function AuditGroup({ g }: { g: Group }) {
  const [open, setOpen] = useState(false);
  const single = g.events.length === 1;

  if (single) {
    const e = g.events[0];
    return (
      <li className="ns-timeline__item">
        <span className={`ns-timeline__dot${dotTone(e.action)}`} />
        <div className="ns-timeline__row">
          <div className="ns-timeline__who ns-mono">{e.action}</div>
          <div className="ns-muted" style={{ fontSize: "var(--ns-size-caption)", whiteSpace: "nowrap" }}>{fmtFull(e.timestamp)}</div>
        </div>
      </li>
    );
  }

  return (
    <li className="ns-timeline__item">
      <span className={`ns-timeline__dot${dotTone(g.action)}`} />
      <div className={`ns-agg${open ? " ns-agg--open" : ""}`}>
        <button className="ns-agg__head" onClick={() => setOpen((v) => !v)} aria-expanded={open}>
          <span className="ns-agg__chev">▶</span>
          <span className="ns-agg__action ns-mono">{g.action}</span>
          <Badge tone="neutral">{g.events.length} events</Badge>
          <span className="ns-agg__span">{span(g.events)}</span>
        </button>
        {open && (
          <div className="ns-agg__body">
            {g.events.map((e) => (
              <div key={e.id} className="ns-agg__row">
                <span className="ns-mono">#{e.id}</span>
                <span>{fmtFull(e.timestamp)}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </li>
  );
}

export function AuditScreen() {
  const [q, setQ] = useState("");
  const path = q ? `/audit/?action=${encodeURIComponent(q)}` : "/audit/";
  const { data, loading } = useApi<Event[]>(path);
  const events = Array.isArray(data) ? data : [];
  const groups = aggregate(events);
  const folded = groups.filter((g) => g.events.length > 1).length;

  return (
    <div>
      <PageHeader
        title="Audit Log"
        sub={`Append-only and hash-chained — every access and change, provable.${folded > 0 ? ` ${events.length} events in ${groups.length} groups.` : ""}`}
        actions={
          <div style={{ width: 280 }}>
            <Field label="Filter by action" value={q} onChange={(e) => setQ(e.target.value)} placeholder="e.g. resolution.signed" />
          </div>
        }
      />
      {loading && <Badge tone="neutral">Loading…</Badge>}
      {groups.length > 0 && (
        <Card>
          <CardBody>
            <ul className="ns-timeline">
              {groups.map((g) => (
                <AuditGroup key={`${g.action}-${g.events[0].id}`} g={g} />
              ))}
            </ul>
          </CardBody>
        </Card>
      )}
      {!loading && events.length === 0 && (
        <EmptyState title="No events match" hint="Try clearing the filter, or check your scope." />
      )}
    </div>
  );
}
