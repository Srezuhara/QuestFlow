/**
 * Web Push helpers. `enablePush()` must only ever be called from a click
 * handler — Chrome penalises and Safari hard-blocks a non-gesture
 * `Notification.requestPermission()` prompt. Registration alone
 * (`registerServiceWorker`) triggers no prompt, so it's safe to call at
 * app load.
 */

const VAPID_PUBLIC_KEY: string | undefined = import.meta.env.VITE_VAPID_PUBLIC_KEY;

/** Converts a URL-safe base64 VAPID public key into the `Uint8Array` the
 * Push API's `applicationServerKey` expects. */
export function urlBase64ToUint8Array(base64String: string): Uint8Array<ArrayBuffer> {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
  const rawData = atob(base64);
  const outputArray = new Uint8Array(new ArrayBuffer(rawData.length));
  for (let i = 0; i < rawData.length; i++) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

export async function registerServiceWorker(): Promise<ServiceWorkerRegistration | null> {
  if (!("serviceWorker" in navigator)) return null;
  try {
    return await navigator.serviceWorker.register("/sw.js");
  } catch {
    return null;
  }
}

export type PermissionState = "unsupported" | "default" | "granted" | "denied";

export function getPermissionState(): PermissionState {
  if (typeof Notification === "undefined") return "unsupported";
  return Notification.permission as PermissionState;
}

/** Only ever call this from a click handler. Requests permission (if not
 * already decided), subscribes via the Push API, and returns the raw
 * subscription for the caller to POST to `/push/subscriptions`. Returns
 * `null` if permission was denied, push isn't supported, or no VAPID key is
 * configured. */
export async function enablePush(): Promise<PushSubscription | null> {
  if (!("serviceWorker" in navigator) || !("PushManager" in window)) return null;
  if (!VAPID_PUBLIC_KEY) return null;

  const permission = await Notification.requestPermission();
  if (permission !== "granted") return null;

  const registration = await navigator.serviceWorker.ready;
  return registration.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY),
  });
}

export async function disablePush(): Promise<void> {
  if (!("serviceWorker" in navigator)) return;
  const registration = await navigator.serviceWorker.ready;
  const subscription = await registration.pushManager.getSubscription();
  await subscription?.unsubscribe();
}

/** Wires the service worker's `postMessage({type: "questflow-notification"})`
 * (sent on every incoming push, see `public/sw.js`) to a callback — used to
 * invalidate the notification queries immediately instead of waiting for the
 * 60s poll (D7-11). Returns an unsubscribe function. */
export function onNotificationMessage(cb: () => void): () => void {
  if (!("serviceWorker" in navigator)) return () => {};
  const handler = (event: MessageEvent) => {
    if (event.data?.type === "questflow-notification") cb();
  };
  navigator.serviceWorker.addEventListener("message", handler);
  return () => navigator.serviceWorker.removeEventListener("message", handler);
}
