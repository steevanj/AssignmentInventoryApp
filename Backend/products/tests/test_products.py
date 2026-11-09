from rest_framework.test import APITestCase

from core.factories import client_for, make_admin, make_customer, make_product, make_user, order_payload
from inventory.models import StockMovement


class ProductApiTests(APITestCase):
    def setUp(self):
        self.client = client_for(make_admin())

    def create(self, **data):
        payload = {"product_code": "NEW-1", "name": "New", "category": "General", "price": "10.00",
                   "stock_quantity": 5}
        payload.update(data)
        return self.client.post("/api/products/", payload, format="json")

    def test_create_records_opening_stock(self):
        response = self.create()
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(StockMovement.objects.get().movement_type, "OPENING")

    def test_product_code_must_be_unique_ignoring_case(self):
        make_product("ABC-1")
        self.assertEqual(self.create(product_code="abc-1").status_code, 400)

    def test_negative_price_and_stock_are_rejected(self):
        response = self.create(price="-1", stock_quantity=-1)
        self.assertEqual(response.status_code, 400)
        self.assertIn("price", response.data["details"])
        self.assertIn("stock_quantity", response.data["details"])

    def test_stock_cannot_be_edited_directly(self):
        product = make_product("ABC-1", stock=5)
        response = self.client.patch(f"/api/products/{product.pk}/", {"stock_quantity": 999}, format="json")
        self.assertEqual(response.status_code, 200)
        product.refresh_from_db()
        self.assertEqual(product.stock_quantity, 5)

    def test_search_and_category_filter(self):
        make_product("KB-1", name="Keyboard", category="Accessories")
        make_product("DSK-1", name="Desk", category="Furniture")
        self.assertEqual(self.client.get("/api/products/?search=key").data["count"], 1)
        self.assertEqual(self.client.get("/api/products/?category=furniture").data["count"], 1)

    def test_unused_product_can_be_deleted(self):
        product = make_product("ABC-1", stock=0)
        self.assertEqual(self.client.delete(f"/api/products/{product.pk}/").status_code, 204)

    def test_product_used_in_an_order_cannot_be_deleted(self):
        product = make_product("ABC-1", stock=0)
        sales = make_user()
        client_for(sales).post("/api/orders/", order_payload(make_customer(), [(product, 1)]), format="json")
        self.assertEqual(self.client.delete(f"/api/products/{product.pk}/").status_code, 409)
