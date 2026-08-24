import { apiJson } from "@/lib/apiClient";
import type { components } from "@/types/api";

export type NoteOut = components["schemas"]["NoteOut"];
export type NoteSummaryOut = components["schemas"]["NoteSummaryOut"];
export type NoteCreate = components["schemas"]["NoteCreate"];
export type NoteUpdate = components["schemas"]["NoteUpdate"];

export function fetchNotes(params: { q?: string; tags?: string[]; includeArchived?: boolean }) {
  const qs = new URLSearchParams();
  if (params.q) qs.set("q", params.q);
  for (const tag of params.tags ?? []) qs.append("tag", tag);
  if (params.includeArchived) qs.set("include_archived", "true");
  const suffix = qs.toString() ? `?${qs.toString()}` : "";
  return apiJson<NoteSummaryOut[]>(`/notes${suffix}`);
}

export function fetchNote(noteId: string): Promise<NoteOut> {
  return apiJson<NoteOut>(`/notes/${noteId}`);
}

export function createNote(data: NoteCreate): Promise<NoteOut> {
  return apiJson<NoteOut>("/notes", { method: "POST", body: JSON.stringify(data) });
}

export function updateNote(noteId: string, data: NoteUpdate): Promise<NoteOut> {
  return apiJson<NoteOut>(`/notes/${noteId}`, { method: "PATCH", body: JSON.stringify(data) });
}

export function archiveNote(noteId: string): Promise<void> {
  return apiJson<void>(`/notes/${noteId}`, { method: "DELETE" });
}

export function toggleCheckbox(
  noteId: string,
  lineIndex: number,
  checked: boolean,
): Promise<NoteOut> {
  return apiJson<NoteOut>(`/notes/${noteId}/checkbox`, {
    method: "PATCH",
    body: JSON.stringify({ line_index: lineIndex, checked }),
  });
}

export function linkTask(noteId: string, taskId: string): Promise<NoteOut> {
  return apiJson<NoteOut>(`/notes/${noteId}/tasks/${taskId}`, { method: "POST" });
}

export function unlinkTask(noteId: string, taskId: string): Promise<NoteOut> {
  return apiJson<NoteOut>(`/notes/${noteId}/tasks/${taskId}`, { method: "DELETE" });
}
