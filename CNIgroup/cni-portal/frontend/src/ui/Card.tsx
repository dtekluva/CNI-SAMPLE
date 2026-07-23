import type { ReactNode } from "react";

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <div className={`ns-card ${className}`.trim()}>{children}</div>;
}

export function CardBody({ children }: { children: ReactNode }) {
  return <div className="ns-card__body">{children}</div>;
}

export function Overline({ children }: { children: ReactNode }) {
  return <div className="ns-overline">{children}</div>;
}
