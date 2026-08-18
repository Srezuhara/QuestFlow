import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "@/lib/queryKeys";
import { fetchDashboard } from "./api";

export function useDashboard() {
  return useQuery({ queryKey: queryKeys.dashboard.root, queryFn: fetchDashboard });
}
