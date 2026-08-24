import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { queryKeys } from "@/lib/queryKeys";
import { useTimerStore } from "./store";
import type { FocusSessionOut, PreferencesOut } from "./api";

vi.mock("./api", async () => {
  const actual = await vi.importActual<typeof import("./api")>("./api");
  return {
    ...actual,
    fetchActiveSession: vi.fn(),
    fetchPreferences: vi.fn(),
    startSession: vi.fn(),
    completeSession: vi.fn(),
    abandonSession: vi.fn(),
  };
});

const api = await import("./api");
const { useFocusTimer } = await import("./useFocusTimer");

const PREFS: PreferencesOut = {
  focus_minutes: 25,
  short_break_minutes: 5,
  long_break_minutes: 15,
  sessions_before_long_break: 4,
  sound_enabled: false,
  leaderboard_opt_in: true,
};

function makeSession(overrides: Partial<FocusSessionOut> = {}): FocusSessionOut {
  return {
    id: "session-1",
    task_id: null,
    task_title: null,
    mode: "focus",
    planned_seconds: 1500,
    actual_seconds: null,
    started_at: new Date().toISOString(),
    ended_at: null,
    status: "running",
    xp_awarded: 0,
    created_at: new Date().toISOString(),
    ...overrides,
  };
}

function makeWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
  return { queryClient, wrapper };
}

afterEach(() => {
  useTimerStore.setState({
    sessionId: null,
    mode: null,
    endsAt: null,
    taskId: null,
    isPaused: false,
    pausedRemainingMs: null,
    completedFocusCount: 0,
  });
  window.localStorage.clear();
  vi.clearAllMocks();
});

describe("useFocusTimer", () => {
  it(
    "computes remaining time from a stored end-timestamp, not tick counting — a " +
      "10-minute jump with no intervening ticks still lands on the correct remainder",
    async () => {
      vi.useFakeTimers();
      const startedAt = new Date(2026, 0, 1, 9, 0, 0);
      vi.setSystemTime(startedAt);

      const activeSession = makeSession({
        started_at: startedAt.toISOString(),
        planned_seconds: 1500, // 25 minutes
      });
      vi.mocked(api.fetchActiveSession).mockResolvedValue(activeSession);
      vi.mocked(api.fetchPreferences).mockResolvedValue(PREFS);

      const { queryClient, wrapper } = makeWrapper();
      queryClient.setQueryData(queryKeys.focus.active, activeSession);
      queryClient.setQueryData(queryKeys.preferences, PREFS);

      const { result } = renderHook(() => useFocusTimer(), { wrapper });

      expect(result.current.isRunning).toBe(true);
      expect(result.current.remainingSeconds).toBe(1500);

      // Jump 10 minutes in one go (simulating a throttled/backgrounded tab
      // that dropped every intervening setInterval tick), then let the
      // 250ms re-render tick fire exactly once.
      act(() => {
        vi.setSystemTime(new Date(startedAt.getTime() + 10 * 60 * 1000));
        vi.advanceTimersByTime(250);
      });

      expect(result.current.remainingSeconds).toBe(900); // 15 minutes left

      vi.useRealTimers();
    },
  );

  it("auto-advances to a long break on the 4th completed focus session", async () => {
    const expiredSession = makeSession({
      id: "session-4",
      started_at: new Date(Date.now() - 2000).toISOString(),
      planned_seconds: 1,
      mode: "focus",
    });

    vi.mocked(api.fetchActiveSession).mockResolvedValue(expiredSession);
    vi.mocked(api.fetchPreferences).mockResolvedValue(PREFS);
    vi.mocked(api.completeSession).mockResolvedValue({
      session: { ...expiredSession, status: "completed", actual_seconds: 1 },
      xp_delta: 1,
      progress: { level: 1, total_xp: 1, xp_into_level: 1, xp_for_next_level: 100, percent: 1 },
      newly_earned_achievements: [],
    });
    vi.mocked(api.startSession).mockImplementation((data) =>
      Promise.resolve(makeSession({ id: "next-session", mode: data.mode })),
    );

    useTimerStore.setState({ completedFocusCount: 3 });

    const { queryClient, wrapper } = makeWrapper();
    queryClient.setQueryData(queryKeys.focus.active, expiredSession);
    queryClient.setQueryData(queryKeys.preferences, PREFS);

    renderHook(() => useFocusTimer(), { wrapper });

    await waitFor(() => expect(api.completeSession).toHaveBeenCalledWith("session-4"));
    await waitFor(() =>
      expect(api.startSession).toHaveBeenCalledWith(
        expect.objectContaining({ mode: "long_break" }),
      ),
    );
  });

  it("auto-advances a completed short/long break back into a focus session", async () => {
    const expiredBreak = makeSession({
      id: "break-1",
      mode: "short_break",
      started_at: new Date(Date.now() - 2000).toISOString(),
      planned_seconds: 1,
    });

    vi.mocked(api.fetchActiveSession).mockResolvedValue(expiredBreak);
    vi.mocked(api.fetchPreferences).mockResolvedValue(PREFS);
    vi.mocked(api.completeSession).mockResolvedValue({
      session: { ...expiredBreak, status: "completed", actual_seconds: 1 },
      xp_delta: 0,
      progress: { level: 1, total_xp: 0, xp_into_level: 0, xp_for_next_level: 100, percent: 0 },
      newly_earned_achievements: [],
    });
    vi.mocked(api.startSession).mockImplementation((data) =>
      Promise.resolve(makeSession({ id: "next-focus", mode: data.mode })),
    );

    const { queryClient, wrapper } = makeWrapper();
    queryClient.setQueryData(queryKeys.focus.active, expiredBreak);
    queryClient.setQueryData(queryKeys.preferences, PREFS);

    renderHook(() => useFocusTimer(), { wrapper });

    await waitFor(() =>
      expect(api.startSession).toHaveBeenCalledWith(expect.objectContaining({ mode: "focus" })),
    );
  });
});
