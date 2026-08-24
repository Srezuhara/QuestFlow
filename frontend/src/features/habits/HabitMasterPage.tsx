import { useState } from "react";
import { NeonButton } from "@/components/ui";
import { SkillTree } from "@/features/skilltree/components/SkillTree";
import { ActiveHabitList } from "./components/ActiveHabitList";
import { NewHabitModal } from "./components/NewHabitModal";
import { StreakMatrix } from "./components/StreakMatrix";
import { WeeklyDirectives } from "./components/WeeklyDirectives";
import { useHabits } from "./hooks";

export function HabitMasterPage() {
  const { data: habits, isLoading, isError } = useHabits();
  const [modalOpen, setModalOpen] = useState(false);

  if (isLoading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <p className="font-mono text-label-mono text-neon-lime uppercase">
          &gt;&gt; loading uplink...
        </p>
      </div>
    );
  }

  if (isError || !habits) {
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
      <header className="flex flex-col gap-2 border-b border-surface-container-highest pb-4 md:flex-row md:items-end md:justify-between">
        <div className="flex flex-col gap-2">
          <p className="font-mono text-label-mono text-neon-lime uppercase">
            &gt; System Status: <span className="animate-pulse">Optimal</span>
          </p>
          <h1 className="font-display text-headline-lg text-on-surface uppercase tracking-tight">
            Habit Master
          </h1>
        </div>
        <NeonButton onClick={() => setModalOpen(true)}>+ New Habit</NeonButton>
      </header>

      {/* Row 1: skill tree + weekly directives — reflowed for phase 6 (D1's
          expected change). Unlike the row below, this renders even with zero
          habits: `core_nexus` is available from registration, so a brand-new
          user must still see the tree. */}
      <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
        <section className="lg:col-span-8">
          <SkillTree />
        </section>
        <aside className="lg:col-span-4">
          <WeeklyDirectives habits={habits} />
        </aside>
      </div>

      {habits.length === 0 ? (
        <p className="border border-dashed border-outline-variant p-10 text-center font-mono text-label-mono text-on-surface-variant uppercase">
          No habits tracked yet — deploy your first directive to get started
        </p>
      ) : (
        <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
          <section className="lg:col-span-6">
            <ActiveHabitList habits={habits} />
          </section>
          <aside className="lg:col-span-6">
            <StreakMatrix habits={habits} />
          </aside>
        </div>
      )}

      <NewHabitModal open={modalOpen} onClose={() => setModalOpen(false)} />
    </div>
  );
}
