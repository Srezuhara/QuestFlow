import { CheckCircle2, Flame, ListChecks, Sparkles, Timer } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { NeonButton, NeonPanel } from "@/components/ui";
import { formatShardTime } from "@/features/notes/format";
import { useXPHistory } from "../hooks";
import type { XPEventOut } from "../api";

type XPSourceType = XPEventOut["source_type"];

const SOURCE_ICON: Record<XPSourceType, LucideIcon> = {
  task_complete: ListChecks,
  habit_log: CheckCircle2,
  streak_bonus: Flame,
  focus_session: Timer,
  achievement: Sparkles,
};

function sourceLabel(source: XPSourceType): string {
  return source.replaceAll("_", " ").toUpperCase();
}

/** Infinite ledger list, one row per `XPEventOut`. "LOAD MORE" is a button
 * (per §6.11) rather than a scroll-triggered fetch, so tests and screen
 * readers don't have to simulate intersection events. */
export function XPHistoryList() {
  const { data, isLoading, isError, fetchNextPage, hasNextPage, isFetchingNextPage } =
    useXPHistory();

  if (isLoading) {
    return (
      <p className="font-mono text-label-mono text-neon-lime uppercase">
        &gt;&gt; loading ledger...
      </p>
    );
  }
  if (isError || !data) {
    return (
      <p className="font-mono text-label-mono text-neon-pink uppercase">
        &gt;&gt; connection to mainframe failed
      </p>
    );
  }

  const events = data.pages.flatMap((page) => page.items);

  return (
    <NeonPanel className="flex flex-col gap-2">
      <h2 className="mb-2 border-b border-surface-container-highest pb-4 font-display text-title-md text-on-surface uppercase">
        XP Ledger
      </h2>

      {events.length === 0 ? (
        <p className="border border-dashed border-outline-variant p-6 text-center font-mono text-label-mono text-on-surface-variant uppercase">
          No XP events yet
        </p>
      ) : (
        <ul className="flex flex-col divide-y divide-surface-container-highest">
          {events.map((event) => {
            const Icon = SOURCE_ICON[event.source_type];
            const positive = event.awarded_xp >= 0;
            return (
              <li key={event.id} className="flex items-center gap-3 py-3">
                <Icon
                  size={18}
                  className={positive ? "text-neon-lime" : "text-neon-pink"}
                  aria-hidden="true"
                />
                <div className="flex-1">
                  <p className="font-mono text-label-mono text-on-surface uppercase">
                    {sourceLabel(event.source_type)}
                  </p>
                  <p className="font-mono text-label-mono text-on-surface-variant">
                    {formatShardTime(event.created_at)}
                  </p>
                </div>
                <span
                  className={`font-mono text-label-mono ${positive ? "text-neon-lime" : "text-neon-pink"}`}
                >
                  {positive ? "+" : ""}
                  {event.awarded_xp} XP
                </span>
              </li>
            );
          })}
        </ul>
      )}

      {hasNextPage && (
        <NeonButton
          variant="ghost"
          onClick={() => fetchNextPage()}
          disabled={isFetchingNextPage}
          className="mt-2 self-center"
        >
          {isFetchingNextPage ? "Loading..." : "Load More"}
        </NeonButton>
      )}
    </NeonPanel>
  );
}
