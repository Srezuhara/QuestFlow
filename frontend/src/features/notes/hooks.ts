import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "@/lib/queryKeys";
import {
  archiveNote,
  createNote,
  fetchNote,
  fetchNotes,
  linkTask,
  toggleCheckbox,
  unlinkTask,
  updateNote,
} from "./api";
import type { NoteCreate, NoteOut, NoteUpdate } from "./api";

export function useNotes({ q, tags }: { q: string; tags: string[] }) {
  return useQuery({
    queryKey: queryKeys.notes.list(q, tags),
    queryFn: () => fetchNotes({ q, tags }),
    staleTime: 10_000,
  });
}

export function useNote(noteId: string | undefined) {
  return useQuery({
    queryKey: noteId ? queryKeys.notes.detail(noteId) : ["notes", "none"],
    queryFn: () => fetchNote(noteId as string),
    enabled: Boolean(noteId),
  });
}

export function useCreateNote() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: NoteCreate) => createNote(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.notes.all });
    },
  });
}

export function useUpdateNote() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ noteId, data }: { noteId: string; data: NoteUpdate }) =>
      updateNote(noteId, data),
    onSuccess: (note) => {
      queryClient.setQueryData(queryKeys.notes.detail(note.id), note);
      queryClient.invalidateQueries({ queryKey: queryKeys.notes.all });
    },
  });
}

export function useArchiveNote() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (noteId: string) => archiveNote(noteId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.notes.all });
    },
  });
}

export function useLinkTask() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ noteId, taskId }: { noteId: string; taskId: string }) =>
      linkTask(noteId, taskId),
    onSuccess: (note) => {
      queryClient.setQueryData(queryKeys.notes.detail(note.id), note);
    },
  });
}

export function useUnlinkTask() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ noteId, taskId }: { noteId: string; taskId: string }) =>
      unlinkTask(noteId, taskId),
    onSuccess: (note) => {
      queryClient.setQueryData(queryKeys.notes.detail(note.id), note);
    },
  });
}

interface CheckboxContext {
  previousNote: NoteOut | undefined;
}

/** Optimistic checkbox toggle — flips the line in the cached body
 * immediately, modelled on `features/tasks/hooks.ts::useToggleTask`; rolls
 * back on error; reconciles from the server's response on success. */
export function useToggleCheckbox() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      noteId,
      lineIndex,
      checked,
    }: {
      noteId: string;
      lineIndex: number;
      checked: boolean;
    }) => toggleCheckbox(noteId, lineIndex, checked),
    onMutate: async ({ noteId, lineIndex, checked }): Promise<CheckboxContext> => {
      await queryClient.cancelQueries({ queryKey: queryKeys.notes.detail(noteId) });
      const previousNote = queryClient.getQueryData<NoteOut>(queryKeys.notes.detail(noteId));
      if (previousNote) {
        const lines = previousNote.body_md.split("\n");
        const line = lines[lineIndex];
        if (line !== undefined) {
          lines[lineIndex] = line.replace(/\[[ xX]\]/, checked ? "[x]" : "[ ]");
          queryClient.setQueryData<NoteOut>(queryKeys.notes.detail(noteId), {
            ...previousNote,
            body_md: lines.join("\n"),
          });
        }
      }
      return { previousNote };
    },
    onError: (_err, { noteId }, context) => {
      if (context?.previousNote) {
        queryClient.setQueryData(queryKeys.notes.detail(noteId), context.previousNote);
      }
    },
    onSuccess: (note) => {
      queryClient.setQueryData(queryKeys.notes.detail(note.id), note);
    },
    onSettled: (_note, _err, { noteId }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.notes.all });
      queryClient.invalidateQueries({ queryKey: queryKeys.notes.detail(noteId) });
    },
  });
}
