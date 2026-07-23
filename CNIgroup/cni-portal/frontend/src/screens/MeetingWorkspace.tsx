import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { apiPost } from "../api/client";
import { useApi } from "../api/useApi";
import { Badge, Button, Card, CardBody, Icon, Overline } from "../ui";
import { AgendaBuilder } from "./AgendaBuilder";

type Meeting = { id: number; title: string; starts_at: string; meeting_type: string; location: string; is_virtual: boolean; virtual_link: string; virtual_provider: string; dial_in: string };
type Quorum = { present: number; quorum: number; met: boolean };
type Live = { active: boolean; current_item: number | null; current_item_title: string | null; allocated_minutes: number | null; elapsed_minutes: number | null; over: boolean };

function LiveBar({ meetingId }: { meetingId: string }) {
  const { data, reload } = useApi<Live>(`/meetings/${meetingId}/in-meeting/`);
  if (!data) return null;
  async function act(action: string, item?: number) {
    await apiPost(`/meetings/${meetingId}/in-meeting/`, { action, item });
    reload();
  }
  if (!data.active) {
    return (
      <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: "var(--ns-space-md)" }}>
        <Button size="sm" variant="secondary" onClick={() => act("start")}>Start in-meeting mode</Button>
      </div>
    );
  }
  return (
    <div className="ns-live" style={{ marginBottom: "var(--ns-space-md)" }}>
      <span className="ns-live__dot" />
      <div className="ns-live__now">
        <div className="ns-live__label">Live · on the floor</div>
        <div className="ns-live__item">{data.current_item_title ?? "—"}</div>
      </div>
      {data.allocated_minutes != null && (
        <span className={`ns-live__timer${data.over ? " over" : ""}`}>
          {data.elapsed_minutes ?? 0} / {data.allocated_minutes} min{data.over ? " · over" : ""}
        </span>
      )}
      <Button size="sm" variant="ghost" onClick={() => act("end")}>End</Button>
    </div>
  );
}

type Conflict = { id: number; director: number };
type Arising = {
  on_agenda: boolean;
  actions: { id: number; title: string; owner_name: string; due_date: string | null; status: string; source_meeting: string | null }[];
};

function MattersArising({ meetingId, onPlanted }: { meetingId: string; onPlanted: () => void }) {
  const { data, reload } = useApi<Arising>(`/meetings/${meetingId}/matters-arising/`);
  const arising = data && Array.isArray(data.actions) ? data : null;
  if (!arising || arising.actions.length === 0) return null;

  async function plant() {
    await apiPost(`/meetings/${meetingId}/matters-arising/`);
    reload();
    onPlanted();
  }

  return (
    <Card>
      <div className="ns-card__header" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <b>Matters arising</b>
        {arising.on_agenda ? (
          <Badge tone="success">On the agenda</Badge>
        ) : (
          <Button size="sm" variant="secondary" onClick={plant}>
            Add to agenda
          </Button>
        )}
      </div>
      <CardBody>
        <p className="ns-muted" style={{ margin: "0 0 var(--ns-space-sm)", fontSize: "var(--ns-size-body-sm)" }}>
          {arising.actions.length} open action{arising.actions.length === 1 ? "" : "s"} carried from previous meetings.
        </p>
        {arising.actions.map((a) => {
          const overdue = a.due_date && new Date(a.due_date) < new Date();
          return (
            <div key={a.id} className="ns-listrow" style={{ paddingLeft: 0, paddingRight: 0 }}>
              <div>
                <div className="ns-table__primary">{a.title}</div>
                <div className="ns-table__meta">
                  {a.owner_name || "Unassigned"}
                  {a.source_meeting ? ` · from ${a.source_meeting}` : ""}
                </div>
              </div>
              <div style={{ display: "flex", gap: "var(--ns-space-2xs)", alignItems: "center", flex: "none" }}>
                {a.due_date && (
                  <span className={overdue ? "ns-due--over" : "ns-muted"} style={{ fontSize: "var(--ns-size-caption)" }}>
                    due {new Date(a.due_date).toLocaleDateString(undefined, { day: "numeric", month: "short" })}
                  </span>
                )}
                {overdue && <Badge tone="danger">overdue</Badge>}
              </div>
            </div>
          );
        })}
      </CardBody>
    </Card>
  );
}

export function MeetingWorkspace() {
  const { id } = useParams();
  const meeting = useApi<Meeting>(`/meetings/${id}/`);
  const quorum = useApi<Quorum>(`/meetings/${id}/quorum/`);
  const conflicts = useApi<Conflict[]>(`/conflicts/?meeting=${id}`);
  const [declared, setDeclared] = useState(false);
  const [agendaVersion, setAgendaVersion] = useState(0);
  const m = meeting.data;
  const hasConflict = declared || (Array.isArray(conflicts.data) && conflicts.data.length > 0);

  async function declareConflict() {
    await apiPost("/conflicts/", { meeting: Number(id), note: "Declared from the meeting workspace" });
    setDeclared(true);
  }

  return (
    <div>
      <header className="ns-page__head">
        <div>
          <Overline>Board Meeting Workspace</Overline>
          <h1 className="ns-page__title">{m?.title ?? "Meeting"}</h1>
          {m && (
            <p className="ns-page__sub">
              {new Date(m.starts_at).toLocaleString(undefined, { weekday: "long", day: "numeric", month: "long", year: "numeric", hour: "2-digit", minute: "2-digit" })}
              {" · "}
              {m.is_virtual ? "Virtual" : m.location || "Location TBC"}
            </p>
          )}
        </div>
        <div className="ns-page__actions">
          {quorum.data && (
            <Badge tone={quorum.data.met ? "success" : "warning"}>
              Quorum {quorum.data.present} / {quorum.data.quorum}
            </Badge>
          )}
          {hasConflict ? (
            <Badge tone="warning">Conflict declared</Badge>
          ) : (
            <Button size="sm" variant="ghost" onClick={declareConflict}>
              Declare conflict
            </Button>
          )}
          <Link to={`/meetings/${id}/minutes`} style={{ textDecoration: "none" }}>
            <Button size="sm" variant="secondary">Open minutes</Button>
          </Link>
        </div>
      </header>
      {m?.is_virtual && (
        <div className="ns-join">
          <Icon name="calendar" />
          <div>
            <b>{m.virtual_provider || "Virtual meeting"}</b>
            <div className="ns-join__meta">{m.dial_in ? `Dial-in: ${m.dial_in}` : "Join online"}</div>
          </div>
          {m.virtual_link && (
            <a href={m.virtual_link} target="_blank" rel="noopener noreferrer" style={{ marginLeft: "auto", textDecoration: "none" }}>
              <Button size="sm">Join meeting →</Button>
            </a>
          )}
        </div>
      )}
      <LiveBar meetingId={id!} />
      <div style={{ display: "flex", flexDirection: "column", gap: "var(--ns-space-md)" }}>
        <MattersArising meetingId={id!} onPlanted={() => setAgendaVersion((v) => v + 1)} />
        <Card>
          <div className="ns-card__header">
            <b>Agenda</b>
          </div>
          <CardBody>
            <AgendaBuilder key={agendaVersion} meetingId={id!} startsAt={m?.starts_at} />
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
