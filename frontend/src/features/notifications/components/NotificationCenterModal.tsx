import { useNavigate } from "react-router";
import { Modal, NeonButton } from "@/components/ui";
import { useMarkAllRead, useMarkRead, useNotifications } from "../hooks";
import type { NotificationOut } from "../api";

function describe(notification: NotificationOut): string {
  const payload = notification.payload as Record<string, unknown>;
  if (typeof payload.message === "string") {
    const label = typeof payload.target_label === "string" ? ` (${payload.target_label})` : "";
    return `${payload.message}${label}`;
  }
  switch (notification.type) {
    case "achievement":
      return "Achievement unlocked";
    case "level_up":
      return "Level up!";
    case "streak_risk":
      return "A streak is at risk";
    default:
      return "System notification";
  }
}

function targetUrl(notification: NotificationOut): string {
  const payload = notification.payload as Record<string, unknown>;
  return typeof payload.url === "string" ? payload.url : "/reminders";
}

export function NotificationCenterModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { data } = useNotifications();
  const markRead = useMarkRead();
  const markAllRead = useMarkAllRead();
  const navigate = useNavigate();

  const items = data?.items ?? [];

  return (
    <Modal open={open} onClose={onClose} title="Notification Center" size="full">
      <div className="flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <p className="font-mono text-label-mono text-on-surface-variant uppercase">
            {data ? `${data.unread_count} unread` : "Loading..."}
          </p>
          <NeonButton
            variant="ghost"
            disabled={markAllRead.isPending || (data?.unread_count ?? 0) === 0}
            onClick={() => markAllRead.mutate()}
          >
            Mark all read
          </NeonButton>
        </div>

        <ul className="flex max-h-96 flex-col gap-2 overflow-y-auto">
          {items.length === 0 && (
            <li className="font-mono text-label-mono text-on-surface-variant uppercase">
              &gt;&gt; no notifications yet
            </li>
          )}
          {items.map((notification) => (
            <li key={notification.id}>
              <button
                type="button"
                onClick={() => {
                  if (!notification.read_at) markRead.mutate(notification.id);
                  onClose();
                  navigate(targetUrl(notification));
                }}
                className={`w-full border-l-2 px-3 py-2 text-left font-body text-body-md ${
                  notification.read_at
                    ? "border-transparent text-on-surface-variant"
                    : "border-neon-lime text-on-surface"
                }`}
              >
                {describe(notification)}
              </button>
            </li>
          ))}
        </ul>
      </div>
    </Modal>
  );
}
