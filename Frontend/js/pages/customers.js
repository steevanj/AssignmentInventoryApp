import { api } from "../api.js";
import { buildQuery, escapeHtml, hideMessage, paginationHtml, showError, withBusyButton } from "../utils.js";

export function renderCustomers(page, ctx) {
  const filters = { search: "", status: "active", page: 1 };

  page.innerHTML = `
    <div class="page-header">
      <h2>Customers</h2>
      ${ctx.isAdmin ? `<button id="new-customer" class="btn btn-primary">+ New customer</button>` : ""}
    </div>

    <form id="customer-form" class="card hidden" novalidate>
      <h3 id="customer-form-title">New customer</h3>
      <input type="hidden" name="id">
      <div class="form-grid">
        <label>Name *<input name="name" maxlength="150"></label>
        <label>Email<input name="email" type="email"></label>
        <label>Mobile<input name="mobile" placeholder="e.g. 9876543210"></label>
        <label>City<input name="city"></label>
        <label>Status
          <select name="is_active"><option value="true">Active</option><option value="false">Inactive</option></select>
        </label>
      </div>
      <div id="customer-form-message" class="message hidden"></div>
      <div class="form-actions">
        <button type="submit" class="btn btn-primary">Save</button>
        <button type="button" id="customer-form-close" class="btn">Close</button>
      </div>
    </form>

    <div class="card">
      <form id="customer-filters" class="filters">
        <label>Search<input name="search" placeholder="Name, email or mobile"></label>
        ${ctx.isAdmin ? `
        <label>Status
          <select name="status">
            <option value="active">Active</option><option value="inactive">Inactive</option><option value="all">All</option>
          </select>
        </label>` : ""}
        <button class="btn" type="submit">Search</button>
      </form>
      <div id="customer-message" class="message hidden"></div>
      <div id="customer-table" class="table-wrap"><p class="muted">Loading...</p></div>
    </div>`;

  const form = page.querySelector("#customer-form");
  const formMessage = page.querySelector("#customer-form-message");
  const listMessage = page.querySelector("#customer-message");
  const tableBox = page.querySelector("#customer-table");
  let customers = [];

  async function load() {
    try {
      const data = await api("/customers/" + buildQuery(filters));
      customers = data.results;
      tableBox.innerHTML = tableHtml(customers, ctx) + paginationHtml(data, filters.page);
    } catch (error) {
      showError(listMessage, error);
    }
  }

  function openForm(customer) {
    hideMessage(formMessage);
    form.reset();
    form.id.value = customer ? customer.id : "";
    page.querySelector("#customer-form-title").textContent = customer ? `Edit ${customer.name}` : "New customer";
    if (customer) {
      form.name.value = customer.name;
      form.email.value = customer.email;
      form.mobile.value = customer.mobile;
      form.city.value = customer.city;
      form.is_active.value = String(customer.is_active);
    }
    form.classList.remove("hidden");
    form.name.focus();
  }

  page.querySelector("#customer-filters").addEventListener("submit", (event) => {
    event.preventDefault();
    Object.assign(filters, Object.fromEntries(new FormData(event.target)), { page: 1 });
    load();
  });

  if (ctx.isAdmin) {
    page.querySelector("#new-customer").addEventListener("click", () => openForm(null));
    page.querySelector("#customer-form-close").addEventListener("click", () => form.classList.add("hidden"));

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      if (!form.name.value.trim()) {
        form.name.classList.add("invalid");
        showError(formMessage, { message: "Customer name is required." });
        return;
      }
      form.name.classList.remove("invalid");

      const body = {
        name: form.name.value.trim(),
        email: form.email.value.trim(),
        mobile: form.mobile.value.trim(),
        city: form.city.value.trim(),
        is_active: form.is_active.value === "true",
      };
      const id = form.id.value;

      await withBusyButton(form.querySelector("[type=submit]"), async () => {
        try {
          await api(id ? `/customers/${id}/` : "/customers/", { method: id ? "PUT" : "POST", body });
          form.classList.add("hidden");
          ctx.notify(id ? "Customer updated." : "Customer created.");
          load();
        } catch (error) {
          showError(formMessage, error);
        }
      }, "Saving...");
    });
  }

  tableBox.addEventListener("click", async (event) => {
    const pageButton = event.target.closest("[data-page]");
    if (pageButton) {
      filters.page = Number(pageButton.dataset.page);
      load();
      return;
    }

    const button = event.target.closest("[data-action]");
    if (!button) return;
    const customer = customers.find((c) => String(c.id) === button.dataset.id);

    if (button.dataset.action === "edit") openForm(customer);

    if (button.dataset.action === "toggle") {
      await withBusyButton(button, async () => {
        try {
          await api(`/customers/${customer.id}/`, { method: "PATCH", body: { is_active: !customer.is_active } });
          ctx.notify(`${customer.name} is now ${customer.is_active ? "inactive" : "active"}.`);
          load();
        } catch (error) {
          showError(listMessage, error);
        }
      });
    }

    if (button.dataset.action === "delete") {
      if (!window.confirm(`Delete customer "${customer.name}"? This cannot be undone.`)) return;
      await withBusyButton(button, async () => {
        try {
          await api(`/customers/${customer.id}/`, { method: "DELETE" });
          ctx.notify("Customer deleted.");
          load();
        } catch (error) {
          showError(listMessage, error); // e.g. 409 when the customer has orders
        }
      });
    }
  });

  load();
}

function tableHtml(customers, ctx) {
  if (!customers.length) return `<p class="muted">No customers found.</p>`;
  const rows = customers.map((c) => `
    <tr class="${c.is_active ? "" : "inactive"}">
      <td>${escapeHtml(c.name)}</td>
      <td>${escapeHtml(c.email)}</td>
      <td>${escapeHtml(c.mobile)}</td>
      <td>${escapeHtml(c.city)}</td>
      <td>${c.is_active ? "Active" : "Inactive"}</td>
      ${ctx.isAdmin ? `
      <td class="nowrap">
        <button class="btn btn-small" data-action="edit" data-id="${c.id}">Edit</button>
        <button class="btn btn-small" data-action="toggle" data-id="${c.id}">${c.is_active ? "Deactivate" : "Activate"}</button>
        <button class="btn btn-small btn-danger" data-action="delete" data-id="${c.id}">Delete</button>
      </td>` : ""}
    </tr>`).join("");
  return `
    <table>
      <thead><tr><th>Name</th><th>Email</th><th>Mobile</th><th>City</th><th>Status</th>${ctx.isAdmin ? "<th></th>" : ""}</tr></thead>
      <tbody>${rows}</tbody>
    </table>`;
}
