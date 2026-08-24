import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { MemoryRouter, Route, Routes } from "react-router";
import { describe, expect, it, vi } from "vitest";

vi.mock("@/features/progress/api", async () => {
  const actual =
    await vi.importActual<typeof import("@/features/progress/api")>("@/features/progress/api");
  return { ...actual, fetchProgress: vi.fn() };
});
vi.mock("@/features/notifications/api", async () => {
  const actual = await vi.importActual<typeof import("@/features/notifications/api")>(
    "@/features/notifications/api",
  );
  return { ...actual, fetchNotifications: vi.fn() };
});

const { fetchProgress } = await import("@/features/progress/api");
const { fetchNotifications } = await import("@/features/notifications/api");
const { AppShell } = await import("./AppShell");

/**
 * PHASE_8_9_PLAN.md §9.2's stated deliverable: an accessible name on every
 * nav link and the bell. The below-400px bottom tab bar is the one D9-7
 * found with **no** accessible name at all before phase 9's fix (`GlowIcon`
 * sets no title, and the visible label span is `hidden … min-[400px]:block`)
 * — this suite covers both the sidebar and that bottom bar, since jsdom
 * renders every breakpoint's markup regardless of viewport width.
 */
function renderShell() {
  vi.mocked(fetchProgress).mockResolvedValue({
    level: 1,
    total_xp: 0,
    xp_into_level: 0,
    xp_for_next_level: 100,
    percent: 0,
    current_streak_days: 0,
    longest_streak_days: 0,
    last_active_on: null,
  });
  vi.mocked(fetchNotifications).mockResolvedValue({
    items: [],
    next_before: null,
    unread_count: 0,
  });

  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  return render(
    <MemoryRouter initialEntries={["/"]}>
      <Routes>
        <Route element={<AppShell />}>
          <Route index element={<p>dashboard content</p>} />
        </Route>
      </Routes>
    </MemoryRouter>,
    { wrapper },
  );
}

const NAV_LABELS = ["Dashboard", "Habits", "Timer", "Progress", "Reminders", "Notes"];

describe("AppShell accessibility", () => {
  it("gives every nav link (sidebar and bottom tab bar) an accessible name", () => {
    renderShell();
    for (const label of NAV_LABELS) {
      // Both the sidebar (>=640px) and bottom tab bar (<640px) render in
      // jsdom regardless of viewport, so each label matches two links.
      const links = screen.getAllByRole("link", { name: label });
      expect(links.length).toBeGreaterThanOrEqual(1);
    }
  });

  it("gives Settings and Log Out accessible names", () => {
    renderShell();
    expect(screen.getByRole("link", { name: "Settings" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Log Out" })).toBeInTheDocument();
  });

  it("gives the notification bell an accessible name", () => {
    renderShell();
    expect(screen.getAllByRole("button", { name: "Notifications" }).length).toBeGreaterThanOrEqual(
      1,
    );
  });
});
