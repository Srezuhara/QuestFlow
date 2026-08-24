import { act, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { detectLevelUp, useLevelUpToastStore } from "./levelUpToastStore";
import { LevelUpToast } from "./LevelUpToast";

describe("detectLevelUp", () => {
  it("fires when the level increases", () => {
    expect(detectLevelUp(3, 4)).toBe(true);
  });

  it("does not fire on an equal level", () => {
    expect(detectLevelUp(4, 4)).toBe(false);
  });

  it("does not fire on a decrease (should never happen, D13, but must not crash)", () => {
    expect(detectLevelUp(4, 3)).toBe(false);
  });

  it("does not fire with no previous level cached yet", () => {
    expect(detectLevelUp(undefined, 1)).toBe(false);
  });
});

describe("LevelUpToast", () => {
  beforeEach(() => {
    useLevelUpToastStore.setState({ queue: [] });
  });

  afterEach(() => {
    useLevelUpToastStore.setState({ queue: [] });
    vi.useRealTimers();
  });

  it("renders nothing when the queue is empty", () => {
    render(<LevelUpToast />);
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });

  it("shows a level-up toast and queues a second one behind it", () => {
    render(<LevelUpToast />);

    act(() => {
      useLevelUpToastStore.getState().pushLevelUp(5);
      useLevelUpToastStore.getState().pushAchievement({
        id: "a1",
        code: "first_unlock",
        name: "First Unlock",
        description: "Unlocked your first skill node.",
        tier: "bronze",
        icon: "sparkles",
        xp_reward: 150,
        earned_at: new Date().toISOString(),
        progress_percent: 100,
      });
    });

    expect(screen.getByText("Level Up")).toBeInTheDocument();
    expect(screen.getByText("Level 5")).toBeInTheDocument();
    expect(screen.queryByText("Achievement Unlocked")).not.toBeInTheDocument();

    act(() => {
      useLevelUpToastStore.getState().dismissCurrent();
    });

    expect(screen.getByText("Achievement Unlocked")).toBeInTheDocument();
    expect(screen.getByText("First Unlock")).toBeInTheDocument();
  });

  it("dismisses the current toast when its close button is clicked", () => {
    render(<LevelUpToast />);

    act(() => {
      useLevelUpToastStore.getState().pushLevelUp(2);
    });
    expect(screen.getByRole("status")).toBeInTheDocument();

    act(() => {
      screen.getByRole("button", { name: "Dismiss" }).click();
    });
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });
});
