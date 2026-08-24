/**
 * Probes the API and web servers before any test runs. Without this, a
 * stopped stack surfaces as a generic 30s navigation timeout on the first
 * test — this converts that into an instant, actionable message.
 */
export default async function globalSetup(): Promise<void> {
  const apiBase = (process.env.E2E_API_BASE_URL ?? "http://localhost:8000").replace(/\/$/, "");
  const webBase = (process.env.E2E_BASE_URL ?? "http://localhost:5173").replace(/\/$/, "");

  const checks = [
    { name: "API", url: `${apiBase}/health` },
    { name: "web", url: `${webBase}/` },
  ];

  for (const { name, url } of checks) {
    try {
      const response = await fetch(url, { signal: AbortSignal.timeout(5_000) });
      if (!response.ok) {
        throw new Error(`${name} responded ${response.status}`);
      }
    } catch {
      throw new Error("QuestFlow stack is not running — run `make up` first.");
    }
  }
}
