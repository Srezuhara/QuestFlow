import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { enablePush, getPermissionState } from "@/lib/push";
import { queryKeys } from "@/lib/queryKeys";
import {
  cancelReminder,
  createPushSubscription,
  createReminder,
  deletePushSubscription,
  dismissReminder,
  fetchPushPublicKey,
  fetchPushSubscriptions,
  fetchReminders,
  type ReminderCreate,
  type ReminderPageOut,
  type ReminderStatus,
} from "./api";

export function useReminders(status?: ReminderStatus) {
  return useQuery({
    queryKey: queryKeys.reminders.list(status),
    queryFn: () => fetchReminders(status ? { status, limit: 100 } : { limit: 100 }),
  });
}

export function useCreateReminder() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: ReminderCreate) => createReminder(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.reminders.all });
    },
  });
}

interface DismissContext {
  previous: ReminderPageOut | undefined;
}

/** Optimistic dismiss — flips status in the cached list immediately, rolls
 * back on error, reconciled via invalidation on settle. */
export function useDismissReminder() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (reminderId: string) => dismissReminder(reminderId),
    onMutate: async (reminderId): Promise<DismissContext> => {
      await queryClient.cancelQueries({ queryKey: queryKeys.reminders.all });
      const previous = queryClient.getQueryData<ReminderPageOut>(
        queryKeys.reminders.list(undefined),
      );
      if (previous) {
        queryClient.setQueryData<ReminderPageOut>(queryKeys.reminders.list(undefined), {
          ...previous,
          items: previous.items.map((r) =>
            r.id === reminderId ? { ...r, status: "dismissed" as const } : r,
          ),
        });
      }
      return { previous };
    },
    onError: (_err, _id, context) => {
      if (context?.previous) {
        queryClient.setQueryData(queryKeys.reminders.list(undefined), context.previous);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.reminders.all });
    },
  });
}

export function useCancelReminder() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (reminderId: string) => cancelReminder(reminderId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.reminders.all });
    },
  });
}

export function usePushSubscriptions() {
  return useQuery({
    queryKey: queryKeys.push.subscriptions,
    queryFn: fetchPushSubscriptions,
  });
}

export function usePushPublicKey() {
  return useQuery({
    queryKey: queryKeys.push.publicKey,
    queryFn: fetchPushPublicKey,
    staleTime: Infinity,
  });
}

export function useEnablePush() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      if (getPermissionState() === "denied") {
        // enablePush() no-ops on denied permission (the browser can't be
        // re-prompted programmatically) — surface that explicitly rather
        // than silently doing nothing.
        throw new Error("Notification permission was denied in browser settings.");
      }
      const subscription = await enablePush();
      if (!subscription) {
        throw new Error("Could not enable push notifications.");
      }
      const json = subscription.toJSON();
      return createPushSubscription({
        endpoint: subscription.endpoint,
        p256dh: json.keys?.p256dh ?? "",
        auth: json.keys?.auth ?? "",
        user_agent: navigator.userAgent,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.push.subscriptions });
    },
  });
}

export function useRevokePushSubscription() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (subscriptionId: string) => deletePushSubscription(subscriptionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.push.subscriptions });
    },
  });
}
