import { useState, type FormEvent } from "react";
import { apiPost } from "../api/client";
import { useApi } from "../api/useApi";
import { Badge, Button, Field } from "../ui";

type Item = { id: number; title: string; item_type: string; time_allocation_minutes: number; position: number };

const TYPE_LABEL: Record<string, string> = { approval: "For Approval", discussion: "For Discussion", noting: "For Noting" };

function tone(t: string): "warning" | "neutral" | "info" {
  return t === "approval" ? "warning" : t === "noting" ? "neutral" : "info";
}

/** Clock time for an item, offset from the meeting start by prior allocations. */
function clockAt(startsAt: string | undefined, offsetMin: number) {
  if (!startsAt) return null;
  const t = new Date(startsAt);
  if (isNaN(t.getTime())) return null;
  t.setMinutes(t.getMinutes() + offsetMin);
  return t.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" });
}

export function AgendaBuilder({ meetingId, startsAt }: { meetingId: string | number; startsAt?: string }) {
  const { data, loading, reload } = useApi<Item[]>(`/meetings/${meetingId}/agenda/`);
  const items = (Array.isArray(data) ? data : []).slice().sort((a, b) => a.position - b.position);
  const [title, setTitle] = useState("");
  const [type, setType] = useState("discussion");
  const [minutes, setMinutes] = useState("15");
  const [busy, setBusy] = useState(false);

  const totalMin = items.reduce((s, it) => s + (it.time_allocation_minutes || 0), 0);
  let offset = 0;

  async function add(e: FormEvent) {
    e.preventDefault();
    if (!title.trim()) return;
    setBusy(true);
    try {
      await apiPost(`/meetings/${meetingId}/agenda/`, {
        title,
        item_type: type,
        time_allocation_minutes: Number(minutes) || 0,
      });
      setTitle("");
      reload();
    } finally {
      setBusy(false);
    }
  }

  async function move(index: number, delta: number) {
    const next = items.map((i) => i.id);
    const [moved] = next.splice(index, 1);
    next.splice(index + delta, 0, moved);
    await apiPost(`/meetings/${meetingId}/agenda/reorder/`, { ordered_ids: next });
    reload();
  }

  return (
    <div className="ns-agenda">
      {items.map((it, idx) => {
        const at = clockAt(startsAt, offset);
        offset += it.time_allocation_minutes || 0;
        return (
          <div key={it.id} className="ns-agenda__row">
            <div className="ns-agenda__num">{String(idx + 1).padStart(2, "0")}</div>
            <div className="ns-agenda__time">{at ?? ""}</div>
            <div>
              <div className="ns-agenda__title">{it.title}</div>
            </div>
            <Badge tone={tone(it.item_type)}>{TYPE_LABEL[it.item_type] ?? it.item_type}</Badge>
            <div style={{ display: "flex", alignItems: "center", gap: "var(--ns-space-sm)" }}>
              <span className="ns-agenda__dur">{it.time_allocation_minutes ? `${it.time_allocation_minutes} min` : "—"}</span>
              <span className="ns-agenda__ctl">
                <button
                  type="button"
                  className="ns-agenda__ctlbtn"
                  aria-label={`Move ${it.title} up`}
                  disabled={idx === 0}
                  onClick={() => move(idx, -1)}
                >
                  ▲
                </button>
                <button
                  type="button"
                  className="ns-agenda__ctlbtn"
                  aria-label={`Move ${it.title} down`}
                  disabled={idx === items.length - 1}
                  onClick={() => move(idx, 1)}
                >
                  ▼
                </button>
              </span>
            </div>
          </div>
        );
      })}
      {!loading && items.length === 0 && (
        <span className="ns-muted" style={{ padding: "var(--ns-space-sm) 0" }}>
          No items yet — build the running order below.
        </span>
      )}

      {items.length > 0 && (
        <div className="ns-agenda__foot">
          <span>
            {items.length} item{items.length === 1 ? "" : "s"}
          </span>
          <span>
            {totalMin > 0 && (
              <>
                {Math.floor(totalMin / 60) > 0 ? `${Math.floor(totalMin / 60)}h ` : ""}
                {totalMin % 60}m total
                {clockAt(startsAt, totalMin) ? ` · ends ~${clockAt(startsAt, totalMin)}` : ""}
              </>
            )}
          </span>
        </div>
      )}

      <form onSubmit={add} className="ns-agenda__add">
        <Field label="New agenda item" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="e.g. Q3 financial performance" />
        <div className="ns-field">
          <label className="ns-field__label" htmlFor="agenda-type">Type</label>
          <select id="agenda-type" className="ns-input" value={type} onChange={(e) => setType(e.target.value)} aria-label="Item type">
            <option value="approval">For Approval</option>
            <option value="discussion">For Discussion</option>
            <option value="noting">For Noting</option>
          </select>
        </div>
        <div className="ns-field">
          <label className="ns-field__label" htmlFor="agenda-min">Minutes</label>
          <input
            id="agenda-min"
            className="ns-input"
            type="number"
            min="0"
            step="5"
            value={minutes}
            onChange={(e) => setMinutes(e.target.value)}
            aria-label="Time allocation (minutes)"
          />
        </div>
        <Button type="submit" disabled={busy || !title.trim()}>
          Add
        </Button>
      </form>
    </div>
  );
}
