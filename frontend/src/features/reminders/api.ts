import { apiJson } from "@/lib/apiClient";
import type { components } from "@/types/api";

export type ReminderOut = components["schemas"]["ReminderOut"];
export type ReminderPageOut = components["schemas"]["ReminderPageOut"];
export type ReminderCreate = components["schemas"]["ReminderCreate"];
export type ReminderStatus = components["schemas"]["ReminderStatus"];
export type PushSubscriptionOut = components["schemas"]["PushSubscriptionOut"];
export type PublicKeyOut = components["schemas"]["PublicKeyOut"];

export function fetchReminders(params: { status?: ReminderStatus; limit?: number } = {}) {
  const qs = new URLSearchParams();
  if (params.status) qs.set("status", params.status);
  qs.set("limit", String(params.limit ?? 50));
  return apiJson<ReminderPageOut>(`/reminders?${qs.toString()}`);
}

export function createReminder(data: ReminderCreate): Promise<ReminderOut> {
  return apiJson<ReminderOut>("/reminders", { method: "POST", body: JSON.stringify(data) });
}

export function dismissReminder(reminderId: string): Promise<ReminderOut> {
  return apiJson<ReminderOut>(`/reminders/${reminderId}/dismiss`, { method: "POST" });
}

export function cancelReminder(reminderId: string): Promise<void> {
  return apiJson<void>(`/reminders/${reminderId}`, { method: "DELETE" });
}

export function fetchPushSubscriptions(): Promise<PushSubscriptionOut[]> {
  return apiJson<PushSubscriptionOut[]>("/push/subscriptions");
}

export function createPushSubscription(sub: {
  endpoint: string;
  p256dh: string;
  auth: string;
  user_agent?: string | null;
}): Promise<PushSubscriptionOut> {
  return apiJson<PushSubscriptionOut>("/push/subscriptions", {
    method: "POST",
    body: JSON.stringify(sub),
  });
}

export function deletePushSubscription(subscriptionId: string): Promise<void> {
  return apiJson<void>(`/push/subscriptions/${subscriptionId}`, { method: "DELETE" });
}

export function fetchPushPublicKey(): Promise<PublicKeyOut> {
  return apiJson<PublicKeyOut>("/push/public-key");
}
