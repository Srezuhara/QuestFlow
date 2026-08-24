import { Trophy } from "lucide-react";
import { Link } from "react-router";
import { DataGrid, NeonPanel } from "@/components/ui";
import type { DataGridColumn } from "@/components/ui";
import { useAuthStore } from "@/features/auth/store";
import type { LeaderboardEntryOut } from "../api";
import { useLeaderboard } from "../hooks";

export function TopArchitectsPanel() {
  const { data } = useLeaderboard(5, 0);
  const currentHandle = useAuthStore((s) => s.user?.handle);

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
    { key: "lvl", header: "LvL", render: (row) => row.level },
    { key: "xp", header: "XP", render: (row) => row.total_xp.toLocaleString() },
  ];

  return (
    <NeonPanel className="!p-4">
      <h3 className="mb-2 flex items-center gap-2 border-b border-surface-container-highest pb-2 font-mono text-label-mono text-neon-pink uppercase">
        <Trophy size={14} aria-hidden="true" /> Top_Architects
      </h3>
      <DataGrid
        columns={columns}
        rows={data?.entries ?? []}
        emptyLabel="No architects ranked yet"
        caption="Top five architects by XP"
      />
      <Link
        to="/progress/leaderboard"
        className="mt-3 inline-block font-mono text-label-mono text-neon-lime uppercase hover:underline"
      >
        View full ranking &gt;&gt;
      </Link>
    </NeonPanel>
  );
}
