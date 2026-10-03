// Tokens stay in memory; closing/reloading the page requires signing in again.
let access = "";
let refresh = "";
let refreshing: Promise<boolean> | null = null;
export function setTokens(pair: {
  access_token: string;
  refresh_token: string;
}) {
  access = pair.access_token;
  refresh = pair.refresh_token;
}
export function clearTokens() {
  access = "";
  refresh = "";
}
export function signedIn() {
  return !!access;
}
async function renew() {
  if (!refresh) return false;
  refreshing ??= fetch("/api/v1/auth/refresh", {
    method: "POST",
    headers: { Authorization: `Bearer ${refresh}` },
  })
    .then(async (r) => {
      if (!r.ok) return false;
      access = (await r.json()).access_token;
      return true;
    })
    .finally(() => {
      refreshing = null;
    });
  return refreshing;
}
export async function api<T>(
  path: string,
  init: RequestInit = {},
  retry = true,
): Promise<T> {
  const response = await fetch("/api/v1" + path, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(access ? { Authorization: `Bearer ${access}` } : {}),
      ...init.headers,
    },
  });
  if (
    response.status === 401 &&
    retry &&
    !path.startsWith("/auth/") &&
    (await renew())
  )
    return api<T>(path, init, false);
  if (!response.ok) {
    let message = "Something went wrong. Please try again.";
    try {
      const data = await response.json();
      message =
        typeof data.detail === "string"
          ? data.detail
          : Array.isArray(data.detail)
            ? data.detail.map((e: { msg: string }) => e.msg).join(". ")
            : data.message || message;
    } catch {
      /* Keep the readable fallback for proxy errors. */
    }
    throw new Error(message);
  }
  return response.status === 204 ? (undefined as T) : response.json();
}
export const post = <T>(path: string, data: unknown) =>
  api<T>(path, { method: "POST", body: JSON.stringify(data) });
export const patch = <T>(path: string, data: unknown) =>
  api<T>(path, { method: "PATCH", body: JSON.stringify(data) });
export async function logout() {
  try {
    await Promise.allSettled(
      [access, refresh]
        .filter(Boolean)
        .map((token) =>
          fetch("/api/v1/auth/logout", {
            method: "POST",
            headers: { Authorization: `Bearer ${token}` },
          }),
        ),
    );
  } finally {
    clearTokens();
  }
}
