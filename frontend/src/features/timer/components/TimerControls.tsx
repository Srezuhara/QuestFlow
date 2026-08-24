import { Pause, Play, RotateCcw, Square } from "lucide-react";

export function TimerControls({
  isRunning,
  isPaused,
  onReset,
  onTogglePause,
  onStop,
  onStart,
}: {
  isRunning: boolean;
  isPaused: boolean;
  onReset: () => void;
  onTogglePause: () => void;
  onStop: () => void;
  onStart: () => void;
}) {
  return (
    <div className="flex items-center justify-center gap-6">
      <button
        type="button"
        onClick={onReset}
        disabled={!isRunning}
        aria-label="Reset session"
        className="flex size-11 items-center justify-center rounded-full border border-outline-variant text-on-surface-variant transition-colors hover:text-neon-lime disabled:cursor-not-allowed disabled:opacity-40"
      >
        <RotateCcw size={20} aria-hidden="true" />
      </button>

      <button
        type="button"
        onClick={isRunning ? onTogglePause : onStart}
        aria-label={isRunning ? (isPaused ? "Resume session" : "Pause session") : "Start session"}
        className="flex size-16 items-center justify-center bg-neon-lime text-neon-black shadow-[0_0_20px_rgba(195,244,0,0.5)] transition-shadow hover:shadow-[0_0_28px_rgba(195,244,0,0.7)]"
      >
        {isRunning && !isPaused ? (
          <Pause size={28} aria-hidden="true" fill="currentColor" />
        ) : (
          <Play size={28} aria-hidden="true" fill="currentColor" />
        )}
      </button>

      <button
        type="button"
        onClick={onStop}
        disabled={!isRunning}
        aria-label="Stop session"
        className="flex size-11 items-center justify-center rounded-full border border-neon-pink text-neon-pink transition-shadow hover:shadow-[0_0_12px_rgba(254,0,254,0.5)] disabled:cursor-not-allowed disabled:opacity-40"
      >
        <Square size={18} aria-hidden="true" />
      </button>
    </div>
  );
}
