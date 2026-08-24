import { NeonPanel, TerminalLog } from "@/components/ui";
import { useReminders } from "../hooks";

const STATUS_VERB: Record<string, string> = {
  sent: "delivered",
  dismissed: "acknowledged",
  cancelled: "cancelled",
};

export function DeliveryLogPanel() {
  const { data: sent } = useReminders("sent");
  const { data: dismissed } = useReminders("dismissed");
  const { data: cancelled } = useReminders("cancelled");

  const entries = [...(sent?.items ?? []), ...(dismissed?.items ?? []), ...(cancelled?.items ?? [])]
    .sort((a, b) => b.updated_at.localeCompare(a.updated_at))
    .slice(0, 30);

  const lines = entries.map(
    (r) =>
      `${new Date(r.updated_at).toLocaleString()} — "${r.message}" ${STATUS_VERB[r.status] ?? r.status}`,
  );

  return (
    <NeonPanel>
      <h2 className="mb-4 border-b border-surface-container-highest pb-4 font-display text-title-md text-on-surface uppercase">
        Delivery Log
      </h2>
      <TerminalLog
        lines={lines.length > 0 ? lines : ["no delivery history yet"]}
        aria-label="Reminder delivery log"
      />
    </NeonPanel>
  );
}
