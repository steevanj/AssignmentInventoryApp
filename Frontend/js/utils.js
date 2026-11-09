import { flattenErrorDetails } from "./api.js";

export function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

// "4050.5" -> "4,050.50"
export function formatMoney(value) {
  const number = Number(value || 0);
  return number.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export function formatDateTime(value) {
  return value ? new Date(value).toLocaleString("en-IN") : "";
}

// ---------- live order calculation (preview only) ----------
// The backend recalculates everything and its numbers are the ones saved.
// Here we work in whole paise (cents) to avoid floating point errors and
// round half up, the same rule as the server.

export function toCents(amountText) {
  return Math.round(Number(amountText) * 100);
}

export function centsToText(cents) {
  return formatMoney(cents / 100);
}

export function calculateTotals(lines, discountPercentage) {
  const lineAmounts = lines.map((line) => line.quantity * line.rateCents);
  const subtotal = lineAmounts.reduce((sum, amount) => sum + amount, 0);
  const discount = Math.round((subtotal * discountPercentage) / 100);
  return { lineAmounts, subtotal, discount, grandTotal: subtotal - discount };
}

// ---------- messages ----------

export function showMessage(element, text, type = "info", detailLines = []) {
  if (!element) return;
  const list = detailLines.length
    ? `<ul>${detailLines.map((line) => `<li>${escapeHtml(line)}</li>`).join("")}</ul>`
    : "";
  element.className = `message message-${type}`;
  element.innerHTML = `${escapeHtml(text)}${list}`;
}

export function hideMessage(element) {
  if (element) element.className = "message hidden";
}

export function showError(element, error) {
  showMessage(element, error.message, "error", flattenErrorDetails(error.details));
}

// Disable a button while an async request runs, so it can't be submitted twice.
export async function withBusyButton(button, task, busyText = "Please wait...") {
  if (button.disabled) return;
  const originalText = button.textContent;
  button.disabled = true;
  button.textContent = busyText;
  try {
    return await task();
  } finally {
    button.disabled = false;
    button.textContent = originalText;
  }
}

export function buildQuery(params) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") query.set(key, value);
  });
  const text = query.toString();
  return text ? `?${text}` : "";
}

export function paginationHtml(data, page) {
  const pages = Math.max(1, Math.ceil(data.count / 20));
  return `
    <div class="pagination">
      <span class="muted">${data.count} record(s) - page ${page} of ${pages}</span>
      <button class="btn btn-small" data-page="${page - 1}" ${data.previous ? "" : "disabled"}>Previous</button>
      <button class="btn btn-small" data-page="${page + 1}" ${data.next ? "" : "disabled"}>Next</button>
    </div>`;
}
