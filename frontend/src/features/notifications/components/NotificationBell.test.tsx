import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";
import { queryKeys } from "@/lib/queryKeys";
import type { NotificationPageOut } from "../api";

vi.mock("../api", async () => {
  const actual = await vi.importActual<typeof import("../api")>("../api");
  return { ...actual, fetchNotifications: vi.fn() };
});

const { fetchNotifications } = await import("../api");
const { NotificationBell } = await import("./NotificationBell");

function makeWrapper(page: NotificationPageOut) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  queryClient.setQueryData([...queryKeys.notifications.all, false], page);
  vi.mocked(fetchNotifications).mockResolvedValue(page);
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
  return wrapper;
}

describe("NotificationBell", () => {
  it("puts the unread count in the accessible name and shows the pill", () => {
    const wrapper = makeWrapper({ items: [], next_before: null, unread_count: 3 });
    render(<NotificationBell onClick={() => {}} />, { wrapper });

    const button = screen.getByRole("button", { name: "Notifications, 3 unread" });
    expect(button).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
  });

  it("uses a plain accessible name and no pill when there are no unread notifications", () => {
    const wrapper = makeWrapper({ items: [], next_before: null, unread_count: 0 });
    render(<NotificationBell onClick={() => {}} />, { wrapper });

    expect(screen.getByRole("button", { name: "Notifications" })).toBeInTheDocument();
  });
});
