/**
 * Hand-rolled service worker (D7-9 in PHASE_7_8_9_PLAN.md) — not
 * vite-plugin-pwa/Workbox, which exists to precache a *built* asset graph;
 * in Docker the app is dev-served by Vite, where precaching the module
 * graph is actively harmful. This file is served verbatim at `/sw.js`
 * (correct root scope) in both dev and build with zero config, and does
 * exactly two things: show a push notification, and route a click on it.
 */

self.addEventListener("push", (event) => {
  let data = {};
  try {
    data = event.data ? event.data.json() : {};
  } catch {
    data = { message: event.data ? event.data.text() : "" };
  }

  const title = "QuestFlow";
  const body = data.message || "You have a new notification.";
  const url = data.url || "/reminders";

  event.waitUntil(
    (async () => {
      await self.registration.showNotification(title, {
        body,
        icon: "/icon-192.png",
        badge: "/badge-72.png",
        tag: data.reminder_id || "questflow-notification",
        data: { url },
      });

      // Let any open tab know immediately, so the notification centre and
      // unread badge update without waiting for the 60s poll (D7-11).
      const clientsList = await self.clients.matchAll({
        type: "window",
        includeUncontrolled: true,
      });
      for (const client of clientsList) {
        client.postMessage({ type: "questflow-notification" });
      }
    })(),
  );
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const url = (event.notification.data && event.notification.data.url) || "/reminders";

  event.waitUntil(
    (async () => {
      const clientsList = await self.clients.matchAll({
        type: "window",
        includeUncontrolled: true,
      });
      const target = new URL(url, self.location.origin).href;

      for (const client of clientsList) {
        if (client.url.startsWith(self.location.origin) && "focus" in client) {
          await client.focus();
          if ("navigate" in client) {
            await client.navigate(target);
          }
          return;
        }
      }
      await self.clients.openWindow(target);
    })(),
  );
});

// Best-effort re-subscribe if the push service rotates the subscription
// (e.g. after a browser update). Not covered by tests — this event is not
// reproducible in jsdom/unit tests, only manually against a real browser.
self.addEventListener("pushsubscriptionchange", (event) => {
  event.waitUntil(
    (async () => {
      try {
        const options = event.oldSubscription
          ? {
              applicationServerKey: event.oldSubscription.options.applicationServerKey,
              userVisibleOnly: true,
            }
          : undefined;
        if (options) {
          await self.registration.pushManager.subscribe(options);
        }
      } catch {
        // Nothing we can do from here without the app's VAPID key context;
        // the next foreground visit's `enablePush()` re-subscribe covers it.
      }
    })(),
  );
});
