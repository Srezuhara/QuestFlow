import { memo, useEffect, useMemo, useRef, useState } from "react";
import { Crosshair, Maximize2, ZoomIn, ZoomOut } from "lucide-react";
import { NeonPanel } from "@/components/ui";
import { computeUnlockCameraTarget } from "../cameraTarget";
import { useSkillTree, useUnlockNode } from "../hooks";
import { MAX_SCALE, useSvgPanZoom } from "../useSvgPanZoom";
import type { SvgViewport } from "../useSvgPanZoom";
import type { SkillNodeOut } from "../api";
import { NodeDetailPanel } from "./NodeDetailPanel";
import { SkillNode } from "./SkillNode";

// The initial framing: Core Nexus + the tier-1 ring (~175 units of visual
// extent from centre), with comfortable margin — nothing clipped. `scale = 1`
// is this box; zooming out to `minScale` reveals the whole catalog (DA-1).
export const INITIAL_VIEW_SIZE = 420;
const NODE_MARGIN = 90;
// Lets the node's own pending-state flip and any achievement/level-up toast
// register before the camera starts moving (§A.5).
const UNLOCK_CAMERA_DELAY_MS = 350;

export interface ViewportModel {
  base: SvgViewport;
  minScale: number;
  maxScale: number;
}

export function computeViewportModel(nodes: SkillNodeOut[]): ViewportModel {
  const origin = nodes.find((n) => n.prerequisite_codes.length === 0) ?? nodes[0];
  const cx = origin?.layout_x ?? 0;
  const cy = origin?.layout_y ?? 0;
  const half = INITIAL_VIEW_SIZE / 2;
  const base = { x: cx - half, y: cy - half, width: INITIAL_VIEW_SIZE, height: INITIAL_VIEW_SIZE };

  if (nodes.length === 0) return { base, minScale: 1, maxScale: MAX_SCALE };

  const fullW =
    Math.max(...nodes.map((n) => n.layout_x)) -
    Math.min(...nodes.map((n) => n.layout_x)) +
    NODE_MARGIN * 2;
  const fullH =
    Math.max(...nodes.map((n) => n.layout_y)) -
    Math.min(...nodes.map((n) => n.layout_y)) +
    NODE_MARGIN * 2;
  const fitScale = Math.min(base.width / fullW, base.height / fullH);
  return { base, minScale: Math.min(1, fitScale * 0.95), maxScale: MAX_SCALE };
}

const CONTROL_BUTTON_CLASS =
  "clip-chamfer border border-outline-variant p-2 text-on-surface-variant hover:border-neon-lime hover:text-neon-lime";

const MemoSkillNode = memo(SkillNode);

function SkillTreeEdges({
  nodes,
  byCode,
}: {
  nodes: SkillNodeOut[];
  byCode: Map<string, SkillNodeOut>;
}) {
  return (
    <g data-testid="skill-tree-edges">
      {nodes.flatMap((node) =>
        node.prerequisite_codes.map((preCode) => {
          const pre = byCode.get(preCode);
          if (!pre) return null;
          const lit = pre.state === "unlocked" && node.state !== "locked";
          return (
            <line
              key={`${pre.code}->${node.code}`}
              data-testid="skill-tree-edge"
              x1={pre.layout_x}
              y1={pre.layout_y}
              x2={node.layout_x}
              y2={node.layout_y}
              strokeWidth={2}
              className={lit ? "stroke-neon-lime/60" : "stroke-outline-variant"}
            />
          );
        }),
      )}
    </g>
  );
}

const MemoSkillTreeEdges = memo(SkillTreeEdges);

export function SkillTree() {
  const { data: tree, isLoading, isError } = useSkillTree();
  const [selectedCode, setSelectedCode] = useState<string | null>(null);
  const unlock = useUnlockNode();

  const nodes = useMemo(() => tree?.nodes ?? [], [tree]);
  const model = useMemo(() => computeViewportModel(nodes), [nodes]);
  const panZoom = useSvgPanZoom(model.base, { minScale: model.minScale, maxScale: model.maxScale });
  const byCode = useMemo(() => new Map(nodes.map((n) => [n.code, n])), [nodes]);
  const selectedNode = selectedCode ? byCode.get(selectedCode) : undefined;

  const cameraTimeoutRef = useRef<number | null>(null);
  useEffect(
    () => () => {
      if (cameraTimeoutRef.current !== null) {
        window.clearTimeout(cameraTimeoutRef.current);
      }
    },
    [],
  );

  const handleUnlock = (code: string) =>
    unlock.mutate(code, {
      onSuccess: (result) => {
        // Ordering caveat: the hook's own onSuccess invalidates
        // queryKeys.skillTree.me, so `nodes`/`model` will get a new identity
        // on refetch. `model.base` is value-stable across that refetch
        // (derived from the catalog's origin node, not mutable per-user
        // state), so capturing `nodes`/`model` in this closure rather than
        // reading them fresh afterward is safe — the camera does not jump.
        const target = computeUnlockCameraTarget(code, result.newly_available, nodes, model);
        if (target) {
          cameraTimeoutRef.current = window.setTimeout(() => {
            panZoom.animateTo(target);
          }, UNLOCK_CAMERA_DELAY_MS);
        }
      },
    });

  if (isLoading) {
    return (
      <NeonPanel>
        <p className="font-mono text-label-mono text-neon-lime uppercase">
          &gt;&gt; loading skill matrix...
        </p>
      </NeonPanel>
    );
  }

  if (isError || !tree) {
    return (
      <NeonPanel>
        <p className="font-mono text-label-mono text-neon-pink uppercase">
          &gt;&gt; connection to mainframe failed
        </p>
      </NeonPanel>
    );
  }

  return (
    <NeonPanel className="flex flex-col gap-4">
      <div className="flex items-center justify-between border-b border-surface-container-highest pb-4">
        <h2 className="font-display text-title-md text-on-surface uppercase">Skill Tree Mastery</h2>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={panZoom.zoomOut}
            aria-label="Zoom out"
            className={CONTROL_BUTTON_CLASS}
          >
            <ZoomOut size={16} aria-hidden="true" />
          </button>
          <button
            type="button"
            onClick={panZoom.reset}
            aria-label="Centre on Core Nexus"
            className={CONTROL_BUTTON_CLASS}
          >
            <Crosshair size={16} aria-hidden="true" />
          </button>
          <button
            type="button"
            onClick={panZoom.fitAll}
            aria-label="Fit whole skill tree"
            className={CONTROL_BUTTON_CLASS}
          >
            <Maximize2 size={16} aria-hidden="true" />
          </button>
          <button
            type="button"
            onClick={panZoom.zoomIn}
            aria-label="Zoom in"
            className={CONTROL_BUTTON_CLASS}
          >
            <ZoomIn size={16} aria-hidden="true" />
          </button>
        </div>
      </div>

      <div className="overflow-hidden bg-surface-container-lowest">
        <svg
          ref={panZoom.svgRef}
          viewBox={panZoom.viewBoxAttr}
          onPointerDown={panZoom.onPointerDown}
          onPointerMove={panZoom.onPointerMove}
          onPointerUp={panZoom.onPointerUp}
          className="h-[420px] w-full touch-none select-none"
          role="img"
          aria-label="Skill tree, opening centred on Core Nexus — pan by dragging, zoom with the wheel or the buttons above"
        >
          <MemoSkillTreeEdges nodes={nodes} byCode={byCode} />
          <g>
            {nodes.map((node) => (
              <MemoSkillNode
                key={node.code}
                node={node}
                isPending={unlock.isPending && unlock.variables === node.code}
                onSelect={setSelectedCode}
              />
            ))}
          </g>
        </svg>
      </div>

      {selectedNode && (
        <NodeDetailPanel
          node={selectedNode}
          allNodes={nodes}
          branchXp={tree.branch_xp}
          unlock={unlock}
          onUnlock={handleUnlock}
          onClose={() => setSelectedCode(null)}
        />
      )}
    </NeonPanel>
  );
}
