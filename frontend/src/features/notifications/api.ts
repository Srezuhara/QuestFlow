import { apiJson } from "@/lib/apiClient";
import type { components } from "@/types/api";

export type NotificationOut = components["schemas"]["NotificationOut"];
export type NotificationPageOut = components["schemas"]["NotificationPageOut"];
export type MarkAllReadResponse = components["schemas"]["MarkAllReadResponse"];

export function fetchNotifications(params: { unreadOnly?: boolean } = {}) {
  const qs = new URLSearchParams();
  if (params.unreadOnly) qs.set("unread_only", "true");
  const suffix = qs.toString() ? `?${qs.toString()}` : "";
  return apiJson<NotificationPageOut>(`/notifications${suffix}`);
}

export function markNotificationRead(notificationId: string): Promise<NotificationOut> {
  return apiJson<NotificationOut>(`/notifications/${notificationId}/read`, { method: "PATCH" });
}

export function markAllNotificationsRead(): Promise<MarkAllReadResponse> {
  return apiJson<MarkAllReadResponse>("/notifications/read-all", { method: "POST" });
}
