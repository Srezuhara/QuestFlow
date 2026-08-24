import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { applyGamificationResult } from "@/features/progress/hooks";
import { queryKeys } from "@/lib/queryKeys";
import { fetchSkillTree, unlockSkillNode } from "./api";

export function useSkillTree() {
  return useQuery({ queryKey: queryKeys.skillTree.me, queryFn: fetchSkillTree });
}

/**
 * NOT optimistic (per the plan §6.10) — unlocking a node is a deliberate,
 * server-validated, irreversible act; the caller shows a pending state on
 * the node (`isPending` from this mutation) rather than flipping it locked
 * to unlocked before the server has actually validated eligibility.
 */
export function useUnlockNode() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (code: string) => unlockSkillNode(code),
    onSuccess: (result) => {
      applyGamificationResult(queryClient, result.progress, result.newly_earned_achievements);
      queryClient.invalidateQueries({ queryKey: queryKeys.skillTree.me });
      queryClient.invalidateQueries({ queryKey: queryKeys.achievements.all });
      queryClient.invalidateQueries({ queryKey: queryKeys.dashboard.root });
      queryClient.invalidateQueries({ queryKey: queryKeys.progress.xpEvents });
    },
  });
}
