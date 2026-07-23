import { useNavigate } from "react-router-dom";
import { useApi } from "../api/useApi";
import { Badge, CellTitle, EmptyState, PageHeader, Table } from "../ui";

type Meeting = { id: number; title: string; meeting_type: string; starts_at: string; location: string; is_virtual: boolean; quorum: number };

const TYPE_LABEL: Record<string, string> = { board: "Board", committee: "Committee", agm: "AGM", egm: "EGM" };

export function MeetingsScreen() {
  const { data, loading, error } = useApi<Meeting[]>("/meetings/");
  const navigate = useNavigate();
  const meetings = (Array.isArray(data) ? data : []).slice().sort((a, b) => b.starts_at.localeCompare(a.starts_at));
  const now = new Date();

  return (
    <div>
      <PageHeader title="Board Meetings" sub="Convene, notice, agenda and quorum — the full meeting lifecycle." />
      {error && <Badge tone="danger">{error}</Badge>}
      {meetings.length > 0 && (
        <Table
          head={<><th>Meeting</th><th>Type</th><th>When</th><th>Where</th><th className="is-num">Quorum</th><th /></>}
        >
          {meetings.map((m) => {
            const upcoming = new Date(m.starts_at) > now;
            return (
              <tr key={m.id} style={{ cursor: "pointer" }} onClick={() => navigate(`/meetings/${m.id}`)}>
                <td><CellTitle title={m.title} /></td>
                <td><Badge tone="neutral">{TYPE_LABEL[m.meeting_type] ?? m.meeting_type}</Badge></td>
                <td className="ns-muted">
                  {new Date(m.starts_at).toLocaleString(undefined, { day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" })}
                </td>
                <td className="ns-muted">{m.is_virtual ? "Virtual" : m.location || "—"}</td>
                <td className="is-num">Quorum {m.quorum}</td>
                <td className="is-num">{upcoming ? <Badge tone="info">Upcoming</Badge> : <Badge tone="success">Held</Badge>}</td>
              </tr>
            );
          })}
        </Table>
      )}
      {!loading && meetings.length === 0 && (
        <EmptyState title="No meetings yet" hint="Meetings you can see will appear here, scoped to your entities." />
      )}
    </div>
  );
}
