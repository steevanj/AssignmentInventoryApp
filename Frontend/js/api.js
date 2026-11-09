// Small wrapper around fetch() for the Django REST API.
// - sends the session cookie (credentials: "include")
// - adds the CSRF token to every request that changes data
// - turns error responses into an ApiError with a readable message

export const API_BASE = `${window.location.protocol}//${window.location.hostname}:8000/api`;

let unauthorizedHandler = null;

export function onUnauthorized(handler) {
  unauthorizedHandler = handler;
}

export class ApiError extends Error {
  constructor(message, status, data) {
    super(message);
    this.status = status;
    this.details = data && data.details ? data.details : null;
    this.rowErrors = data && data.row_errors ? data.row_errors : [];
  }
}

function getCookie(name) {
  const match = document.cookie.split("; ").find((row) => row.startsWith(name + "="));
  return match ? decodeURIComponent(match.split("=")[1]) : "";
}

export async function api(path, { method = "GET", body, form } = {}) {
  const options = { method, credentials: "include", headers: {} };

  if (method !== "GET") {
    options.headers["X-CSRFToken"] = getCookie("csrftoken");
  }
  if (form) {
    options.body = form; // the browser sets the multipart Content-Type itself
  } else if (body !== undefined) {
    options.headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(body);
  }

  let response;
  try {
    response = await fetch(API_BASE + path, options);
  } catch (networkError) {
    throw new ApiError("Cannot reach the server. Is the backend running on port 8000?", 0, null);
  }

  const data = response.status === 204 ? null : await response.json().catch(() => null);

  if (!response.ok) {
    if (response.status === 401 && unauthorizedHandler && !path.startsWith("/auth/login")) {
      unauthorizedHandler();
    }
    const message = (data && data.error) || `Request failed (${response.status}).`;
    throw new ApiError(message, response.status, data);
  }
  return data;
}

// Turns DRF's nested "details" into flat lines like "items row 2 - quantity: Must be at least 1."
export function flattenErrorDetails(details, prefix = "") {
  if (!details) return [];
  if (typeof details === "string") return [prefix ? `${prefix}: ${details}` : details];
  if (Array.isArray(details)) {
    return details.flatMap((entry, index) => {
      if (typeof entry === "string") return [prefix ? `${prefix}: ${entry}` : entry];
      if (entry && Object.keys(entry).length === 0) return [];
      return flattenErrorDetails(entry, `${prefix} row ${index + 1}`.trim());
    });
  }
  return Object.entries(details).flatMap(([field, value]) =>
    flattenErrorDetails(value, prefix ? `${prefix} - ${field}` : field)
  );
}
