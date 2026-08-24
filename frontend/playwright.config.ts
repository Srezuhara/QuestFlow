import { defineConfig, devices } from "@playwright/test";

/**
 * Drives the already-running Dockerized stack at localhost:5173 — no
 * `webServer` block. Starting Vite on the host would run against a second,
 * divergent `node_modules` and still couldn't start the API or Postgres.
 * `globalSetup` checks the stack is actually up before any test runs.
 */
export default defineConfig({
  testDir: "./e2e",
  // One shared Postgres; serial keeps XP and leaderboard assertions deterministic.
  fullyParallel: false,
  workers: 1,
  retries: 0,
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:5173",
    trace: "retain-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  globalSetup: "./e2e/global-setup.ts",
});
