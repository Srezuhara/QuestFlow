import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";
import { queryKeys } from "@/lib/queryKeys";
import type { HabitOut } from "./api";

vi.mock("./api", async () => {
  const actual = await vi.importActual<typeof import("./api")>("./api");
  return { ...actual, logHabit: vi.fn() };
});

const { logHabit } = await import("./api");
const { useLogHabit } = await import("./hooks");

function makeHabit(overrides: Partial<HabitOut> = {}): HabitOut {
  return {
    id: "habit-1",
    project_id: null,
    name: "Morning Run",
    description: null,
    cadence: "daily",
    target_per_period: 1,
    skill_branch: "focus",
    xp_value: 100,
    is_active: true,
    archived_at: null,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    streak: { current_streak: 0, longest_streak: 0, last_completed_on: null },
    current_period: { period_start: "2026-08-18", count: 0, target: 1, is_hit: false },
    due_today: true,
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

describe("useLogHabit", () => {
  it("optimistically bumps current_period.count on mutate", async () => {
    const habit = makeHabit();
    const { queryClient, wrapper } = makeWrapper();
    queryClient.setQueryData(queryKeys.habits.all, [habit]);
    vi.mocked(logHabit).mockImplementation(() => new Promise(() => {}));

    const { result } = renderHook(() => useLogHabit(), { wrapper });
    result.current.mutate(habit);

    await waitFor(() => {
      const habits = queryClient.getQueryData<HabitOut[]>(queryKeys.habits.all);
      expect(habits?.[0].current_period.count).toBe(1);
      expect(habits?.[0].due_today).toBe(false);
    });
  });

  it("rolls back the optimistic update when the request fails", async () => {
    const habit = makeHabit();
    const { queryClient, wrapper } = makeWrapper();
    queryClient.setQueryData(queryKeys.habits.all, [habit]);
    vi.mocked(logHabit).mockRejectedValue(new Error("network down"));

    const { result } = renderHook(() => useLogHabit(), { wrapper });
    result.current.mutate(habit);

    await waitFor(() => expect(result.current.isError).toBe(true));

    const habits = queryClient.getQueryData<HabitOut[]>(queryKeys.habits.all);
    expect(habits?.[0].current_period.count).toBe(0);
  });
});
