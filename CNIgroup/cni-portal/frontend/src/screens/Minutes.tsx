import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { apiPost } from "../api/client";
import { useApi } from "../api/useApi";
import { Badge, Button, Card, CardBody, CellTitle, EmptyState, PageHeader, Table } from "../ui";

type Block = { id: number; agenda_item: number; agenda_item_title?: string; agenda_item_position?: number; text: string };
type Minutes = { id: number; state: string; attendees: number[]; blocks: Block[] };
type Meeting = { id: number; title: string; starts_at: string; meeting_type: string };

const EDITABLE = new Set(["draft", "chairman_review", "circulated"]);

const STATES = ["draft", "chairman_review", "circulated", "adopted", "signed"] as const;
const NEXT: Record<string, string> = {
  draft: "chairman_review",
  chairman_review: "circulated",
  circulated: "adopted",
  adopted: "signed",
};
const label = (s: string) => s.replace(/_/g, " ");
const capLabel = (s: string) => { const t = label(s); return t.charAt(0).toUpperCase() + t.slice(1); };

export function MinutesList() {
  const { data, loading } = useApi<Meeting[]>("/meetings/");
  const navigate = useNavigate();
  const meetings = (Array.isArray(data) ? data : []).slice().sort((a, b) => b.starts_at.localeCompare(a.starts_at));
  return (
    <div>
      <PageHeader title="Minutes" sub="Item-by-item minuting, tied to each meeting's agenda and workflow." />
      {meetings.length > 0 && (
        <Table head={<><th>Meeting</th><th>Held</th><th /></>}>
          {meetings.map((m) => (
            <tr key={m.id} style={{ cursor: "pointer" }} onClick={() => navigate(`/meetings/${m.id}/minutes`)}>
              <td><CellTitle title={m.title} meta={m.meeting_type} /></td>
              <td className="ns-muted">{new Date(m.starts_at).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" })}</td>
              <td className="is-num"><span className="ns-muted">Open minutes →</span></td>
            </tr>
          ))}
        </Table>
      )}
      {!loading && meetings.length === 0 && <EmptyState title="No meetings yet" />}
    </div>
  );
}

function Pipeline({ state }: { state: string }) {
  const at = STATES.indexOf(state as (typeof STATES)[number]);
  return (
    <div className="ns-pipeline">
      {STATES.map((s, i) => (
        <span key={s} style={{ display: "contents" }}>
          {i > 0 && <span className="ns-pipeline__bar" />}
          <span className={`ns-pipeline__step${i < at ? " ns-pipeline__step--done" : i === at ? " ns-pipeline__step--now" : ""}`}>
            <span className="ns-pipeline__dot" />
            {capLabel(s)}
          </span>
        </span>
      ))}
    </div>
  );
}

function BlockEditor({ meetingId, block, index, editable, onSaved }: {
  meetingId: string;
  block: Block;
  index: number;
  editable: boolean;
  onSaved: () => void;
}) {
  const [text, setText] = useState(block.text);
  const [saving, setSaving] = useState(false);
  const dirty = text !== block.text;

  async function save() {
    setSaving(true);
    try {
      await apiPost(`/meetings/${meetingId}/minutes/block/`, { block: block.id, text });
      onSaved();
    } finally {
      setSaving(false);
    }
  }

  return (
    <div style={{ padding: "var(--ns-space-md) 0", borderTop: index > 0 ? "var(--ns-border-hairline) solid var(--ns-color-border-subtle)" : undefined }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: "var(--ns-space-sm)", marginBottom: "var(--ns-space-2xs)" }}>
        <div style={{ fontWeight: "var(--ns-weight-semibold)" }}>
          {block.agenda_item_position ?? index + 1}. {block.agenda_item_title ?? "Agenda item"}
        </div>
        {editable && dirty && (
          <Button size="sm" onClick={save} disabled={saving}>
            {saving ? "Saving…" : "Save minute"}
          </Button>
        )}
      </div>
      {editable ? (
        <textarea
          className="ns-input"
          aria-label={`Minute for ${block.agenda_item_title ?? `item ${index + 1}`}`}
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Record what was discussed and decided…"
          style={{ minHeight: 96, padding: "var(--ns-space-2xs) var(--ns-space-xs)", fontFamily: "var(--ns-font-reading)", lineHeight: "var(--ns-lh-body)", resize: "vertical" }}
        />
      ) : (
        <div style={{ fontFamily: "var(--ns-font-reading)", lineHeight: "var(--ns-lh-body)", whiteSpace: "pre-wrap" }}>
          {block.text || <span style={{ color: "var(--ns-color-text-tertiary)" }}>— (no minute recorded)</span>}
        </div>
      )}
    </div>
  );
}

export function MinutesEditor() {
  const { id } = useParams();
  const { data, loading, reload } = useApi<Minutes>(`/meetings/${id}/minutes/`);
  const meeting = useApi<Meeting>(`/meetings/${id}/`);
  const [busy, setBusy] = useState(false);

  const editable = !!data && EDITABLE.has(data.state);

  async function advance() {
    if (!data) return;
    const to = NEXT[data.state];
    if (!to) return;
    setBusy(true);
    try {
      await apiPost(`/meetings/${id}/minutes/transition/`, { to_state: to });
      reload();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <PageHeader
        title={meeting.data?.title ? `Minutes — ${meeting.data.title}` : "Minutes"}
        sub={
          editable
            ? "Record each item's minute below, then advance the record through review to signature."
            : "This record is fixed — adopted minutes can no longer be edited."
        }
        actions={
          data && NEXT[data.state] ? (
            <Button size="sm" onClick={advance} disabled={busy}>
              Advance to {label(NEXT[data.state])}
            </Button>
          ) : undefined
        }
      />
      {loading && <Badge tone="neutral">Loading…</Badge>}
      {data && (
        <>
          <div style={{ display: "flex", alignItems: "center", gap: "var(--ns-space-md)", marginBottom: "var(--ns-space-md)" }}>
            <Badge tone="info">{label(data.state)}</Badge>
            <Pipeline state={data.state} />
            <span className="ns-muted" style={{ fontSize: "var(--ns-size-caption)" }}>
              {data.attendees.length > 0 ? `${data.attendees.length} attendees recorded` : "No attendance recorded yet"}
            </span>
          </div>
          <Card>
            <CardBody>
              {data.blocks.map((b, i) => (
                <BlockEditor key={b.id} meetingId={id!} block={b} index={i} editable={editable} onSaved={reload} />
              ))}
              {data.blocks.length === 0 && (
                <span className="ns-muted">No agenda items yet — build the agenda in the meeting workspace first.</span>
              )}
            </CardBody>
          </Card>
        </>
      )}
    </div>
  );
}
