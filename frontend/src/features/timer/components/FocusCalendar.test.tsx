import { render } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { FocusCalendar } from "./FocusCalendar";
import type { FocusDaySummaryOut } from "../api";

function makeDays(year: number, month: number): FocusDaySummaryOut[] {
  const daysInMonth = new Date(year, month, 0).getDate();
  return Array.from({ length: daysInMonth }, (_, i) => ({
    date: `${year}-${String(month).padStart(2, "0")}-${String(i + 1).padStart(2, "0")}`,
    focus_seconds: i === 4 ? 1500 : 0,
    session_count: i === 4 ? 1 : 0,
  }));
}

describe("FocusCalendar", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2026, 7, 18)); // 2026-08-18
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("renders the right number of day cells for the month and marks today", () => {
    const days = makeDays(2026, 8);
    render(
      <FocusCalendar
        year={2026}
        month={8}
        days={days}
        isLoading={false}
        selectedDate="2026-08-18"
        onSelectDate={() => {}}
        onPrevMonth={() => {}}
        onNextMonth={() => {}}
      />,
    );

    const dayButtons = document.querySelectorAll('button[aria-label*="—"]');
    expect(dayButtons).toHaveLength(31);

    const today = document.querySelector('button[aria-current="date"]');
    expect(today).not.toBeNull();
    expect(today?.getAttribute("aria-label")).toContain("2026-08-18");
  });

  it("shows a session dot only on days with logged sessions", () => {
    const days = makeDays(2026, 8);
    render(
      <FocusCalendar
        year={2026}
        month={8}
        days={days}
        isLoading={false}
        selectedDate="2026-08-18"
        onSelectDate={() => {}}
        onPrevMonth={() => {}}
        onNextMonth={() => {}}
      />,
    );

    const dayButtons = document.querySelectorAll('button[aria-label*="—"]');
    const dayWithSession = dayButtons[4];
    expect(dayWithSession.querySelector(".bg-neon-pink")).not.toBeNull();
    const dayWithoutSession = dayButtons[0];
    expect(dayWithoutSession.querySelector(".bg-neon-pink")).toBeNull();
  });
});
