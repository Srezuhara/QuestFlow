import { ChamferBox, NeonButton, NeonPanel } from "@/components/ui";
import { useCancelReminder, useDismissReminder, useReminders } from "../hooks";
import type { ReminderOut } from "../api";

function groupLabel(remindAt: string): "Today" | "Tomorrow" | "Later" {
  const now = new Date();
  const target = new Date(remindAt);
  const startOfDay = (d: Date) => new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime();
  const diffDays = Math.round((startOfDay(target) - startOfDay(now)) / 86_400_000);
  if (diffDays <= 0) return "Today";
  if (diffDays === 1) return "Tomorrow";
  return "Later";
}

function ReminderRow({ reminder }: { reminder: ReminderOut }) {
  const dismiss = useDismissReminder();
  const cancel = useCancelReminder();
  const time = new Date(reminder.remind_at).toLocaleString(undefined, {
    hour: "2-digit",
    minute: "2-digit",
    month: "short",
    day: "numeric",
  });

  return (
    <ChamferBox className="flex items-center justify-between gap-3 border border-outline-variant bg-surface-container-lowest px-4 py-3">
      <div className="flex flex-col gap-1">
        <p className="font-body text-body-md text-on-surface">{reminder.message}</p>
        <p className="font-mono text-label-mono text-on-surface-variant uppercase">
          {time}
          {reminder.target_label ? ` · ${reminder.target_label}` : ""}
        </p>
      </div>
      <div className="flex shrink-0 gap-2">
        <NeonButton
          variant="ghost"
          disabled={dismiss.isPending}
          onClick={() => dismiss.mutate(reminder.id)}
        >
          Ack
        </NeonButton>
        <NeonButton
          variant="ghost"
          disabled={cancel.isPending}
          onClick={() => cancel.mutate(reminder.id)}
        >
          Cancel
        </NeonButton>
      </div>
    </ChamferBox>
  );
}

export function UpcomingRemindersPanel() {
  const { data, isLoading } = useReminders("scheduled");
  const items = data?.items ?? [];

  const groups: Record<"Today" | "Tomorrow" | "Later", ReminderOut[]> = {
    Today: [],
    Tomorrow: [],
    Later: [],
  };
  for (const item of items) {
    groups[groupLabel(item.remind_at)].push(item);
  }

  return (
    <NeonPanel>
      <h2 className="mb-4 border-b border-surface-container-highest pb-4 font-display text-title-md text-on-surface uppercase">
        Upcoming
      </h2>

      {isLoading && (
        <p className="font-mono text-label-mono text-on-surface-variant uppercase">
          &gt;&gt; loading reminders...
        </p>
      )}

      {!isLoading && items.length === 0 && (
        <p className="font-mono text-label-mono text-on-surface-variant uppercase">
          &gt;&gt; no scheduled reminders
        </p>
      )}

      <div className="flex flex-col gap-6">
        {(["Today", "Tomorrow", "Later"] as const).map((label) =>
          groups[label].length === 0 ? null : (
            <div key={label} className="flex flex-col gap-2">
              <p className="font-mono text-label-mono text-neon-lime uppercase">{label}</p>
              <div className="flex flex-col gap-2">
                {groups[label].map((reminder) => (
                  <ReminderRow key={reminder.id} reminder={reminder} />
                ))}
              </div>
            </div>
          ),
        )}
      </div>
    </NeonPanel>
  );
}
