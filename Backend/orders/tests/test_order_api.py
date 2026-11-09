from decimal import Decimal

from rest_framework.test import APITestCase

from core.factories import client_for, make_customer, make_product, make_user, order_payload
from orders.models import SalesOrder


class CreateOrderTests(APITestCase):
    def setUp(self):
        self.sales = make_user()
        self.client = client_for(self.sales)
        self.customer = make_customer()
        self.keyboard = make_product("KB-1", price="1500.00", stock=20)
        self.mouse = make_product("MS-1", price="500.00", stock=50)

    def post_order(self, lines, discount="0", **extra):
        payload = order_payload(self.customer, lines, discount)
        payload.update(extra)
        return self.client.post("/api/orders/", payload, format="json")

    def test_order_with_multiple_items_and_discount_has_correct_totals(self):
        response = self.post_order([(self.keyboard, 2), (self.mouse, 3)], discount="10")

        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["status"], "DRAFT")
        self.assertEqual(response.data["subtotal"], "4500.00")
        self.assertEqual(response.data["discount_amount"], "450.00")
        self.assertEqual(response.data["grand_total"], "4050.00")
        self.assertTrue(response.data["order_number"].startswith("SO-"))

    def test_draft_order_does_not_touch_stock(self):
        self.post_order([(self.keyboard, 2)])
        self.keyboard.refresh_from_db()
        self.assertEqual(self.keyboard.stock_quantity, 20)

    def test_values_sent_by_browser_are_ignored(self):
        response = self.post_order(
            [(self.keyboard, 1)],
            grand_total="1.00", subtotal="1.00", status="CONFIRMED", created_by=999,
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["grand_total"], "1500.00")
        self.assertEqual(response.data["status"], "DRAFT")
        self.assertEqual(response.data["created_by"], self.sales.pk)

    def test_item_rate_from_browser_is_ignored(self):
        payload = order_payload(self.customer, [(self.keyboard, 1)])
        payload["items"][0]["rate"] = "1.00"
        response = self.client.post("/api/orders/", payload, format="json")
        self.assertEqual(response.data["items"][0]["rate"], "1500.00")

    def test_zero_quantity_is_rejected(self):
        response = self.post_order([(self.keyboard, 0)])
        self.assertEqual(response.status_code, 400)
        self.assertIn("items", response.data["details"])
        self.assertFalse(SalesOrder.objects.exists())

    def test_negative_quantity_is_rejected(self):
        response = self.post_order([(self.keyboard, -2)])
        self.assertEqual(response.status_code, 400)
        self.assertFalse(SalesOrder.objects.exists())

    def test_decimal_quantity_is_rejected(self):
        payload = order_payload(self.customer, [(self.keyboard, 1)])
        payload["items"][0]["quantity"] = 2.5
        self.assertEqual(self.client.post("/api/orders/", payload, format="json").status_code, 400)

    def test_discount_above_20_is_rejected(self):
        response = self.post_order([(self.keyboard, 1)], discount="20.01")
        self.assertEqual(response.status_code, 400)
        self.assertIn("discount_percentage", response.data["details"])

    def test_negative_discount_is_rejected(self):
        self.assertEqual(self.post_order([(self.keyboard, 1)], discount="-1").status_code, 400)

    def test_discount_limits_0_and_20_are_allowed(self):
        self.assertEqual(self.post_order([(self.keyboard, 1)], discount="0").status_code, 201)
        self.assertEqual(self.post_order([(self.keyboard, 1)], discount="20").status_code, 201)

    def test_order_needs_at_least_one_item(self):
        self.assertEqual(self.post_order([]).status_code, 400)

    def test_duplicate_product_is_rejected(self):
        response = self.post_order([(self.keyboard, 1), (self.keyboard, 2)])
        self.assertEqual(response.status_code, 400)

    def test_inactive_customer_is_rejected(self):
        self.customer.is_active = False
        self.customer.save()
        self.assertEqual(self.post_order([(self.keyboard, 1)]).status_code, 400)

    def test_inactive_product_is_rejected(self):
        old = make_product("OLD-1", is_active=False)
        self.assertEqual(self.post_order([(old, 1)]).status_code, 400)

    def test_later_price_change_does_not_change_existing_order(self):
        order_id = self.post_order([(self.keyboard, 2)]).data["id"]

        self.keyboard.price = Decimal("9999.00")
        self.keyboard.save()

        order = self.client.get(f"/api/orders/{order_id}/").data
        self.assertEqual(order["items"][0]["rate"], "1500.00")
        self.assertEqual(order["grand_total"], "3000.00")


class EditDraftOrderTests(APITestCase):
    def setUp(self):
        self.sales = make_user()
        self.client = client_for(self.sales)
        self.customer = make_customer()
        self.keyboard = make_product("KB-1", price="1500.00", stock=20)
        self.mouse = make_product("MS-1", price="500.00", stock=50)
        response = self.client.post(
            "/api/orders/", order_payload(self.customer, [(self.keyboard, 2), (self.mouse, 1)]), format="json"
        )
        self.order_id = response.data["id"]

    def test_draft_quantities_can_change_and_rows_be_removed(self):
        response = self.client.put(
            f"/api/orders/{self.order_id}/", order_payload(self.customer, [(self.keyboard, 5)], "5"), format="json"
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(len(response.data["items"]), 1)
        self.assertEqual(response.data["subtotal"], "7500.00")
        self.assertEqual(response.data["grand_total"], "7125.00")
