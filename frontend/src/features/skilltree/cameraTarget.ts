import type { CameraTarget } from "./useSvgPanZoom";
import type { SkillNodeOut } from "./api";
import type { ViewportModel } from "./components/SkillTree";

const NODE_MARGIN = 90;

/**
 * The unlock camera rule (DA-7), kept pure and out of the component so it's
 * unit-testable without rAF or the DOM:
 *
 * - zero newly-available nodes (a tier-5 leaf) -> centre the just-unlocked node
 * - exactly one -> centre it, at the same comfortable scale-1 framing as the
 *   start view
 * - more than one -> frame the bounding box of the targets plus the
 *   just-unlocked node
 * - unknown `unlockedCode` -> null (defensive; caller skips the move)
 */
export function computeUnlockCameraTarget(
  unlockedCode: string,
  newlyAvailable: string[],
  nodes: SkillNodeOut[],
  model: ViewportModel,
): CameraTarget | null {
  const byCode = new Map(nodes.map((n) => [n.code, n]));
  const unlocked = byCode.get(unlockedCode);
  if (!unlocked) return null;

  const resolved = newlyAvailable
    .map((code) => byCode.get(code))
    .filter((n): n is SkillNodeOut => n !== undefined);

  if (resolved.length === 0) {
    return { x: unlocked.layout_x, y: unlocked.layout_y, scale: 1 };
  }

  if (resolved.length === 1) {
    const target = resolved[0];
    return { x: target.layout_x, y: target.layout_y, scale: 1 };
  }

  const boxNodes = [unlocked, ...resolved];
  const xs = boxNodes.map((n) => n.layout_x);
  const ys = boxNodes.map((n) => n.layout_y);
  const minX = Math.min(...xs) - NODE_MARGIN;
  const maxX = Math.max(...xs) + NODE_MARGIN;
  const minY = Math.min(...ys) - NODE_MARGIN;
  const maxY = Math.max(...ys) + NODE_MARGIN;
  const boxW = maxX - minX;
  const boxH = maxY - minY;
  const scale = clamp(
    Math.min(model.base.width / boxW, model.base.height / boxH),
    model.minScale,
    model.maxScale,
  );

  return {
    x: (minX + maxX) / 2,
    y: (minY + maxY) / 2,
    scale,
  };
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}
