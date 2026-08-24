import { create } from "zustand";
import type { AchievementOut } from "@/features/achievements/api";

export interface LevelUpToastItem {
  id: string;
  kind: "level" | "achievement";
  level?: number;
  achievement?: AchievementOut;
}

interface ToastState {
  queue: LevelUpToastItem[];
  pushLevelUp: (level: number) => void;
  pushAchievement: (achievement: AchievementOut) => void;
  dismissCurrent: () => void;
}

let counter = 0;
function nextId(): string {
  counter += 1;
  return `toast-${counter}`;
}

/** Small standalone store (no new dependency — reuses the project's existing
 * Zustand) so any mutation's `onSuccess` anywhere in the app can enqueue a
 * toast without prop-drilling through the component tree; `LevelUpToast`'s
 * single host (mounted once in `AppShell`) is the only reader. */
export const useLevelUpToastStore = create<ToastState>((set) => ({
  queue: [],
  pushLevelUp: (level) =>
    set((s) => ({ queue: [...s.queue, { id: nextId(), kind: "level", level }] })),
  pushAchievement: (achievement) =>
    set((s) => ({ queue: [...s.queue, { id: nextId(), kind: "achievement", achievement }] })),
  dismissCurrent: () => set((s) => ({ queue: s.queue.slice(1) })),
}));

/** A level-up toast fires only when we can prove XP actually crossed a
 * level boundary — an `undefined` previous level (first load, nothing
 * cached yet) or an equal/lower level must never fire one. */
export function detectLevelUp(previousLevel: number | undefined, nextLevel: number): boolean {
  return previousLevel !== undefined && nextLevel > previousLevel;
}
