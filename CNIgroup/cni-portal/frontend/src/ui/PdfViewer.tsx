import { useEffect } from "react";
import { Button } from "./Button";
import { Overline } from "./Card";

/**
 * In-app PDF viewer (Northstar modal + native browser PDF rendering).
 * Same-origin /api PDFs inherit the session, so no extra auth plumbing.
 */
export function PdfViewer({ title, src, onClose, overline = "Document" }: { title: string; src: string; onClose: () => void; overline?: string }) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div className="ns-modal" onClick={onClose} role="dialog" aria-modal="true" aria-label={title}>
      <div className="ns-modal__card ns-modal__card--pdf" onClick={(e) => e.stopPropagation()}>
        <div className="ns-modal__head">
          <div>
            <Overline>{overline}</Overline>
            <h2 className="ns-modal__title" style={{ fontSize: "var(--ns-size-subheading)" }}>{title}</h2>
          </div>
          <div style={{ display: "flex", gap: "var(--ns-space-2xs)", alignItems: "center" }}>
            <a href={src} target="_blank" rel="noopener noreferrer" style={{ textDecoration: "none" }}>
              <Button size="sm" variant="ghost">Open in tab</Button>
            </a>
            <button className="ns-modal__close" onClick={onClose} aria-label="Close">✕</button>
          </div>
        </div>
        <iframe className="ns-pdfframe" src={src} title={title} />
      </div>
    </div>
  );
}
