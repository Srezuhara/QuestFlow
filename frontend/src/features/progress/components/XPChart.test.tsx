import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";
import type { XPSummaryOut } from "../api";

vi.mock("../api", async () => {
  const actual = await vi.importActual<typeof import("../api")>("../api");
  return { ...actual, fetchXpSummary: vi.fn() };
});

const { fetchXpSummary } = await import("../api");
const { XPChart } = await import("./XPChart");

function makeSummary(): XPSummaryOut {
  const days = Array.from({ length: 30 }, (_, i) => ({
    date: new Date(2026, 7, i + 1).toISOString().slice(0, 10),
    xp: i * 10,
  }));
  return { days, by_branch: [], by_source: [] };
}

function renderWithClient(ui: ReactNode) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
}

describe("XPChart", () => {
  it("renders one bar per day and a visually-hidden table mirror of the same data", async () => {
    vi.mocked(fetchXpSummary).mockResolvedValue(makeSummary());
    renderWithClient(<XPChart days={30} />);

    await waitFor(() => {
      expect(document.querySelectorAll('[data-testid="xp-chart-bar"]')).toHaveLength(30);
    });

    const table = document.querySelector("table.sr-only");
    expect(table).not.toBeNull();
    expect(table?.querySelectorAll("tbody tr")).toHaveLength(30);
  });
});
