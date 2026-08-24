import { NeonPanel } from "@/components/ui";
import { cn } from "@/lib/cn";
import type { FocusMode, FocusSessionOut } from "../api";

const MODE_LABEL: Record<FocusMode, string> = {
  focus: "FOCUS",
  short_break: "SHORT BREAK",
  long_break: "LONG BREAK",
};

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" });
}

function formatDuration(seconds: number | null): string {
  if (seconds === null) return "—";
  const minutes = Math.round(seconds / 60);
  return `${minutes}m`;
}

export function MissionLog({
  sessions,
  isLoading,
}: {
  sessions: FocusSessionOut[] | undefined;
  isLoading: boolean;
}) {
  return (
    <NeonPanel>
      <h2 className="mb-4 border-b border-surface-container-highest pb-4 font-display text-title-md text-on-surface uppercase">
        Mission Log
      </h2>

      {isLoading ? (
        <p className="font-mono text-label-mono text-on-surface-variant uppercase">
          &gt;&gt; loading log...
        </p>
      ) : !sessions || sessions.length === 0 ? (
        <p className="border border-dashed border-outline-variant p-6 text-center font-mono text-label-mono text-on-surface-variant uppercase">
          No focus sessions logged for this day
        </p>
      ) : (
        <ol className="flex flex-col gap-3">
          {sessions.map((session) => {
            const abandoned = session.status === "abandoned";
            return (
              <li
                key={session.id}
                className={cn(
                  "flex items-center justify-between gap-3 border-l-2 py-2 pl-3",
                  abandoned ? "border-outline-variant opacity-50" : "border-neon-lime",
                )}
              >
                <div className="flex flex-col gap-0.5">
                  <span
                    className={cn(
                      "font-mono text-label-mono uppercase",
                      abandoned ? "text-on-surface-variant line-through" : "text-neon-lime",
                    )}
                  >
                    {formatTime(session.started_at)} // {MODE_LABEL[session.mode]}
                  </span>
                  {session.task_title && (
                    <span className="font-body text-body-md text-on-surface">
                      {session.task_title}
                    </span>
                  )}
                </div>
                <div className="flex flex-col items-end gap-0.5">
                  <span className="font-mono text-body-md text-on-surface-variant">
                    {formatDuration(session.actual_seconds)}
                  </span>
                  {session.xp_awarded > 0 && (
                    <span className="font-mono text-label-mono text-neon-lime">
                      +{session.xp_awarded} XP
                    </span>
                  )}
                </div>
              </li>
            );
          })}
        </ol>
      )}
    </NeonPanel>
  );
}
