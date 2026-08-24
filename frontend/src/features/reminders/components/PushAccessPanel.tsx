import { useEffect, useState } from "react";
import { NeonButton, NeonPanel, StatusBadge } from "@/components/ui";
import { getPermissionState, type PermissionState } from "@/lib/push";
import { useEnablePush, usePushSubscriptions, useRevokePushSubscription } from "../hooks";

const STATUS_LABEL: Record<
  PermissionState,
  { level: "important" | "urgent" | "later"; text: string }
> = {
  granted: { level: "important", text: "ONLINE" },
  denied: { level: "urgent", text: "BLOCKED" },
  default: { level: "later", text: "OFFLINE" },
  unsupported: { level: "later", text: "UNSUPPORTED" },
};

/** The one PUSH ACCESS panel — reused verbatim on both the Reminders page
 * and the Settings page (D7-10). */
export function PushAccessPanel() {
  const [permission, setPermission] = useState<PermissionState>(getPermissionState);
  const { data: subscriptions } = usePushSubscriptions();
  const enablePush = useEnablePush();
  const revoke = useRevokePushSubscription();

  useEffect(() => {
    setPermission(getPermissionState());
  }, [subscriptions]);

  const status = STATUS_LABEL[permission];
  const canEnable = permission !== "denied" && permission !== "unsupported";

  return (
    <NeonPanel>
      <div className="mb-4 flex items-center justify-between border-b border-surface-container-highest pb-4">
        <h2 className="font-display text-title-md text-on-surface uppercase">Push Access</h2>
        <StatusBadge level={status.level}>{status.text}</StatusBadge>
      </div>

      <div className="flex flex-col gap-4">
        {permission === "denied" ? (
          <p className="font-body text-body-md text-on-surface-variant">
            Notifications were blocked in your browser settings. The app cannot re-prompt for
            permission — reset it from your browser&apos;s site settings for this page, then reload.
          </p>
        ) : (
          <NeonButton
            disabled={!canEnable || enablePush.isPending}
            onClick={() =>
              enablePush.mutate(undefined, {
                onSuccess: () => setPermission(getPermissionState()),
              })
            }
          >
            {enablePush.isPending ? "Enabling..." : "Enable Notifications"}
          </NeonButton>
        )}

        {enablePush.isError && (
          <p className="font-mono text-label-mono text-neon-pink">
            {enablePush.error instanceof Error
              ? enablePush.error.message
              : "Failed to enable push."}
          </p>
        )}

        <div className="flex flex-col gap-2">
          <p className="font-mono text-label-mono text-on-surface-variant uppercase">Devices</p>
          {(subscriptions ?? []).length === 0 && (
            <p className="font-mono text-label-mono text-on-surface-variant">
              &gt;&gt; no registered devices
            </p>
          )}
          {(subscriptions ?? []).map((sub) => (
            <div
              key={sub.id}
              className="flex items-center justify-between border border-outline-variant px-3 py-2"
            >
              <span className="truncate font-body text-body-md text-on-surface">
                {sub.user_agent ?? "Unknown device"}
              </span>
              <button
                type="button"
                onClick={() => revoke.mutate(sub.id)}
                className="font-mono text-label-mono text-neon-pink uppercase hover:underline"
              >
                Revoke
              </button>
            </div>
          ))}
        </div>
      </div>
    </NeonPanel>
  );
}
