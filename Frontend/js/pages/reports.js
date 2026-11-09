import { api } from "../api.js";
import { buildQuery, escapeHtml, formatDateTime, formatMoney, paginationHtml, showError, showMessage, withBusyButton } from "../utils.js";

export function renderReports(page) {
  page.innerHTML = `
    <div class="page-header"><h2>Reports</h2><span class="muted">Sales figures include Confirmed orders only.</span></div>

    <div class="card">
      <h3>Customer sales summary</h3>
      <form id="customer-sales-form" class="filters">
        <label>From<input type="date" name="date_from"></label>
        <label>To<input type="date" name="date_to"></label>
        <button class="btn btn-primary" type="submit">Run</button>
      </form>
      <div id="customer-sales-result"></div>
    </div>

    <div class="card">
      <h3>Product sales summary</h3>
      <form id="product-sales-form" class="filters">
        <label>From<input type="date" name="date_from"></label>
        <label>To<input type="date" name="date_to"></label>
        <button class="btn btn-primary" type="submit">Run</button>
      </form>
      <div id="product-sales-result"></div>
    </div>

    <div class="card">
      <h3>Low stock</h3>
      <form id="low-stock-form" class="filters">
        <label>Stock below<input type="number" name="threshold" min="0" step="1" value="10" style="width:100px"></label>
        <button class="btn btn-primary" type="submit">Run</button>
      </form>
      <div id="low-stock-result"></div>
    </div>

    <div class="card">
      <h3>Stock movement history</h3>
      <form id="movement-form" class="filters">
        <label>Type
          <select name="movement_type">
            <option value="">All</option>
            <option value="OPENING">Opening stock</option>
            <option value="ADJUSTMENT_IN">Manual increase</option>
            <option value="ADJUSTMENT_OUT">Manual decrease</option>
            <option value="SALE">Order confirmed</option>
            <option value="SALE_REVERSAL">Order cancelled</option>
          </select>
        </label>
        <label>From<input type="date" name="date_from"></label>
        <label>To<input type="date" name="date_to"></label>
        <button class="btn btn-primary" type="submit">Run</button>
      </form>
      <div id="movement-result"></div>
    </div>`;

  setupReport(page, "#customer-sales-form", "#customer-sales-result", "/reports/customer-sales/", customerSalesHtml);
  setupReport(page, "#product-sales-form", "#product-sales-result", "/reports/product-sales/", productSalesHtml);
  setupReport(page, "#low-stock-form", "#low-stock-result", "/reports/low-stock/", lowStockHtml, (params) => {
    if (!/^\d+$/.test(params.threshold || "")) return "Enter a whole number threshold (0 or more).";
    return null;
  });
  setupReport(page, "#movement-form", "#movement-result", "/reports/stock-movements/", movementHtml, null, true);
}

function setupReport(page, formSelector, resultSelector, path, render, validate = null, paginated = false) {
  const form = page.querySelector(formSelector);
  const result = page.querySelector(resultSelector);
  let params = {};

  async function run(button) {
    const task = async () => {
      try {
        const data = await api(path + buildQuery(params));
        result.innerHTML = render(data) + (paginated ? paginationHtml(data, params.page || 1) : "");
      } catch (error) {
        result.innerHTML = `<div class="message"></div>`;
        showError(result.firstChild, error);
      }
    };
    return button ? withBusyButton(button, task, "Running...") : task();
  }

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    params = Object.fromEntries(new FormData(form));
    if (params.date_from && params.date_to && params.date_from > params.date_to) {
      result.innerHTML = `<div class="message"></div>`;
      showMessage(result.firstChild, "The end date cannot be before the start date.", "error");
      return;
    }
    const problem = validate ? validate(params) : null;
    if (problem) {
      result.innerHTML = `<div class="message"></div>`;
      showMessage(result.firstChild, problem, "error");
      return;
    }
    params.page = 1;
    run(form.querySelector("button"));
  });

  result.addEventListener("click", (event) => {
    const button = event.target.closest("[data-page]");
    if (button) {
      params.page = Number(button.dataset.page);
      run();
    }
  });
}

function emptyOr(rows, html) {
  return rows.length ? html : `<p class="muted">No data for this selection.</p>`;
}

function customerSalesHtml(data) {
  const rows = data.results.map((r) => `
    <tr class="${r.is_active ? "" : "inactive"}">
      <td>${escapeHtml(r.name)}</td><td>${escapeHtml(r.city)}</td>
      <td class="right">${r.confirmed_order_count}</td><td class="right">${formatMoney(r.total_sales)}</td>
    </tr>`).join("");
  return emptyOr(data.results, `
    <div class="table-wrap"><table>
      <thead><tr><th>Customer</th><th>City</th><th class="right">Confirmed orders</th><th class="right">Sales after discount</th></tr></thead>
      <tbody>${rows}</tbody>
      <tfoot><tr><td colspan="2">Total</td><td class="right">${data.total_orders}</td><td class="right">${formatMoney(data.total_sales)}</td></tr></tfoot>
    </table></div>`);
}

function productSalesHtml(data) {
  const rows = data.results.map((r) => `
    <tr><td>${escapeHtml(r.product_code)}</td><td>${escapeHtml(r.name)}</td><td>${escapeHtml(r.category)}</td>
      <td class="right">${r.quantity_sold}</td><td class="right">${formatMoney(r.gross_sales)}</td></tr>`).join("");
  return emptyOr(data.results, `
    <div class="table-wrap"><table>
      <thead><tr><th>Code</th><th>Product</th><th>Category</th><th class="right">Qty sold</th><th class="right">Gross value (before discount)</th></tr></thead>
      <tbody>${rows}</tbody>
    </table></div>`);
}

function lowStockHtml(data) {
  const rows = data.results.map((r) => `
    <tr><td>${escapeHtml(r.product_code)}</td><td>${escapeHtml(r.name)}</td><td>${escapeHtml(r.category)}</td>
      <td class="right">${r.stock_quantity}</td></tr>`).join("");
  return emptyOr(data.results, `
    <div class="table-wrap"><table>
      <thead><tr><th>Code</th><th>Product</th><th>Category</th><th class="right">Stock</th></tr></thead>
      <tbody>${rows}</tbody>
    </table></div>`);
}

function movementHtml(data) {
  const rows = data.results.map((m) => `
    <tr>
      <td class="nowrap">${formatDateTime(m.created_at)}</td>
      <td>${escapeHtml(m.product_code)}</td>
      <td>${escapeHtml(m.movement_type_display)}</td>
      <td class="right">${m.quantity_change > 0 ? "+" : ""}${m.quantity_change}</td>
      <td class="right">${m.stock_after}</td>
      <td>${m.order_number ? `<a href="#/orders/${m.related_order}">${escapeHtml(m.order_number)}</a>` : ""}</td>
      <td>${escapeHtml(m.reason)}</td>
      <td>${escapeHtml(m.created_by_name)}</td>
    </tr>`).join("");
  return emptyOr(data.results, `
    <div class="table-wrap"><table>
      <thead><tr><th>When</th><th>Product</th><th>Type</th><th class="right">Change</th><th class="right">Stock after</th>
        <th>Order</th><th>Reason</th><th>By</th></tr></thead>
      <tbody>${rows}</tbody>
    </table></div>`);
}
