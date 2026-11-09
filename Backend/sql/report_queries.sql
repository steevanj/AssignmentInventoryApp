-- ============================================================================
-- Part 9 - Standalone SQL queries (MySQL 8)
--
-- Table names are Django's defaults: <app>_<model>
--   customers_customer, products_product,
--   orders_salesorder, orders_salesorderitem
-- Order status values are stored as 'DRAFT', 'CONFIRMED', 'CANCELLED'.
--
-- Run against the sales_inventory database, e.g.
--   mysql -u <user> -p sales_inventory < report_queries.sql
-- ============================================================================


-- ----------------------------------------------------------------------------
-- 1. Top three customers by Confirmed order grand total
--    Joins orders only (not order items), so each order's grand_total is
--    added exactly once even when the order has several lines.
-- ----------------------------------------------------------------------------
SELECT
    c.id,
    c.name,
    COUNT(o.id)        AS confirmed_orders,
    SUM(o.grand_total) AS total_sales
FROM customers_customer AS c
JOIN orders_salesorder  AS o
      ON o.customer_id = c.id
     AND o.status = 'CONFIRMED'
GROUP BY c.id, c.name
ORDER BY total_sales DESC, c.name
LIMIT 3;


-- ----------------------------------------------------------------------------
-- 2. Top three products by quantity sold in Confirmed orders
-- ----------------------------------------------------------------------------
SELECT
    p.id,
    p.product_code,
    p.name,
    SUM(i.quantity) AS quantity_sold,
    SUM(i.amount)   AS gross_sales
FROM products_product      AS p
JOIN orders_salesorderitem AS i ON i.product_id = p.id
JOIN orders_salesorder     AS o ON o.id = i.order_id
WHERE o.status = 'CONFIRMED'
GROUP BY p.id, p.product_code, p.name
ORDER BY quantity_sold DESC, p.product_code
LIMIT 3;


-- ----------------------------------------------------------------------------
-- 3. Customers who have never placed any order (of any status)
--    LEFT JOIN keeps every customer; rows with no matching order have
--    o.id = NULL.
-- ----------------------------------------------------------------------------
SELECT
    c.id,
    c.name,
    c.email,
    c.mobile,
    c.city,
    c.is_active
FROM customers_customer     AS c
LEFT JOIN orders_salesorder AS o ON o.customer_id = c.id
WHERE o.id IS NULL
ORDER BY c.name;


-- ----------------------------------------------------------------------------
-- 4. Month-wise Confirmed sales totals, grouped by year and month
-- ----------------------------------------------------------------------------
SELECT
    YEAR(o.order_date)      AS sales_year,
    MONTH(o.order_date)     AS sales_month,
    COUNT(o.id)             AS confirmed_orders,
    SUM(o.subtotal)         AS gross_sales,
    SUM(o.discount_amount)  AS total_discount,
    SUM(o.grand_total)      AS net_sales
FROM orders_salesorder AS o
WHERE o.status = 'CONFIRMED'
GROUP BY YEAR(o.order_date), MONTH(o.order_date)
ORDER BY sales_year, sales_month;


-- ----------------------------------------------------------------------------
-- 5. Products below a supplied stock threshold
--    Change the value of @stock_threshold to the threshold you need.
-- ----------------------------------------------------------------------------
SET @stock_threshold = 10;

SELECT
    p.id,
    p.product_code,
    p.name,
    p.category,
    p.stock_quantity,
    p.is_active
FROM products_product AS p
WHERE p.stock_quantity < @stock_threshold
ORDER BY p.stock_quantity, p.product_code;
