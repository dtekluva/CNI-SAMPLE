import { apiPost } from "../api/client";
import { useApi } from "../api/useApi";
import { Badge, Button, EmptyState, PageHeader } from "../ui";

type Note = { id: number; event_type: string; channel: string; subject: string; body: string; read: boolean; created_at?: string };

export function NotificationsScreen() {
  const { data, loading, reload } = useApi<Note[]>("/notifications/");
  const inbox = (Array.isArray(data) ? data : []).filter((n) => n.channel === "in_portal");
  const unread = inbox.filter((n) => !n.read).length;

  async function markRead(id: number) {
    await apiPost(`/notifications/${id}/read/`);
    reload();
  }

  return (
    <div>
      <PageHeader
        title="Notifications"
        sub={unread > 0 ? `${unread} unread — email only ever carries a link, never board content.` : "You're all caught up."}
      />
      {inbox.length > 0 && (
        <div className="ns-tablewrap">
          {inbox.map((n) => (
            <div key={n.id} className={`ns-listrow${!n.read ? " ns-listrow--unread" : ""}`}>
              <div>
                <div className="ns-table__primary">{n.subject}</div>
                <div className="ns-table__meta">{n.body}</div>
              </div>
              <div style={{ display: "flex", gap: "var(--ns-space-2xs)", alignItems: "center", flex: "none" }}>
                {!n.read && <Badge tone="info">New</Badge>}
                {!n.read && (
                  <Button size="sm" variant="ghost" onClick={() => markRead(n.id)}>
                    Mark read
                  </Button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
      {!loading && inbox.length === 0 && <EmptyState title="No notifications" hint="Meeting notices, pack updates and signature requests will land here." />}
    </div>
  );
}
