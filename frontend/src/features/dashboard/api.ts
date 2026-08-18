import { apiJson } from "@/lib/apiClient";
import type { components } from "@/types/api";

export type DashboardOut = components["schemas"]["DashboardOut"];

export function fetchDashboard(): Promise<DashboardOut> {
  return apiJson<DashboardOut>("/dashboard");
}
