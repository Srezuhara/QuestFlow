import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

export type StatusLevel = "urgent" | "important" | "warning" | "later";

const LEVEL_CLASSES: Record<StatusLevel, string> = {
  urgent: "border-neon-pink text-neon-pink",
  important: "border-neon-lime text-neon-lime",
  warning: "border-neon-yellow text-neon-yellow",
  later: "border-outline text-on-surface-variant",
};

/**
 * Priority/status pill — DESIGN.md "Status Indicators" mapped per the plan's
 * task-priority scheme: urgent=pink, important=lime, warning=yellow,
 * later=muted outline.
 */
export function StatusBadge({ level, children }: { level: StatusLevel; children: ReactNode }) {
  return (
    <span
      className={cn(
        "inline-block border px-2 py-0.5 font-mono text-label-mono uppercase leading-none",
        LEVEL_CLASSES[level],
      )}
    >
      {children}
    </span>
  );
}
