import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";
import type { HabitMatrixCellOut, HabitMatrixOut, HabitOut } from "../api";

vi.mock("../api", async () => {
  const actual = await vi.importActual<typeof import("../api")>("../api");
  return { ...actual, fetchHabitMatrix: vi.fn() };
});

const { fetchHabitMatrix } = await import("../api");
const { StreakMatrix } = await import("./StreakMatrix");

function makeMatrix(): HabitMatrixOut {
  const cells: HabitMatrixCellOut[] = Array.from({ length: 30 }, (_, i) => {
    const date = new Date(2026, 7, 18 - (29 - i));
    return {
      date: date.toISOString().slice(0, 10),
      count: i === 29 ? 1 : 0,
      status: i === 29 ? "hit" : "empty",
    };
  });
  cells[15] = { ...cells[15], status: "broken", count: 0 };
  return { habit_id: "habit-1", days: 30, cells };
}

function makeHabit(): HabitOut {
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
    streak: { current_streak: 1, longest_streak: 1, last_completed_on: null },
    current_period: { period_start: "2026-08-18", count: 1, target: 1, is_hit: true },
    due_today: false,
  };
}

function renderWithClient(ui: ReactNode) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
}

describe("StreakMatrix", () => {
  it("renders 30 cells and marks the broken cell pink", async () => {
    vi.mocked(fetchHabitMatrix).mockResolvedValue(makeMatrix());
    renderWithClient(<StreakMatrix habits={[makeHabit()]} />);

    await waitFor(() => {
      expect(document.querySelectorAll("button.size-6")).toHaveLength(30);
    });
    const brokenCell = document.querySelectorAll("button.size-6")[15];
    expect(brokenCell.className).toContain("bg-neon-pink");
  });

  it("moves focus with the arrow keys", async () => {
    vi.mocked(fetchHabitMatrix).mockResolvedValue(makeMatrix());
    renderWithClient(<StreakMatrix habits={[makeHabit()]} />);

    await waitFor(() => {
      expect(document.querySelectorAll("button.size-6")).toHaveLength(30);
    });
    const cells = document.querySelectorAll<HTMLButtonElement>("button.size-6");
    cells[0].focus();
    expect(document.activeElement).toBe(cells[0]);

    cells[0].dispatchEvent(
      new KeyboardEvent("keydown", { key: "ArrowRight", bubbles: true, cancelable: true }),
    );
    await waitFor(() => expect(document.activeElement).toBe(cells[1]));
  });
});
