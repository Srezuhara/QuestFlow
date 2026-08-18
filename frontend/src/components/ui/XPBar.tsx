import { cn } from "@/lib/cn";

/**
 * Level progress bar (sidebar mockup: "XP: 85% TO NEXT LEVEL"). Pure
 * presentational — the real level/XP numbers come from the gamification
 * engine landing in phase 2; callers pass `percent` directly.
 */
export function XPBar({
  percent,
  label,
  className,
}: {
  percent: number;
  label?: string;
  className?: string;
}) {
  const clamped = Math.min(100, Math.max(0, percent));
  return (
    <div className={cn("w-full", className)}>
      <div
        role="progressbar"
        aria-valuenow={clamped}
        aria-valuemin={0}
        aria-valuemax={100}
        className="h-1.5 w-full bg-surface-container-high"
      >
        <div
          className="h-full bg-neon-lime shadow-[0_0_8px_rgba(195,244,0,0.6)] transition-[width] duration-300"
          style={{ width: `${clamped}%` }}
        />
      </div>
      {label && (
        <p className="mt-1 font-mono text-label-mono text-on-surface-variant uppercase">{label}</p>
      )}
    </div>
  );
}
