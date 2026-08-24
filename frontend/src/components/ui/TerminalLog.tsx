import { cn } from "@/lib/cn";

/**
 * Scrollable mono-font log output — DESIGN.md "Terminals". Each line is
 * prefixed with `>` per the mockups' SYSTEM_LOG panel.
 *
 * `role="log"` + `aria-live="polite"` announce newly appended lines to
 * screen readers without re-announcing the whole log on every update
 * (`aria-relevant="additions"`). `aria-label` is required on every call
 * site — there is more than one `TerminalLog` on a page (dashboard's own
 * activity vs. everyone's), and they must be distinguishable.
 */
export function TerminalLog({
  lines,
  className,
  "aria-label": ariaLabel,
}: {
  lines: string[];
  className?: string;
  "aria-label": string;
}) {
  return (
    <div
      role="log"
      aria-live="polite"
      aria-relevant="additions"
      aria-label={ariaLabel}
      className={cn(
        "max-h-64 overflow-y-auto bg-surface-container-lowest p-3 font-mono text-label-mono text-on-surface-variant",
        className,
      )}
    >
      {lines.map((line, i) => (
        // Log lines are append-only and positionally stable within a render — index key is safe here.
        <p key={i} className="whitespace-pre-wrap py-0.5">
          <span aria-hidden="true">&gt; </span>
          {line}
        </p>
      ))}
    </div>
  );
}
