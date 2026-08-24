import { useState } from "react";
import { Modal, NeonButton } from "@/components/ui";
import { useCreateReminder } from "../hooks";

/** Converts a `datetime-local` input value (no timezone) into an ISO string
 * *with offset*, using the browser's local timezone — the API requires an
 * aware datetime (D7-7). */
function toIsoWithOffset(datetimeLocal: string): string {
  return new Date(datetimeLocal).toISOString();
}

export function NewReminderModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [message, setMessage] = useState("");
  const [remindAt, setRemindAt] = useState("");
  const createReminder = useCreateReminder();

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!message.trim() || !remindAt) return;
    createReminder.mutate(
      { message: message.trim(), remind_at: toIsoWithOffset(remindAt) },
      {
        onSuccess: () => {
          setMessage("");
          setRemindAt("");
          onClose();
        },
      },
    );
  }

  return (
    <Modal open={open} onClose={onClose} title="New Reminder">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div className="flex flex-col gap-2">
          <label
            htmlFor="reminder-message"
            className="font-mono text-label-mono text-on-surface-variant uppercase"
          >
            Message
          </label>
          <input
            id="reminder-message"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            maxLength={200}
            required
            className="clip-chamfer border border-outline-variant bg-surface-container-lowest px-3 py-2 font-body text-body-md text-on-surface outline-none focus:border-neon-lime"
          />
        </div>

        <div className="flex flex-col gap-2">
          <label
            htmlFor="reminder-remind-at"
            className="font-mono text-label-mono text-on-surface-variant uppercase"
          >
            Remind At
          </label>
          <input
            id="reminder-remind-at"
            type="datetime-local"
            value={remindAt}
            onChange={(e) => setRemindAt(e.target.value)}
            required
            className="clip-chamfer border border-outline-variant bg-surface-container-lowest px-3 py-2 font-body text-body-md text-on-surface outline-none focus:border-neon-lime"
          />
        </div>

        {createReminder.isError && (
          <p className="font-mono text-label-mono text-neon-pink">
            Failed to create reminder. Please try again.
          </p>
        )}

        <div className="mt-2 flex justify-end gap-3">
          <NeonButton type="button" variant="ghost" onClick={onClose}>
            Cancel
          </NeonButton>
          <NeonButton type="submit" disabled={createReminder.isPending}>
            {createReminder.isPending ? "Scheduling..." : "Schedule"}
          </NeonButton>
        </div>
      </form>
    </Modal>
  );
}
