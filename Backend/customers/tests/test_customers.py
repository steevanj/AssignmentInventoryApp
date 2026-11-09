from rest_framework.test import APITestCase

from core.factories import client_for, make_admin, make_customer, make_product, make_user, order_payload


class CustomerApiTests(APITestCase):
    def setUp(self):
        self.admin_client = client_for(make_admin())

    def test_admin_can_create_and_edit(self):
        response = self.admin_client.post(
            "/api/customers/", {"name": "Acme", "email": "A@ACME.IN", "mobile": "98765 43210"}, format="json"
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["email"], "a@acme.in")
        self.assertEqual(response.data["mobile"], "9876543210")

        customer_id = response.data["id"]
        patch = self.admin_client.patch(f"/api/customers/{customer_id}/", {"is_active": False}, format="json")
        self.assertFalse(patch.data["is_active"])

    def test_invalid_mobile_and_blank_name_are_rejected(self):
        response = self.admin_client.post("/api/customers/", {"name": "", "mobile": "12ab"}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("name", response.data["details"])
        self.assertIn("mobile", response.data["details"])

    def test_search_by_name_email_or_mobile(self):
        make_customer(name="Sharma Traders", email="s@x.in", mobile="9000000001")
        make_customer(name="Kumar Stores", email="k@y.in", mobile="9000000002")
        for term in ["sharma", "s@x", "0001"]:
            with self.subTest(term=term):
                self.assertEqual(self.admin_client.get(f"/api/customers/?search={term}").data["count"], 1)

    def test_status_filter(self):
        make_customer(name="Active")
        make_customer(name="Inactive", is_active=False)
        self.assertEqual(self.admin_client.get("/api/customers/?status=inactive").data["count"], 1)
        self.assertEqual(self.admin_client.get("/api/customers/?status=all").data["count"], 2)

    def test_customer_with_orders_cannot_be_deleted(self):
        customer = make_customer()
        client_for(make_user()).post(
            "/api/orders/", order_payload(customer, [(make_product("KB-1"), 1)]), format="json"
        )
        response = self.admin_client.delete(f"/api/customers/{customer.pk}/")
        self.assertEqual(response.status_code, 409)
        self.assertIn("inactive", response.data["error"])

    def test_unused_customer_can_be_deleted(self):
        customer = make_customer()
        self.assertEqual(self.admin_client.delete(f"/api/customers/{customer.pk}/").status_code, 204)
