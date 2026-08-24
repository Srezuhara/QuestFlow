import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "@/lib/queryKeys";
import { fetchAchievements } from "./api";

export function useAchievements() {
  return useQuery({ queryKey: queryKeys.achievements.all, queryFn: fetchAchievements });
}
