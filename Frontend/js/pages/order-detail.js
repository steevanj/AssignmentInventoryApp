import { api } from "../api.js";
import { escapeHtml, formatDateTime, formatMoney, showError, withBusyButton } from "../utils.js";

export async function renderOrderDetail(page, ctx, orderId) {
  page.innerHTML = `<p class="muted">Loading order...</p>`;

  let order;
  try {
    order = await api(`/orders/${orderId}/`);
  } catch (error) {
    page.innerHTML = `<div id="detail-message"></div><a href="#/orders">Back to orders</a>`;
    showError(page.querySelector("#detail-message"), error);
    return;
  }

  draw(page, ctx, order);
}

function draw(page, ctx, order) {
  const items = order.items.map((item) => `
    <tr>
      <td>${escapeHtml(item.product_code)}</td>
      <td>${escapeHtml(item.product_name)}</td>
      <td class="right">${item.quantity}</td>
      <td class="right">${formatMoney(item.rate)}</td>
      <td class="right">${formatMoney(item.amount)}</td>
    </tr>`).join("");

  const canConfirm = order.status === "DRAFT";
  const canCancel = order.status !== "CANCELLED";

  page.innerHTML = `
    <div class="page-header">
      <h2>Order ${escapeHtml(order.order_number)}
        <span class="badge badge-${escapeHtml(order.status)}">${escapeHtml(order.status_display)}</span>
      </h2>
      <a href="#/orders" class="btn">Back to orders</a>
    </div>
    <div id="detail-message" class="message hidden"></div>

    <div class="card">
      <div class="form-grid">
        <div><label>Customer</label><div>${escapeHtml(order.customer_name)}</div></div>
        <div><label>Order date</label><div>${escapeHtml(order.order_date)}</div></div>
        <div><label>Created by</label><div>${escapeHtml(order.created_by_name)}</div></div>
        ${order.confirmed_at ? `<div><label>Confirmed</label><div>${formatDateTime(order.confirmed_at)}</div></div>` : ""}
        ${order.cancelled_at ? `<div><label>Cancelled</label><div>${formatDateTime(order.cancelled_at)}</div></div>` : ""}
      </div>
    </div>

    <div class="card">
      <div class="table-wrap">
        <table>
          <thead><tr><th>Code</th><th>Product</th><th class="right">Qty</th><th class="right">Rate</th><th class="right">Amount</th></tr></thead>
          <tbody>${items}</tbody>
        </table>
      </div>
      <table class="totals-table">
        <tr><td>Subtotal</td><td class="right">${formatMoney(order.subtotal)}</td></tr>
        <tr><td>Discount (${Number(order.discount_percentage)}%)</td><td class="right">- ${formatMoney(order.discount_amount)}</td></tr>
        <tr class="grand"><td>Grand total</td><td class="right">${formatMoney(order.grand_total)}</td></tr>
      </table>

      <div class="form-actions">
        ${order.is_editable ? `<a class="btn" href="#/orders/${order.id}/edit">Edit draft</a>` : ""}
        ${canConfirm ? `<button id="confirm-button" class="btn btn-success">Confirm order</button>` : ""}
        ${canCancel ? `<button id="cancel-button" class="btn btn-danger">Cancel order</button>` : ""}
        ${!order.is_editable ? `<span class="muted">This order is ${escapeHtml(order.status_display.toLowerCase())} and can no longer be edited.</span>` : ""}
      </div>
    </div>`;

  const message = page.querySelector("#detail-message");

  const confirmButton = page.querySelector("#confirm-button");
  if (confirmButton) {
    confirmButton.addEventListener("click", () =>
      changeStatus(page, ctx, order, "confirm", confirmButton, message,
        `Confirm order ${order.order_number}? Stock will be deducted and the order can no longer be edited.`)
    );
  }

  const cancelButton = page.querySelector("#cancel-button");
  if (cancelButton) {
    const warning = order.status === "CONFIRMED"
      ? `Cancel order ${order.order_number}? The deducted stock will be put back.`
      : `Cancel draft order ${order.order_number}?`;
    cancelButton.addEventListener("click", () =>
      changeStatus(page, ctx, order, "cancel", cancelButton, message, warning)
    );
  }
}

async function changeStatus(page, ctx, order, action, button, message, question) {
  if (!window.confirm(question)) return;

  await withBusyButton(button, async () => {
    try {
      const result = await api(`/orders/${order.id}/${action}/`, { method: "POST" });
      draw(page, ctx, result.order);
      ctx.notify(result.message);
    } catch (error) {
      showError(message, error);
    }
  }, action === "confirm" ? "Confirming..." : "Cancelling...");
}
