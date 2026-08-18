import { CalendarDays, ListChecks, Terminal } from "lucide-react";
import { NeonPanel, TerminalLog } from "@/components/ui";
import { TaskItem } from "@/features/tasks/components/TaskItem";
import { useDashboard } from "./hooks";

function formatActivityLine(source_type: string, awarded_xp: number, occurred_on: string): string {
  const sign = awarded_xp >= 0 ? "+" : "";
  return `${sign}${awarded_xp} XP — ${source_type.replaceAll("_", " ").toUpperCase()} (${occurred_on})`;
}

export function DashboardPage() {
  const { data: dashboard, isLoading, isError } = useDashboard();

  if (isLoading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <p className="font-mono text-label-mono text-neon-lime uppercase">
          &gt;&gt; loading uplink...
        </p>
      </div>
    );
  }

  if (isError || !dashboard) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <p className="font-mono text-label-mono text-neon-pink uppercase">
          &gt;&gt; connection to mainframe failed
        </p>
      </div>
    );
  }

  return (
    <div className="mx-auto flex max-w-[1440px] flex-col gap-8 p-4 md:p-8 lg:p-16">
      <header className="flex flex-col gap-2 border-b border-surface-container-highest pb-4">
        <p className="font-mono text-label-mono text-neon-lime uppercase">
          System Status: <span className="animate-pulse">Optimal</span>
        </p>
        <h1 className="font-display text-headline-lg text-on-surface uppercase tracking-tight">
          Command Center
        </h1>
      </header>

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
        <section className="flex flex-col gap-4 lg:col-span-8">
          <NeonPanel>
            <div className="mb-6 flex items-center justify-between border-b border-surface-container-highest pb-4">
              <h2 className="flex items-center gap-2 font-display text-title-md text-on-surface uppercase">
                <ListChecks size={20} className="text-neon-lime" aria-hidden="true" />
                Daily Objectives
              </h2>
              <span className="bg-neon-lime px-2 py-1 font-mono text-label-mono font-bold text-neon-black">
                {dashboard.active_count} ACTIVE
              </span>
            </div>

            {dashboard.objectives.length === 0 ? (
              <p className="border border-dashed border-outline-variant p-6 text-center font-mono text-label-mono text-on-surface-variant uppercase">
                No active objectives — deploy a new quest to get started
              </p>
            ) : (
              <div className="flex flex-col gap-3">
                {dashboard.objectives.map((task) => (
                  <TaskItem key={task.id} task={task} />
                ))}
              </div>
            )}
          </NeonPanel>
        </section>

        <aside className="flex flex-col gap-6 lg:col-span-4">
          <NeonPanel className="!p-4">
            <h3 className="mb-2 flex items-center gap-2 border-b border-surface-container-highest pb-2 font-mono text-label-mono text-neon-pink uppercase">
              <Terminal size={14} aria-hidden="true" /> System_Log
            </h3>
            {dashboard.recent_activity.length === 0 ? (
              <p className="p-3 font-mono text-label-mono text-on-surface-variant">
                &gt; awaiting first XP event...
              </p>
            ) : (
              <TerminalLog
                lines={dashboard.recent_activity.map((e) =>
                  formatActivityLine(e.source_type, e.awarded_xp, e.occurred_on),
                )}
              />
            )}
          </NeonPanel>

          <NeonPanel>
            <h3 className="mb-4 flex items-center gap-2 font-display text-lg text-on-surface uppercase">
              <CalendarDays size={18} className="text-neon-lime" aria-hidden="true" />
              Future Pipeline
            </h3>

            <div className="mb-4">
              <h4 className="mb-2 border-b border-surface-container-highest pb-1 font-mono text-label-mono text-on-surface-variant uppercase">
                Due Tomorrow
              </h4>
              {dashboard.pipeline.due_tomorrow.length === 0 ? (
                <p className="font-mono text-label-mono text-on-surface-variant">
                  Nothing scheduled
                </p>
              ) : (
                dashboard.pipeline.due_tomorrow.map((task) => (
                  <div
                    key={task.id}
                    className="flex items-center gap-2 border-l-2 border-outline-variant py-2 pl-2"
                  >
                    <span className="size-2 rounded-full bg-neon-lime shadow-[0_0_5px_rgba(195,244,0,0.6)]" />
                    <span className="font-mono text-body-md text-on-surface">{task.title}</span>
                  </div>
                ))
              )}
            </div>

            <div>
              <h4 className="mb-2 border-b border-surface-container-highest pb-1 font-mono text-label-mono text-on-surface-variant uppercase">
                Next 7 Days
              </h4>
              {dashboard.pipeline.due_next_week.length === 0 ? (
                <p className="font-mono text-label-mono text-on-surface-variant">
                  Nothing scheduled
                </p>
              ) : (
                dashboard.pipeline.due_next_week.map((task) => (
                  <div
                    key={task.id}
                    className="flex items-center gap-2 border-l-2 border-outline-variant py-2 pl-2"
                  >
                    <span className="size-2 rounded-full bg-neon-pink shadow-[0_0_5px_rgba(254,0,254,0.6)]" />
                    <span className="font-mono text-body-md text-on-surface">{task.title}</span>
                  </div>
                ))
              )}
            </div>
          </NeonPanel>
        </aside>
      </div>
    </div>
  );
}
