import { useState } from "react";
import { Link } from "react-router";
import { DataGrid, NeonButton, NeonPanel } from "@/components/ui";
import type { DataGridColumn } from "@/components/ui";
import { useAuthStore } from "@/features/auth/store";
import { cn } from "@/lib/cn";
import { ProgressTabs } from "./components/ProgressTabs";
import type { LeaderboardEntryOut } from "./api";
import { useLeaderboard } from "./hooks";

const LIMIT = 25;

export function LeaderboardPage() {
  const [offset, setOffset] = useState(0);
  const { data, isLoading, isError } = useLeaderboard(LIMIT, offset);
  const currentHandle = useAuthStore((s) => s.user?.handle);

  if (isLoading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <p className="font-mono text-label-mono text-neon-lime uppercase">
          &gt;&gt; loading uplink...
        </p>
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <p className="font-mono text-label-mono text-neon-pink uppercase">
          &gt;&gt; connection to mainframe failed
        </p>
      </div>
    );
  }

  const columns: DataGridColumn<LeaderboardEntryOut>[] = [
    { key: "rank", header: "Rank", render: (row) => `#${row.rank}` },
    {
      key: "architect",
      header: "Architect",
      render: (row) => (
        <span
          className={row.actor.handle === currentHandle ? "font-bold text-neon-lime" : undefined}
        >
          {row.actor.handle}
        </span>
      ),
    },
    {
      key: "title",
      header: "Title",
      hideBelow: "sm",
      render: (row) => row.actor.title,
    },
    { key: "lvl", header: "LvL", render: (row) => row.level },
    { key: "xp", header: "XP", render: (row) => row.total_xp.toLocaleString() },
    {
      key: "streak",
      header: "Streak",
      hideBelow: "sm",
      render: (row) => `${row.current_streak_days}d`,
    },
  ];

  const hasPrev = offset > 0;
  const hasNext = offset + LIMIT < data.total;

  return (
    <div className="mx-auto flex max-w-[1440px] flex-col gap-8 p-4 md:p-8 lg:p-16">
      <header className="flex flex-col gap-2 border-b border-surface-container-highest pb-4">
        <p className="font-mono text-label-mono text-neon-lime uppercase">
          &gt; System Status: <span className="animate-pulse">Optimal</span>
        </p>
        <h1 className="font-display text-headline-lg text-on-surface uppercase tracking-tight">
          Leaderboard
        </h1>
        <ProgressTabs />
      </header>

      <div
        className={cn(
          "sticky top-0 z-10 border border-outline-variant bg-surface-container-lowest px-4 py-2",
          "font-mono text-label-mono uppercase",
        )}
      >
        {data.me.rank !== null ? (
          <span className="text-neon-lime">You: #{data.me.rank}</span>
        ) : (
          <span className="text-on-surface-variant">
            You are hidden —{" "}
            <Link to="/settings" className="text-neon-pink underline">
              enable Public Profile in Settings
            </Link>
          </span>
        )}
      </div>

      <NeonPanel>
        <DataGrid
          columns={columns}
          rows={data.entries.map((e) => ({ ...e }))}
          emptyLabel="No architects ranked yet"
          caption="Leaderboard ranking"
        />
        <div className="mt-4 flex items-center justify-between">
          <NeonButton
            variant="secondary"
            disabled={!hasPrev}
            onClick={() => setOffset((o) => Math.max(0, o - LIMIT))}
          >
            Prev
          </NeonButton>
          <NeonButton
            variant="secondary"
            disabled={!hasNext}
            onClick={() => setOffset((o) => o + LIMIT)}
          >
            Next
          </NeonButton>
        </div>
      </NeonPanel>
    </div>
  );
}
