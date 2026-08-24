import { useInfiniteQuery, useQuery } from "@tanstack/react-query";
import type { QueryClient } from "@tanstack/react-query";
import { detectLevelUp, useLevelUpToastStore } from "@/components/ui/levelUpToastStore";
import type { AchievementOut } from "@/features/achievements/api";
import { queryKeys } from "@/lib/queryKeys";
import { fetchProgress, fetchXpEvents, fetchXpHistory, fetchXpSummary } from "./api";
import type { LevelProgressOut } from "./api";

export function useProgress() {
  return useQuery({ queryKey: queryKeys.progress.me, queryFn: fetchProgress });
}

export function useRecentActivity(limit = 10) {
  return useQuery({
    queryKey: [...queryKeys.progress.xpEvents, limit],
    queryFn: () => fetchXpEvents(limit),
  });
}

/** Ledger history, paginated via the server's `before` cursor. "LOAD MORE" is
 * a button per the plan (§6.11), not scroll-triggered — callers call
 * `fetchNextPage()` from a click handler, never an intersection observer. */
export function useXPHistory() {
  return useInfiniteQuery({
    queryKey: queryKeys.xp.history,
    queryFn: ({ pageParam }: { pageParam: string | null }) => fetchXpHistory(pageParam),
    initialPageParam: null as string | null,
    getNextPageParam: (lastPage) => lastPage.next_before ?? undefined,
  });
}

export function useXPSummary(days = 30) {
  return useQuery({
    queryKey: queryKeys.xp.summary(days),
    queryFn: () => fetchXpSummary(days),
  });
}

/**
 * A same-shape, client-side *estimate* of the post-award progress bar, used
 * only to fill the bar between clicking "complete" and the server's
 * authoritative response landing (which always overwrites this via
 * `setQueryData` in the mutation's `onSuccess`). The real level curve is
 * defined once, server-side (`services/gamification/leveling.py`) — this
 * never recomputes it, it just linearly extrapolates within the current
 * level's already-known span so the bar animates instead of jumping.
 */
export function estimateProgressAfterDelta<T extends LevelProgressOut>(
  progress: T,
  delta: number,
): T {
  const xpIntoLevel = Math.max(0, progress.xp_into_level + delta);
  const percent =
    progress.xp_for_next_level <= 0
      ? progress.percent
      : Math.min(100, Math.max(0, (xpIntoLevel / progress.xp_for_next_level) * 100));
  return {
    ...progress,
    total_xp: progress.total_xp + delta,
    xp_into_level: xpIntoLevel,
    percent,
  };
}

/**
 * The one place every gamification-producing mutation (task complete, habit
 * log, focus complete, skill unlock) reconciles the sidebar XP bar from the
 * server's authoritative response *and* enqueues level-up / achievement
 * toasts. Centralised here rather than duplicated in each feature's
 * `onSuccess` so the "did we actually cross a level boundary" check
 * (`detectLevelUp`) can't drift between call sites.
 */
export function applyGamificationResult(
  queryClient: QueryClient,
  progress: LevelProgressOut,
  newlyEarnedAchievements: AchievementOut[] = [],
): void {
  const previous = queryClient.getQueryData<LevelProgressOut>(queryKeys.progress.me);
  queryClient.setQueryData(queryKeys.progress.me, progress);

  if (detectLevelUp(previous?.level, progress.level)) {
    useLevelUpToastStore.getState().pushLevelUp(progress.level);
  }
  for (const achievement of newlyEarnedAchievements) {
    useLevelUpToastStore.getState().pushAchievement(achievement);
  }
}
