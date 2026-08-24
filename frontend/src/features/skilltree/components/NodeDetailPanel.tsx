import { NeonButton, NeonPanel, StatusBadge, XPBar } from "@/components/ui";
import { ApiError } from "@/lib/apiClient";
import { lucideByName } from "@/lib/lucideByName";
import type { useUnlockNode } from "../hooks";
import type { SkillNodeOut } from "../api";

function prereqLabel(code: string, allNodes: SkillNodeOut[]): { label: string; unlocked: boolean } {
  const node = allNodes.find((n) => n.code === code);
  return { label: node?.name ?? code, unlocked: node?.state === "unlocked" };
}

/**
 * Selected node's name/description/branch/tier, `xp_cost` vs. the user's
 * branch XP as a progress bar, prerequisite chips with their own states, and
 * an UNLOCK button — disabled with the server's own rejection reason when
 * not available (the plan's instruction: "the UI shows it verbatim").
 *
 * The unlock mutation is owned by `SkillTree` and passed down (§A.5) — this
 * component used to call `useUnlockNode()` on its own separate instance,
 * which meant `SkillTree`'s own copy of the mutation never fired and the
 * node's "unlocking" pending state was dead code.
 */
export function NodeDetailPanel({
  node,
  allNodes,
  branchXp,
  unlock,
  onUnlock,
  onClose,
}: {
  node: SkillNodeOut;
  allNodes: SkillNodeOut[];
  branchXp: Record<string, number>;
  unlock: ReturnType<typeof useUnlockNode>;
  onUnlock: (code: string) => void;
  onClose: () => void;
}) {
  const Icon = lucideByName(node.icon);
  const currentBranchXp = node.branch ? (branchXp[node.branch] ?? 0) : 0;
  const percent = node.xp_cost > 0 ? Math.min(100, (currentBranchXp / node.xp_cost) * 100) : 100;

  const errorReason =
    unlock.error instanceof ApiError && typeof unlock.error.body === "object"
      ? ((unlock.error.body as { detail?: string } | null)?.detail ?? null)
      : null;

  const disabledReason =
    node.state === "unlocked"
      ? "Already unlocked"
      : node.state === "locked"
        ? "Requirements not yet met"
        : null;

  return (
    <NeonPanel glow className="flex flex-col gap-4">
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-3">
          <Icon size={28} className="text-neon-lime" aria-hidden="true" />
          <div>
            <h3 className="font-display text-title-md text-on-surface uppercase">{node.name}</h3>
            {node.branch && (
              <StatusBadge level="important">{node.branch.toUpperCase()}</StatusBadge>
            )}
          </div>
        </div>
        <button
          type="button"
          onClick={onClose}
          aria-label="Close detail panel"
          className="font-mono text-label-mono text-on-surface-variant hover:text-neon-pink"
        >
          &times;
        </button>
      </div>

      <p className="font-body text-body-md text-on-surface-variant">{node.description}</p>

      <dl className="grid grid-cols-2 gap-3 font-mono text-label-mono uppercase">
        <div>
          <dt className="text-on-surface-variant">Tier</dt>
          <dd className="text-on-surface">{node.tier}</dd>
        </div>
        <div>
          <dt className="text-on-surface-variant">State</dt>
          <dd className="text-neon-lime">{node.state}</dd>
        </div>
      </dl>

      {node.xp_cost > 0 && (
        <div>
          <XPBar
            percent={percent}
            label={`${Math.min(currentBranchXp, node.xp_cost)}/${node.xp_cost} ${node.branch?.toUpperCase() ?? ""} XP`}
          />
        </div>
      )}

      {node.prerequisite_codes.length > 0 && (
        <div>
          <p className="mb-2 font-mono text-label-mono text-on-surface-variant uppercase">
            Prerequisites
          </p>
          <div className="flex flex-wrap gap-2">
            {node.prerequisite_codes.map((code) => {
              const { label, unlocked } = prereqLabel(code, allNodes);
              return (
                <StatusBadge key={code} level={unlocked ? "important" : "later"}>
                  {label}
                </StatusBadge>
              );
            })}
          </div>
        </div>
      )}

      {(errorReason ?? disabledReason) && (
        <p className="font-mono text-label-mono text-neon-pink uppercase">
          {errorReason ?? disabledReason}
        </p>
      )}

      <NeonButton
        onClick={() => onUnlock(node.code)}
        disabled={node.state !== "available" || unlock.isPending}
      >
        {unlock.isPending ? "Unlocking..." : "Unlock"}
      </NeonButton>
    </NeonPanel>
  );
}
