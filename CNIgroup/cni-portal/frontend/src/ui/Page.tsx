import type { ReactNode } from "react";
import { Overline } from "./Card";

/** Page header: overline, title, supporting sentence, actions (Vol IV). */
export function PageHeader({ title, sub, actions }: { title: string; sub?: string; actions?: ReactNode }) {
  return (
    <header className="ns-page__head">
      <div>
        <Overline>CNI Group</Overline>
        <h1 className="ns-page__title">{title}</h1>
        {sub && <p className="ns-page__sub">{sub}</p>}
      </div>
      {actions && <div className="ns-page__actions">{actions}</div>}
    </header>
  );
}

/** Data table wrapper: bordered card surface, inner horizontal scroll, calm density. */
export function Table({ head, children }: { head: ReactNode; children: ReactNode }) {
  return (
    <div className="ns-tablewrap">
      <div className="ns-tablescroll">
        <table className="ns-table">
          <thead>
            <tr>{head}</tr>
          </thead>
          <tbody>{children}</tbody>
        </table>
      </div>
    </div>
  );
}

/** Search input with a leading magnifier, for table toolbars. */
export function SearchBox({ value, onChange, placeholder }: { value: string; onChange: (v: string) => void; placeholder?: string }) {
  return (
    <div className="ns-search ns-toolbar__grow">
      <svg className="ns-ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <circle cx="11" cy="11" r="7" />
        <path d="M21 21l-4.3-4.3" />
      </svg>
      <input
        type="search"
        className="ns-input"
        aria-label={placeholder ?? "Search"}
        placeholder={placeholder ?? "Search…"}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  );
}

export function EmptyState({ title, hint }: { title: string; hint?: string }) {
  return (
    <div className="ns-empty">
      <div className="ns-empty__title">{title}</div>
      {hint && <div className="ns-empty__hint">{hint}</div>}
    </div>
  );
}

export function Stat({ label, value, tone }: { label: string; value: ReactNode; tone?: "danger" | "accent" }) {
  return (
    <div className={`ns-stat${tone ? ` ns-stat--${tone}` : ""}`}>
      <Overline>{label}</Overline>
      <div className="ns-stat__value">{value}</div>
    </div>
  );
}

/** Two-cell primary/meta table cell content. */
export function CellTitle({ title, meta }: { title: ReactNode; meta?: ReactNode }) {
  return (
    <div>
      <div className="ns-table__primary">{title}</div>
      {meta && <div className="ns-table__meta">{meta}</div>}
    </div>
  );
}
