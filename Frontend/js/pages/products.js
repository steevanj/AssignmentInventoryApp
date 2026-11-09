import { api } from "../api.js";
import {
  buildQuery, escapeHtml, formatMoney, hideMessage, paginationHtml, showError, showMessage, withBusyButton,
} from "../utils.js";

export async function renderProducts(page, ctx) {
  const filters = { search: "", category: "", status: "active", page: 1 };

  page.innerHTML = `
    <div class="page-header">
      <h2>Products</h2>
      ${ctx.isAdmin ? `
      <div class="form-actions" style="margin:0">
        <button id="new-product" class="btn btn-primary">+ New product</button>
        <button id="open-import" class="btn">Import CSV</button>
      </div>` : ""}
    </div>

    ${ctx.isAdmin ? adminPanelsHtml() : ""}

    <div class="card">
      <form id="product-filters" class="filters">
        <label>Search<input name="search" placeholder="Code or name"></label>
        <label>Category<select name="category"><option value="">All</option></select></label>
        ${ctx.isAdmin ? `
        <label>Status
          <select name="status">
            <option value="active">Active</option><option value="inactive">Inactive</option><option value="all">All</option>
          </select>
        </label>` : ""}
        <button class="btn" type="submit">Search</button>
      </form>
      <div id="product-message" class="message hidden"></div>
      <div id="product-table" class="table-wrap"><p class="muted">Loading...</p></div>
    </div>`;

  const listMessage = page.querySelector("#product-message");
  const tableBox = page.querySelector("#product-table");
  let products = [];

  async function loadCategories() {
    try {
      const data = await api("/products/categories/");
      const select = page.querySelector("#product-filters [name=category]");
      select.innerHTML = `<option value="">All</option>` +
        data.categories.map((c) => `<option value="${escapeHtml(c)}">${escapeHtml(c)}</option>`).join("");
      select.value = filters.category;
    } catch (error) {
      showError(listMessage, error);
    }
  }

  async function load() {
    try {
      const data = await api("/products/" + buildQuery(filters));
      products = data.results;
      tableBox.innerHTML = tableHtml(products, ctx) + paginationHtml(data, filters.page);
    } catch (error) {
      showError(listMessage, error);
    }
  }

  page.querySelector("#product-filters").addEventListener("submit", (event) => {
    event.preventDefault();
    Object.assign(filters, Object.fromEntries(new FormData(event.target)), { page: 1 });
    load();
  });

  tableBox.addEventListener("click", async (event) => {
    const pageButton = event.target.closest("[data-page]");
    if (pageButton) {
      filters.page = Number(pageButton.dataset.page);
      load();
      return;
    }
    const button = event.target.closest("[data-action]");
    if (!button) return;
    const product = products.find((p) => String(p.id) === button.dataset.id);

    if (button.dataset.action === "edit") admin.openProductForm(product);
    if (button.dataset.action === "adjust") admin.openAdjustForm(product);
    if (button.dataset.action === "delete") {
      if (!window.confirm(`Delete product ${product.product_code}? This cannot be undone.`)) return;
      await withBusyButton(button, async () => {
        try {
          await api(`/products/${product.id}/`, { method: "DELETE" });
          ctx.notify("Product deleted.");
          load();
        } catch (error) {
          showError(listMessage, error); // 409 when used in orders or stock history
        }
      });
    }
  });

  const refresh = () => { loadCategories(); load(); };
  const admin = ctx.isAdmin ? setupAdminPanels(page, ctx, refresh) : {};

  await loadCategories();
  load();
}

function tableHtml(products, ctx) {
  if (!products.length) return `<p class="muted">No products found.</p>`;
  const rows = products.map((p) => `
    <tr class="${p.is_active ? "" : "inactive"}">
      <td>${escapeHtml(p.product_code)}</td>
      <td>${escapeHtml(p.name)}</td>
      <td>${escapeHtml(p.category)}</td>
      <td class="right">${formatMoney(p.price)}</td>
      <td class="right">${p.stock_quantity}</td>
      <td>${p.is_active ? "Active" : "Inactive"}</td>
      ${ctx.isAdmin ? `
      <td class="nowrap">
        <button class="btn btn-small" data-action="edit" data-id="${p.id}">Edit</button>
        <button class="btn btn-small" data-action="adjust" data-id="${p.id}">Adjust stock</button>
        <button class="btn btn-small btn-danger" data-action="delete" data-id="${p.id}">Delete</button>
      </td>` : ""}
    </tr>`).join("");
  return `
    <table>
      <thead><tr><th>Code</th><th>Name</th><th>Category</th><th class="right">Price</th><th class="right">Stock</th>
      <th>Status</th>${ctx.isAdmin ? "<th></th>" : ""}</tr></thead>
      <tbody>${rows}</tbody>
    </table>`;
}

// ---------------------------------------------------------------------------
// Admin only: product form, stock adjustment and CSV import
// ---------------------------------------------------------------------------

function adminPanelsHtml() {
  return `
    <form id="product-form" class="card hidden" novalidate>
      <h3 id="product-form-title">New product</h3>
      <input type="hidden" name="id">
      <div class="form-grid">
        <label>Product code *<input name="product_code" maxlength="30"></label>
        <label>Name *<input name="name" maxlength="150"></label>
        <label>Category *<input name="category" maxlength="100"></label>
        <label>Price *<input name="price" type="number" min="0" step="0.01"></label>
        <label id="opening-stock-label">Opening stock<input name="stock_quantity" type="number" min="0" step="1" value="0"></label>
        <label>Status
          <select name="is_active"><option value="true">Active</option><option value="false">Inactive</option></select>
        </label>
      </div>
      <p id="stock-note" class="muted hidden">Stock can't be edited here. Use "Adjust stock" so the change is recorded.</p>
      <div id="product-form-message" class="message hidden"></div>
      <div class="form-actions">
        <button type="submit" class="btn btn-primary">Save</button>
        <button type="button" class="btn" data-close="product-form">Close</button>
      </div>
    </form>

    <form id="adjust-form" class="card hidden" novalidate>
      <h3 id="adjust-title">Adjust stock</h3>
      <input type="hidden" name="product">
      <div class="form-grid">
        <label>Change (+ to add, - to remove) *<input name="quantity_change" type="number" step="1"></label>
        <label>Reason *<input name="reason" maxlength="255" placeholder="e.g. Damaged, stock count"></label>
      </div>
      <div id="adjust-message" class="message hidden"></div>
      <div class="form-actions">
        <button type="submit" class="btn btn-primary">Save adjustment</button>
        <button type="button" class="btn" data-close="adjust-form">Close</button>
      </div>
    </form>

    <form id="import-form" class="card hidden" novalidate>
      <h3>Import products from CSV</h3>
      <p class="muted">Columns: product_code, product_name, category, price, stock_quantity, status (Active/Inactive).
        If any row has an error, nothing is imported.</p>
      <input type="file" name="file" accept=".csv">
      <div id="import-message" class="message hidden"></div>
      <div class="form-actions">
        <button type="submit" class="btn btn-primary">Upload</button>
        <button type="button" class="btn" data-close="import-form">Close</button>
      </div>
    </form>`;
}

function setupAdminPanels(page, ctx, refresh) {
  const productForm = page.querySelector("#product-form");
  const adjustForm = page.querySelector("#adjust-form");
  const importForm = page.querySelector("#import-form");

  function hideAll() {
    [productForm, adjustForm, importForm].forEach((f) => f.classList.add("hidden"));
  }

  page.querySelectorAll("[data-close]").forEach((button) =>
    button.addEventListener("click", () => page.querySelector(`#${button.dataset.close}`).classList.add("hidden"))
  );

  // ----- add / edit product -----

  function openProductForm(product) {
    hideAll();
    productForm.reset();
    hideMessage(page.querySelector("#product-form-message"));
    productForm.id.value = product ? product.id : "";
    page.querySelector("#product-form-title").textContent = product ? `Edit ${product.product_code}` : "New product";
    page.querySelector("#opening-stock-label").classList.toggle("hidden", Boolean(product));
    page.querySelector("#stock-note").classList.toggle("hidden", !product);
    if (product) {
      productForm.product_code.value = product.product_code;
      productForm.name.value = product.name;
      productForm.category.value = product.category;
      productForm.price.value = product.price;
      productForm.is_active.value = String(product.is_active);
    }
    productForm.classList.remove("hidden");
  }

  productForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const message = page.querySelector("#product-form-message");
    const id = productForm.id.value;
    const problems = [];
    ["product_code", "name", "category"].forEach((field) => {
      const empty = !productForm[field].value.trim();
      productForm[field].classList.toggle("invalid", empty);
      if (empty) problems.push(`${field.replace("_", " ")} is required.`);
    });
    const price = productForm.price.value.trim();
    if (price === "" || Number(price) < 0) problems.push("Price must be 0 or more.");
    const stock = productForm.stock_quantity.value.trim();
    if (!id && !/^\d+$/.test(stock)) problems.push("Opening stock must be a whole number, 0 or more.");
    if (problems.length) {
      showMessage(message, "Please fix the following:", "error", problems);
      return;
    }

    const body = {
      product_code: productForm.product_code.value.trim(),
      name: productForm.name.value.trim(),
      category: productForm.category.value.trim(),
      price,
      is_active: productForm.is_active.value === "true",
    };
    if (!id) body.stock_quantity = Number(stock);

    await withBusyButton(productForm.querySelector("[type=submit]"), async () => {
      try {
        await api(id ? `/products/${id}/` : "/products/", { method: id ? "PUT" : "POST", body });
        productForm.classList.add("hidden");
        ctx.notify(id ? "Product updated." : "Product created.");
        refresh();
      } catch (error) {
        showError(message, error);
      }
    }, "Saving...");
  });

  // ----- stock adjustment -----

  function openAdjustForm(product) {
    hideAll();
    adjustForm.reset();
    hideMessage(page.querySelector("#adjust-message"));
    adjustForm.product.value = product.id;
    page.querySelector("#adjust-title").textContent =
      `Adjust stock - ${product.product_code} (current stock: ${product.stock_quantity})`;
    adjustForm.classList.remove("hidden");
    adjustForm.quantity_change.focus();
  }

  adjustForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const message = page.querySelector("#adjust-message");
    const change = adjustForm.quantity_change.value.trim();
    const reason = adjustForm.reason.value.trim();
    const problems = [];
    if (!/^-?\d+$/.test(change) || Number(change) === 0) problems.push("Change must be a whole number other than 0.");
    if (!reason) problems.push("A reason is required.");
    if (problems.length) {
      showMessage(message, "Please fix the following:", "error", problems);
      return;
    }

    await withBusyButton(adjustForm.querySelector("[type=submit]"), async () => {
      try {
        const result = await api("/inventory/adjustments/", {
          method: "POST",
          body: { product: Number(adjustForm.product.value), quantity_change: Number(change), reason },
        });
        adjustForm.classList.add("hidden");
        ctx.notify(`Stock updated. ${result.movement.product_code} now has ${result.movement.stock_after}.`);
        refresh();
      } catch (error) {
        showError(message, error);
      }
    }, "Saving...");
  });

  // ----- CSV import -----

  page.querySelector("#new-product").addEventListener("click", () => openProductForm(null));
  page.querySelector("#open-import").addEventListener("click", () => {
    hideAll();
    importForm.reset();
    hideMessage(page.querySelector("#import-message"));
    importForm.classList.remove("hidden");
  });

  importForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const message = page.querySelector("#import-message");
    const file = importForm.file.files[0];
    if (!file) {
      showMessage(message, "Choose a CSV file first.", "error");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    await withBusyButton(importForm.querySelector("[type=submit]"), async () => {
      try {
        const result = await api("/products/import/", { method: "POST", form: formData });
        showMessage(message, result.message, "success", result.product_codes);
        refresh();
      } catch (error) {
        const rowLines = error.rowErrors.map((r) => `Row ${r.row}: ${r.errors.join(" ")}`);
        showMessage(message, error.message, "error", rowLines);
      }
    }, "Uploading...");
  });

  return { openProductForm, openAdjustForm };
}
