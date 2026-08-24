import { apiJson } from "@/lib/apiClient";
import type { components } from "@/types/api";

export type LeaderboardPageOut = components["schemas"]["LeaderboardPageOut"];
export type LeaderboardEntryOut = components["schemas"]["LeaderboardEntryOut"];
export type FeedPageOut = components["schemas"]["FeedPageOut"];
export type FeedItemOut = components["schemas"]["FeedItemOut"];

export function fetchLeaderboard(limit = 25, offset = 0): Promise<LeaderboardPageOut> {
  const qs = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  return apiJson<LeaderboardPageOut>(`/social/leaderboard?${qs.toString()}`);
}

export function fetchFeed(before: string | null, limit = 25): Promise<FeedPageOut> {
  const qs = new URLSearchParams({ limit: String(limit) });
  if (before) qs.set("before", before);
  return apiJson<FeedPageOut>(`/social/feed?${qs.toString()}`);
}
