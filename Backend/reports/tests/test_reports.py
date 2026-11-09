from datetime import date

from rest_framework.test import APITestCase

from core.factories import client_for, make_admin, make_customer, make_product, make_user
from orders import services
from orders.models import SalesOrder


class ReportTests(APITestCase):
    def setUp(self):
        self.admin_client = client_for(make_admin())
        self.sales = make_user()
        self.big = make_customer(name="Big Buyer")
        self.idle = make_customer(name="Idle Customer")
        self.keyboard = make_product("KB-1", price="1000.00", stock=100)
        self.mouse = make_product("MS-1", price="100.00", stock=100)

    def order(self, customer, lines, discount="0", confirm=True, cancel=False):
        order = services.create_order(
            user=self.sales, customer=customer, discount_percentage=discount,
            items=[{"product": p, "quantity": q} for p, q in lines],
        )
        if confirm:
            services.confirm_order(order_id=order.pk, user=self.sales)
        if cancel:
            services.cancel_order(order_id=order.pk, user=self.sales)
        return order

    def customer_rows(self, query=""):
        response = self.admin_client.get(f"/api/reports/customer-sales/{query}")
        self.assertEqual(response.status_code, 200, response.data)
        return {row["name"]: row for row in response.data["results"]}

    def test_customer_sales_counts_multi_item_order_once(self):
        self.order(self.big, [(self.keyboard, 2), (self.mouse, 5)], discount="10")  # 2500 - 250 = 2250

        row = self.customer_rows()["Big Buyer"]
        self.assertEqual(row["confirmed_order_count"], 1)
        self.assertEqual(row["total_sales"], "2250.00")

    def test_customer_sales_includes_customers_without_orders_and_ignores_other_statuses(self):
        self.order(self.big, [(self.keyboard, 1)])
        self.order(self.big, [(self.keyboard, 1)], confirm=False)              # draft
        self.order(self.big, [(self.keyboard, 1)], cancel=True)                # cancelled

        rows = self.customer_rows()
        self.assertEqual(rows["Big Buyer"]["confirmed_order_count"], 1)
        self.assertEqual(rows["Big Buyer"]["total_sales"], "1000.00")
        self.assertEqual(rows["Idle Customer"]["confirmed_order_count"], 0)
        self.assertEqual(rows["Idle Customer"]["total_sales"], "0.00")

    def test_customer_sales_date_range(self):
        old = self.order(self.big, [(self.keyboard, 1)])
        SalesOrder.objects.filter(pk=old.pk).update(order_date=date(2024, 1, 15))
        self.order(self.big, [(self.mouse, 1)])

        rows = self.customer_rows("?date_from=2024-01-01&date_to=2024-01-31")
        self.assertEqual(rows["Big Buyer"]["total_sales"], "1000.00")
        self.assertEqual(rows["Idle Customer"]["total_sales"], "0.00")

    def test_invalid_date_range_is_rejected(self):
        response = self.admin_client.get("/api/reports/customer-sales/?date_from=2025-02-01&date_to=2025-01-01")
        self.assertEqual(response.status_code, 400)

    def test_product_sales_uses_gross_value_before_discount(self):
        self.order(self.big, [(self.keyboard, 2), (self.mouse, 3)], discount="20")
        rows = {r["product_code"]: r for r in self.admin_client.get("/api/reports/product-sales/").data["results"]}
        self.assertEqual(rows["KB-1"]["quantity_sold"], 2)
        self.assertEqual(rows["KB-1"]["gross_sales"], "2000.00")
        self.assertEqual(rows["MS-1"]["gross_sales"], "300.00")

    def test_low_stock_report(self):
        make_product("LOW-1", stock=2)
        codes = [r["product_code"] for r in self.admin_client.get("/api/reports/low-stock/?threshold=5").data["results"]]
        self.assertEqual(codes, ["LOW-1"])
        self.assertEqual(self.admin_client.get("/api/reports/low-stock/").status_code, 400)

    def test_stock_movement_history(self):
        self.order(self.big, [(self.keyboard, 3)])
        response = self.admin_client.get("/api/reports/stock-movements/?movement_type=SALE")
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["quantity_change"], -3)
