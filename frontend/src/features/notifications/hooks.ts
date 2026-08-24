import { useEffect } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { onNotificationMessage } from "@/lib/push";
import { queryKeys } from "@/lib/queryKeys";
import {
  fetchNotifications,
  markAllNotificationsRead,
  markNotificationRead,
  type NotificationPageOut,
} from "./api";

/** Polls at 60s + `refetchOnWindowFocus` (D7-11) — push users get instant
 * updates via `useNotificationSocketBridge`; this poll is the fallback for
 * permission-denied users and the initial paint. */
export function useNotifications(unreadOnly = false) {
  return useQuery({
    queryKey: [...queryKeys.notifications.all, unreadOnly] as const,
    queryFn: () => fetchNotifications({ unreadOnly }),
    refetchInterval: 60_000,
    refetchOnWindowFocus: true,
  });
}

interface MarkReadContext {
  previous: NotificationPageOut | undefined;
}

export function useMarkRead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (notificationId: string) => markNotificationRead(notificationId),
    onMutate: async (notificationId): Promise<MarkReadContext> => {
      await queryClient.cancelQueries({ queryKey: queryKeys.notifications.all });
      const previous = queryClient.getQueryData<NotificationPageOut>([
        ...queryKeys.notifications.all,
        false,
      ]);
      if (previous) {
        const now = new Date().toISOString();
        queryClient.setQueryData<NotificationPageOut>([...queryKeys.notifications.all, false], {
          ...previous,
          items: previous.items.map((n) =>
            n.id === notificationId ? { ...n, read_at: n.read_at ?? now } : n,
          ),
          unread_count: previous.items.some((n) => n.id === notificationId && !n.read_at)
            ? Math.max(0, previous.unread_count - 1)
            : previous.unread_count,
        });
      }
      return { previous };
    },
    onError: (_err, _id, context) => {
      if (context?.previous) {
        queryClient.setQueryData([...queryKeys.notifications.all, false], context.previous);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.notifications.all });
    },
  });
}

export function useMarkAllRead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => markAllNotificationsRead(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.notifications.all });
    },
  });
}

/** Wires the service worker's push-arrival message to an immediate
 * invalidation of the notification queries — mounted once in `AppShell`. */
export function useNotificationSocketBridge(): void {
  const queryClient = useQueryClient();
  useEffect(() => {
    return onNotificationMessage(() => {
      queryClient.invalidateQueries({ queryKey: queryKeys.notifications.all });
    });
  }, [queryClient]);
}
