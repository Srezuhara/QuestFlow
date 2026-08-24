import { describe, expect, it } from "vitest";
import { computeUnlockCameraTarget } from "./cameraTarget";
import type { SkillNodeOut } from "./api";
import { computeViewportModel } from "./components/SkillTree";

function makeNode(overrides: Partial<SkillNodeOut>): SkillNodeOut {
  return {
    id: overrides.code ?? "node",
    code: "node",
    branch: null,
    name: "Node",
    description: "",
    tier: 1,
    xp_cost: 500,
    prerequisite_codes: [],
    icon: "circuit-board",
    layout_x: 0,
    layout_y: 0,
    state: "locked",
    unlocked_at: null,
    ...overrides,
  };
}

// A small subset of the real catalog geometry: core_nexus at the origin,
// five tier-1 branches spoked at 72° apart (radius 120), and one tier-2 leaf
// off the focus branch.
const CORE = makeNode({
  id: "n0",
  code: "core_nexus",
  tier: 0,
  xp_cost: 0,
  layout_x: 0,
  layout_y: 0,
});
const FOCUS = makeNode({
  id: "n1",
  code: "deep_work",
  branch: "focus",
  tier: 1,
  layout_x: 0,
  layout_y: -120,
  prerequisite_codes: ["core_nexus"],
});
const HEALTH = makeNode({
  id: "n2",
  code: "health_1",
  branch: "health",
  tier: 1,
  layout_x: 114,
  layout_y: -37,
  prerequisite_codes: ["core_nexus"],
});
const DISCIPLINE = makeNode({
  id: "n3",
  code: "discipline_1",
  branch: "discipline",
  tier: 1,
  layout_x: 70,
  layout_y: 97,
  prerequisite_codes: ["core_nexus"],
});
const GROWTH = makeNode({
  id: "n4",
  code: "growth_1",
  branch: "growth",
  tier: 1,
  layout_x: -70,
  layout_y: 97,
  prerequisite_codes: ["core_nexus"],
});
const WEALTH = makeNode({
  id: "n5",
  code: "wealth_1",
  branch: "wealth",
  tier: 1,
  layout_x: -114,
  layout_y: -37,
  prerequisite_codes: ["core_nexus"],
});
const TIME_BLOCK = makeNode({
  id: "n6",
  code: "time_block",
  branch: "focus",
  tier: 2,
  layout_x: 0,
  layout_y: -240,
  prerequisite_codes: ["deep_work"],
});
const LEAF = makeNode({
  id: "n7",
  code: "focus_tier5",
  branch: "focus",
  tier: 5,
  layout_x: 0,
  layout_y: -600,
  prerequisite_codes: ["time_block"],
});

const ALL_NODES = [CORE, FOCUS, HEALTH, DISCIPLINE, GROWTH, WEALTH, TIME_BLOCK, LEAF];
const MODEL = computeViewportModel(ALL_NODES);

describe("computeUnlockCameraTarget", () => {
  it("centres the single newly-available node at scale 1", () => {
    const target = computeUnlockCameraTarget("deep_work", ["time_block"], ALL_NODES, MODEL);
    expect(target).toEqual({ x: TIME_BLOCK.layout_x, y: TIME_BLOCK.layout_y, scale: 1 });
  });

  it("frames the whole ring near the origin at ~scale 1 when core_nexus unlocks five nodes", () => {
    const target = computeUnlockCameraTarget(
      "core_nexus",
      ["deep_work", "health_1", "discipline_1", "growth_1", "wealth_1"],
      ALL_NODES,
      MODEL,
    );
    expect(target).not.toBeNull();
    expect(target!.x).toBeCloseTo(0, 0);
    expect(target!.y).toBeCloseTo(-12, -1);
    expect(target!.scale).toBeGreaterThan(0.5);
    expect(target!.scale).toBeLessThanOrEqual(MODEL.maxScale);
  });

  it("centres the just-unlocked node itself when there are no newly-available successors", () => {
    const target = computeUnlockCameraTarget("focus_tier5", [], ALL_NODES, MODEL);
    expect(target).toEqual({ x: LEAF.layout_x, y: LEAF.layout_y, scale: 1 });
  });

  it("returns null for an unknown unlocked code", () => {
    const target = computeUnlockCameraTarget("nonexistent", ["time_block"], ALL_NODES, MODEL);
    expect(target).toBeNull();
  });

  it("ignores unknown codes inside newlyAvailable", () => {
    const target = computeUnlockCameraTarget(
      "deep_work",
      ["time_block", "ghost_node"],
      ALL_NODES,
      MODEL,
    );
    expect(target).toEqual({ x: TIME_BLOCK.layout_x, y: TIME_BLOCK.layout_y, scale: 1 });
  });
});
