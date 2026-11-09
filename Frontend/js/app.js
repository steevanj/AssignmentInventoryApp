import { api, onUnauthorized } from "./api.js";
import { renderCustomers } from "./pages/customers.js";
import { renderOrderDetail } from "./pages/order-detail.js";
import { renderOrderForm } from "./pages/order-form.js";
import { renderOrders } from "./pages/orders.js";
import { renderProducts } from "./pages/products.js";
import { renderReports } from "./pages/reports.js";
import { escapeHtml, hideMessage, showError, showMessage, withBusyButton } from "./utils.js";

const loginView = document.getElementById("login-view");
const appView = document.getElementById("app-view");
const page = document.getElementById("page");
const globalMessage = document.getElementById("global-message");

const state = { user: null };

// ---------- routing (#/orders, #/orders/5, #/orders/5/edit ...) ----------

const routes = [
  { pattern: /^#\/orders\/new$/, render: (ctx) => renderOrderForm(page, ctx, null) },
  { pattern: /^#\/orders\/(\d+)\/edit$/, render: (ctx, id) => renderOrderForm(page, ctx, id) },
  { pattern: /^#\/orders\/(\d+)$/, render: (ctx, id) => renderOrderDetail(page, ctx, id) },
  { pattern: /^#\/orders$/, render: (ctx) => renderOrders(page, ctx) },
  { pattern: /^#\/customers$/, render: (ctx) => renderCustomers(page, ctx) },
  { pattern: /^#\/products$/, render: (ctx) => renderProducts(page, ctx) },
  { pattern: /^#\/reports$/, render: (ctx) => renderReports(page, ctx), adminOnly: true },
];

function context() {
  return {
    user: state.user,
    isAdmin: state.user && state.user.role === "ADMIN",
    notify: (text, type = "success") => showMessage(globalMessage, text, type),
  };
}

function handleRoute() {
  if (!state.user) return;
  hideMessage(globalMessage);
  const hash = window.location.hash || "#/orders";
  const ctx = context();

  for (const route of routes) {
    const match = hash.match(route.pattern);
    if (match) {
      if (route.adminOnly && !ctx.isAdmin) {
        showMessage(globalMessage, "Only Admin users can open reports.", "error");
        page.innerHTML = "";
        return;
      }
      highlightNav(hash);
      route.render(ctx, match[1]);
      return;
    }
  }
  window.location.hash = "#/orders";
}

function highlightNav(hash) {
  document.querySelectorAll("#main-nav a").forEach((link) => {
    link.classList.toggle("active", hash.startsWith(`#/${link.dataset.route}`));
  });
}

// ---------- login / logout ----------

function showLogin() {
  state.user = null;
  appView.classList.add("hidden");
  loginView.classList.remove("hidden");
}

function showApp(user) {
  state.user = user;
  loginView.classList.add("hidden");
  appView.classList.remove("hidden");
  document.getElementById("user-name").textContent = user.name;
  const role = document.getElementById("user-role");
  role.textContent = user.role_display;
  role.className = `badge badge-${escapeHtml(user.role)}`;
  document.querySelectorAll("[data-admin-only]").forEach((el) => {
    el.classList.toggle("hidden", user.role !== "ADMIN");
  });
  handleRoute();
}

document.getElementById("login-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.target;
  const message = document.getElementById("login-message");
  const email = form.email.value.trim();
  const password = form.password.value;

  if (!email || !password) {
    showMessage(message, "Enter your email and password.", "error");
    return;
  }

  await withBusyButton(form.querySelector("button"), async () => {
    try {
      const data = await api("/auth/login/", { method: "POST", body: { email, password } });
      await api("/auth/csrf/"); // Django rotates the CSRF token on login
      hideMessage(message);
      form.reset();
      showApp(data.user);
    } catch (error) {
      showError(message, error);
    }
  }, "Signing in...");
});

document.getElementById("logout-button").addEventListener("click", async (event) => {
  await withBusyButton(event.target, async () => {
    try {
      await api("/auth/logout/", { method: "POST" });
    } finally {
      window.location.hash = "";
      showLogin();
    }
  });
});

onUnauthorized(() => {
  const wasLoggedIn = Boolean(state.user);
  showLogin();
  if (!wasLoggedIn) return; // first visit, not an expired session
  showMessage(document.getElementById("login-message"), "Your session has ended. Please sign in again.", "info");
});

window.addEventListener("hashchange", handleRoute);

// ---------- start ----------

async function start() {
  try {
    await api("/auth/csrf/");
    const user = await api("/auth/me/");
    showApp(user);
  } catch (error) {
    showLogin();
    if (error.status === 0) showError(document.getElementById("login-message"), error);
  }
}

start();
