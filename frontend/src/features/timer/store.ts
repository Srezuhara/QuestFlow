import { create } from "zustand";
import type { FocusMode } from "./api";

const STORAGE_KEY = "questflow.timer";

export interface TimerSnapshot {
  sessionId: string;
  mode: FocusMode;
  /** Epoch ms — when this session's planned duration elapses. */
  endsAt: number;
  taskId: string | null;
}

interface TimerState {
  sessionId: string | null;
  mode: FocusMode | null;
  endsAt: number | null;
  taskId: string | null;
  isPaused: boolean;
  pausedRemainingMs: number | null;
  completedFocusCount: number;
  begin: (snapshot: TimerSnapshot) => void;
  clear: () => void;
  pause: () => void;
  resume: () => void;
  incrementCompletedFocusCount: () => void;
}

function persist(snapshot: TimerSnapshot | null): void {
  if (snapshot) {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(snapshot));
  } else {
    window.localStorage.removeItem(STORAGE_KEY);
  }
}

/** Read the last-known timer state written to localStorage — used on mount
 * to resume a session across a page refresh, before the server's active
 * session (which always wins on conflict) has loaded. */
export function readPersistedTimer(): TimerSnapshot | null {
  const raw = window.localStorage.getItem(STORAGE_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as TimerSnapshot;
  } catch {
    return null;
  }
}

export const useTimerStore = create<TimerState>((set, get) => ({
  sessionId: null,
  mode: null,
  endsAt: null,
  taskId: null,
  isPaused: false,
  pausedRemainingMs: null,
  completedFocusCount: 0,
  begin: (snapshot) => {
    persist(snapshot);
    set({
      sessionId: snapshot.sessionId,
      mode: snapshot.mode,
      endsAt: snapshot.endsAt,
      taskId: snapshot.taskId,
      isPaused: false,
      pausedRemainingMs: null,
    });
  },
  clear: () => {
    persist(null);
    set({
      sessionId: null,
      mode: null,
      endsAt: null,
      taskId: null,
      isPaused: false,
      pausedRemainingMs: null,
    });
  },
  pause: () => {
    const { endsAt, isPaused } = get();
    if (isPaused || endsAt === null) return;
    set({ isPaused: true, pausedRemainingMs: Math.max(0, endsAt - Date.now()) });
  },
  resume: () => {
    const { isPaused, pausedRemainingMs, sessionId, mode, taskId } = get();
    if (!isPaused || pausedRemainingMs === null || sessionId === null || mode === null) return;
    const endsAt = Date.now() + pausedRemainingMs;
    persist({ sessionId, mode, endsAt, taskId });
    set({ isPaused: false, pausedRemainingMs: null, endsAt });
  },
  incrementCompletedFocusCount: () =>
    set((s) => ({ completedFocusCount: s.completedFocusCount + 1 })),
}));
