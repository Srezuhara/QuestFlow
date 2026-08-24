import type { KeyboardEvent } from "react";
import { lucideByName } from "@/lib/lucideByName";
import type { SkillNodeOut } from "../api";

const NODE_RADIUS = 26;

/**
 * One `<g>` per catalog node, positioned by the parent at `layout_x/layout_y`
 * (already computed server-side, D20). SVG glow uses `filter: drop-shadow`
 * (the "never use `filter`" rule from phase 3 was about HTML boxes, not SVG
 * — this is the correct mechanism here). The pulse on `available` nodes is a
 * Tailwind `motion-safe:animate-pulse` utility, so `prefers-reduced-motion`
 * disables it for free without a separate branch.
 */
export function SkillNode({
  node,
  isPending = false,
  onSelect,
}: {
  node: SkillNodeOut;
  isPending?: boolean;
  onSelect: (code: string) => void;
}) {
  const Icon = lucideByName(node.icon);
  const state = node.state;

  const strokeClass =
    state === "unlocked"
      ? "stroke-neon-lime"
      : state === "available"
        ? "stroke-neon-lime"
        : "stroke-outline-variant";
  const fillClass = state === "unlocked" ? "fill-neon-lime" : "fill-surface-container-high";
  const iconColorClass =
    state === "unlocked"
      ? "text-neon-black"
      : state === "available"
        ? "text-neon-lime"
        : "text-on-surface-variant";
  const glowClass =
    state === "unlocked"
      ? "drop-shadow-[0_0_10px_rgba(195,244,0,0.9)]"
      : state === "available"
        ? "motion-safe:animate-pulse drop-shadow-[0_0_8px_rgba(195,244,0,0.6)]"
        : "";

  function handleKeyDown(e: KeyboardEvent<SVGGElement>) {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      onSelect(node.code);
    }
  }

  return (
    <g transform={`translate(${node.layout_x} ${node.layout_y})`}>
      {/* The interactive `<g>` deliberately contains *only* the circle/icon
          (a symmetric hit-target around the node's own origin) — the label
          `<text>` below lives outside it as a sibling. SVG hit-testing (and
          any tooling that clicks at the center of an element's bounding
          box) only registers a click on painted geometry actually under the
          pointer; if the text were inside this `<g>`, its bbox — and its
          *center* — would skew downward toward the label, off the visible
          circle, especially at this tree's default zoomed-out scale where
          nodes render only a few px across. The oversized transparent
          `hit-circle` also gives real pointer users (and touch) a more
          forgiving target than the thin visible ring alone. */}
      <g
        tabIndex={0}
        role="button"
        aria-label={`${node.name} — ${state}${isPending ? ", unlocking" : ""}`}
        data-state={state}
        onClick={() => onSelect(node.code)}
        onKeyDown={handleKeyDown}
        className={`cursor-pointer outline-none ${glowClass} ${isPending ? "opacity-60" : ""}`}
      >
        <circle r={NODE_RADIUS + 14} fill="transparent" pointerEvents="all" />
        <circle
          r={NODE_RADIUS}
          strokeWidth={state === "locked" ? 1.5 : 2.5}
          className={`${fillClass} ${strokeClass} focus-visible:stroke-neon-yellow`}
        />
        <foreignObject x={-12} y={-12} width={24} height={24} className="pointer-events-none">
          <Icon size={24} className={iconColorClass} aria-hidden="true" />
        </foreignObject>
      </g>
      <text
        y={NODE_RADIUS + 16}
        textAnchor="middle"
        aria-hidden="true"
        className="fill-on-surface-variant font-mono text-[10px] uppercase"
      >
        {node.name}
      </text>
    </g>
  );
}
