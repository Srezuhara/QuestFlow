import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { applyGamificationResult } from "@/features/progress/hooks";
import { queryKeys } from "@/lib/queryKeys";
import {
  abandonSession,
  completeSession,
  fetchActiveSession,
  fetchCalendar,
  fetchPreferences,
  fetchSessions,
  startSession,
  updatePreferences,
} from "./api";
import type { FocusMode, PreferencesUpdate } from "./api";

export function useActiveSession() {
  return useQuery({ queryKey: queryKeys.focus.active, queryFn: fetchActiveSession });
}

export function useMissionLog(onDate?: string) {
  return useQuery({
    queryKey: [...queryKeys.focus.sessions, onDate ?? "recent"],
    queryFn: () => fetchSessions(onDate),
  });
}

export function useFocusCalendar(year: number, month: number) {
  return useQuery({
    queryKey: queryKeys.focus.calendar(year, month),
    queryFn: () => fetchCalendar(year, month),
  });
}

export function usePreferences() {
  return useQuery({ queryKey: queryKeys.preferences, queryFn: fetchPreferences });
}

export function useUpdatePreferences() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: PreferencesUpdate) => updatePreferences(data),
    onSuccess: (prefs) => {
      queryClient.setQueryData(queryKeys.preferences, prefs);
    },
  });
}

export function useStartSession() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { mode: FocusMode; planned_seconds: number; task_id?: string | null }) =>
      startSession(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.focus.active });
    },
  });
}

export function useCompleteSession() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (sessionId: string) => completeSession(sessionId),
    onSuccess: (result) => {
      applyGamificationResult(queryClient, result.progress, result.newly_earned_achievements);
      queryClient.invalidateQueries({ queryKey: queryKeys.focus.sessions });
      queryClient.invalidateQueries({ queryKey: queryKeys.focus.active });
      queryClient.invalidateQueries({ queryKey: queryKeys.dashboard.root });
      queryClient.invalidateQueries({ queryKey: queryKeys.progress.xpEvents });
    },
  });
}

export function useAbandonSession() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (sessionId: string) => abandonSession(sessionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.focus.sessions });
      queryClient.invalidateQueries({ queryKey: queryKeys.focus.active });
    },
  });
}
