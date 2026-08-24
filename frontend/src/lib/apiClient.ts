/**
 * Thin fetch wrapper for `/api/v1`. Cookies (httpOnly access/refresh tokens)
 * ride along via `credentials: "include"`; on a 401 the wrapper transparently
 * refreshes the session once (via `POST /auth/refresh`) and retries the
 * original request, so callers never have to think about token expiry.
 */

const API_BASE_URL: string = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

export class ApiError extends Error {
  /** From the RFC 7807 problem+json envelope's `request_id`, when present
   * (existing consumers read `body.detail`, which is unchanged by that
   * envelope — this is purely additive). */
  public requestId: string | null;

  constructor(
    public status: number,
    public body: unknown,
  ) {
    super(`API error ${status}`);
    const maybeRequestId = (body as { request_id?: unknown } | null)?.request_id;
    this.requestId = typeof maybeRequestId === "string" ? maybeRequestId : null;
  }
}

// Requests that must NOT trigger a refresh-and-retry (refresh itself, and
// login/register where a 401/409 is a normal, user-facing outcome).
const NO_REFRESH_PATHS = new Set(["/auth/refresh", "/auth/login", "/auth/register"]);

// Dedupe concurrent refresh attempts *within this tab* — if five requests
// 401 at once, only one `/auth/refresh` call should fire.
let refreshInFlight: Promise<boolean> | null = null;

const REFRESH_LOCK_NAME = "questflow-auth-refresh";

async function doRefresh(): Promise<boolean> {
  return fetch(`${API_BASE_URL}/auth/refresh`, {
    method: "POST",
    credentials: "include",
  })
    .then((res) => res.ok)
    .catch(() => false);
}

/**
 * Two tabs (or a React StrictMode double-mount) can both have access cookies
 * expire around the same time and both call this. Without cross-tab
 * coordination they'd race to POST /auth/refresh with the same raw refresh
 * token — the loser trips the backend's reuse-detection chain-kill (mitigated
 * server-side by a grace window, but avoiding the race in the first place is
 * cheaper and faster). `navigator.locks` serializes refreshes across tabs in
 * browsers that support it (Chrome/Edge/Firefox/Safari 15.4+); elsewhere we
 * fall back to the in-context dedupe alone.
 */
async function refreshSession(probe: () => Promise<boolean>): Promise<boolean> {
  if (refreshInFlight) {
    return refreshInFlight;
  }

  const run = async (): Promise<boolean> => {
    // Inside the lock: another tab may have already refreshed while we were
    // waiting for it. Re-checking with the original request first is the
    // cheapest correct way to find out — cheaper than an extra endpoint, and
    // it avoids burning this tab's refresh token unnecessarily.
    if (await probe()) {
      return true;
    }
    return doRefresh();
  };

  const requestLock = navigator.locks?.request.bind(navigator.locks) as
    ((name: string, callback: () => Promise<boolean>) => Promise<boolean>) | undefined;

  refreshInFlight = (requestLock ? requestLock(REFRESH_LOCK_NAME, run) : run()).finally(() => {
    refreshInFlight = null;
  });
  return refreshInFlight;
}

async function rawFetch(path: string, init?: RequestInit): Promise<Response> {
  return fetch(`${API_BASE_URL}${path}`, {
    credentials: "include",
    ...init,
  });
}

export async function apiFetch(path: string, init?: RequestInit): Promise<Response> {
  const response = await rawFetch(path, init);

  if (response.status !== 401 || NO_REFRESH_PATHS.has(path)) {
    return response;
  }

  // The probe re-issues the original request to check whether another tab's
  // refresh already landed. Only safe for GET/HEAD — replaying a mutation as
  // a "probe" would double-apply it (on top of the retry below).
  const method = (init?.method ?? "GET").toUpperCase();
  const canProbe = method === "GET" || method === "HEAD";
  const refreshed = await refreshSession(
    canProbe ? async () => (await rawFetch(path, init)).ok : async () => false,
  );
  if (!refreshed) {
    return response;
  }
  return rawFetch(path, init);
}

/** JSON convenience wrapper — throws `ApiError` on non-2xx. */
export async function apiJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await apiFetch(path, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new ApiError(response.status, body);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}
