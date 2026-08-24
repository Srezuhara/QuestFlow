import type { FeedItemOut } from "./api";

const VERBS: Record<string, string> = {
  task_complete: "completed a quest",
  habit_log: "logged a habit",
  streak_bonus: "hit a streak milestone",
  focus_session: "finished a focus session",
  achievement: "unlocked an achievement",
};

/**
 * Pure. No React, no i18n, no Date locale formatting. Unknown source types
 * render a generic line rather than crashing — the server ships new
 * `XPSourceType` values before the frontend knows about them.
 */
export function formatFeedLine(item: FeedItemOut): string {
  const verb = VERBS[item.source_type] ?? "earned XP";
  const branch = item.skill_branch ? ` [${item.skill_branch.toUpperCase()}]` : "";
  return `${item.actor.handle} ${verb} +${item.awarded_xp} XP${branch}`;
}
