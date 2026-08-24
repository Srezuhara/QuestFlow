import { useState } from "react";
import { Modal, NeonButton } from "@/components/ui";
import { TaskLinkPicker } from "@/features/timer/components/TaskLinkPicker";
import { useCreateNote } from "../hooks";

function slugify(raw: string): string {
  return raw
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

export function NewNoteModal({
  open,
  onClose,
  onCreated,
}: {
  open: boolean;
  onClose: () => void;
  onCreated: (noteId: string) => void;
}) {
  const [title, setTitle] = useState("");
  const [tagsInput, setTagsInput] = useState("");
  const [taskId, setTaskId] = useState<string | null>(null);
  const createNote = useCreateNote();

  function handleClose() {
    setTitle("");
    setTagsInput("");
    setTaskId(null);
    createNote.reset();
    onClose();
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim()) return;
    const tagSlugs = tagsInput
      .split(",")
      .map((t) => slugify(t))
      .filter((t) => t.length > 0);

    createNote.mutate(
      {
        title: title.trim(),
        body_md: "",
        is_pinned: false,
        tag_slugs: tagSlugs,
        task_ids: taskId ? [taskId] : [],
      },
      {
        onSuccess: (note) => {
          handleClose();
          onCreated(note.id);
        },
      },
    );
  }

  return (
    <Modal open={open} onClose={handleClose} title="New Data Shard">
      <form onSubmit={handleSubmit} className="flex flex-col gap-5">
        <div className="flex flex-col gap-2">
          <label
            htmlFor="note-title"
            className="font-mono text-label-mono text-on-surface-variant uppercase"
          >
            Title
          </label>
          <input
            id="note-title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Mission Brief Alpha"
            autoFocus
            required
            className="clip-chamfer border border-outline-variant bg-surface-container-lowest px-3 py-2 font-body text-body-md text-on-surface outline-none focus:border-neon-lime"
          />
        </div>

        <div className="flex flex-col gap-2">
          <label
            htmlFor="note-tags"
            className="font-mono text-label-mono text-on-surface-variant uppercase"
          >
            Tags (comma-separated)
          </label>
          <input
            id="note-tags"
            value={tagsInput}
            onChange={(e) => setTagsInput(e.target.value)}
            placeholder="focus, protocol"
            className="clip-chamfer border border-outline-variant bg-surface-container-lowest px-3 py-2 font-body text-body-md text-on-surface outline-none focus:border-neon-lime"
          />
        </div>

        <TaskLinkPicker value={taskId} onChange={setTaskId} />

        {createNote.isError && (
          <p className="font-mono text-label-mono text-neon-pink">
            Failed to create the shard. Please try again.
          </p>
        )}

        <div className="mt-2 flex justify-end gap-3">
          <NeonButton type="button" variant="ghost" onClick={handleClose}>
            Cancel
          </NeonButton>
          <NeonButton type="submit" disabled={createNote.isPending}>
            {createNote.isPending ? "Uploading..." : "Create Shard"}
          </NeonButton>
        </div>
      </form>
    </Modal>
  );
}
