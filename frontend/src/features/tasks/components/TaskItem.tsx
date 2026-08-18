import { useState } from "react";
import { Check, Clock, Star } from "lucide-react";
import { Modal, NeonButton, StatusBadge } from "@/components/ui";
import type { StatusLevel } from "@/components/ui";
import { cn } from "@/lib/cn";
import { useCompleteTask, useUncompleteTask } from "../hooks";
import type { TaskOut } from "../api";

const PRIORITY_BORDER: Record<TaskOut["priority"], string> = {
  urgent: "border-l-neon-pink",
  important: "border-l-neon-lime",
  warning: "border-l-neon-yellow",
  later: "border-l-outline",
};

export function TaskItem({ task }: { task: TaskOut }) {
  const complete = useCompleteTask();
  const uncomplete = useUncompleteTask();
  const [confirmOpen, setConfirmOpen] = useState(false);
  const isDone = task.status === "done";
  const pending = complete.isPending || uncomplete.isPending;

  function toggle() {
    if (isDone) {
      uncomplete.mutate(task);
    } else {
      // Completing (not un-completing) awards XP, so it gets a confirm
      // step — a mistap shouldn't silently bank +500 XP for the wrong quest.
      setConfirmOpen(true);
    }
  }

  function confirmComplete() {
    setConfirmOpen(false);
    complete.mutate(task);
  }

  return (
    <div
      className={cn(
        "group relative flex items-start gap-4 border border-l-4 border-outline-variant bg-surface-container-lowest p-4 transition-colors hover:bg-surface-container",
        PRIORITY_BORDER[task.priority],
        isDone && "opacity-50",
      )}
    >
      <button
        type="button"
        onClick={toggle}
        disabled={pending}
        aria-label={isDone ? "Mark incomplete" : "Mark complete"}
        className={cn(
          "mt-1 flex size-6 shrink-0 items-center justify-center border-2 transition-colors disabled:cursor-not-allowed",
          isDone
            ? "border-neon-lime bg-neon-lime/20"
            : "border-outline-variant hover:border-neon-lime",
        )}
      >
        {isDone && <Check size={16} className="text-neon-lime" aria-hidden="true" />}
      </button>

      <div className="min-w-0 flex-1">
        <div className="mb-1 flex items-start justify-between gap-3">
          <h4
            className={cn(
              "font-body text-body-lg font-bold uppercase text-on-surface",
              isDone && "line-through",
            )}
          >
            {task.title}
          </h4>
          <StatusBadge level={task.priority as StatusLevel}>{task.priority}</StatusBadge>
        </div>
        {task.description && (
          <p className="mb-2 font-mono text-label-mono text-on-surface-variant">
            {task.description}
          </p>
        )}
        <div className="flex items-center gap-4 font-mono text-label-mono text-on-surface-variant">
          <span className="flex items-center gap-1 text-neon-lime">
            <Star size={14} aria-hidden="true" /> +{task.xp_value} XP
          </span>
          {task.due_at && (
            <span className="flex items-center gap-1">
              <Clock size={14} aria-hidden="true" />
              {new Date(task.due_at).toLocaleString(undefined, {
                month: "short",
                day: "numeric",
                hour: "numeric",
                minute: "2-digit",
              })}
            </span>
          )}
        </div>
      </div>

      <Modal open={confirmOpen} onClose={() => setConfirmOpen(false)} title="Confirm Completion">
        <p className="mb-6 font-body text-body-md text-on-surface">
          Mark <span className="font-bold text-neon-lime">&ldquo;{task.title}&rdquo;</span> as
          complete? You&apos;ll earn{" "}
          <span className="font-bold text-neon-lime">+{task.xp_value} XP</span>.
        </p>
        <div className="flex justify-end gap-3">
          <NeonButton type="button" variant="ghost" onClick={() => setConfirmOpen(false)}>
            Cancel
          </NeonButton>
          <NeonButton type="button" onClick={confirmComplete}>
            Confirm
          </NeonButton>
        </div>
      </Modal>
    </div>
  );
}
