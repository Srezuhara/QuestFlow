import { useState } from "react";
import { Modal, NeonButton, StatusBadge } from "@/components/ui";
import type { StatusLevel } from "@/components/ui";
import { useCreateTask } from "../hooks";
import type { TaskPriority } from "../api";

const PRIORITIES: TaskPriority[] = ["urgent", "important", "warning", "later"];

export function NewQuestModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [title, setTitle] = useState("");
  const [priority, setPriority] = useState<TaskPriority>("important");
  const [dueDate, setDueDate] = useState("");
  const createTask = useCreateTask();

  function handleClose() {
    setTitle("");
    setPriority("important");
    setDueDate("");
    createTask.reset();
    onClose();
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim()) return;
    createTask.mutate(
      {
        title: title.trim(),
        priority,
        // End-of-day on the chosen date, in the browser's local timezone —
        // a plain `date` input avoids the native `datetime-local` control's
        // confusing "invalid date" error when only the date half is filled.
        due_at: dueDate ? new Date(`${dueDate}T23:59:59`).toISOString() : null,
      },
      { onSuccess: handleClose },
    );
  }

  return (
    <Modal open={open} onClose={handleClose} title="New Quest">
      <form onSubmit={handleSubmit} className="flex flex-col gap-5">
        <div className="flex flex-col gap-2">
          <label
            htmlFor="quest-title"
            className="font-mono text-label-mono text-on-surface-variant uppercase"
          >
            Objective
          </label>
          <input
            id="quest-title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Deploy mainframe patch v2.4"
            autoFocus
            required
            className="clip-chamfer border border-outline-variant bg-surface-container-lowest px-3 py-2 font-body text-body-md text-on-surface outline-none focus:border-neon-lime"
          />
        </div>

        <div className="flex flex-col gap-2">
          <span className="font-mono text-label-mono text-on-surface-variant uppercase">
            Priority
          </span>
          <div className="flex flex-wrap gap-2">
            {PRIORITIES.map((level) => (
              <button
                key={level}
                type="button"
                onClick={() => setPriority(level)}
                className={
                  priority === level
                    ? "opacity-100"
                    : "opacity-40 hover:opacity-70 transition-opacity"
                }
              >
                <StatusBadge level={level as StatusLevel}>{level}</StatusBadge>
              </button>
            ))}
          </div>
        </div>

        <div className="flex flex-col gap-2">
          <label
            htmlFor="quest-due"
            className="font-mono text-label-mono text-on-surface-variant uppercase"
          >
            Due (optional)
          </label>
          <input
            id="quest-due"
            type="date"
            value={dueDate}
            onChange={(e) => setDueDate(e.target.value)}
            className="clip-chamfer border border-outline-variant bg-surface-container-lowest px-3 py-2 font-body text-body-md text-on-surface outline-none focus:border-neon-lime"
          />
        </div>

        {createTask.isError && (
          <p className="font-mono text-label-mono text-neon-pink">
            Failed to create the quest. Please try again.
          </p>
        )}

        <div className="mt-2 flex justify-end gap-3">
          <NeonButton type="button" variant="ghost" onClick={handleClose}>
            Cancel
          </NeonButton>
          <NeonButton type="submit" disabled={createTask.isPending}>
            {createTask.isPending ? "Deploying..." : "Deploy Quest"}
          </NeonButton>
        </div>
      </form>
    </Modal>
  );
}
