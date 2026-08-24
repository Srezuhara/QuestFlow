import { apiJson } from "@/lib/apiClient";
import type { components } from "@/types/api";

export type AchievementOut = components["schemas"]["AchievementOut"];
export type AchievementTier = components["schemas"]["AchievementTier"];

export function fetchAchievements(): Promise<AchievementOut[]> {
  return apiJson<AchievementOut[]>("/me/achievements");
}
