import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { QueryKey } from "@tanstack/react-query";
import { estimateProgressAfterDelta } from "@/features/progress/hooks";
import type { LevelProgressOut } from "@/features/progress/api";
import { queryKeys } from "@/lib/queryKeys";
import {
  completeTask,
  createTask,
  deleteTask,
  fetchTasks,
  uncompleteTask,
  updateTask,
} from "./api";
import type { TaskCreate, TaskOut, TaskStatus, TaskUpdate } from "./api";

export function useTasks(status?: TaskStatus) {
  return useQuery({
    queryKey: [...queryKeys.tasks.all, status ?? "all"],
    queryFn: () => fetchTasks(status ? { status } : undefined),
  });
}

export function useCreateTask() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: TaskCreate) => createTask(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.tasks.all });
      queryClient.invalidateQueries({ queryKey: queryKeys.dashboard.root });
    },
  });
}

export function useUpdateTask() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ taskId, data }: { taskId: string; data: TaskUpdate }) =>
      updateTask(taskId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.tasks.all });
      queryClient.invalidateQueries({ queryKey: queryKeys.dashboard.root });
    },
  });
}

export function useDeleteTask() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (taskId: string) => deleteTask(taskId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.tasks.all });
      queryClient.invalidateQueries({ queryKey: queryKeys.dashboard.root });
    },
  });
}

interface ToggleContext {
  previousTaskLists: [QueryKey, TaskOut[] | undefined][];
  previousProgress: LevelProgressOut | undefined;
}

/** Shared optimistic-toggle logic for complete/uncomplete: the checkbox
 * fills and the XP bar moves immediately, and both roll back together if
 * the request fails. `sign` is +1 for complete, -1 for uncomplete. */
function useToggleTask(
  mutationFn: (task: TaskOut) => ReturnType<typeof completeTask>,
  sign: 1 | -1,
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn,
    onMutate: async (task: TaskOut): Promise<ToggleContext> => {
      await queryClient.cancelQueries({ queryKey: queryKeys.tasks.all });
      await queryClient.cancelQueries({ queryKey: queryKeys.progress.me });

      const previousTaskLists = queryClient.getQueriesData<TaskOut[]>({
        queryKey: queryKeys.tasks.all,
      });
      const previousProgress = queryClient.getQueryData<LevelProgressOut>(queryKeys.progress.me);

      const nextStatus = sign === 1 ? "done" : "todo";
      const nextCompletedAt = sign === 1 ? new Date().toISOString() : null;
      for (const [key, tasks] of previousTaskLists) {
        if (!tasks) continue;
        queryClient.setQueryData<TaskOut[]>(
          key,
          tasks.map((t) =>
            t.id === task.id ? { ...t, status: nextStatus, completed_at: nextCompletedAt } : t,
          ),
        );
      }
      if (previousProgress) {
        queryClient.setQueryData(
          queryKeys.progress.me,
          estimateProgressAfterDelta(previousProgress, sign * task.xp_value),
        );
      }

      return { previousTaskLists, previousProgress };
    },
    onError: (_err, _task, context) => {
      context?.previousTaskLists.forEach(([key, tasks]) => queryClient.setQueryData(key, tasks));
      if (context?.previousProgress) {
        queryClient.setQueryData(queryKeys.progress.me, context.previousProgress);
      }
    },
    onSuccess: (result) => {
      queryClient.setQueryData(queryKeys.progress.me, result.progress);
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.tasks.all });
      queryClient.invalidateQueries({ queryKey: queryKeys.dashboard.root });
      queryClient.invalidateQueries({ queryKey: queryKeys.progress.xpEvents });
    },
  });
}

export function useCompleteTask() {
  return useToggleTask((task) => completeTask(task.id), 1);
}

export function useUncompleteTask() {
  return useToggleTask((task) => uncompleteTask(task.id), -1);
}
