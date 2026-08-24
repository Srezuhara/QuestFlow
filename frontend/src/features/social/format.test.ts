import { describe, expect, it } from "vitest";
import type { FeedItemOut } from "./api";
import { formatFeedLine } from "./format";

function makeItem(overrides: Partial<FeedItemOut> = {}): FeedItemOut {
  return {
    id: "00000000-0000-0000-0000-000000000001",
    actor: { handle: "player1", display_name: "Player One", title: "ARCHITECT", avatar_url: null },
    source_type: "task_complete",
    awarded_xp: 100,
    skill_branch: null,
    created_at: "2026-08-24T00:00:00Z",
    ...overrides,
  };
}

describe("formatFeedLine", () => {
  it("renders task_complete", () => {
    expect(formatFeedLine(makeItem({ source_type: "task_complete" }))).toBe(
      "player1 completed a quest +100 XP",
    );
  });

  it("renders habit_log", () => {
    expect(formatFeedLine(makeItem({ source_type: "habit_log" }))).toBe(
      "player1 logged a habit +100 XP",
    );
  });

  it("renders streak_bonus", () => {
    expect(formatFeedLine(makeItem({ source_type: "streak_bonus" }))).toBe(
      "player1 hit a streak milestone +100 XP",
    );
  });

  it("renders focus_session", () => {
    expect(formatFeedLine(makeItem({ source_type: "focus_session" }))).toBe(
      "player1 finished a focus session +100 XP",
    );
  });

  it("renders achievement", () => {
    expect(formatFeedLine(makeItem({ source_type: "achievement" }))).toBe(
      "player1 unlocked an achievement +100 XP",
    );
  });

  it("falls back to a generic line for an unknown source_type", () => {
    const item = makeItem({ source_type: "quantum_leap" as FeedItemOut["source_type"] });
    expect(formatFeedLine(item)).toBe("player1 earned XP +100 XP");
  });

  it("renders with no bracket when skill_branch is null", () => {
    expect(formatFeedLine(makeItem({ skill_branch: null }))).not.toContain("[");
  });

  it("renders the branch in brackets when present", () => {
    expect(formatFeedLine(makeItem({ skill_branch: "focus" }))).toBe(
      "player1 completed a quest +100 XP [FOCUS]",
    );
  });
});
