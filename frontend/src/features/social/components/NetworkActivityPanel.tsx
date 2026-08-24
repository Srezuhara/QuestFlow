import { Radio } from "lucide-react";
import { NeonPanel, TerminalLog } from "@/components/ui";
import { formatFeedLine } from "../format";
import { useFeed } from "../hooks";

/** Everyone's XP events, ambient on the dashboard — distinct from the
 * `System_Log` panel above it, which is *your* activity only. */
export function NetworkActivityPanel() {
  const { data } = useFeed();
  const items = data?.pages[0]?.items ?? [];

  return (
    <NeonPanel className="!p-4">
      <h3 className="mb-2 flex items-center gap-2 border-b border-surface-container-highest pb-2 font-mono text-label-mono text-neon-pink uppercase">
        <Radio size={14} aria-hidden="true" /> Network_Activity
      </h3>
      {items.length === 0 ? (
        <p className="p-3 font-mono text-label-mono text-on-surface-variant">
          &gt; awaiting network activity...
        </p>
      ) : (
        <TerminalLog lines={items.map(formatFeedLine)} aria-label="Everyone's recent XP activity" />
      )}
    </NeonPanel>
  );
}
