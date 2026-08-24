import { useState } from "react";
import { useNavigate } from "react-router";
import { Modal, NeonButton } from "@/components/ui";
import { useDeleteAccount } from "@/features/auth/hooks";
import { useAuthStore } from "@/features/auth/store";

/**
 * Type-your-handle-to-confirm delete flow (D9-2). No password re-entry —
 * the session is already authenticated, and the typed handle is the
 * confirmation gate.
 */
export function DeleteAccountDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const user = useAuthStore((s) => s.user);
  const deleteAccount = useDeleteAccount();
  const navigate = useNavigate();
  const [confirmText, setConfirmText] = useState("");

  function handleClose() {
    setConfirmText("");
    deleteAccount.reset();
    onClose();
  }

  function handleDelete() {
    deleteAccount.mutate(undefined, {
      onSuccess: () => {
        navigate("/register");
      },
    });
  }

  const canDelete = user !== null && confirmText === user.handle;

  return (
    <Modal open={open} onClose={handleClose} title="Delete Account">
      <div className="flex flex-col gap-4">
        <p className="font-body text-body-sm text-on-surface-variant">
          This permanently deletes your account and everything tied to it: quests, habits, notes,
          focus sessions, reminders, XP history, and skill tree progress. This cannot be undone.
        </p>

        <div className="flex flex-col gap-2">
          <label
            htmlFor="confirm-handle"
            className="font-mono text-label-mono text-on-surface-variant uppercase"
          >
            Type <span className="text-neon-pink">{user?.handle}</span> to confirm
          </label>
          <input
            id="confirm-handle"
            type="text"
            autoComplete="off"
            value={confirmText}
            onChange={(e) => setConfirmText(e.target.value)}
            className="clip-chamfer border border-outline-variant bg-surface-container-lowest px-3 py-2 font-body text-body-md text-on-surface outline-none focus:border-neon-pink"
          />
        </div>

        {deleteAccount.isError && (
          <p className="font-mono text-label-mono text-neon-pink">
            Failed to delete account. Please try again.
          </p>
        )}

        <div className="flex justify-end gap-3">
          <NeonButton type="button" variant="ghost" onClick={handleClose}>
            Cancel
          </NeonButton>
          <NeonButton
            type="button"
            variant="secondary"
            disabled={!canDelete || deleteAccount.isPending}
            onClick={handleDelete}
          >
            {deleteAccount.isPending ? "Deleting..." : "Delete Account"}
          </NeonButton>
        </div>
      </div>
    </Modal>
  );
}
