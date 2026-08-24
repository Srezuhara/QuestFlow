import { useEffect, useState } from "react";
import { Save } from "lucide-react";
import { NeonButton } from "@/components/ui";
import { useToggleCheckbox, useUpdateNote } from "../hooks";
import { MarkdownBody } from "./MarkdownBody";
import type { NoteOut } from "../api";

function formatModTime(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  return `${(bytes / 1024).toFixed(1)} KB`;
}

/**
 * The right pane — two modes (D12): VIEW renders `body_md` through
 * `MarkdownBody`; EDIT swaps to a raw-markdown textarea with an explicit
 * SAVE. No side-by-side preview, no autosave.
 */
export function NoteEditor({
  note,
  onDirtyChange,
}: {
  note: NoteOut;
  onDirtyChange: (dirty: boolean) => void;
}) {
  const [mode, setMode] = useState<"view" | "edit">("view");
  const [title, setTitle] = useState(note.title);
  const [body, setBody] = useState(note.body_md);
  const updateNote = useUpdateNote();
  const toggleCheckbox = useToggleCheckbox();

  const dirty = mode === "edit" && (title !== note.title || body !== note.body_md);

  useEffect(() => {
    onDirtyChange(dirty);
  }, [dirty, onDirtyChange]);

  function enterEdit() {
    setTitle(note.title);
    setBody(note.body_md);
    setMode("edit");
  }

  function handleSave() {
    updateNote.mutate(
      { noteId: note.id, data: { title, body_md: body } },
      { onSuccess: () => setMode("view") },
    );
  }

  function handleCancel() {
    setTitle(note.title);
    setBody(note.body_md);
    setMode("view");
  }

  return (
    <div className="flex h-full flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-surface-container-highest pb-4">
        <div>
          {mode === "edit" ? (
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              aria-label="Note title"
              className="clip-chamfer border border-outline-variant bg-surface-container-lowest px-2 py-1 font-display text-title-md text-on-surface uppercase outline-none focus:border-neon-lime"
            />
          ) : (
            <h2 className="font-display text-title-md text-on-surface uppercase">{note.title}</h2>
          )}
          <p className="mt-1 font-mono text-label-mono text-on-surface-variant uppercase">
            MOD: {formatModTime(note.updated_at)} &nbsp; SIZE: {formatSize(note.size_bytes)}
          </p>
        </div>

        {mode === "edit" ? (
          <div className="flex gap-2">
            <NeonButton type="button" variant="ghost" onClick={handleCancel}>
              Cancel
            </NeonButton>
            <NeonButton
              type="button"
              onClick={handleSave}
              disabled={updateNote.isPending || title.trim().length === 0}
            >
              <Save size={16} aria-hidden="true" />
              Save
            </NeonButton>
          </div>
        ) : (
          <NeonButton type="button" onClick={enterEdit}>
            Edit
          </NeonButton>
        )}
      </div>

      {mode === "edit" ? (
        <textarea
          value={body}
          onChange={(e) => setBody(e.target.value)}
          aria-label="Note body (markdown)"
          className="clip-chamfer min-h-[50vh] flex-1 resize-y border border-outline-variant bg-surface-container-lowest p-3 font-mono text-body-md text-on-surface outline-none focus:border-neon-lime"
        />
      ) : (
        <MarkdownBody
          body={note.body_md}
          onToggleCheckbox={(lineIndex, checked) =>
            toggleCheckbox.mutate({ noteId: note.id, lineIndex, checked })
          }
        />
      )}
    </div>
  );
}
