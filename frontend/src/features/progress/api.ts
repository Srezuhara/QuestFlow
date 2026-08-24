import { apiJson } from "@/lib/apiClient";
import type { components } from "@/types/api";

export type LevelProgressOut = components["schemas"]["LevelProgressOut"];
export type UserProgressOut = components["schemas"]["UserProgressOut"];
export type XPEventOut = components["schemas"]["XPEventOut"];
export type XPEventPageOut = components["schemas"]["XPEventPageOut"];
export type XPSummaryOut = components["schemas"]["XPSummaryOut"];

export function fetchProgress(): Promise<UserProgressOut> {
  return apiJson<UserProgressOut>("/me/progress");
}

export function fetchXpEvents(limit = 50): Promise<XPEventOut[]> {
  return apiJson<XPEventOut[]>(`/me/xp-events?limit=${limit}`);
}

export function fetchXpHistory(before: string | null, limit = 25): Promise<XPEventPageOut> {
  const qs = new URLSearchParams({ limit: String(limit) });
  if (before) qs.set("before", before);
  return apiJson<XPEventPageOut>(`/me/xp-events?${qs.toString()}`);
}

export function fetchXpSummary(days = 30): Promise<XPSummaryOut> {
  return apiJson<XPSummaryOut>(`/me/xp-summary?days=${days}`);
}
