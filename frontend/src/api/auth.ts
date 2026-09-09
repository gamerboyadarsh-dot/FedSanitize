/**
 * FedSanitize Auth — Frontend Helper
 * ====================================
 * Drop-in companion to `backend_api/auth/`. Merge this file into
 * `frontend/src/api/`, then update `frontend/src/api/client.ts` to call
 * `authFetch(...)` instead of the bare `fetch(...)` it uses today.
 *
 * Usage:
 *
 *   import { loginAdmin, loginClient, logout, authFetch } from "./auth";
 *
 *   // On your login screen:
 *   await loginAdmin(username, password);
 *   // or, for an edge client:
 *   await loginClient(clientId, clientSecret);
 *
 *   // Everywhere else, instead of `fetch(url, opts)`:
 *   const res = await authFetch(url, opts);
 */

const API_BASE = "http://127.0.0.1:8000";
const STORAGE_KEY = "fedsanitize_auth";

export interface StoredAuth {
  accessToken: string;
  refreshToken: string;
  role: "admin" | "client";
  clientId?: string;
}

function readAuth(): StoredAuth | null {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as StoredAuth;
  } catch {
    return null;
  }
}

function writeAuth(auth: StoredAuth): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(auth));
}

export function getAuth(): StoredAuth | null {
  return readAuth();
}

export function logout(): void {
  localStorage.removeItem(STORAGE_KEY);
}

export function getRole(): "admin" | "client" | null {
  return readAuth()?.role ?? null;
}

export function isAuthenticated(): boolean {
  return readAuth() !== null;
}

export async function fetchMe(): Promise<{ subject: string; role: string; client_id?: string; auth_type: string } | null> {
  try {
    const res = await authFetch(`${API_BASE}/auth/me`);
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

/** Admin login — username/password (OAuth2 form-encoded, per FastAPI's OAuth2PasswordRequestForm). */
export async function loginAdmin(username: string, password: string): Promise<void> {
  const body = new URLSearchParams({ username, password });
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
  if (!res.ok) {
    throw new Error((await safeErrorDetail(res)) ?? "Login failed");
  }
  const data = await res.json();
  writeAuth({
    accessToken: data.access_token,
    refreshToken: data.refresh_token,
    role: data.role,
  });
}

/** Edge-client login — client_id + shared secret. */
export async function loginClient(clientId: string, clientSecret: string): Promise<void> {
  const res = await fetch(`${API_BASE}/auth/client-login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ client_id: clientId, client_secret: clientSecret }),
  });
  if (!res.ok) {
    throw new Error((await safeErrorDetail(res)) ?? "Login failed");
  }
  const data = await res.json();
  writeAuth({
    accessToken: data.access_token,
    refreshToken: data.refresh_token,
    role: data.role,
    clientId: data.client_id,
  });
}

async function safeErrorDetail(res: Response): Promise<string | undefined> {
  try {
    const data = await res.json();
    return data?.detail;
  } catch {
    return undefined;
  }
}

async function refreshAccessToken(): Promise<boolean> {
  const auth = readAuth();
  if (!auth) return false;

  const res = await fetch(`${API_BASE}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: auth.refreshToken }),
  });
  if (!res.ok) {
    logout();
    return false;
  }
  const data = await res.json();
  writeAuth({ ...auth, accessToken: data.access_token });
  return true;
}

/**
 * Drop-in replacement for `fetch()` that attaches the stored access
 * token and retries once (after a silent refresh) on a 401.
 */
export async function authFetch(input: RequestInfo, init: RequestInit = {}): Promise<Response> {
  const auth = readAuth();
  const headers = new Headers(init.headers);
  if (auth) {
    headers.set("Authorization", `Bearer ${auth.accessToken}`);
  }

  let res = await fetch(input, { ...init, headers });

  if (res.status === 401 && auth) {
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      const retryAuth = readAuth();
      const retryHeaders = new Headers(init.headers);
      if (retryAuth) {
        retryHeaders.set("Authorization", `Bearer ${retryAuth.accessToken}`);
      }
      res = await fetch(input, { ...init, headers: retryHeaders });
    }
  }

  return res;
}
