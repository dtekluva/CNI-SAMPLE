import type { ButtonHTMLAttributes } from "react";

type Variant = "primary" | "secondary" | "ghost" | "danger" | "ai";
type Size = "sm" | "md" | "lg";

export function Button({
  variant = "primary",
  size = "md",
  className = "",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant; size?: Size }) {
  const sizeClass = size === "md" ? "" : ` ns-btn--${size}`;
  return <button className={`ns-btn ns-btn--${variant}${sizeClass} ${className}`.trim()} {...props} />;
}
