import { describe, expect, it } from "vitest";
import { formatShardTime } from "../format";

describe("formatShardTime", () => {
  const now = new Date(2026, 7, 20, 15, 0, 0); // 2026-08-20 15:00 local

  it("shows a time for today", () => {
    const today = new Date(2026, 7, 20, 9, 42, 0);
    expect(formatShardTime(today.toISOString(), now)).toBe("09:42");
  });

  it("shows YESTERDAY for the previous day", () => {
    const yesterday = new Date(2026, 7, 19, 23, 59, 0);
    expect(formatShardTime(yesterday.toISOString(), now)).toBe("YESTERDAY");
  });

  it("shows a day/month for older dates", () => {
    const older = new Date(2026, 9, 12, 10, 0, 0); // Oct 12
    expect(formatShardTime(older.toISOString(), now)).toBe("12 OCT");
  });
});
