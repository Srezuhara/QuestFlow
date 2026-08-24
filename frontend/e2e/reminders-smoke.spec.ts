import { expect, test } from "./fixtures";

/**
 * Discharges phase 7's unrun manual browser checklist (PHASE_8_9_PLAN.md
 * §9.1.6) — the reminders feature shipped with its walkthrough never
 * performed in that session.
 *
 * The bell-badge-increments-after-the-worker-tick assertion the plan
 * describes is **deliberately not included**, per the plan's own escape
 * hatch ("if that proves flaky ... drop the timing assertion and note in
 * PROGRESS.md"). Worked out before writing this: the worker ticks every 30s
 * (`app/workers/scheduler.py`) and `useNotifications` polls every 60s
 * (`refetchInterval: 60_000`) — worst case latency for the badge to reflect
 * a reminder that just fired is up to 90s, which makes a bounded assertion
 * either flaky or so long it isn't worth what it proves over the backend's
 * own live-verified worker test (`test_reminder_worker.py`) plus the
 * curl-driven smoke test already recorded in PROGRESS.md's phase 7 write-up.
 * This spec proves the browser-side surface instead: the page renders, the
 * Push Access panel resolves to *some* real permission state (not stuck
 * loading or crashed), and creating a reminder makes it appear in the
 * Upcoming list.
 *
 * Note on push permission: `context.grantPermissions(["notifications"])`
 * grants the Permissions API state, but headless Chromium's
 * `Notification.permission` was observed to still report "denied" here
 * (a documented headless quirk, not an app bug — verified against this
 * exact run: the panel renders "BLOCKED" even with the grant in place).
 * Asserting a specific state (e.g. "ONLINE") would therefore be asserting
 * on Chromium's headless behaviour, not this app's — so this only asserts
 * that the panel renders one of its four defined states.
 */
test("reminders page renders, reflects push permission, and lists a newly created reminder", async ({
  player,
}) => {
  const { page } = player;

  await page.context().grantPermissions(["notifications"]);
  await page.goto("/reminders");

  await expect(page.getByRole("heading", { name: "Upcoming" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Push Access" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Delivery Log" })).toBeVisible();

  await expect(page.getByText(/^(ONLINE|OFFLINE|BLOCKED|UNSUPPORTED)$/)).toBeVisible();

  await page.getByRole("button", { name: "New Reminder" }).click();
  await page.getByLabel("Message").fill("E2E smoke reminder");

  const soon = new Date(Date.now() + 60 * 60 * 1000);
  const localValue = new Date(soon.getTime() - soon.getTimezoneOffset() * 60_000)
    .toISOString()
    .slice(0, 16);
  await page.getByLabel("Remind At").fill(localValue);
  await page.getByRole("button", { name: "Schedule" }).click();

  await expect(page.getByText("Today")).toBeVisible();
  await expect(page.getByText("E2E smoke reminder")).toBeVisible();
});
