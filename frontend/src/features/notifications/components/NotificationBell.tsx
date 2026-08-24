import { Bell } from "lucide-react";
import { GlowIcon } from "@/components/ui";
import { useNotifications } from "../hooks";

export function NotificationBell({
  onClick,
  className,
}: {
  onClick: () => void;
  className?: string;
}) {
  const { data } = useNotifications();
  const unreadCount = data?.unread_count ?? 0;

  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={unreadCount > 0 ? `Notifications, ${unreadCount} unread` : "Notifications"}
      className={`relative flex items-center gap-3 px-3 py-2.5 font-mono text-label-mono text-on-surface-variant uppercase hover:text-neon-lime ${className ?? ""}`}
    >
      <span className="relative">
        <GlowIcon icon={Bell} active={unreadCount > 0} />
        {unreadCount > 0 && (
          <span
            aria-hidden="true"
            className="absolute -top-1.5 -right-1.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-neon-pink px-1 font-mono text-[10px] text-neon-black"
          >
            {unreadCount > 99 ? "99+" : unreadCount}
          </span>
        )}
      </span>
      <span className="hidden lg:inline">Notifications</span>
    </button>
  );
}
