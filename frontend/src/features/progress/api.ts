import { apiJson } from "@/lib/apiClient";
import type { components } from "@/types/api";

export type LevelProgressOut = components["schemas"]["LevelProgressOut"];
export type UserProgressOut = components["schemas"]["UserProgressOut"];
export type XPEventOut = components["schemas"]["XPEventOut"];

export function fetchProgress(): Promise<UserProgressOut> {
  return apiJson<UserProgressOut>("/me/progress");
}

export function fetchXpEvents(limit = 50): Promise<XPEventOut[]> {
  return apiJson<XPEventOut[]>(`/me/xp-events?limit=${limit}`);
}
