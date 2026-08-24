import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";
import { queryKeys } from "@/lib/queryKeys";
import type { NoteOut } from "./api";

vi.mock("./api", async () => {
  const actual = await vi.importActual<typeof import("./api")>("./api");
  return { ...actual, toggleCheckbox: vi.fn() };
});

const { toggleCheckbox } = await import("./api");
const { useToggleCheckbox } = await import("./hooks");

function makeNote(overrides: Partial<NoteOut> = {}): NoteOut {
  return {
    id: "note-1",
    title: "Mission Brief",
    body_md: "- [ ] first\n- [ ] second",
    is_pinned: false,
    archived_at: null,
    tags: [],
    linked_tasks: [],
    size_bytes: 20,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    newly_earned_achievements: [],
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

describe("useToggleCheckbox", () => {
  it("optimistically flips the cached body's checkbox on mutate", async () => {
    const note = makeNote();
    const { queryClient, wrapper } = makeWrapper();
    queryClient.setQueryData(queryKeys.notes.detail(note.id), note);
    vi.mocked(toggleCheckbox).mockImplementation(() => new Promise(() => {}));

    const { result } = renderHook(() => useToggleCheckbox(), { wrapper });
    result.current.mutate({ noteId: note.id, lineIndex: 1, checked: true });

    await waitFor(() => {
      const cached = queryClient.getQueryData<NoteOut>(queryKeys.notes.detail(note.id));
      expect(cached?.body_md).toBe("- [ ] first\n- [x] second");
    });
  });

  it("rolls back the optimistic flip when the request fails", async () => {
    const note = makeNote();
    const { queryClient, wrapper } = makeWrapper();
    queryClient.setQueryData(queryKeys.notes.detail(note.id), note);
    vi.mocked(toggleCheckbox).mockRejectedValue(new Error("network down"));

    const { result } = renderHook(() => useToggleCheckbox(), { wrapper });
    result.current.mutate({ noteId: note.id, lineIndex: 1, checked: true });

    await waitFor(() => expect(result.current.isError).toBe(true));

    const cached = queryClient.getQueryData<NoteOut>(queryKeys.notes.detail(note.id));
    expect(cached?.body_md).toBe("- [ ] first\n- [ ] second");
  });
});
