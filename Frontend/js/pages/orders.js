import { api } from "../api.js";
import { buildQuery, escapeHtml, formatMoney, paginationHtml, showError } from "../utils.js";

export function renderOrders(page, ctx) {
  const filters = { status: "", search: "", date_from: "", date_to: "", page: 1 };

  page.innerHTML = `
    <div class="page-header">
      <h2>${ctx.isAdmin ? "All orders" : "My orders"}</h2>
      <a class="btn btn-primary" href="#/orders/new">+ New order</a>
    </div>
    <div class="card">
      <form id="order-filters" class="filters">
        <label>Search<input name="search" placeholder="Order no. or customer"></label>
        <label>Status
          <select name="status">
            <option value="">All</option>
            <option value="DRAFT">Draft</option>
            <option value="CONFIRMED">Confirmed</option>
            <option value="CANCELLED">Cancelled</option>
          </select>
        </label>
        <label>From<input type="date" name="date_from"></label>
        <label>To<input type="date" name="date_to"></label>
        <button class="btn" type="submit">Apply</button>
      </form>
      <div id="orders-message" class="message hidden"></div>
      <div id="orders-table" class="table-wrap"><p class="muted">Loading...</p></div>
    </div>`;

  const form = page.querySelector("#order-filters");
  const tableBox = page.querySelector("#orders-table");
  const message = page.querySelector("#orders-message");

  async function load() {
    try {
      const data = await api("/orders/" + buildQuery(filters));
      tableBox.innerHTML = tableHtml(data.results, ctx) + paginationHtml(data, filters.page);
    } catch (error) {
      tableBox.innerHTML = "";
      showError(message, error);
    }
  }

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    Object.assign(filters, Object.fromEntries(new FormData(form)), { page: 1 });
    message.className = "message hidden";
    load();
  });

  tableBox.addEventListener("click", (event) => {
    const button = event.target.closest("[data-page]");
    if (button) {
      filters.page = Number(button.dataset.page);
      load();
    }
  });

  load();
}

function tableHtml(orders, ctx) {
  if (!orders.length) return `<p class="muted">No orders found.</p>`;
  const rows = orders.map((order) => `
    <tr>
      <td><a href="#/orders/${order.id}">${escapeHtml(order.order_number)}</a></td>
      <td>${escapeHtml(order.order_date)}</td>
      <td>${escapeHtml(order.customer_name)}</td>
      ${ctx.isAdmin ? `<td>${escapeHtml(order.created_by_name)}</td>` : ""}
      <td><span class="badge badge-${escapeHtml(order.status)}">${escapeHtml(order.status_display)}</span></td>
      <td class="right">${formatMoney(order.grand_total)}</td>
    </tr>`).join("");
  return `
    <table>
      <thead><tr>
        <th>Order no.</th><th>Date</th><th>Customer</th>${ctx.isAdmin ? "<th>Created by</th>" : ""}
        <th>Status</th><th class="right">Grand total</th>
      </tr></thead>
      <tbody>${rows}</tbody>
    </table>`;
}
