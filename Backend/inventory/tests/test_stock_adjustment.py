from rest_framework.test import APITestCase

from core.factories import client_for, make_admin, make_product
from inventory.models import StockMovement


class StockAdjustmentTests(APITestCase):
    def setUp(self):
        self.admin = make_admin()
        self.client = client_for(self.admin)
        self.product = make_product("KB-1", stock=10)

    def adjust(self, change, reason="Stock count"):
        return self.client.post(
            "/api/inventory/adjustments/",
            {"product": self.product.pk, "quantity_change": change, "reason": reason},
            format="json",
        )

    def test_increase_creates_movement(self):
        response = self.adjust(5, "New delivery")
        self.assertEqual(response.status_code, 201, response.data)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 15)
        movement = StockMovement.objects.get()
        self.assertEqual(movement.movement_type, "ADJUSTMENT_IN")
        self.assertEqual(movement.stock_after, 15)
        self.assertEqual(movement.created_by, self.admin)

    def test_decrease(self):
        self.assertEqual(self.adjust(-4).status_code, 201)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 6)
        self.assertEqual(StockMovement.objects.get().movement_type, "ADJUSTMENT_OUT")

    def test_adjustment_that_makes_stock_negative_is_rejected(self):
        response = self.adjust(-11)
        self.assertEqual(response.status_code, 400)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 10)
        self.assertFalse(StockMovement.objects.exists())

    def test_reason_is_mandatory(self):
        self.assertEqual(self.adjust(5, reason="").status_code, 400)

    def test_zero_change_is_rejected(self):
        self.assertEqual(self.adjust(0).status_code, 400)
