import type { InputHTMLAttributes } from "react";

export function Field({
  label,
  hint,
  error,
  id,
  ...props
}: InputHTMLAttributes<HTMLInputElement> & { label: string; hint?: string; error?: string }) {
  const inputId = id ?? `f-${label.replace(/\s+/g, "-").toLowerCase()}`;
  return (
    <div className="ns-field">
      <label className="ns-field__label" htmlFor={inputId}>
        {label}
      </label>
      <input id={inputId} className="ns-input" aria-invalid={error ? "true" : undefined} {...props} />
      {hint && !error && <span className="ns-field__hint">{hint}</span>}
      {error && <span className="ns-field__error">{error}</span>}
    </div>
  );
}
