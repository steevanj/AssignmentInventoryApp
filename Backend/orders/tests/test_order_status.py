from rest_framework.test import APITestCase

from core.factories import client_for, make_customer, make_product, make_user, order_payload
from inventory.models import StockMovement
from orders.models import SalesOrder


class OrderStatusTests(APITestCase):
    def setUp(self):
        self.sales = make_user()
        self.client = client_for(self.sales)
        self.customer = make_customer()
        self.keyboard = make_product("KB-1", price="1500.00", stock=10)
        self.mouse = make_product("MS-1", price="500.00", stock=5)

    def create_order(self, lines):
        response = self.client.post("/api/orders/", order_payload(self.customer, lines), format="json")
        self.assertEqual(response.status_code, 201, response.data)
        return response.data["id"]

    def confirm(self, order_id):
        return self.client.post(f"/api/orders/{order_id}/confirm/")

    def cancel(self, order_id):
        return self.client.post(f"/api/orders/{order_id}/cancel/")

    def stock(self, product):
        product.refresh_from_db()
        return product.stock_quantity

    # --- confirm --------------------------------------------------------

    def test_confirm_with_sufficient_stock_deducts_stock(self):
        order_id = self.create_order([(self.keyboard, 3), (self.mouse, 2)])

        response = self.confirm(order_id)

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["order"]["status"], "CONFIRMED")
        self.assertEqual(self.stock(self.keyboard), 7)
        self.assertEqual(self.stock(self.mouse), 3)
        movements = StockMovement.objects.filter(related_order_id=order_id, movement_type="SALE")
        self.assertEqual(movements.count(), 2)

    def test_confirm_with_one_insufficient_item_changes_nothing(self):
        order_id = self.create_order([(self.keyboard, 3), (self.mouse, 6)])  # only 5 mice

        response = self.confirm(order_id)

        self.assertEqual(response.status_code, 409)
        self.assertIn("MS-1", response.data["error"])
        self.assertEqual(self.stock(self.keyboard), 10)  # keyboard line was fine but not deducted
        self.assertEqual(self.stock(self.mouse), 5)
        self.assertEqual(SalesOrder.objects.get(pk=order_id).status, "DRAFT")
        self.assertFalse(StockMovement.objects.filter(related_order_id=order_id).exists())

    def test_confirm_can_use_exactly_all_stock(self):
        order_id = self.create_order([(self.mouse, 5)])
        self.assertEqual(self.confirm(order_id).status_code, 200)
        self.assertEqual(self.stock(self.mouse), 0)

    def test_repeated_confirmation_does_not_deduct_again(self):
        order_id = self.create_order([(self.keyboard, 4)])
        self.confirm(order_id)

        response = self.confirm(order_id)

        self.assertEqual(response.status_code, 409)
        self.assertEqual(self.stock(self.keyboard), 6)
        self.assertEqual(StockMovement.objects.filter(related_order_id=order_id).count(), 1)

    def test_confirmed_order_is_read_only(self):
        order_id = self.create_order([(self.keyboard, 1)])
        self.confirm(order_id)

        response = self.client.put(
            f"/api/orders/{order_id}/", order_payload(self.customer, [(self.keyboard, 9)]), format="json"
        )
        self.assertEqual(response.status_code, 409)

    # --- cancel ---------------------------------------------------------

    def test_cancel_confirmed_order_restores_stock_once(self):
        order_id = self.create_order([(self.keyboard, 4), (self.mouse, 2)])
        self.confirm(order_id)

        first = self.cancel(order_id)
        second = self.cancel(order_id)

        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.data["order"]["status"], "CANCELLED")
        self.assertEqual(second.status_code, 409)
        self.assertEqual(self.stock(self.keyboard), 10)
        self.assertEqual(self.stock(self.mouse), 5)
        self.assertEqual(
            StockMovement.objects.filter(related_order_id=order_id, movement_type="SALE_REVERSAL").count(), 2
        )

    def test_cancel_draft_order_does_not_change_stock(self):
        order_id = self.create_order([(self.keyboard, 4)])

        response = self.cancel(order_id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.stock(self.keyboard), 10)
        self.assertFalse(StockMovement.objects.filter(related_order_id=order_id).exists())

    def test_cancelled_order_cannot_be_confirmed(self):
        order_id = self.create_order([(self.keyboard, 1)])
        self.cancel(order_id)
        self.assertEqual(self.confirm(order_id).status_code, 409)
        self.assertEqual(self.stock(self.keyboard), 10)
