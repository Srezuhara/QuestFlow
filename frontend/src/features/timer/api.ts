import { apiJson } from "@/lib/apiClient";
import type { components } from "@/types/api";

export type FocusMode = components["schemas"]["FocusMode"];
export type FocusSessionOut = components["schemas"]["FocusSessionOut"];
export type FocusCompleteResponse = components["schemas"]["FocusCompleteResponse"];
export type FocusMonthOut = components["schemas"]["FocusMonthOut"];
export type FocusDaySummaryOut = components["schemas"]["FocusDaySummaryOut"];
export type PreferencesOut = components["schemas"]["PreferencesOut"];
export type PreferencesUpdate = components["schemas"]["PreferencesUpdate"];

export function fetchActiveSession(): Promise<FocusSessionOut | null> {
  return apiJson<FocusSessionOut | null>("/focus/sessions/active");
}

export function startSession(data: {
  mode: FocusMode;
  planned_seconds: number;
  task_id?: string | null;
}): Promise<FocusSessionOut> {
  return apiJson<FocusSessionOut>("/focus/sessions", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function completeSession(sessionId: string): Promise<FocusCompleteResponse> {
  return apiJson<FocusCompleteResponse>(`/focus/sessions/${sessionId}`, {
    method: "PATCH",
    body: JSON.stringify({ action: "complete" }),
  });
}

export function abandonSession(sessionId: string): Promise<FocusCompleteResponse> {
  return apiJson<FocusCompleteResponse>(`/focus/sessions/${sessionId}`, {
    method: "PATCH",
    body: JSON.stringify({ action: "abandon" }),
  });
}

export function fetchSessions(onDate?: string): Promise<FocusSessionOut[]> {
  const qs = onDate ? `?on_date=${onDate}` : "";
  return apiJson<FocusSessionOut[]>(`/focus/sessions${qs}`);
}

export function fetchCalendar(year: number, month: number): Promise<FocusMonthOut> {
  return apiJson<FocusMonthOut>(`/focus/calendar?year=${year}&month=${month}`);
}

export function fetchPreferences(): Promise<PreferencesOut> {
  return apiJson<PreferencesOut>("/me/preferences");
}

export function updatePreferences(data: PreferencesUpdate): Promise<PreferencesOut> {
  return apiJson<PreferencesOut>("/me/preferences", {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}
