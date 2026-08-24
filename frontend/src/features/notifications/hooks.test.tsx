import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { queryKeys } from "@/lib/queryKeys";
import { useNotificationSocketBridge } from "./hooks";

function makeWrapper(queryClient: QueryClient) {
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

describe("useNotificationSocketBridge", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  function stubServiceWorker(): { listeners: ((event: MessageEvent) => void)[] } {
    const listeners: ((event: MessageEvent) => void)[] = [];
    vi.stubGlobal("navigator", {
      ...navigator,
      serviceWorker: {
        addEventListener: (_type: string, handler: (event: MessageEvent) => void) => {
          listeners.push(handler);
        },
        removeEventListener: (_type: string, handler: (event: MessageEvent) => void) => {
          const i = listeners.indexOf(handler);
          if (i >= 0) listeners.splice(i, 1);
        },
      },
    });
    return { listeners };
  }

  it("invalidates the notifications queries when the service worker posts a message", () => {
    const { listeners } = stubServiceWorker();

    const queryClient = new QueryClient();
    const invalidateSpy = vi.spyOn(queryClient, "invalidateQueries");

    const { unmount } = renderHook(() => useNotificationSocketBridge(), {
      wrapper: makeWrapper(queryClient),
    });

    expect(listeners).toHaveLength(1);
    listeners[0]?.({ data: { type: "questflow-notification" } } as MessageEvent);

    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: queryKeys.notifications.all });
    unmount();
  });

  it("ignores unrelated messages", () => {
    const { listeners } = stubServiceWorker();

    const queryClient = new QueryClient();
    const invalidateSpy = vi.spyOn(queryClient, "invalidateQueries");

    const { unmount } = renderHook(() => useNotificationSocketBridge(), {
      wrapper: makeWrapper(queryClient),
    });
    listeners[0]?.({ data: { type: "something-else" } } as MessageEvent);

    expect(invalidateSpy).not.toHaveBeenCalled();
    unmount();
  });
});
