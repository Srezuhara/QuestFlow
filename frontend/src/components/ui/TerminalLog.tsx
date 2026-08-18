import { cn } from "@/lib/cn";

/**
 * Scrollable mono-font log output — DESIGN.md "Terminals". Each line is
 * prefixed with `>` per the mockups' SYSTEM_LOG panel.
 */
export function TerminalLog({ lines, className }: { lines: string[]; className?: string }) {
  return (
    <div
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
