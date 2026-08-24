import { NeonPanel } from "@/components/ui";
import type { HabitOut } from "../api";

const ACCENTS = ["text-neon-lime", "text-neon-pink", "text-neon-yellow"] as const;
const BAR_ACCENTS = ["bg-neon-lime", "bg-neon-pink", "bg-neon-yellow"] as const;

export function WeeklyDirectives({ habits }: { habits: HabitOut[] }) {
  return (
    <NeonPanel>
      <h2 className="mb-4 border-b border-surface-container-highest pb-4 font-display text-title-md text-on-surface uppercase">
        Weekly Directives
      </h2>

      {habits.length === 0 ? (
        <p className="border border-dashed border-outline-variant p-6 text-center font-mono text-label-mono text-on-surface-variant uppercase">
          No directives tracked yet
        </p>
      ) : (
        <div className="flex flex-col gap-4">
          {habits.map((habit, i) => {
            const percent = Math.min(
              100,
              (habit.current_period.count / Math.max(1, habit.current_period.target)) * 100,
            );
            const accent = ACCENTS[i % ACCENTS.length];
            const barAccent = BAR_ACCENTS[i % BAR_ACCENTS.length];
            return (
              <div key={habit.id} className="flex flex-col gap-1.5">
                <div className="flex items-center justify-between">
                  <span className={`font-mono text-label-mono uppercase ${accent}`}>
                    {habit.name}
                  </span>
                  <span className="font-mono text-label-mono text-on-surface-variant">
                    {habit.current_period.count}/{habit.current_period.target}
                  </span>
                </div>
                <div className="h-1.5 w-full bg-surface-container-high">
                  <div
                    className={`h-full ${barAccent} transition-[width] duration-300`}
                    style={{ width: `${percent}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </NeonPanel>
  );
}
