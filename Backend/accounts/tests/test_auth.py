from rest_framework.test import APIClient, APITestCase

from core.factories import TEST_PASSWORD, make_user


class AuthTests(APITestCase):
    def setUp(self):
        self.user = make_user(email="ravi@test.local")
        self.client = APIClient()

    def test_password_is_stored_hashed(self):
        self.assertNotEqual(self.user.password, TEST_PASSWORD)
        self.assertTrue(self.user.password.startswith("pbkdf2_sha256$"))
        self.assertTrue(self.user.check_password(TEST_PASSWORD))

    def test_login_logout_flow(self):
        login = self.client.post("/api/auth/login/", {"email": "RAVI@test.local", "password": TEST_PASSWORD},
                                 format="json")
        self.assertEqual(login.status_code, 200)
        self.assertEqual(login.data["user"]["role"], "SALES")
        self.assertNotIn("password", login.data["user"])

        self.assertEqual(self.client.get("/api/auth/me/").status_code, 200)
        self.assertEqual(self.client.post("/api/auth/logout/").status_code, 200)
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 401)

    def test_wrong_password_and_unknown_email_give_same_error(self):
        wrong = self.client.post("/api/auth/login/", {"email": "ravi@test.local", "password": "nope"}, format="json")
        unknown = self.client.post("/api/auth/login/", {"email": "x@test.local", "password": "nope"}, format="json")
        self.assertEqual(wrong.status_code, 400)
        self.assertEqual(wrong.data, unknown.data)

    def test_inactive_user_cannot_log_in(self):
        self.user.is_active = False
        self.user.save()
        response = self.client.post("/api/auth/login/", {"email": "ravi@test.local", "password": TEST_PASSWORD},
                                    format="json")
        self.assertEqual(response.status_code, 400)

    def test_unknown_api_url_returns_json_404(self):
        response = self.client.get("/api/does-not-exist/")
        self.assertEqual(response.status_code, 404)
        self.assertIn("error", response.json())
