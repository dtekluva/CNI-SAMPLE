import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { EntitySwitcher } from "../components/EntitySwitcher";
import { useApi } from "../api/useApi";
import { Icon, Overline } from "../ui";

type NavEntry = { to: string; label: string; icon: string };
type NavGroup = { section: string | null; items: NavEntry[] };

const NAV: NavGroup[] = [
  {
    section: null,
    items: [
      { to: "/", label: "Dashboard", icon: "dashboard" },
      { to: "/search", label: "Search & Reports", icon: "search" },
      { to: "/group", label: "Group Overview", icon: "building" },
    ],
  },
  {
    section: "Govern",
    items: [
      { to: "/meetings", label: "Board Meetings", icon: "calendar" },
      { to: "/committees", label: "Committees", icon: "people" },
      { to: "/minutes", label: "Minutes", icon: "minutes" },
      { to: "/resolutions", label: "Resolutions", icon: "gavel" },
      { to: "/delegation", label: "Delegated Authority", icon: "shield" },
      { to: "/actions", label: "Actions", icon: "checks" },
      { to: "/interests", label: "Interests", icon: "check" },
      { to: "/compliance", label: "Compliance", icon: "clipboard" },
    ],
  },
  {
    section: "Records",
    items: [
      { to: "/entities", label: "Entities", icon: "building" },
      { to: "/directors", label: "Directors", icon: "people" },
      { to: "/minute-book", label: "Minute Book", icon: "minutes" },
      { to: "/registers", label: "Registers", icon: "registers" },
      { to: "/documents", label: "Documents", icon: "folder" },
      { to: "/audit", label: "Audit Log", icon: "shield" },
    ],
  },
  {
    section: "Account",
    items: [
      { to: "/notifications", label: "Notifications", icon: "bell" },
      { to: "/announcements", label: "Announcements", icon: "bell" },
      { to: "/access", label: "Access & Roles", icon: "key" },
      { to: "/settings", label: "Settings", icon: "settings" },
    ],
  },
];

type Summary = { upcoming_meetings: number; my_open_actions: number; overdue_actions: number; awaiting_my_signature: number };
type Meeting = { id: number; title: string; starts_at: string };

function initials(nameOrMail: string) {
  const parts = nameOrMail.replace(/@.*/, "").split(/[\s._-]+/).filter(Boolean);
  return ((parts[0]?.[0] ?? "?") + (parts[1]?.[0] ?? "")).toUpperCase();
}

function ContextRail() {
  const { data: summary } = useApi<Summary>("/dashboard/");
  const { data: meetings } = useApi<Meeting[]>("/meetings/");
  const next = (Array.isArray(meetings) ? meetings : [])
    .filter((m) => new Date(m.starts_at) > new Date())
    .sort((a, b) => a.starts_at.localeCompare(b.starts_at))[0];

  return (
    <>
      <EntitySwitcher />
      {next && (
        <div className="ns-ctxcard">
          <Overline>Up next</Overline>
          <div style={{ fontWeight: "var(--ns-weight-semibold)", fontSize: "var(--ns-size-body-sm)" }}>{next.title}</div>
          <div className="ns-muted" style={{ fontSize: "var(--ns-size-caption)", marginTop: 2 }}>
            {new Date(next.starts_at).toLocaleString(undefined, { weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" })}
          </div>
        </div>
      )}
      {summary && typeof summary.my_open_actions === "number" && (
        <div className="ns-ctxcard">
          <Overline>Awaiting you</Overline>
          <div className="ns-ctxcard__row"><span>Open actions</span><b>{summary.my_open_actions}</b></div>
          <div className="ns-ctxcard__row">
            <span>Overdue</span>
            <b className={summary.overdue_actions > 0 ? "ns-due--over" : undefined}>{summary.overdue_actions}</b>
          </div>
          <div className="ns-ctxcard__row"><span>Signatures</span><b>{summary.awaiting_my_signature}</b></div>
        </div>
      )}
    </>
  );
}

export function AppShell() {
  const { session, logout } = useAuth();
  const who = session?.name || session?.email || "";
  return (
    <div className="ns ns-shell">
      <nav className="ns-shell__nav">
        <div className="ns-shell__brand">
          <span className="mark">CL</span> C&I Leasing
        </div>
        <div className="ns-nav__scroll">
          {NAV.map((group) => (
            <div key={group.section ?? "root"} style={{ display: "contents" }}>
              {group.section && <div className="ns-nav__section">{group.section}</div>}
              {group.items.map(({ to, label, icon }) => (
                <NavLink
                  key={to}
                  to={to}
                  end={to === "/"}
                  className={({ isActive }) => `ns-navitem${isActive ? " ns-navitem--active" : ""}`}
                >
                  <Icon name={icon} />
                  {label}
                </NavLink>
              ))}
            </div>
          ))}
        </div>
        <div className="ns-nav__foot" title={session?.email ?? undefined}>
          <span className="ns-avatar">{initials(who)}</span>
          <span className="ns-nav__mail">{session?.name || session?.email}</span>
          <button className="ns-nav__out" onClick={() => logout()} aria-label="Sign out" title="Sign out">
            <Icon name="logout" />
          </button>
        </div>
      </nav>
      <main className="ns-shell__work">
        <Outlet />
      </main>
      <aside className="ns-shell__ctx">
        <ContextRail />
      </aside>
    </div>
  );
}
