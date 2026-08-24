import { expect, test } from "./fixtures";

/**
 * The canonical e2e spec (PHASE_8_9_PLAN.md §9.1.5). Proves the whole
 * auth -> task -> XP -> level path against the real stack — nothing else in
 * the suite does, since unit tests mock `fetch` and can't catch a broken
 * cookie-refresh dance or a reconciliation that never happens.
 *
 * Two deliberate deviations from the plan's literal wording, discovered
 * while writing this against the actual app rather than assumed from the
 * plan text:
 *
 * 1. Task **creation** is not optimistic (`useCreateTask` only invalidates
 *    on success — unlike `useCompleteTask`/`useUncompleteTask`, which are).
 *    So there is no "optimistic insert, before any refetch" moment to
 *    assert for step 3; the test asserts the quest appears after the real
 *    round trip instead, which Playwright's auto-retrying locators handle
 *    for free.
 * 2. There is no literal "DONE" state ever rendered for a completed task.
 *    `TaskItem` is only rendered from the Dashboard's "Daily Objectives"
 *    panel, which the backend (`dashboard_service.get_dashboard`) filters
 *    to **active** tasks only — and the optimistic patch in
 *    `useCompleteTask` touches the `tasks.all` query cache, not
 *    `dashboard.root`, so the dashboard's own copy of the task is never
 *    optimistically flipped either. What is genuinely observable, and what
 *    this test asserts instead, is: the task disappears from Daily
 *    Objectives once the real completion round-trips (proving the backend
 *    state changed), and the sidebar level/XP figures update via
 *    `applyGamificationResult` on the same round trip.
 */
test("register -> create quest -> complete -> level up -> reload persists -> ledger shows it", async ({
  player,
}) => {
  const { page } = player;

  // 1. Register -> LVL 1, capture the XP bar's accessible label.
  await expect(page.getByText(/^LVL 1\b/)).toBeVisible();
  const xpBarLabel = page.getByText(/XP TO NEXT LEVEL/);
  await expect(xpBarLabel).toBeVisible();

  async function createAndCompleteQuest(title: string): Promise<void> {
    // 2. Open the New Quest modal.
    await page.getByRole("button", { name: "New Quest" }).click();

    // 3. Submit a quest -> assert it appears (see deviation 1 above: the
    // real round trip, not an optimistic insert, since task creation isn't
    // optimistic in this codebase).
    await page.getByLabel("Objective").fill(title);
    await page.getByRole("button", { name: "Deploy Quest" }).click();
    await expect(page.getByRole("heading", { name: title, exact: true })).toBeVisible();

    // 4. Complete it -> confirm -> assert it leaves Daily Objectives (see
    // deviation 2 above) and the XP label changed.
    const heading = page.getByRole("heading", { name: title, exact: true });
    const row = page.locator("div", { has: heading }).first();
    await row.getByRole("button", { name: "Mark complete" }).click();
    await page.getByRole("button", { name: "Confirm" }).click();
    await expect(heading).toHaveCount(0);
  }

  const beforeXp = await xpBarLabel.textContent();

  // 5. Complete quests in a bounded loop (max 15) until the sidebar level
  // text changes -> assert the level-up toast. Bounded-loop-until-observed
  // rather than a hardcoded count, since the leveling curve is server-side.
  let leveledUp = false;
  for (let i = 0; i < 15 && !leveledUp; i++) {
    await createAndCompleteQuest(`E2E Quest ${i}`);
    leveledUp = !(await page.getByText(/^LVL 1\b/).isVisible());
  }
  expect(leveledUp).toBe(true);
  await expect(page.getByRole("status")).toContainText("Level Up");

  await expect(xpBarLabel).not.toHaveText(beforeXp ?? "");
  const levelLocator = page.getByText(/^LVL \d+\b/);
  const levelAfterCompletion = await levelLocator.textContent();

  // 6. Reload and assert the XP total persisted — the load-bearing
  // assertion. An optimistic update that never reconciles is invisible to
  // every unit test in the suite and is exactly the class of bug e2e exists
  // to catch.
  await page.reload();
  await expect(levelLocator).toHaveText(levelAfterCompletion ?? "");

  // 7. /progress shows the award as the newest ledger row.
  await page.goto("/progress");
  const newestRow = page.locator("ul li").first();
  await expect(newestRow).toContainText("TASK COMPLETE");

  // 8. Teardown deletes the account (automatic, via the `player` fixture).
});
