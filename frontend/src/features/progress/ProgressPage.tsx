import { Flame, TrendingUp } from "lucide-react";
import { NeonPanel, XPBar } from "@/components/ui";
import { AchievementWall } from "@/features/achievements/components/AchievementWall";
import { ProgressTabs } from "@/features/social/components/ProgressTabs";
import { XPChart } from "./components/XPChart";
import { XPHistoryList } from "./components/XPHistoryList";
import { useProgress } from "./hooks";

function StatTile({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Flame;
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-center gap-3 border-l-2 border-neon-lime pl-3">
      <Icon size={22} className="text-neon-lime" aria-hidden="true" />
      <div>
        <p className="font-mono text-label-mono text-on-surface-variant uppercase">{label}</p>
        <p className="font-display text-title-md text-on-surface uppercase">{value}</p>
      </div>
    </div>
  );
}

export function ProgressPage() {
  const { data: progress, isLoading, isError } = useProgress();

  if (isLoading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <p className="font-mono text-label-mono text-neon-lime uppercase">
          &gt;&gt; loading uplink...
        </p>
      </div>
    );
  }

  if (isError || !progress) {
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
          &gt; System Status: <span className="animate-pulse">Optimal</span>
        </p>
        <h1 className="font-display text-headline-lg text-on-surface uppercase tracking-tight">
          Progression
        </h1>
        <ProgressTabs />
      </header>

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
        <section className="lg:col-span-8">
          <XPChart />
        </section>
        <aside className="lg:col-span-4">
          <NeonPanel className="flex flex-col gap-6">
            <div>
              <p className="mb-2 font-mono text-label-mono text-neon-lime uppercase">
                Level {progress.level}
              </p>
              <XPBar
                percent={progress.percent}
                label={`${progress.xp_into_level}/${progress.xp_for_next_level} XP TO NEXT LEVEL`}
              />
            </div>
            <StatTile
              icon={TrendingUp}
              label="Total XP"
              value={progress.total_xp.toLocaleString()}
            />
            <StatTile
              icon={Flame}
              label="Current Streak"
              value={`${progress.current_streak_days} days`}
            />
            <StatTile
              icon={Flame}
              label="Longest Streak"
              value={`${progress.longest_streak_days} days`}
            />
          </NeonPanel>
        </aside>
      </div>

      <NeonPanel>
        <h2 className="mb-4 border-b border-surface-container-highest pb-4 font-display text-title-md text-on-surface uppercase">
          Achievement Wall
        </h2>
        <AchievementWall />
      </NeonPanel>

      <XPHistoryList />
    </div>
  );
}
