import type { ReactNode } from "react";
import { createPortal } from "react-dom";
import { X } from "lucide-react";
import { NeonPanel } from "./NeonPanel";

/**
 * Minimal centered overlay dialog built from `NeonPanel` — the design
 * system's one reusable modal chrome (quest creation now; habit/note
 * creation in later phases reuse it rather than growing their own).
 *
 * Rendered via a portal into `document.body` rather than in place: several
 * callers (e.g. `TaskItem`) mount this inside an ancestor that has
 * `clip-path` (the chamfered-corner `.clip-chamfer` utility on `NeonPanel`/
 * `ChamferBox`), which establishes a new containing block for `position:
 * fixed` descendants in modern browsers — without the portal, the "fixed"
 * overlay gets trapped inside that ancestor's clipped box instead of
 * covering the viewport, and sibling elements intercept its clicks.
 */
export function Modal({
  open,
  onClose,
  title,
  children,
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
}) {
  if (!open) return null;

  return createPortal(
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-neon-black/80 p-4"
      role="dialog"
      aria-modal="true"
      aria-label={title}
      onClick={onClose}
    >
      <NeonPanel glow className="w-full max-w-md" onClick={(e) => e.stopPropagation()}>
        <div className="mb-6 flex items-center justify-between">
          <h2 className="font-display text-title-md text-on-surface uppercase">{title}</h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="text-on-surface-variant hover:text-neon-pink"
          >
            <X size={20} aria-hidden="true" />
          </button>
        </div>
        {children}
      </NeonPanel>
    </div>,
    document.body,
  );
}
