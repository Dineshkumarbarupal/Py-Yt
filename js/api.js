const API_BASE = "/api/v1";

export async function apiRequest(path, options = {}) {
  const headers = new Headers(options.headers || {});
  if (options.body && !(options.body instanceof FormData)) headers.set("Content-Type", "application/json");
  const response = await fetch(`${API_BASE}${path}`, {
    credentials: "same-origin",
    ...options,
    headers,
  });
  const payload = response.status === 204 ? null : await response.json().catch(() => null);
  if (!response.ok) {
    const message = payload?.detail || payload?.message || `Request failed (${response.status})`;
    throw new Error(typeof message === "string" ? message : "The request could not be completed.");
  }
  return payload;
}
