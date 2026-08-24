import { test as base } from "@playwright/test";
import type { Page } from "@playwright/test";

export interface Player {
  page: Page;
  email: string;
  handle: string;
}

const API_BASE_URL = (process.env.E2E_API_BASE_URL ?? "http://localhost:8000").replace(/\/$/, "");

/**
 * IMPORTANT: e2e runs against the **dev** database `questflow`, not
 * `questflow_test` — the API container is wired to `questflow`, and the test
 * DB's conftest teardown wipes *all* users, which would destroy dev data.
 * That is precisely why cleanup here is per-test (DELETE /auth/me) and never
 * a global truncate. The dev DB has data the developer cares about.
 */
export const test = base.extend<{ player: Player }>({
  player: async ({ page }, use) => {
    const id = crypto.randomUUID();
    const email = `e2e+${id}@example.com`;
    const handle = `e2e${id.slice(0, 8)}`;

    await page.goto("/register");
    await page.getByLabel("Display name").fill("E2E Player");
    await page.getByLabel("Handle").fill(handle);
    await page.getByLabel("Email").fill(email);
    await page.getByLabel("Password").fill("correct-horse-battery-staple");
    await page.getByRole("button", { name: "Register" }).click();
    await page.waitForURL("/");

    await use({ page, email, handle });

    // Teardown runs even when the test fails. `page.request` inherits the
    // browser context's cookie jar, so this is authenticated.
    await page.request.delete(`${API_BASE_URL}/api/v1/auth/me`);
  },
});

export { expect } from "@playwright/test";
