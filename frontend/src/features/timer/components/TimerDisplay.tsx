import type { FocusMode } from "../api";

const MODE_LABEL: Record<FocusMode, string> = {
  focus: "FOCUS_LINK_ACTIVE",
  short_break: "BREAK_CYCLE // SHORT",
  long_break: "BREAK_CYCLE // LONG",
};

function formatClock(totalSeconds: number): string {
  const minutes = Math.floor(totalSeconds / 60)
    .toString()
    .padStart(2, "0");
  const seconds = (totalSeconds % 60).toString().padStart(2, "0");
  return `${minutes}:${seconds}`;
}

export function TimerDisplay({
  mode,
  remainingSeconds,
  isPaused,
}: {
  mode: FocusMode | null;
  remainingSeconds: number;
  isPaused: boolean;
}) {
  return (
    <div className="flex flex-col items-center gap-3 py-8">
      <p className="font-mono text-label-mono text-neon-lime uppercase">
        {mode ? MODE_LABEL[mode] : "STANDBY"}
        {isPaused && " // PAUSED"}
      </p>
      <p
        className="font-display text-[clamp(3.5rem,12vw,7rem)] leading-none tracking-tight text-on-surface tabular-nums"
        style={{ textShadow: "0 0 24px rgba(195,244,0,0.45)" }}
        aria-live="polite"
      >
        {formatClock(remainingSeconds)}
      </p>
    </div>
  );
}
