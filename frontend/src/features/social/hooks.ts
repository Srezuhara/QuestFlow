import { keepPreviousData, useInfiniteQuery, useQuery } from "@tanstack/react-query";
import { queryKeys } from "@/lib/queryKeys";
import { fetchFeed, fetchLeaderboard, type FeedPageOut } from "./api";

export function useLeaderboard(limit = 25, offset = 0) {
  return useQuery({
    queryKey: queryKeys.social.leaderboard(limit, offset),
    queryFn: () => fetchLeaderboard(limit, offset),
    // Page flips keep the previous table on screen instead of blanking it.
    placeholderData: keepPreviousData,
  });
}

/** Social data is ambient, not urgent — a 2 minute poll, unlike
 * notifications' 60s. */
export function useFeed() {
  return useInfiniteQuery({
    queryKey: queryKeys.social.feed,
    queryFn: ({ pageParam }: { pageParam: string | null }) => fetchFeed(pageParam),
    initialPageParam: null as string | null,
    getNextPageParam: (lastPage: FeedPageOut) => lastPage.next_before ?? undefined,
    refetchInterval: 120_000,
  });
}
