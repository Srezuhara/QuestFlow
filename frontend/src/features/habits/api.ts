import { apiJson } from "@/lib/apiClient";
import type { components } from "@/types/api";

export type HabitOut = components["schemas"]["HabitOut"];
export type HabitCreate = components["schemas"]["HabitCreate"];
export type HabitUpdate = components["schemas"]["HabitUpdate"];
export type HabitCadence = components["schemas"]["HabitCadence"];
export type HabitLogResponse = components["schemas"]["HabitLogResponse"];
export type HabitMatrixOut = components["schemas"]["HabitMatrixOut"];
export type HabitMatrixCellOut = components["schemas"]["HabitMatrixCellOut"];
export type MatrixCellStatus = components["schemas"]["MatrixCellStatus"];

export function fetchHabits(includeArchived = false): Promise<HabitOut[]> {
  const qs = includeArchived ? "?include_archived=true" : "";
  return apiJson<HabitOut[]>(`/habits${qs}`);
}

export function createHabit(data: HabitCreate): Promise<HabitOut> {
  return apiJson<HabitOut>("/habits", { method: "POST", body: JSON.stringify(data) });
}

export function updateHabit(habitId: string, data: HabitUpdate): Promise<HabitOut> {
  return apiJson<HabitOut>(`/habits/${habitId}`, { method: "PATCH", body: JSON.stringify(data) });
}

export function archiveHabit(habitId: string): Promise<void> {
  return apiJson<void>(`/habits/${habitId}`, { method: "DELETE" });
}

export function logHabit(
  habitId: string,
  data: { logged_for?: string | null; count?: number } = {},
): Promise<HabitLogResponse> {
  return apiJson<HabitLogResponse>(`/habits/${habitId}/log`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function unlogHabit(habitId: string, loggedFor: string): Promise<HabitLogResponse> {
  return apiJson<HabitLogResponse>(`/habits/${habitId}/log/${loggedFor}`, { method: "DELETE" });
}

export function fetchHabitMatrix(habitId: string, days = 30): Promise<HabitMatrixOut> {
  return apiJson<HabitMatrixOut>(`/habits/${habitId}/matrix?days=${days}`);
}
