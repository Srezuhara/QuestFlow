import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";
import type { SkillNodeOut, SkillTreeOut } from "../api";

vi.mock("../api", async () => {
  const actual = await vi.importActual<typeof import("../api")>("../api");
  return { ...actual, fetchSkillTree: vi.fn(), unlockSkillNode: vi.fn() };
});

const { fetchSkillTree } = await import("../api");
const { SkillTree } = await import("./SkillTree");

function makeNode(overrides: Partial<SkillNodeOut>): SkillNodeOut {
  return {
    id: "node-1",
    code: "core_nexus",
    branch: null,
    name: "Core Nexus",
    description: "The origin node.",
    tier: 0,
    xp_cost: 0,
    prerequisite_codes: [],
    icon: "circuit-board",
    layout_x: 0,
    layout_y: 0,
    state: "available",
    unlocked_at: null,
    ...overrides,
  };
}

function makeTree(): SkillTreeOut {
  return {
    nodes: [
      makeNode({ id: "n1", code: "core_nexus", state: "available" }),
      makeNode({
        id: "n2",
        code: "deep_work",
        branch: "focus",
        name: "Deep Work",
        description: "Sustained, undistracted output.",
        tier: 1,
        xp_cost: 500,
        prerequisite_codes: ["core_nexus"],
        icon: "brain-circuit",
        layout_x: 0,
        layout_y: -120,
        state: "locked",
      }),
    ],
    branch_xp: { focus: 0, health: 0, discipline: 0, growth: 0, wealth: 0 },
  };
}

function renderWithClient(ui: ReactNode) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
}

describe("SkillTree", () => {
  it("renders one node per catalog entry and one edge per prerequisite", async () => {
    vi.mocked(fetchSkillTree).mockResolvedValue(makeTree());
    renderWithClient(<SkillTree />);

    await waitFor(() => {
      expect(document.querySelectorAll('[role="button"]')).toHaveLength(2);
    });
    expect(document.querySelectorAll('[data-testid="skill-tree-edge"]')).toHaveLength(1);
  });

  it("a locked node's UNLOCK button is disabled, and Enter on the node opens the detail panel", async () => {
    vi.mocked(fetchSkillTree).mockResolvedValue(makeTree());
    renderWithClient(<SkillTree />);

    const lockedNode = await screen.findByRole("button", { name: /deep work — locked/i });
    fireEvent.keyDown(lockedNode, { key: "Enter" });

    const unlockButton = await screen.findByRole("button", { name: "Unlock" });
    expect(unlockButton).toBeDisabled();
  });

  it("opens nexus-centred at a 420x420 box on mount, not fit to the full node bounds", async () => {
    vi.mocked(fetchSkillTree).mockResolvedValue(makeTree());
    renderWithClient(<SkillTree />);

    const svg = await screen.findByRole("img");
    const [x, y, width, height] = svg.getAttribute("viewBox")!.split(" ").map(Number);
    expect(width).toBeCloseTo(420, 5);
    expect(height).toBeCloseTo(420, 5);
    // core_nexus sits at (0, 0) in this fixture — the 420x420 box centred on
    // it starts at (-210, -210), not the full-tree bounds (which would
    // extend up to y = -120 - 90 = -210 on this fixture's single deep_work
    // node alone, but the point of this test is that it's the *nexus* box,
    // not a fit-to-bounds one).
    expect(x).toBeCloseTo(-210, 5);
    expect(y).toBeCloseTo(-210, 5);
  });
});
