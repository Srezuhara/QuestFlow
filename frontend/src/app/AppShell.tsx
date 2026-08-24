import { useState } from "react";
import type { LucideIcon } from "lucide-react";
import {
  BellRing,
  FileText,
  LayoutGrid,
  LogOut,
  Plus,
  Settings,
  Timer,
  TrendingUp,
  UserCircle2,
  Zap,
} from "lucide-react";
import { NavLink, Outlet } from "react-router";
import { GlowIcon, LevelUpToast, NeonButton, XPBar } from "@/components/ui";
import { useAuthStore } from "@/features/auth/store";
import { useLogout } from "@/features/auth/hooks";
import { NewQuestModal } from "@/features/tasks/components/NewQuestModal";
import { NotificationBell } from "@/features/notifications/components/NotificationBell";
import { NotificationCenterModal } from "@/features/notifications/components/NotificationCenterModal";
import { useNotificationSocketBridge } from "@/features/notifications/hooks";
import { useProgress } from "@/features/progress/hooks";
import { cn } from "@/lib/cn";

const NAV_ITEMS: { to: string; label: string; icon: LucideIcon }[] = [
  { to: "/", label: "Dashboard", icon: LayoutGrid },
  { to: "/habits", label: "Habits", icon: Zap },
  { to: "/timer", label: "Timer", icon: Timer },
  { to: "/progress", label: "Progress", icon: TrendingUp },
  { to: "/reminders", label: "Reminders", icon: BellRing },
  { to: "/notes", label: "Notes", icon: FileText },
];

/**
 * Fixed sidebar + outlet shell, identical across all four mockups (Command
 * Center, Habit Master, Time Keeper, Knowledge Vault). Responsive per the
 * plan: full sidebar with labels >=1024px, icon-only rail 640-1023px,
 * bottom tab bar <640px (a deliberate addition beyond the desktop-only
 * mockups).
 */
export function AppShell() {
  const user = useAuthStore((s) => s.user);
  const logout = useLogout();
  const { data: progress } = useProgress();
  const [questModalOpen, setQuestModalOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  useNotificationSocketBridge();

  return (
    <div className="min-h-screen bg-neon-black sm:pl-18 lg:pl-70">
      <aside className="fixed inset-y-0 left-0 z-10 hidden w-18 flex-col border-r border-outline-variant bg-surface-container-lowest sm:flex lg:w-70">
        <div className="flex flex-col gap-6 p-4 lg:p-6">
          <span className="hidden font-display text-title-md text-on-surface uppercase lg:block">
            Questflow
          </span>

          <div className="flex flex-col items-center gap-3 lg:items-stretch">
            <div className="flex items-center gap-3">
              {user?.avatar_url ? (
                <img
                  src={user.avatar_url}
                  alt=""
                  className="size-10 shrink-0 rounded-full border border-neon-lime object-cover"
                />
              ) : (
                <UserCircle2 className="size-10 shrink-0 text-neon-lime" />
              )}
              <div className="hidden lg:block">
                <p className="font-mono text-label-mono text-neon-lime uppercase">
                  {progress ? `LVL ${progress.level} ` : ""}
                  {user?.title ?? "ARCHITECT"}
                </p>
                <p className="truncate font-body text-body-md text-on-surface">
                  {user?.display_name}
                </p>
              </div>
            </div>
            <XPBar
              percent={progress?.percent ?? 0}
              label={
                progress
                  ? `${progress.xp_into_level}/${progress.xp_for_next_level} XP TO NEXT LEVEL`
                  : "Loading..."
              }
              className="hidden lg:block"
            />
          </div>

          <NeonButton
            className="w-full !px-2.5 lg:!px-5"
            aria-label="New Quest"
            onClick={() => setQuestModalOpen(true)}
          >
            <Plus size={16} aria-hidden="true" />
            <span className="hidden lg:inline">New Quest</span>
          </NeonButton>
        </div>

        <NewQuestModal open={questModalOpen} onClose={() => setQuestModalOpen(false)} />
        <NotificationCenterModal
          open={notificationsOpen}
          onClose={() => setNotificationsOpen(false)}
        />

        <nav className="flex flex-1 flex-col gap-1 px-2 lg:px-4">
          {NAV_ITEMS.map(({ to, label, icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              aria-label={label}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 border-l-2 border-transparent px-3 py-2.5 font-mono text-label-mono uppercase",
                  isActive
                    ? "border-neon-lime bg-surface-container text-neon-lime"
                    : "text-on-surface-variant hover:text-on-surface",
                )
              }
            >
              {({ isActive }) => (
                <>
                  <GlowIcon icon={icon} active={isActive} />
                  <span className="hidden lg:inline">{label}</span>
                </>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="flex flex-col gap-1 border-t border-outline-variant px-2 py-4 lg:px-4">
          <NotificationBell className="hidden sm:flex" onClick={() => setNotificationsOpen(true)} />
          <NavLink
            to="/settings"
            aria-label="Settings"
            className="flex items-center gap-3 px-3 py-2.5 font-mono text-label-mono text-on-surface-variant uppercase hover:text-on-surface"
          >
            <Settings size={18} aria-hidden="true" />
            <span className="hidden lg:inline">Settings</span>
          </NavLink>
          <button
            onClick={() => logout.mutate()}
            aria-label="Log Out"
            className="flex items-center gap-3 px-3 py-2.5 font-mono text-label-mono text-on-surface-variant uppercase hover:text-neon-pink"
          >
            <LogOut size={18} aria-hidden="true" />
            <span className="hidden lg:inline">Log Out</span>
          </button>
        </div>
      </aside>

      <main className="pb-20 sm:pb-0">
        <Outlet />
      </main>

      <nav className="fixed inset-x-0 bottom-0 z-10 flex border-t border-outline-variant bg-surface-container-lowest sm:hidden">
        {NAV_ITEMS.map(({ to, label, icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            aria-label={label}
            className="flex flex-1 flex-col items-center gap-1 py-2.5"
          >
            {({ isActive }) => (
              <>
                <GlowIcon icon={icon} active={isActive} />
                {/* 6 items no longer fit labels-and-all at the narrowest
                    supported width (phase 4 already found 5 tight at
                    375px) — per the plan's fallback instruction, drop to
                    icon-only below 400px rather than shortening labels
                    inconsistently. The NavLink's own `aria-label` above
                    keeps the accessible name intact below 400px even
                    though this visible label disappears — PHASE_8_9_PLAN.md
                    §9.0/D9-7 found this was the one nav link with no
                    accessible name at all before this fix. */}
                <span
                  className={cn(
                    "hidden font-mono text-[10px] uppercase min-[400px]:block",
                    isActive ? "text-neon-lime" : "text-on-surface-variant",
                  )}
                >
                  {label}
                </span>
              </>
            )}
          </NavLink>
        ))}
      </nav>

      <LevelUpToast />
    </div>
  );
}
