import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { applyGamificationResult, estimateProgressAfterDelta } from "@/features/progress/hooks";
import type { LevelProgressOut } from "@/features/progress/api";
import { queryKeys } from "@/lib/queryKeys";
import {
  archiveHabit,
  createHabit,
  fetchHabitMatrix,
  fetchHabits,
  logHabit,
  unlogHabit,
  updateHabit,
} from "./api";
import type { HabitCreate, HabitOut, HabitUpdate } from "./api";

export function useHabits() {
  return useQuery({ queryKey: queryKeys.habits.all, queryFn: () => fetchHabits() });
}

export function useHabitMatrix(habitId: string | undefined, days = 30) {
  return useQuery({
    queryKey: habitId ? queryKeys.habits.matrix(habitId) : ["habits", "matrix", "none"],
    queryFn: () => fetchHabitMatrix(habitId as string, days),
    enabled: Boolean(habitId),
  });
}

export function useCreateHabit() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: HabitCreate) => createHabit(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.habits.all });
    },
  });
}

export function useUpdateHabit() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ habitId, data }: { habitId: string; data: HabitUpdate }) =>
      updateHabit(habitId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.habits.all });
    },
  });
}

export function useArchiveHabit() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (habitId: string) => archiveHabit(habitId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.habits.all });
    },
  });
}

interface LogContext {
  previousHabits: HabitOut[] | undefined;
  previousProgress: LevelProgressOut | undefined;
}

/** Optimistic log — the row's progress bar and the sidebar XP bar move
 * immediately; both roll back together on error; the server's authoritative
 * response reconciles both in `onSuccess`, modelled on
 * `tasks/hooks.ts::useToggleTask`. */
export function useLogHabit() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (habit: HabitOut) => logHabit(habit.id),
    onMutate: async (habit: HabitOut): Promise<LogContext> => {
      await queryClient.cancelQueries({ queryKey: queryKeys.habits.all });
      await queryClient.cancelQueries({ queryKey: queryKeys.progress.me });

      const previousHabits = queryClient.getQueryData<HabitOut[]>(queryKeys.habits.all);
      const previousProgress = queryClient.getQueryData<LevelProgressOut>(queryKeys.progress.me);

      if (previousHabits) {
        queryClient.setQueryData<HabitOut[]>(
          queryKeys.habits.all,
          previousHabits.map((h) => {
            if (h.id !== habit.id) return h;
            const nextCount = h.current_period.count + 1;
            const nextIsHit = nextCount >= h.current_period.target;
            return {
              ...h,
              current_period: { ...h.current_period, count: nextCount, is_hit: nextIsHit },
              due_today: !nextIsHit && h.is_active,
            };
          }),
        );
      }
      if (previousProgress) {
        queryClient.setQueryData(
          queryKeys.progress.me,
          estimateProgressAfterDelta(previousProgress, habit.xp_value),
        );
      }

      return { previousHabits, previousProgress };
    },
    onError: (_err, _habit, context) => {
      if (context?.previousHabits) {
        queryClient.setQueryData(queryKeys.habits.all, context.previousHabits);
      }
      if (context?.previousProgress) {
        queryClient.setQueryData(queryKeys.progress.me, context.previousProgress);
      }
    },
    onSuccess: (result) => {
      applyGamificationResult(queryClient, result.progress, result.newly_earned_achievements);
    },
    onSettled: (_result, _err, habit) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.habits.all });
      queryClient.invalidateQueries({ queryKey: queryKeys.dashboard.root });
      queryClient.invalidateQueries({ queryKey: queryKeys.progress.xpEvents });
      queryClient.invalidateQueries({ queryKey: queryKeys.habits.matrix(habit.id) });
    },
  });
}

export function useUnlogHabit() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ habitId, loggedFor }: { habitId: string; loggedFor: string }) =>
      unlogHabit(habitId, loggedFor),
    onSuccess: (result) => {
      applyGamificationResult(queryClient, result.progress, result.newly_earned_achievements);
    },
    onSettled: (_result, _err, vars) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.habits.all });
      queryClient.invalidateQueries({ queryKey: queryKeys.dashboard.root });
      queryClient.invalidateQueries({ queryKey: queryKeys.progress.xpEvents });
      queryClient.invalidateQueries({ queryKey: queryKeys.habits.matrix(vars.habitId) });
    },
  });
}
