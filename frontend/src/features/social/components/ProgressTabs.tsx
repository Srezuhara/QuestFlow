import { NavLink } from "react-router";
import { cn } from "@/lib/cn";

const TABS = [
  { to: "/progress", label: "Overview", end: true },
  { to: "/progress/leaderboard", label: "Leaderboard", end: false },
];

/** Rendered by both `ProgressPage` and `LeaderboardPage` — D8-7: no 7th nav
 * item, the leaderboard is a nested route under Progress with this in-page
 * tab strip instead. */
export function ProgressTabs() {
  return (
    <nav className="flex gap-1" aria-label="Progress sections">
      {TABS.map(({ to, label, end }) => (
        <NavLink
          key={to}
          to={to}
          end={end}
          className={({ isActive }) =>
            cn(
              "border-b-2 border-transparent px-3 py-2 font-mono text-label-mono uppercase",
              isActive
                ? "border-neon-lime text-neon-lime"
                : "text-on-surface-variant hover:text-on-surface",
            )
          }
        >
          {label}
        </NavLink>
      ))}
    </nav>
  );
}
