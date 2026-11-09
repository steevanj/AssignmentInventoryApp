import { api } from "../api.js";
import {
  calculateTotals, centsToText, escapeHtml, hideMessage, showError, showMessage, toCents, withBusyButton,
} from "../utils.js";

// Create a new Draft order or edit an existing one.
// Totals shown here are a live preview; the server recalculates and saves the real values.

export async function renderOrderForm(page, ctx, orderId) {
  page.innerHTML = `<p class="muted">Loading...</p>`;

  let customers, products, existingOrder = null;
  try {
    [customers, products] = await Promise.all([
      api("/customers/?page_size=100"),
      api("/products/?page_size=100"),
    ]);
    if (orderId) existingOrder = await api(`/orders/${orderId}/`);
  } catch (error) {
    page.innerHTML = `<div id="form-message"></div>`;
    showError(page.querySelector("#form-message"), error);
    return;
  }

  if (existingOrder && !existingOrder.is_editable) {
    window.location.hash = `#/orders/${orderId}`;
    return;
  }

  const productList = products.results;
  // rates already stored on an edited order stay as they are (same rule as the server)
  const storedRates = {};
  if (existingOrder) existingOrder.items.forEach((item) => { storedRates[item.product] = item.rate; });

  page.innerHTML = `
    <div class="page-header">
      <h2>${existingOrder ? `Edit draft ${escapeHtml(existingOrder.order_number)}` : "New sales order"}</h2>
      <a class="btn" href="${existingOrder ? `#/orders/${orderId}` : "#/orders"}">Back</a>
    </div>
    <form id="order-form" class="card" novalidate>
      <div class="form-grid">
        <label>Customer *
          <select name="customer">
            <option value="">-- choose a customer --</option>
            ${customers.results.map((c) => `<option value="${c.id}">${escapeHtml(c.name)}${c.city ? ` (${escapeHtml(c.city)})` : ""}</option>`).join("")}
          </select>
          <div class="field-error" data-error="customer"></div>
        </label>
        <label>Discount % (0 - 20)
          <input name="discount" type="number" min="0" max="20" step="0.01" value="0">
          <div class="field-error" data-error="discount"></div>
        </label>
      </div>

      <h3 style="margin-top:20px">Items</h3>
      <div class="table-wrap">
        <table>
          <thead><tr>
            <th style="width:38%">Product</th><th>Price / stock</th><th style="width:110px">Quantity</th>
            <th class="right">Amount</th><th></th>
          </tr></thead>
          <tbody id="item-rows"></tbody>
        </table>
      </div>
      <div class="field-error" data-error="items"></div>
      <button type="button" id="add-row" class="btn btn-small" style="margin-top:8px">+ Add item</button>

      <table class="totals-table">
        <tr><td>Subtotal</td><td class="right" id="subtotal">0.00</td></tr>
        <tr><td>Discount</td><td class="right" id="discount-amount">0.00</td></tr>
        <tr class="grand"><td>Grand total</td><td class="right" id="grand-total">0.00</td></tr>
      </table>
      <p class="muted right">Totals are a preview. The server calculates the final values.</p>

      <div id="form-message" class="message hidden"></div>
      <div class="form-actions">
        <button type="submit" id="save-button" class="btn btn-primary">Save draft</button>
      </div>
    </form>`;

  const form = page.querySelector("#order-form");
  const rowsBody = page.querySelector("#item-rows");
  const message = page.querySelector("#form-message");

  // ---------- rows ----------

  function addRow(productId = "", quantity = 1) {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>
        <select class="product-select">
          <option value="">-- choose a product --</option>
          ${productList.map((p) => `<option value="${p.id}">${escapeHtml(p.product_code)} - ${escapeHtml(p.name)}</option>`).join("")}
        </select>
        <div class="field-error row-error"></div>
      </td>
      <td class="product-info"><span class="muted">-</span></td>
      <td><input class="quantity-input" type="number" min="1" step="1" value="${quantity}" style="width:90px"></td>
      <td class="right amount">0.00</td>
      <td class="right"><button type="button" class="btn btn-small remove-row" title="Remove">Remove</button></td>`;
    row.dataset.rateCents = "0";
    rowsBody.appendChild(row);

    if (productId) {
      row.querySelector(".product-select").value = String(productId);
      loadProductInfo(row);
    }
    recalculate();
  }

  // Product selection: fetch the product to show its current price and stock.
  async function loadProductInfo(row) {
    const productId = row.querySelector(".product-select").value;
    const info = row.querySelector(".product-info");
    row.dataset.rateCents = "0";
    row.dataset.stock = "";

    if (!productId) {
      info.innerHTML = `<span class="muted">-</span>`;
      recalculate();
      return;
    }

    info.innerHTML = `<span class="muted">Loading...</span>`;
    try {
      const product = await api(`/products/${productId}/`);
      const rate = storedRates[product.id] ?? product.price;
      row.dataset.rateCents = String(toCents(rate));
      row.dataset.stock = String(product.stock_quantity);
      const rateNote = storedRates[product.id] && storedRates[product.id] !== product.price
        ? ` <span class="muted">(order rate; current price ${centsToText(toCents(product.price))})</span>` : "";
      info.innerHTML = `${centsToText(toCents(rate))}${rateNote}<br><span class="stock-hint">In stock: ${product.stock_quantity}</span>`;
    } catch (error) {
      info.innerHTML = `<span class="field-error">${escapeHtml(error.message)}</span>`;
    }
    recalculate();
  }

  // ---------- live calculation + validation ----------

  function readRows() {
    return [...rowsBody.querySelectorAll("tr")].map((row) => ({
      row,
      productId: row.querySelector(".product-select").value,
      quantityText: row.querySelector(".quantity-input").value.trim(),
      rateCents: Number(row.dataset.rateCents || 0),
      stock: row.dataset.stock === "" || row.dataset.stock === undefined ? null : Number(row.dataset.stock),
    }));
  }

  function isWholePositive(text) {
    return /^\d+$/.test(text) && Number(text) >= 1;
  }

  function recalculate() {
    const rows = readRows();
    const discount = Number(form.discount.value) || 0;
    const totals = calculateTotals(
      rows.map((r) => ({ quantity: isWholePositive(r.quantityText) ? Number(r.quantityText) : 0, rateCents: r.rateCents })),
      discount >= 0 && discount <= 20 ? discount : 0,
    );

    rows.forEach((r, index) => {
      r.row.querySelector(".amount").textContent = centsToText(totals.lineAmounts[index]);
      const hint = r.row.querySelector(".stock-hint");
      if (hint && r.stock !== null) {
        const short = isWholePositive(r.quantityText) && Number(r.quantityText) > r.stock;
        hint.classList.toggle("low", short);
        hint.textContent = short ? `In stock: ${r.stock} - not enough to confirm` : `In stock: ${r.stock}`;
      }
    });
    page.querySelector("#subtotal").textContent = centsToText(totals.subtotal);
    page.querySelector("#discount-amount").textContent = centsToText(totals.discount);
    page.querySelector("#grand-total").textContent = centsToText(totals.grandTotal);
  }

  function setFieldError(name, text) {
    page.querySelector(`[data-error="${name}"]`).textContent = text || "";
  }

  // Returns the payload, or null when something needs fixing.
  function validate() {
    let valid = true;
    setFieldError("customer", "");
    setFieldError("discount", "");
    setFieldError("items", "");
    form.customer.classList.remove("invalid");
    form.discount.classList.remove("invalid");

    if (!form.customer.value) {
      setFieldError("customer", "Choose a customer.");
      form.customer.classList.add("invalid");
      valid = false;
    }

    const discountText = form.discount.value.trim();
    const discount = Number(discountText);
    if (discountText === "" || Number.isNaN(discount) || discount < 0 || discount > 20) {
      setFieldError("discount", "Discount must be a number from 0 to 20.");
      form.discount.classList.add("invalid");
      valid = false;
    }

    const rows = readRows();
    if (!rows.length) {
      setFieldError("items", "Add at least one item.");
      valid = false;
    }

    const seen = new Set();
    rows.forEach((r) => {
      const select = r.row.querySelector(".product-select");
      const qty = r.row.querySelector(".quantity-input");
      const error = r.row.querySelector(".row-error");
      select.classList.remove("invalid");
      qty.classList.remove("invalid");
      error.textContent = "";

      if (!r.productId) {
        error.textContent = "Choose a product.";
        select.classList.add("invalid");
        valid = false;
      } else if (seen.has(r.productId)) {
        error.textContent = "This product is already in the order. Change the quantity instead.";
        select.classList.add("invalid");
        valid = false;
      }
      seen.add(r.productId);

      if (!isWholePositive(r.quantityText)) {
        error.textContent += (error.textContent ? " " : "") + "Quantity must be a whole number of at least 1.";
        qty.classList.add("invalid");
        valid = false;
      }
    });

    if (!valid) return null;
    return {
      customer: Number(form.customer.value),
      discount_percentage: discountText,
      items: rows.map((r) => ({ product: Number(r.productId), quantity: Number(r.quantityText) })),
    };
  }

  // ---------- events ----------

  page.querySelector("#add-row").addEventListener("click", () => addRow());
  form.discount.addEventListener("input", recalculate);

  rowsBody.addEventListener("change", (event) => {
    if (event.target.classList.contains("product-select")) loadProductInfo(event.target.closest("tr"));
  });
  rowsBody.addEventListener("input", (event) => {
    if (event.target.classList.contains("quantity-input")) recalculate();
  });
  rowsBody.addEventListener("click", (event) => {
    if (event.target.classList.contains("remove-row")) {
      event.target.closest("tr").remove();
      recalculate();
    }
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    hideMessage(message);
    const payload = validate();
    if (!payload) {
      showMessage(message, "Please fix the highlighted fields.", "error");
      return;
    }

    await withBusyButton(page.querySelector("#save-button"), async () => {
      try {
        const saved = existingOrder
          ? await api(`/orders/${orderId}/`, { method: "PUT", body: payload })
          : await api("/orders/", { method: "POST", body: payload });
        window.location.hash = `#/orders/${saved.id}`;
        ctx.notify(`Draft ${saved.order_number} saved. Grand total ${centsToText(toCents(saved.grand_total))}.`);
      } catch (error) {
        showError(message, error); // server-side validation messages
      }
    }, "Saving...");
  });

  // ---------- initial state ----------

  if (existingOrder) {
    form.customer.value = String(existingOrder.customer);
    form.discount.value = Number(existingOrder.discount_percentage);
    existingOrder.items.forEach((item) => addRow(item.product, item.quantity));
    if (!form.customer.value) {
      showMessage(message, "The customer on this order is no longer active. Choose another customer.", "info");
    }
  } else {
    addRow();
  }
}
