import { apiJson } from "@/lib/apiClient";
import type { components } from "@/types/api";

export type TaskOut = components["schemas"]["TaskOut"];
export type TaskCreate = components["schemas"]["TaskCreate"];
export type TaskUpdate = components["schemas"]["TaskUpdate"];
export type TaskStatus = components["schemas"]["TaskStatus"];
export type TaskPriority = components["schemas"]["TaskPriority"];
export type TaskCompleteResponse = components["schemas"]["TaskCompleteResponse"];

export function fetchTasks(params?: {
  status?: TaskStatus;
  projectId?: string;
}): Promise<TaskOut[]> {
  const search = new URLSearchParams();
  if (params?.status) search.set("status_filter", params.status);
  if (params?.projectId) search.set("project_id", params.projectId);
  const qs = search.toString();
  return apiJson<TaskOut[]>(`/tasks${qs ? `?${qs}` : ""}`);
}

export function createTask(data: TaskCreate): Promise<TaskOut> {
  return apiJson<TaskOut>("/tasks", { method: "POST", body: JSON.stringify(data) });
}

export function updateTask(taskId: string, data: TaskUpdate): Promise<TaskOut> {
  return apiJson<TaskOut>(`/tasks/${taskId}`, { method: "PATCH", body: JSON.stringify(data) });
}

export function deleteTask(taskId: string): Promise<void> {
  return apiJson<void>(`/tasks/${taskId}`, { method: "DELETE" });
}

export function completeTask(taskId: string): Promise<TaskCompleteResponse> {
  return apiJson<TaskCompleteResponse>(`/tasks/${taskId}/complete`, { method: "PATCH" });
}

export function uncompleteTask(taskId: string): Promise<TaskCompleteResponse> {
  return apiJson<TaskCompleteResponse>(`/tasks/${taskId}/uncomplete`, { method: "PATCH" });
}
