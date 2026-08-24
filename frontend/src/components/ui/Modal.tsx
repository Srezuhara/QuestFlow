import type { ReactNode } from "react";
import { useEffect, useRef } from "react";
import { createPortal } from "react-dom";
import { X } from "lucide-react";
import { cn } from "@/lib/cn";
import { NeonPanel } from "./NeonPanel";

const FOCUSABLE_SELECTOR =
  'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])';

function getFocusable(container: HTMLElement): HTMLElement[] {
  return Array.from(container.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR));
}

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
 *
 * Focus management (PHASE_8_9_PLAN.md §9.2 item 5 / D9-11): on open, focus
 * moves into the panel and Tab/Shift+Tab cycle within it; Escape closes it
 * the same way the backdrop click does; on close, focus returns to
 * whatever triggered the open. None of this existed before phase 9 — the
 * `role="dialog"`/`aria-modal` attributes were correct but unaccompanied by
 * any actual behaviour.
 */
export function Modal({
  open,
  onClose,
  title,
  children,
  size = "default",
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  /** `"full"` fills the viewport edge-to-edge below `sm` (no backdrop
   * padding, `h-full`) and reverts to the normal centered/chamfered card at
   * `sm` and up — PHASE_8_9_PLAN.md §9.3.1 gap 3. This codebase clips
   * corners with `clip-path` (`clip-chamfer`), not `border-radius`, so
   * "full" keeps the chamfer rather than fighting the utility-class
   * cascade to force it off below `sm` — full-bleed sizing is what actually
   * matters for the cramped-mobile-modal problem this solves. */
  size?: "default" | "full";
}) {
  // `NeonPanel`/`ChamferBox` are plain function components, not
  // `forwardRef`-wrapped — the trap needs a real DOM node to query and
  // focus, so it lives on a plain inner `<div>` rather than reaching for a
  // ref on shared design-system chrome.
  const panelRef = useRef<HTMLDivElement>(null);
  const previouslyFocusedRef = useRef<HTMLElement | null>(null);

  // Latest `onClose` without making it a dependency of the effect below —
  // callers typically pass a fresh arrow function each render (e.g.
  // `onClose={() => setOpen(false)}`), and depending on it directly would
  // re-run the open effect (and steal focus back to the first field) on
  // every keystroke inside the modal's own form.
  const onCloseRef = useRef(onClose);
  useEffect(() => {
    onCloseRef.current = onClose;
  }, [onClose]);

  useEffect(() => {
    if (!open) return;

    previouslyFocusedRef.current = document.activeElement as HTMLElement | null;
    const panel = panelRef.current;
    const initial = panel ? getFocusable(panel)[0] : undefined;
    (initial ?? panel)?.focus();

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        onCloseRef.current();
        return;
      }
      if (event.key !== "Tab") return;

      const current = panelRef.current;
      if (!current) return;
      const focusable = getFocusable(current);
      if (focusable.length === 0) {
        event.preventDefault();
        return;
      }
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }

    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      previouslyFocusedRef.current?.focus?.();
    };
  }, [open]);

  if (!open) return null;

  return createPortal(
    <div
      className={cn(
        "fixed inset-0 z-50 flex bg-neon-black/80",
        size === "full"
          ? "items-stretch justify-stretch p-0 sm:items-center sm:justify-center sm:p-4"
          : "items-center justify-center p-4",
      )}
      role="dialog"
      aria-modal="true"
      aria-label={title}
      onClick={onClose}
    >
      <NeonPanel
        glow
        className={cn(
          "w-full overflow-y-auto",
          size === "full" ? "h-full sm:h-auto sm:max-w-md" : "max-w-md",
        )}
        onClick={(e) => e.stopPropagation()}
      >
        <div ref={panelRef} tabIndex={-1} className="outline-none">
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
        </div>
      </NeonPanel>
    </div>,
    document.body,
  );
}
