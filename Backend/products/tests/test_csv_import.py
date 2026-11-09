from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase

from core.factories import client_for, make_admin, make_product, make_user
from inventory.models import StockMovement
from products.models import Product

HEADER = "product_code,product_name,category,price,stock_quantity,status\n"


def csv_file(body, name="products.csv"):
    return SimpleUploadedFile(name, (HEADER + body).encode("utf-8"), content_type="text/csv")


class CsvImportTests(APITestCase):
    def setUp(self):
        self.client = client_for(make_admin())
        make_product("EXIST-1")

    def upload(self, file):
        return self.client.post("/api/products/import/", {"file": file}, format="multipart")

    def test_valid_file_imports_products_and_opening_stock(self):
        response = self.upload(csv_file(
            "PRD-001,Keyboard,Accessories,1500,20,Active\n"
            "PRD-002,Mouse,Accessories,500,0,Inactive\n"
        ))

        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["imported"], 2)
        self.assertFalse(Product.objects.get(product_code="PRD-002").is_active)
        opening = StockMovement.objects.filter(movement_type="OPENING")
        self.assertEqual(opening.count(), 1)  # zero stock creates no movement
        self.assertEqual(opening.get().quantity_change, 20)

    def test_file_with_one_invalid_row_imports_nothing(self):
        products_before = Product.objects.count()

        response = self.upload(csv_file(
            "PRD-001,Keyboard,Accessories,1500,20,Active\n"
            "PRD-002,Mouse,Accessories,-5,50,Active\n"
            "PRD-003,Cable,Cables,100,10,Active\n"
        ))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Product.objects.count(), products_before)
        self.assertFalse(StockMovement.objects.exists())
        self.assertEqual(response.data["row_errors"][0]["row"], 3)
        self.assertIn("price", response.data["row_errors"][0]["errors"][0])

    def test_reports_every_kind_of_row_error_with_row_numbers(self):
        response = self.upload(csv_file(
            "PRD-001,Keyboard,Accessories,1500,20,Active\n"   # row 2 ok
            "PRD-001,Copy,Accessories,1500,20,Active\n"       # row 3 duplicate in file
            "EXIST-1,Existing,General,10,1,Active\n"          # row 4 already in DB
            "PRD-004,Bad Price,General,abc,1,Active\n"        # row 5 not a number
            "PRD-005,Bad Stock,General,10,2.5,Active\n"       # row 6 not whole
            "PRD-006,Bad Status,General,10,1,Available\n"     # row 7 bad status
            "PRD-007,,General,10,1,Active\n"                  # row 8 missing name
        ))

        self.assertEqual(response.status_code, 400)
        self.assertEqual([e["row"] for e in response.data["row_errors"]], [3, 4, 5, 6, 7, 8])
        self.assertEqual(Product.objects.count(), 1)

    def test_missing_column_is_rejected(self):
        file = SimpleUploadedFile("p.csv", b"product_code,product_name,price\nA,B,1\n")
        response = self.upload(file)
        self.assertEqual(response.status_code, 400)
        self.assertIn("category", response.data["error"])

    def test_non_csv_file_is_rejected(self):
        response = self.upload(SimpleUploadedFile("p.txt", b"hello"))
        self.assertEqual(response.status_code, 400)

    def test_sales_user_cannot_import(self):
        response = client_for(make_user()).post(
            "/api/products/import/", {"file": csv_file("PRD-001,K,A,1,1,Active\n")}, format="multipart"
        )
        self.assertEqual(response.status_code, 403)
