from rest_framework.test import APIClient, APITestCase

from core.factories import client_for, make_admin, make_customer, make_product, make_user, order_payload


class OrderAccessTests(APITestCase):
    def setUp(self):
        self.owner = make_user(email="owner@test.local")
        self.other = make_user(email="other@test.local")
        self.admin = make_admin()
        self.customer = make_customer()
        self.product = make_product("KB-1", stock=10)

        response = client_for(self.owner).post(
            "/api/orders/", order_payload(self.customer, [(self.product, 2)]), format="json"
        )
        self.order_id = response.data["id"]
        self.other_client = client_for(self.other)

    def test_sales_user_cannot_view_another_users_order(self):
        response = self.other_client.get(f"/api/orders/{self.order_id}/")
        self.assertEqual(response.status_code, 404)

    def test_sales_user_cannot_confirm_cancel_or_edit_another_users_order(self):
        base = f"/api/orders/{self.order_id}/"
        self.assertEqual(self.other_client.post(base + "confirm/").status_code, 404)
        self.assertEqual(self.other_client.post(base + "cancel/").status_code, 404)
        put = self.other_client.put(base, order_payload(self.customer, [(self.product, 9)]), format="json")
        self.assertEqual(put.status_code, 404)

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 10)

    def test_sales_user_list_shows_only_own_orders(self):
        self.assertEqual(self.other_client.get("/api/orders/").data["count"], 0)
        self.assertEqual(client_for(self.owner).get("/api/orders/").data["count"], 1)

    def test_admin_can_view_and_confirm_any_order(self):
        admin_client = client_for(self.admin)
        self.assertEqual(admin_client.get(f"/api/orders/{self.order_id}/").status_code, 200)
        self.assertEqual(admin_client.post(f"/api/orders/{self.order_id}/confirm/").status_code, 200)

    def test_unauthenticated_request_gets_401(self):
        response = APIClient().get(f"/api/orders/{self.order_id}/")
        self.assertEqual(response.status_code, 401)


class RolePermissionTests(APITestCase):
    def setUp(self):
        self.sales_client = client_for(make_user())
        self.product = make_product("KB-1")

    def test_sales_user_cannot_modify_master_data(self):
        self.assertEqual(self.sales_client.post("/api/customers/", {"name": "X"}, format="json").status_code, 403)
        self.assertEqual(self.sales_client.patch(f"/api/products/{self.product.pk}/", {"price": "1"},
                                                 format="json").status_code, 403)
        self.assertEqual(self.sales_client.delete(f"/api/products/{self.product.pk}/").status_code, 403)

    def test_sales_user_cannot_adjust_stock_or_view_reports(self):
        adjust = self.sales_client.post(
            "/api/inventory/adjustments/", {"product": self.product.pk, "quantity_change": 5, "reason": "x"},
            format="json",
        )
        self.assertEqual(adjust.status_code, 403)
        self.assertEqual(self.sales_client.get("/api/reports/customer-sales/").status_code, 403)

    def test_sales_user_only_sees_active_products(self):
        make_product("OLD-1", is_active=False)
        response = self.sales_client.get("/api/products/?status=all")
        codes = [row["product_code"] for row in response.data["results"]]
        self.assertEqual(codes, ["KB-1"])
