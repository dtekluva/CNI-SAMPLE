import type { ReactNode } from "react";

type Tone = "neutral" | "success" | "warning" | "danger" | "info" | "ai";

export function Badge({ tone = "neutral", children }: { tone?: Tone; children: ReactNode }) {
  return (
    <span className={`ns-badge ns-badge--${tone}`}>
      <span className="ns-badge__dot" />
      {children}
    </span>
  );
}
