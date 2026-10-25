export class ApiError extends Error {
  /** @param {number} status @param {string} code @param {string} message */
  constructor(status, code, message) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

export const token = decodeURIComponent(location.pathname.split("/r/")[1] ?? "").replace(/\/$/, "");

/**
 * @param {string} path
 * @param {{method?: string, body?: BodyInit, json?: unknown, timeoutMs?: number}} [options]
 */
export async function api(path, options = {}) {
  const headers = { "x-round-token": token };
  let body = options.body;
  if (options.json !== undefined) {
    headers["content-type"] = "application/json";
    body = JSON.stringify(options.json);
  }
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), options.timeoutMs ?? 20000);
  let response;
  try {
    response = await fetch(`/api${path}`, {
      method: options.method ?? (body ? "POST" : "GET"),
      headers,
      body,
      signal: controller.signal,
    });
  } catch {
    throw new ApiError(0, "network", "Network nahi mila. Dobara bhejo.");
  } finally {
    clearTimeout(timer);
  }
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new ApiError(response.status, data.error ?? "error", data.message ?? "Kuch gadbad hui.");
  }
  return data;
}
