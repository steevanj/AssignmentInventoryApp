# Sales Order & Inventory Management

Django REST API (backend) + plain HTML/JS frontend + MySQL.

## Requirements

- Python 3.9 or newer
- MySQL 8.0
- Git

## 1. Get the code

```bash
git clone https://github.com/steevanj/AssignmentInventoryApp.git
cd AssignmentInventoryApp
```

## 2. Create the database

Open MySQL and run:

```sql
CREATE DATABASE sales_inventory CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

## 3. Set up the backend

```bash
cd Backend
python -m venv .venv
```

Activate the virtual environment:

- Windows: `.venv\Scripts\activate`
- Mac / Linux: `source .venv/bin/activate`

Install the packages:

```bash
pip install -r requirements.txt
```

## 4. Add your credentials

Copy the example file:

- Windows: `copy .env.example .env`
- Mac / Linux: `cp .env.example .env`

Open `.env` and fill in your own MySQL user and password:

```
DJANGO_SECRET_KEY=any-long-random-text
DJANGO_DEBUG=True
DB_NAME=sales_inventory
DB_USER=your_mysql_user
DB_PASSWORD=your_mysql_password
DB_HOST=127.0.0.1
DB_PORT=3306
```

The `.env` file is not committed to Git.

## 5. Create tables and sample data

```bash
python manage.py migrate
python manage.py seed_data
```

## 6. Run the backend

```bash
python manage.py runserver
```

The API runs at http://localhost:8000/api/

## 7. Run the frontend

Open a second terminal:

```bash
cd Frontend
python -m http.server 5500
```

Open http://localhost:5500 in the browser.

Use `localhost` for both the backend and the frontend. Don't mix `localhost` and `127.0.0.1`, or the login won't stick.

## Login accounts

Created by `seed_data` (sample accounts for local use only):

| Role | Email | Password |
|---|---|---|
| Admin | admin@example.com | Admin@12345 |
| Sales User | sales1@example.com | Sales@12345 |
| Sales User | sales2@example.com | Sales@12345 |

## Run the tests

From the `Backend` folder (the MySQL user must be allowed to create a test database):

```bash
python manage.py test
```

## Other files

- `samples/products_valid.csv`, `samples/products_invalid.csv`: files for the product CSV import
- `Backend/sql/report_queries.sql`: the report SQL queries
- `Backend/debugging_exercise/`: the `calculate_total` fix and its tests
