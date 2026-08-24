import { useCallback, useEffect, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "@/lib/queryKeys";
import {
  useAbandonSession,
  useActiveSession,
  useCompleteSession,
  usePreferences,
  useStartSession,
} from "./hooks";
import { readPersistedTimer, useTimerStore } from "./store";
import type { FocusMode, PreferencesOut } from "./api";

const TICK_MS = 250;

const DEFAULT_PREFERENCES: PreferencesOut = {
  focus_minutes: 25,
  short_break_minutes: 5,
  long_break_minutes: 15,
  sessions_before_long_break: 4,
  sound_enabled: true,
  leaderboard_opt_in: true,
};

function plannedSecondsFor(mode: FocusMode, prefs: PreferencesOut): number {
  const minutes =
    mode === "focus"
      ? prefs.focus_minutes
      : mode === "short_break"
        ? prefs.short_break_minutes
        : prefs.long_break_minutes;
  return minutes * 60;
}

function playChime(): void {
  try {
    const AudioCtx = window.AudioContext;
    const ctx = new AudioCtx();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.frequency.value = 880;
    osc.connect(gain);
    gain.connect(ctx.destination);
    gain.gain.setValueAtTime(0.2, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.5);
    osc.start();
    osc.stop(ctx.currentTime + 0.5);
  } catch {
    // Web Audio unavailable/blocked — the chime is a nicety, not required.
  }
}

/**
 * Drives the Pomodoro timer. Remaining time is always computed from
 * `Date.now()` against a stored end-timestamp — never decremented on each
 * tick — so a throttled background tab can't cause drift. A `localStorage`
 * mirror lets a mid-session refresh resume instantly; the server's
 * `GET /focus/sessions/active` is reconciled against it once on mount and
 * always wins on conflict.
 */
export function useFocusTimer() {
  const queryClient = useQueryClient();
  const { data: preferences } = usePreferences();
  const { data: activeSession } = useActiveSession();
  const startSessionMutation = useStartSession();
  const completeSessionMutation = useCompleteSession();
  const abandonSessionMutation = useAbandonSession();

  const sessionId = useTimerStore((s) => s.sessionId);
  const mode = useTimerStore((s) => s.mode);
  const endsAt = useTimerStore((s) => s.endsAt);
  const taskId = useTimerStore((s) => s.taskId);
  const isPaused = useTimerStore((s) => s.isPaused);
  const pausedRemainingMs = useTimerStore((s) => s.pausedRemainingMs);
  const completedFocusCount = useTimerStore((s) => s.completedFocusCount);
  const begin = useTimerStore((s) => s.begin);
  const clear = useTimerStore((s) => s.clear);
  const pause = useTimerStore((s) => s.pause);
  const resume = useTimerStore((s) => s.resume);
  const incrementCompletedFocusCount = useTimerStore((s) => s.incrementCompletedFocusCount);

  const [, forceTick] = useState(0);
  const originalTitleRef = useRef<string | null>(null);
  const completingRef = useRef(false);
  const reconciledRef = useRef(false);

  useEffect(() => {
    // A functional timer (forces a re-render so the displayed countdown
    // stays accurate), not visual motion — correctly exempt from the
    // reduced-motion audit in PHASE_8_9_PLAN.md §9.5. Do not gate this on
    // `usePrefersReducedMotion()`.
    const id = window.setInterval(() => forceTick((n) => n + 1), TICK_MS);
    return () => window.clearInterval(id);
  }, []);

  useEffect(() => {
    if (reconciledRef.current || activeSession === undefined) return;
    reconciledRef.current = true;

    if (activeSession) {
      const persisted = readPersistedTimer();
      const sameSession = persisted && persisted.sessionId === activeSession.id;
      begin({
        sessionId: activeSession.id,
        mode: activeSession.mode,
        endsAt: sameSession
          ? persisted.endsAt
          : new Date(activeSession.started_at).getTime() + activeSession.planned_seconds * 1000,
        taskId: activeSession.task_id,
      });
    } else {
      clear();
    }
  }, [activeSession, begin, clear]);

  const remainingMs = isPaused
    ? (pausedRemainingMs ?? 0)
    : endsAt === null
      ? 0
      : Math.max(0, endsAt - Date.now());
  const remainingSeconds = Math.ceil(remainingMs / 1000);
  const isRunning = sessionId !== null;

  const start = useCallback(
    (nextMode: FocusMode, nextTaskId?: string | null) => {
      const prefs = preferences ?? DEFAULT_PREFERENCES;
      const plannedSeconds = plannedSecondsFor(nextMode, prefs);
      startSessionMutation.mutate(
        { mode: nextMode, planned_seconds: plannedSeconds, task_id: nextTaskId ?? null },
        {
          onSuccess: (session) => {
            begin({
              sessionId: session.id,
              mode: session.mode,
              endsAt: Date.now() + plannedSeconds * 1000,
              taskId: session.task_id,
            });
          },
        },
      );
    },
    [preferences, startSessionMutation, begin],
  );

  const stop = useCallback(() => {
    if (!sessionId) return;
    abandonSessionMutation.mutate(sessionId);
    clear();
  }, [sessionId, abandonSessionMutation, clear]);

  const reset = useCallback(() => {
    if (!sessionId || !mode) return;
    abandonSessionMutation.mutate(sessionId);
    clear();
    start(mode, taskId);
  }, [sessionId, mode, taskId, abandonSessionMutation, clear, start]);

  const togglePause = useCallback(() => {
    if (isPaused) resume();
    else pause();
  }, [isPaused, resume, pause]);

  // Auto-complete on reaching zero, then auto-advance per the Pomodoro
  // cycle (plan D4): focus -> short break, and every
  // `sessions_before_long_break`-th focus -> long break.
  useEffect(() => {
    if (isPaused || !sessionId || endsAt === null || remainingMs > 0 || completingRef.current) {
      return;
    }
    completingRef.current = true;

    const finishedMode = mode;
    const finishedSessionId = sessionId;
    const finishedTaskId = taskId;

    if (preferences?.sound_enabled ?? true) playChime();

    completeSessionMutation.mutate(finishedSessionId, {
      onSuccess: (response) => {
        queryClient.setQueryData(queryKeys.progress.me, response.progress);
        clear();

        if (finishedMode === "focus") {
          const sessionsBeforeLong = preferences?.sessions_before_long_break ?? 4;
          const nextCount = completedFocusCount + 1;
          incrementCompletedFocusCount();
          start(
            nextCount % sessionsBeforeLong === 0 ? "long_break" : "short_break",
            finishedTaskId,
          );
        } else {
          start("focus", finishedTaskId);
        }
        completingRef.current = false;
      },
      onError: () => {
        completingRef.current = false;
      },
    });
    // Deliberately narrow deps: this effect should only re-evaluate when
    // the countdown crosses zero or pause state changes, not on every
    // preferences/mutation-object identity change.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [remainingMs, isPaused, sessionId, endsAt]);

  useEffect(() => {
    originalTitleRef.current ??= document.title;
    if (isRunning) {
      const mins = Math.floor(remainingSeconds / 60)
        .toString()
        .padStart(2, "0");
      const secs = (remainingSeconds % 60).toString().padStart(2, "0");
      document.title = `${mins}:${secs} — QuestFlow`;
    } else if (originalTitleRef.current) {
      document.title = originalTitleRef.current;
    }
  }, [remainingSeconds, isRunning]);

  useEffect(
    () => () => {
      if (originalTitleRef.current) document.title = originalTitleRef.current;
    },
    [],
  );

  return {
    mode,
    remainingSeconds,
    isRunning,
    isPaused,
    completedFocusCount,
    start,
    stop,
    reset,
    togglePause,
  };
}
