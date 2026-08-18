/**
 * Thin fetch wrapper for `/api/v1`. Cookies (httpOnly access/refresh tokens)
 * ride along via `credentials: "include"`; on a 401 the wrapper transparently
 * refreshes the session once (via `POST /auth/refresh`) and retries the
 * original request, so callers never have to think about token expiry.
 */

const API_BASE_URL: string = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

export class ApiError extends Error {
  constructor(
    public status: number,
    public body: unknown,
  ) {
    super(`API error ${status}`);
  }
}

// Requests that must NOT trigger a refresh-and-retry (refresh itself, and
// login/register where a 401/409 is a normal, user-facing outcome).
const NO_REFRESH_PATHS = new Set(["/auth/refresh", "/auth/login", "/auth/register"]);

// Dedupe concurrent refresh attempts — if five requests 401 at once, only
// one `/auth/refresh` call should fire.
let refreshInFlight: Promise<boolean> | null = null;

async function refreshSession(): Promise<boolean> {
  refreshInFlight ??= fetch(`${API_BASE_URL}/auth/refresh`, {
    method: "POST",
    credentials: "include",
  })
    .then((res) => res.ok)
    .catch(() => false)
    .finally(() => {
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

  const refreshed = await refreshSession();
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
