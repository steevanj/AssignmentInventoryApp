# Sales Order & Inventory Management

A web application for a small trading company that currently tracks customers, products and orders in spreadsheets. It manages customer and product master data, multi-item sales orders with totals calculated on the server, and stock that stays correct when orders are confirmed or cancelled, including when several users work at the same time. It also provides sales and stock reports.

- **Backend:** Python, Django + Django REST Framework (JSON API), MySQL
- **Frontend:** plain HTML/CSS/JavaScript prototype in `Frontend/`, calling the API with `fetch()`

---

## Contents
1. [Tech stack and versions](#1-tech-stack-and-versions)
2. [Project structure](#2-project-structure)
3. [How to run the project](#3-how-to-run-the-project)
4. [Sample accounts](#4-sample-accounts)
5. [Roles and permissions](#5-roles-and-permissions)
6. [API reference with examples](#6-api-reference-with-examples)
7. [Database design](#7-database-design)
8. [Order and stock logic](#8-order-and-stock-logic)
9. [Reports](#9-reports)
10. [CSV product import](#10-csv-product-import)
11. [Edge cases handled](#11-edge-cases-handled)
12. [Assumptions](#12-assumptions)
13. [Known limitations and remaining work](#13-known-limitations-and-remaining-work)

---

## 1. Tech stack and versions

| Area | Technology | Version |
|---|---|---|
| Language | Python | 3.9 or newer (developed on 3.9.0) |
| Framework | Django | 4.2 LTS |
| API | Django REST Framework | 3.15.1 |
| Database | MySQL | 8.0.16 or newer (CHECK constraints); tested on 8.0.20 |
| DB driver | mysqlclient | 2.2.7 |
| Config | python-dotenv | 1.2.1 |
| CORS | django-cors-headers | 4.4.0 |

All Python dependencies are pinned in `Backend/requirements.txt`.

---

## 2. Project structure

```
Assignment/
├── Backend/                     Django project (backend only)
│   ├── core/                    settings, root urls, shared helpers
│   │   ├── settings.py          reads everything sensitive from .env
│   │   ├── urls.py              includes each app's urls
│   │   ├── authentication.py    session auth that returns 401 when not logged in
│   │   ├── permissions.py       IsAdminRole, IsAdminOrReadOnly
│   │   ├── exceptions.py        one JSON error format, 409 ConflictError
│   │   ├── pagination.py
│   │   └── api.py               query-param parsing, filters, pagination helper
│   ├── accounts/                User model, login/logout, seed_data command
│   ├── customers/               Customer CRUD
│   ├── products/                Product CRUD, categories, CSV import
│   ├── inventory/               StockMovement model, stock services, adjustments
│   ├── orders/                  SalesOrder/Item, calculations, order services
│   ├── reports/                 sales and stock reports
│   ├── manage.py
│   ├── requirements.txt
│   └── .env.example             copy to .env and fill in
├── Frontend/                    HTML/CSS/JS prototype
├── samples/                     products_valid.csv, products_invalid.csv
└── README.md
```

**Code organisation**

Each app keeps its own `models`, `serializers`, `views` and `urls`. When a module holds more than one class, it is a package with one file per class, for example `orders/views/order_confirm_view.py`.

- **Views** are thin DRF `APIView` classes. They parse the request, validate with a `ModelSerializer`, call a service and return a response.
- **Business rules** live in services:
  - `orders/calculations.py`: all money calculations
  - `orders/services.py`: order lifecycle
  - `inventory/services.py`: every stock change
  - `products/csv_import.py`: CSV import

---

## 3. How to run the project

### 3.1 Prerequisites
- Python 3.9+
- MySQL 8.0 running locally
- Git

### 3.2 Clone
```bash
git clone https://github.com/steevanj/AssignmentInventoryApp.git
cd AssignmentInventoryApp/Backend
```

### 3.3 Create a virtual environment and install dependencies
**Windows (PowerShell)**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
**macOS / Linux**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
> On Linux, `mysqlclient` needs the MySQL client headers first, e.g. `sudo apt install python3-dev default-libmysqlclient-dev build-essential pkg-config`.

### 3.4 Create the database
Log in to MySQL and run:
```sql
CREATE DATABASE sales_inventory CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```
The test database (`test_sales_inventory`) is created automatically when tests run, so the MySQL user needs permission to create databases.

### 3.5 Configure environment variables
```bash
cp .env.example .env          # Windows: copy .env.example .env
```
Edit `.env` with your own values:

| Variable | Meaning | Example |
|---|---|---|
| `DJANGO_SECRET_KEY` | any long random string | `python -c "import secrets;print(secrets.token_urlsafe(50))"` |
| `DJANGO_DEBUG` | `True` for local development | `True` |
| `DJANGO_ALLOWED_HOSTS` | comma separated | `localhost,127.0.0.1` |
| `DB_NAME` / `DB_USER` / `DB_PASSWORD` | your MySQL database and login | `sales_inventory` / `root` / `...` |
| `DB_HOST` / `DB_PORT` | MySQL address | `127.0.0.1` / `3306` |
| `FRONTEND_ORIGINS` | where the frontend is served from | `http://localhost:5500,http://127.0.0.1:5500` |
| `SEED_ADMIN_PASSWORD` / `SEED_SALES_PASSWORD` | optional, override the sample passwords | |

`.env` is listed in `.gitignore`. Real credentials are never committed.

### 3.6 Create the tables and load sample data
```bash
python manage.py migrate
python manage.py seed_data
```
`seed_data` creates sample users, customers and products (with opening stock movements). It also creates four orders through the real order logic: two Confirmed, one Draft and one Cancelled. It is safe to run more than once.

### 3.7 Start the backend
```bash
python manage.py runserver
```
The API is now at **http://127.0.0.1:8000/api/**. The Django admin is at http://127.0.0.1:8000/admin/: log in with the sample admin account. It is read-only for orders and stock.

### 3.8 Start the frontend
Serve the `Frontend/` folder on port 5500, the origin allowed in `FRONTEND_ORIGINS`:
```bash
cd ../Frontend
python -m http.server 5500
```
Open **http://localhost:5500** and log in with a sample account. The VS Code "Live Server" extension on port 5500 also works.

> Use `localhost` for both the frontend and the API, or `127.0.0.1` for both. Don't mix them, or the browser won't send the session cookie.

### 3.9 Quick check from the command line
```bash
curl -c cookies.txt http://127.0.0.1:8000/api/auth/csrf/
# copy the csrftoken value from cookies.txt, then:
curl -b cookies.txt -c cookies.txt -H "Content-Type: application/json" \
     -H "X-CSRFToken: <token>" -H "Referer: http://127.0.0.1:8000/" \
     -d '{"email":"admin@example.com","password":"Admin@12345"}' \
     http://127.0.0.1:8000/api/auth/login/
curl -b cookies.txt http://127.0.0.1:8000/api/products/
```
With `DJANGO_DEBUG=True` you can also open any `/api/...` URL in the browser to use DRF's browsable API.

---

## 4. Sample accounts

These are **sample accounts for local use only**, created by `seed_data`.

| Role | Email | Password |
|---|---|---|
| Admin | admin@example.com | Admin@12345 |
| Sales User | sales1@example.com | Sales@12345 |
| Sales User | sales2@example.com | Sales@12345 |

To use different passwords, set `SEED_ADMIN_PASSWORD` / `SEED_SALES_PASSWORD` in `.env` before running `seed_data`. To create your own admin instead, run `python manage.py createsuperuser` (it asks for email, name and password).

---

## 5. Roles and permissions

Everything is enforced on the **backend**. Hiding a button in the UI is never the only protection.

| Action | Admin | Sales User |
|---|---|---|
| View customers and products | all (active and inactive) | active only |
| Create, edit or delete customers and products | ✅ | ❌ 403 |
| Adjust stock, import products from CSV | ✅ | ❌ 403 |
| Create orders | ✅ | ✅ |
| View, edit, confirm or cancel orders | all orders | **only their own** |
| Reports | ✅ | ❌ 403 |

A Sales User who opens another user's order, for example by changing the id in the URL, gets **404 Not Found**, the same as for an id that doesn't exist. This doesn't reveal whether the order exists.

**Security notes**
- Passwords are stored as salted PBKDF2 hashes (Django's `set_password`).
- Login uses Django sessions with an HttpOnly cookie, and the session id is rotated on login.
- POST/PUT/PATCH/DELETE requests need the CSRF token (`X-CSRFToken` header).
- The login error is the same for an unknown email, a wrong password and an inactive account.
- Errors never include tracebacks or secrets. Unexpected errors are logged on the server and the client gets a generic message.

---

## 6. API reference with examples

Base URL: `http://127.0.0.1:8000/api/`. All endpoints return JSON and require login, except `auth/csrf/` and `auth/login/`.

### 6.1 Endpoint list

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/auth/csrf/` | sets the CSRF cookie |
| POST | `/auth/login/` | log in `{email, password}` |
| POST | `/auth/logout/` | log out |
| GET | `/auth/me/` | current user and role |
| GET / POST | `/customers/` | list (`search`, `status`, `page`) / create |
| GET / PUT / PATCH / DELETE | `/customers/{id}/` | view / edit / delete |
| GET / POST | `/products/` | list active products (`search`, `category`, `status`, `page`, `page_size`) / create |
| GET | `/products/categories/` | distinct categories |
| POST | `/products/import/` | CSV import (multipart `file`) |
| GET / PUT / PATCH / DELETE | `/products/{id}/` | view / edit / delete |
| POST | `/inventory/adjustments/` | stock adjustment `{product, quantity_change, reason}` |
| GET / POST | `/orders/` | list (`status`, `search`, `date_from`, `date_to`) / create Draft order |
| GET / PUT | `/orders/{id}/` | view with items / edit (Draft only) |
| POST | `/orders/{id}/confirm/` | confirm and deduct stock |
| POST | `/orders/{id}/cancel/` | cancel and restore stock if it was confirmed |
| GET | `/reports/customer-sales/` | `date_from`, `date_to` |
| GET | `/reports/product-sales/` | `date_from`, `date_to` |
| GET | `/reports/low-stock/` | `threshold` (required) |
| GET | `/reports/stock-movements/` | `product`, `movement_type`, `date_from`, `date_to`, `page` |

`status` for customers and products: `active` (default), `inactive` or `all`. Admin only; Sales Users always get active records.

### 6.2 Status codes

| Code | Meaning |
|---|---|
| 200 / 201 / 204 | OK / created / deleted |
| 400 | invalid input; field errors are listed in `details` |
| 401 | not logged in |
| 403 | logged in but not allowed (wrong role) |
| 404 | record not found, or not yours |
| 409 | conflicts with the current state (already confirmed, not enough stock, record in use) |
| 500 | unexpected server error (generic message only) |

Every error has the same shape:
```json
{ "error": "Readable message", "details": { "field": ["message"] } }
```

### 6.3 Examples

**Log in**
```http
POST /api/auth/login/
Content-Type: application/json

{"email": "admin@example.com", "password": "Admin@12345"}
```
```json
200 OK
{"message": "Logged in successfully.",
 "user": {"id": 1, "name": "Asha Admin", "email": "admin@example.com", "role": "ADMIN", "role_display": "Admin"}}
```
```json
400 Bad Request
{"error": "Invalid email or password."}
```

**List products**
```http
GET /api/products/?search=key&page=1&page_size=20
```
```json
200 OK
{"count": 1, "next": null, "previous": null,
 "results": [{"id": 1, "product_code": "PRD-001", "name": "Keyboard", "category": "Accessories",
              "price": "1500.00", "stock_quantity": 20, "is_active": true,
              "created_at": "...", "updated_at": "..."}]}
```

**Create a Draft order** (only customer, discount and product/quantity are accepted; rates and totals come from the server)
```http
POST /api/orders/
{"customer": 1, "discount_percentage": "10",
 "items": [{"product": 1, "quantity": 2}, {"product": 2, "quantity": 3}]}
```
```json
201 Created
{"id": 5, "order_number": "SO-202611-00005", "customer": 1, "customer_name": "Sharma Traders",
 "order_date": "2026-11-09", "status": "DRAFT", "status_display": "Draft",
 "discount_percentage": "10.00", "subtotal": "4500.00", "discount_amount": "450.00", "grand_total": "4050.00",
 "created_by": 2, "created_by_name": "Ravi Sales", "is_editable": true,
 "items": [
   {"id": 9, "product": 1, "product_code": "PRD-001", "product_name": "Keyboard", "quantity": 2, "rate": "1500.00", "amount": "3000.00"},
   {"id": 10, "product": 2, "product_code": "PRD-002", "product_name": "Mouse", "quantity": 3, "rate": "500.00", "amount": "1500.00"}
 ]}
```
Validation failure:
```json
400 Bad Request
{"error": "Please correct the highlighted fields.",
 "details": {"discount_percentage": ["Discount must be between 0 and 20."],
             "items": [{"quantity": ["Quantity must be at least 1."]}]}}
```

**Get an order**
```http
GET /api/orders/5/
```
`200` with the same body as above. `404 {"error": "Order not found."}` if it doesn't exist or belongs to another Sales User.

**Confirm an order**
```http
POST /api/orders/5/confirm/
```
```json
200 OK
{"message": "Order SO-202611-00005 confirmed and stock deducted.", "order": { ...status "CONFIRMED"... }}
```
```json
409 Conflict
{"error": "Order cannot be confirmed. PRD-004 (USB-C Hub): ordered 5, only 3 in stock."}
```
```json
409 Conflict
{"error": "Order SO-202611-00005 is already confirmed. Stock was not deducted again."}
```

**Cancel an order**
```http
POST /api/orders/5/cancel/
```
```json
200 OK
{"message": "Order SO-202611-00005 cancelled. Stock has been restored.", "order": { ...status "CANCELLED"... }}
```

**Stock adjustment** (Admin)
```http
POST /api/inventory/adjustments/
{"product": 3, "quantity_change": -2, "reason": "Damaged in transit"}
```
```json
201 Created
{"message": "Stock updated.",
 "movement": {"id": 21, "product": 3, "product_code": "PRD-003", "movement_type": "ADJUSTMENT_OUT",
              "quantity_change": -2, "stock_after": 5, "reason": "Damaged in transit", "...": "..."}}
```

**Delete a customer who has orders**
```json
409 Conflict
{"error": "This customer has sales orders and cannot be deleted. Mark the customer inactive instead."}
```

**Not logged in**
```json
401 Unauthorized
{"error": "Please log in to continue."}
```

---

## 7. Database design

### 7.1 Entities and relationships

```
User ──1:N── SalesOrder ──1:N── SalesOrderItem ──N:1── Product
               │  N:1                                    │ 1:N
            Customer                                StockMovement ──N:1── SalesOrder (optional)
                                                         │ N:1
                                                        User (created_by)
```

| Table | Main fields | Keys and constraints |
|---|---|---|
| `accounts_user` | name, email, password (hash), role | email UNIQUE, index on role |
| `customers_customer` | name, email, mobile, city, is_active | indexes on name, email, mobile, is_active |
| `products_product` | product_code, name, category, price, stock_quantity, is_active | product_code UNIQUE; CHECK price >= 0; CHECK stock >= 0 |
| `orders_salesorder` | order_number, customer, order_date, status, discount_percentage, subtotal, discount_amount, grand_total, created_by | order_number UNIQUE; CHECK discount 0–20; CHECK amounts >= 0; indexes (status, order_date) and (created_by, status) |
| `orders_salesorderitem` | order, product, quantity, rate, amount | UNIQUE (order, product); CHECK quantity > 0 |
| `inventory_stockmovement` | product, movement_type, quantity_change, stock_after, related_order, reason, created_by, created_at | CHECK quantity_change != 0; index (product, created_at) |

The schema is created by Django migrations in each app's `migrations/` folder. Sample data comes from `python manage.py seed_data`.

### 7.2 Design decisions
- **Money is `DECIMAL(…, 2)`**, never float, so totals are exact.
- **The rate is copied onto each order item** when the line is added. Changing a product's price later doesn't change existing orders.
- **Totals are stored on the order**, calculated by the server. Reports can sum them directly, and an order always shows what was agreed.
- **Customers and products can't be deleted once used.** The foreign keys use `ON DELETE PROTECT`, and the API returns a clear 409 suggesting deactivation (`is_active = false`). Order items are deleted with their order.
- **Stock has a balance and a ledger.** `products.stock_quantity` is the current balance. `inventory_stockmovement` is an append-only record of every change (who, why, which order, balance after). All stock changes go through `inventory/services.py`, so the two always agree.
- **Rules are enforced in three layers:** serializer validation (clear messages), model validators, and database CHECK / UNIQUE constraints (a last line of defence).
- **The order number** (`SO-YYYYMM-00042`) is built from the primary key, so it is unique even when orders are created at the same moment.
- **Email is the login.** A custom user model with a `role` field (ADMIN / SALES).

---

## 8. Order and stock logic

### 8.1 Calculations (`orders/calculations.py`)
```
Item Amount     = Quantity × Rate
Subtotal        = Sum of Item Amounts
Discount Amount = Subtotal × Discount Percentage / 100
Grand Total     = Subtotal − Discount Amount
```

**Rounding rule**
- Every amount is rounded to 2 decimal places with ROUND_HALF_UP.
- Line amounts are rounded first, and the subtotal is their sum.
- The grand total is the subtotal minus the rounded discount, so the figures always add up.

All calculation happens on the backend. Values sent by the browser for rate, amount, totals, status or owner are ignored.

### 8.2 Status flow

| Current | Action | Result | Stock effect |
|---|---|---|---|
| Draft | Edit | Draft | none |
| Draft | Confirm | Confirmed | deduct ordered quantities |
| Draft | Cancel | Cancelled | none |
| Confirmed | Cancel | Cancelled | restore deducted quantities |
| Cancelled | — | Cancelled | none (read-only) |

- Draft orders don't reserve or deduct stock.
- When a Draft is edited, lines already on the order keep their stored rate. Newly added products use the current price.

### 8.3 Preventing conflicting stock updates
Confirm and cancel each run inside **one database transaction** (`transaction.atomic()`). The status change, the stock changes and the stock movement rows are saved together, or not at all.

Concurrency is handled with **row locks** (`SELECT … FOR UPDATE`):
1. **Lock the order row.** Two requests to confirm the same order queue up. The second sees the order is already Confirmed and gets 409, so stock is never deducted twice. Cancel works the same way, so stock is never restored twice.
2. **Lock all product rows of the order, in product-id order.** Locking in a fixed order means two transactions can't deadlock waiting on each other.
3. **Check stock for every line before changing anything.** If any line is short, the whole confirmation is rejected and nothing changes.
4. **Read the latest committed stock.** MySQL runs at **READ COMMITTED** (set in settings). A second user confirming another order for the same product waits for the lock, then reads the stock left after the first commit.
5. **The database CHECK `stock_quantity >= 0`** is the final safety net.

Tested with two simultaneous confirmations of 4 units each against a stock of 5: one succeeded, the other was rejected with "only 1 in stock", and the final stock was 1.

### 8.4 Stock adjustments
- Admin can increase or decrease stock with a **mandatory reason**.
- Every adjustment creates a stock movement (`ADJUSTMENT_IN` / `ADJUSTMENT_OUT`).
- Adjustments that would make stock negative are rejected.
- Product stock can't be edited directly through the product API. It is read-only there, so the ledger always stays complete.

---

## 9. Reports

All reports are Admin only and count **Confirmed orders only**.

| Report | Endpoint | Content |
|---|---|---|
| Customer Sales Summary | `/api/reports/customer-sales/?date_from=&date_to=` | every customer, confirmed order count, total sales after discount. Customers with no confirmed orders in the range show 0. |
| Product Sales Summary | `/api/reports/product-sales/?date_from=&date_to=` | quantity sold and gross item value (before the order discount) |
| Low Stock | `/api/reports/low-stock/?threshold=10` | active products with stock below the threshold |
| Stock Movement History | `/api/reports/stock-movements/` | product, movement type, quantity change, order, reason, user, timestamp |

The customer report joins customers to **orders only, never to order items**. An order with several lines is therefore counted once, and its grand total is added once.

---

## 10. CSV product import

`POST /api/products/import/`, Admin only, as a multipart form with a field named `file`.

```csv
product_code,product_name,category,price,stock_quantity,status
PRD-001,Keyboard,Accessories,1500,20,Active
PRD-002,Mouse,Accessories,500,50,Active
```

- Checks that all required columns are present, then validates **every** row.
- Rejects:
  - duplicate codes within the file
  - codes that already exist in the database
  - invalid or negative numbers
  - stock that isn't a whole number
  - statuses other than Active/Inactive
- Reports errors with **row numbers** (the header is row 1):
  ```json
  400 {"error": "8 row(s) have errors. Nothing was imported - fix the file and upload it again.",
       "row_errors": [{"row": 4, "errors": ["price: Price cannot be negative."]}, ...]}
  ```
- **All or nothing:** if any row is invalid, nothing is imported. Otherwise every product and its opening stock movement is saved in one transaction.
- Uses the same validation as the "add product" API.
- Sample files:
  - `samples/products_valid.csv` imports 5 products.
  - `samples/products_invalid.csv` has one example of each error and imports nothing.

---

## 11. Edge cases handled

**Orders**
- Quantity of 0, negative, decimal (2.5) or text → 400.
- Discount below 0 or above 20, or not a number → 400.
- No items, or the same product twice in one order → 400.
- Inactive customer or inactive product → 400. Also checked again at confirm time, in case it was deactivated after the Draft was saved.
- Rates, totals, status or `created_by` sent by the browser → ignored, recalculated on the server.
- Product price changed after the order was created → the order keeps its stored rate.
- Editing a Confirmed or Cancelled order → 409, read-only.
- Confirming twice or cancelling twice (double click, retry, two tabs) → 409, stock unchanged.
- Confirming when one line is short → 409, listing every short product. No stock or status change.
- Two users confirming orders for the same limited stock at the same time → one succeeds, the other gets 409. Stock never goes negative.
- Someone confirms the order while another user is editing it → the edit re-checks the status under a row lock and gets 409.

**Access**
- Not logged in → 401.
- Sales User trying Admin actions (master data, adjustments, import, reports) → 403.
- Sales User opening, editing, confirming or cancelling another user's order by changing the id → 404.
- Sales User asking for inactive records (`?status=all`) → still only active records.
- Unknown `/api/...` URL → JSON 404 instead of an HTML page.

**Master data and stock**
- Duplicate product code, including a different upper/lower case version (`prd-001` vs `PRD-001`) → 400.
- Negative price or stock → 400 (and blocked by DB constraints).
- Deleting a customer with orders, or a product with orders or stock history → 409 with a "mark inactive instead" message.
- Stock adjustment of 0, without a reason, or one that would make stock negative → 400.
- Editing `stock_quantity` through the product API → ignored (read-only).

**Reports and query parameters**
- Invalid dates, or an end date before the start date → 400 naming the field.
- Missing or negative low-stock threshold → 400.
- Invalid `status` or `movement_type` filter → 400 listing the allowed values.

**CSV import**
- Missing file, a file that isn't `.csv`, an empty file, a header with no rows, or missing columns → 400 with a clear message.
- Non-UTF-8 file → 400. Excel's BOM is handled.
- File over 2 MB or more than 5000 rows → 400. Blank lines are skipped.
- Another user creates the same product code during the import → the whole import is rolled back with a message.

**Errors**
- Unexpected server errors return a generic message. The traceback is only logged on the server.

---

## 12. Assumptions
- One currency and one stock location. Prices are shown with 2 decimals, no currency symbol.
- Product quantities are whole numbers.
- Taxes, delivery, purchasing and payments are out of scope.
- Sales reports include Confirmed orders only.
- The order date is the date the order was created (server time zone, `Asia/Kolkata` by default). It isn't editable.
- A Sales User can cancel their own Confirmed orders ("manage their own orders"). Admin can manage all orders.
- Products and customers default to the *active* list. Admin can view inactive or all records with `?status=`.
- A product created with an opening stock, or imported, gets an OPENING stock movement. That means it counts as "referenced by a stock movement" and can no longer be deleted, only deactivated.
- When a Draft order is edited, existing lines keep their original rate. Only newly added products take the current price.

---

## 13. Known limitations and remaining work
- **Frontend:** the HTML/JS prototype in `Frontend/` is still in progress. The backend API is complete.
- **Automated tests, standalone SQL queries and the debugging exercise** (Parts 9, 11 and 12) are not yet in the repository. They are being added next.
- The API uses session authentication, designed for the browser frontend. A mobile or third-party client would need token authentication.
- Reports return all rows without pagination, which is fine at this company's size. Large datasets would need pagination or export.
- No password reset or user management screens. Users are created with `seed_data`, `createsuperuser` or the Django admin.
- Local development setup only (`runserver`). It hasn't been configured for production hosting (static files, HTTPS, a real WSGI server).
