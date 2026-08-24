import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { Sparkles, TrendingUp } from "lucide-react";
import { useLevelUpToastStore } from "./levelUpToastStore";

const AUTO_DISMISS_MS = 5000;

/**
 * Portal-based toast host (same `createPortal`-into-`document.body` approach
 * as `Modal`, for the same clip-path-containing-block reason). Mounted once
 * in `AppShell`; reads a shared Zustand queue so any mutation anywhere in the
 * app can enqueue a level-up or achievement toast. Only the head of the
 * queue renders — a second toast can't stack on top of the first, it waits.
 * The entrance transition is a plain CSS `transition` class, so the global
 * `prefers-reduced-motion` rule in `tokens.css` (which zeroes every
 * transition/animation duration app-wide) covers it for free — no separate
 * reduced-motion branch needed here.
 */
export function LevelUpToast() {
  const queue = useLevelUpToastStore((s) => s.queue);
  const dismissCurrent = useLevelUpToastStore((s) => s.dismissCurrent);
  const current = queue[0];
  const [entered, setEntered] = useState(false);

  useEffect(() => {
    if (!current) {
      setEntered(false);
      return;
    }
    setEntered(false);
    const enterFrame = requestAnimationFrame(() => setEntered(true));
    const dismissTimer = setTimeout(dismissCurrent, AUTO_DISMISS_MS);
    return () => {
      cancelAnimationFrame(enterFrame);
      clearTimeout(dismissTimer);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- re-run only when the toast identity changes
  }, [current?.id]);

  if (!current) return null;

  const isLevel = current.kind === "level";

  return createPortal(
    <div
      role="status"
      aria-live="polite"
      className={`fixed top-6 right-6 z-[60] w-full max-w-xs clip-chamfer border p-4 transition-all duration-300 ease-out ${
        isLevel
          ? "border-neon-lime bg-surface-container-lowest shadow-[0_0_20px_rgba(195,244,0,0.4)]"
          : "border-neon-pink bg-surface-container-lowest shadow-[0_0_20px_rgba(254,0,254,0.4)]"
      } ${entered ? "translate-y-0 opacity-100" : "-translate-y-2 opacity-0"}`}
    >
      <button
        type="button"
        onClick={dismissCurrent}
        aria-label="Dismiss"
        className="absolute top-2 right-2 font-mono text-label-mono text-on-surface-variant hover:text-on-surface"
      >
        &times;
      </button>
      {isLevel ? (
        <div className="flex items-center gap-3">
          <TrendingUp className="text-neon-lime" size={24} aria-hidden="true" />
          <div>
            <p className="font-mono text-label-mono text-neon-lime uppercase">Level Up</p>
            <p className="font-display text-title-md text-on-surface uppercase">
              Level {current.level}
            </p>
          </div>
        </div>
      ) : (
        <div className="flex items-center gap-3">
          <Sparkles className="text-neon-pink" size={24} aria-hidden="true" />
          <div>
            <p className="font-mono text-label-mono text-neon-pink uppercase">
              Achievement Unlocked
            </p>
            <p className="font-display text-title-md text-on-surface uppercase">
              {current.achievement?.name}
            </p>
          </div>
        </div>
      )}
    </div>,
    document.body,
  );
}
