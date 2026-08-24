import { useState } from "react";
import { Plus } from "lucide-react";
import { NeonButton } from "@/components/ui";
import { NotificationBell } from "@/features/notifications/components/NotificationBell";
import { NotificationCenterModal } from "@/features/notifications/components/NotificationCenterModal";
import { DeliveryLogPanel } from "./components/DeliveryLogPanel";
import { NewReminderModal } from "./components/NewReminderModal";
import { PushAccessPanel } from "./components/PushAccessPanel";
import { UpcomingRemindersPanel } from "./components/UpcomingRemindersPanel";

export function SignalRelayPage() {
  const [newReminderOpen, setNewReminderOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);

  return (
    <div className="mx-auto flex max-w-[1440px] flex-col gap-8 p-4 md:p-8 lg:p-16">
      <header className="flex flex-col gap-4 border-b border-surface-container-highest pb-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-col gap-2">
          <p className="font-mono text-label-mono text-neon-lime uppercase">
            &gt; Signal Relay: <span className="animate-pulse">Listening</span>
          </p>
          <h1 className="font-display text-headline-lg text-on-surface uppercase tracking-tight">
            Reminders
          </h1>
        </div>
        <div className="flex items-center gap-3">
          {/* The bell also lives here below 640px — the sidebar footer's
              copy is hidden on that breakpoint (D7-10). */}
          <NotificationBell className="sm:hidden" onClick={() => setNotificationsOpen(true)} />
          <NeonButton onClick={() => setNewReminderOpen(true)}>
            <Plus size={16} aria-hidden="true" />
            New Reminder
          </NeonButton>
        </div>
      </header>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <UpcomingRemindersPanel />
        <PushAccessPanel />
        <div className="lg:col-span-2">
          <DeliveryLogPanel />
        </div>
      </div>

      <NewReminderModal open={newReminderOpen} onClose={() => setNewReminderOpen(false)} />
      <NotificationCenterModal
        open={notificationsOpen}
        onClose={() => setNotificationsOpen(false)}
      />
    </div>
  );
}
