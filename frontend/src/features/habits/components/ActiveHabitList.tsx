import { Flame } from "lucide-react";
import { NeonButton, NeonPanel, StatusBadge } from "@/components/ui";
import { useLogHabit } from "../hooks";
import type { HabitOut } from "../api";

export function ActiveHabitList({ habits }: { habits: HabitOut[] }) {
  const dueHabits = habits.filter((h) => h.due_today);
  const logHabit = useLogHabit();

  return (
    <NeonPanel>
      <div className="mb-6 flex items-center justify-between border-b border-surface-container-highest pb-4">
        <h2 className="flex items-center gap-2 font-display text-title-md text-on-surface uppercase">
          <Flame size={20} className="text-neon-lime" aria-hidden="true" />
          Active Habits
        </h2>
        <span className="bg-neon-lime px-2 py-1 font-mono text-label-mono font-bold text-neon-black">
          {dueHabits.length} ACTION REQ
        </span>
      </div>

      {dueHabits.length === 0 ? (
        <p className="border border-dashed border-outline-variant p-6 text-center font-mono text-label-mono text-on-surface-variant uppercase">
          No active objectives — every habit is on track today
        </p>
      ) : (
        <div className="flex flex-col gap-3">
          {dueHabits.map((habit) => (
            <div
              key={habit.id}
              className="flex items-center justify-between gap-4 border-l-2 border-neon-lime bg-surface-container-low p-4"
            >
              <div className="flex flex-col gap-1">
                <div className="flex items-center gap-2">
                  <span className="font-body text-body-md text-on-surface">{habit.name}</span>
                  <StatusBadge level="urgent">Action Req</StatusBadge>
                </div>
                {habit.description && (
                  <p className="font-mono text-label-mono text-on-surface-variant">
                    {habit.description}
                  </p>
                )}
              </div>
              <NeonButton
                variant="ghost"
                disabled={logHabit.isPending}
                onClick={() => logHabit.mutate(habit)}
              >
                Execute
              </NeonButton>
            </div>
          ))}
        </div>
      )}
    </NeonPanel>
  );
}
