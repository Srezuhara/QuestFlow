import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "@/lib/queryKeys";
import { fetchProgress, fetchXpEvents } from "./api";
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
