import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";
import { queryKeys } from "@/lib/queryKeys";
import type { ReminderOut, ReminderPageOut } from "./api";

vi.mock("./api", async () => {
  const actual = await vi.importActual<typeof import("./api")>("./api");
  return { ...actual, dismissReminder: vi.fn() };
});

const { dismissReminder } = await import("./api");
const { useDismissReminder } = await import("./hooks");

function makeReminder(overrides: Partial<ReminderOut> = {}): ReminderOut {
  return {
    id: "reminder-1",
    message: "Take a break",
    remind_at: new Date().toISOString(),
    task_id: null,
    habit_id: null,
    target_label: null,
    rrule: null,
    channels: ["push", "in_app"],
    status: "scheduled",
    sent_at: null,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
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

describe("useDismissReminder", () => {
  it("optimistically flips the cached status to dismissed", async () => {
    const reminder = makeReminder();
    const page: ReminderPageOut = { items: [reminder], next_before: null };
    const { queryClient, wrapper } = makeWrapper();
    queryClient.setQueryData(queryKeys.reminders.list(undefined), page);
    vi.mocked(dismissReminder).mockImplementation(() => new Promise(() => {}));

    const { result } = renderHook(() => useDismissReminder(), { wrapper });
    result.current.mutate(reminder.id);

    await waitFor(() => {
      const cached = queryClient.getQueryData<ReminderPageOut>(queryKeys.reminders.list(undefined));
      expect(cached?.items[0]?.status).toBe("dismissed");
    });
  });

  it("rolls back the optimistic flip when the request fails", async () => {
    const reminder = makeReminder();
    const page: ReminderPageOut = { items: [reminder], next_before: null };
    const { queryClient, wrapper } = makeWrapper();
    queryClient.setQueryData(queryKeys.reminders.list(undefined), page);
    vi.mocked(dismissReminder).mockRejectedValue(new Error("network down"));

    const { result } = renderHook(() => useDismissReminder(), { wrapper });
    result.current.mutate(reminder.id);

    await waitFor(() => expect(result.current.isError).toBe(true));

    const cached = queryClient.getQueryData<ReminderPageOut>(queryKeys.reminders.list(undefined));
    expect(cached?.items[0]?.status).toBe("scheduled");
  });
});
