import { useState, type FormEvent } from "react";
import { apiPost, api } from "../api/client";
import { useApi } from "../api/useApi";
import { Badge, Button, Card, CardBody, EmptyState, Overline, PageHeader, Table } from "../ui";

type Assignment = {
  id: number;
  user: number;
  user_email: string;
  user_name: string;
  role: string;
  role_display: string;
  entity: number | null;
  scope: string;
  created_at: string;
};
type Options = {
  can_manage: boolean;
  roles: { value: string; label: string }[];
  users: { id: number; email: string; name: string }[];
  entities: { id: number; legal_name: string }[];
};

export function AccessScreen() {
  const { data, loading, reload } = useApi<Assignment[]>("/roles/");
  const { data: opts } = useApi<Options>("/roles/options/");
  const rows = Array.isArray(data) ? data : [];
  const canManage = opts?.can_manage ?? false;

  const [user, setUser] = useState("");
  const [role, setRole] = useState("");
  const [entity, setEntity] = useState(""); // "" = Group (all entities)
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function assign(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await apiPost("/roles/", {
        user: Number(user),
        role,
        entity: entity ? Number(entity) : null,
      });
      reload();
    } catch {
      setError("Could not assign the role.");
    } finally {
      setBusy(false);
    }
  }

  async function revoke(id: number) {
    await api(`/roles/${id}/`, { method: "DELETE" });
    reload();
  }

  const byUser = new Map<string, Assignment[]>();
  for (const r of rows) {
    const key = r.user_name || r.user_email;
    byUser.set(key, [...(byUser.get(key) ?? []), r]);
  }

  return (
    <div>
      <PageHeader
        title="Access & Roles"
        sub="Who can do what, per entity. Least-privilege by default — scoped roles, all changes audited."
      />

      <div className={canManage ? "ns-twocol" : undefined}>
        <div>
          {rows.length > 0 ? (
            <Table head={<><th>Member</th><th>Role</th><th>Scope</th><th /></>}>
              {rows.map((r) => (
                <tr key={r.id}>
                  <td>
                    <div className="ns-table__primary">{r.user_name || r.user_email}</div>
                    {r.user_name && <div className="ns-table__meta">{r.user_email}</div>}
                  </td>
                  <td><Badge tone="info">{r.role_display}</Badge></td>
                  <td>
                    {r.entity === null ? (
                      <Badge tone="warning">Group</Badge>
                    ) : (
                      <span className="ns-muted">{r.scope}</span>
                    )}
                  </td>
                  <td className="is-num">
                    {canManage && (
                      <Button size="sm" variant="ghost" onClick={() => revoke(r.id)}>
                        Revoke
                      </Button>
                    )}
                  </td>
                </tr>
              ))}
            </Table>
          ) : (
            !loading && <EmptyState title="No role assignments visible" hint={canManage ? "Assign the first role using the form." : "You'll see the roles that apply to you here."} />
          )}
          {!canManage && rows.length > 0 && (
            <p className="ns-muted" style={{ fontSize: "var(--ns-size-caption)", marginTop: "var(--ns-space-sm)" }}>
              These are the roles that apply to you. Only a group Company Secretary can assign or revoke roles.
            </p>
          )}
        </div>

        {canManage && (
          <Card>
            <CardBody>
              <Overline>Assign a role</Overline>
              <form onSubmit={assign} style={{ display: "flex", flexDirection: "column", gap: "var(--ns-space-sm)", marginTop: "var(--ns-space-2xs)" }}>
                <div className="ns-field">
                  <label className="ns-field__label" htmlFor="rb-user">Member</label>
                  <select id="rb-user" className="ns-input" value={user} onChange={(e) => setUser(e.target.value)} required>
                    <option value="">Select a member…</option>
                    {opts?.users.map((u) => (
                      <option key={u.id} value={u.id}>{u.name ? `${u.name} (${u.email})` : u.email}</option>
                    ))}
                  </select>
                </div>
                <div className="ns-field">
                  <label className="ns-field__label" htmlFor="rb-role">Role</label>
                  <select id="rb-role" className="ns-input" value={role} onChange={(e) => setRole(e.target.value)} required>
                    <option value="">Select a role…</option>
                    {opts?.roles.map((r) => (
                      <option key={r.value} value={r.value}>{r.label}</option>
                    ))}
                  </select>
                </div>
                <div className="ns-field">
                  <label className="ns-field__label" htmlFor="rb-entity">Scope</label>
                  <select id="rb-entity" className="ns-input" value={entity} onChange={(e) => setEntity(e.target.value)}>
                    <option value="">Group (all entities)</option>
                    {opts?.entities.map((en) => (
                      <option key={en.id} value={en.id}>{en.legal_name}</option>
                    ))}
                  </select>
                  <span className="ns-field__hint">A scoped role cascades to that entity's subsidiaries.</span>
                </div>
                {error && <span className="ns-field__error">{error}</span>}
                <Button type="submit" disabled={busy || !user || !role}>
                  {busy ? "Assigning…" : "Assign role"}
                </Button>
              </form>
            </CardBody>
          </Card>
        )}
      </div>
    </div>
  );
}
