"""
Loads sample data for local development and the demo:

    python manage.py seed_data

Sample account passwords come from SEED_ADMIN_PASSWORD / SEED_SALES_PASSWORD
in .env. If they are not set, the demo passwords documented in the README are
used. These are sample accounts only - never reuse them anywhere real.
"""

import os
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import User
from customers.models import Customer
from inventory.models import StockMovement
from products.models import Product

SAMPLE_USERS = [
    {"email": "admin@example.com", "name": "Asha Admin", "role": User.Role.ADMIN, "env": "SEED_ADMIN_PASSWORD",
     "default": "Admin@12345"},
    {"email": "sales1@example.com", "name": "Ravi Sales", "role": User.Role.SALES, "env": "SEED_SALES_PASSWORD",
     "default": "Sales@12345"},
    {"email": "sales2@example.com", "name": "Meera Sales", "role": User.Role.SALES, "env": "SEED_SALES_PASSWORD",
     "default": "Sales@12345"},
]

SAMPLE_CUSTOMERS = [
    ("Sharma Traders", "contact@sharmatraders.in", "9876500001", "Mumbai", True),
    ("Kumar Electronics", "sales@kumarelec.in", "9876500002", "Bengaluru", True),
    ("Patel & Sons", "info@patelsons.in", "9876500003", "Ahmedabad", True),
    ("Green Leaf Stores", "hello@greenleaf.in", "9876500004", "Chennai", True),
    ("Old Town Supplies", "oldtown@example.in", "9876500005", "Pune", False),
]

SAMPLE_PRODUCTS = [
    ("PRD-001", "Keyboard", "Accessories", "1500.00", 20, True),
    ("PRD-002", "Mouse", "Accessories", "500.00", 50, True),
    ("PRD-003", "27in Monitor", "Displays", "14500.00", 8, True),
    ("PRD-004", "USB-C Hub", "Accessories", "2200.00", 3, True),
    ("PRD-005", "Laptop Stand", "Furniture", "1800.00", 15, True),
    ("PRD-006", "Webcam HD", "Accessories", "3200.00", 0, True),
    ("PRD-007", "VGA Cable", "Cables", "150.00", 40, False),
]


class Command(BaseCommand):
    help = "Create sample users, customers and products (safe to run more than once)."

    @transaction.atomic
    def handle(self, *args, **options):
        admin = self._create_users()
        self._create_customers()
        self._create_products(admin)
        self.stdout.write(self.style.SUCCESS("Sample data is ready."))

    def _create_users(self):
        admin = None
        for spec in SAMPLE_USERS:
            user = User.objects.filter(email=spec["email"]).first()
            if user is None:
                password = os.getenv(spec["env"], spec["default"])
                user = User.objects.create_user(
                    spec["email"], password, name=spec["name"], role=spec["role"],
                    is_staff=spec["role"] == User.Role.ADMIN,
                )
                self.stdout.write(f"  created user {user.email} ({user.get_role_display()})")
            if user.role == User.Role.ADMIN and admin is None:
                admin = user
        return admin

    def _create_customers(self):
        for name, email, mobile, city, is_active in SAMPLE_CUSTOMERS:
            Customer.objects.get_or_create(
                name=name, defaults={"email": email, "mobile": mobile, "city": city, "is_active": is_active}
            )

    def _create_products(self, admin):
        for code, name, category, price, stock, is_active in SAMPLE_PRODUCTS:
            product, created = Product.objects.get_or_create(
                product_code=code,
                defaults={"name": name, "category": category, "price": Decimal(price),
                          "stock_quantity": stock, "is_active": is_active},
            )
            if created and stock > 0:
                StockMovement.objects.create(
                    product=product,
                    movement_type=StockMovement.MovementType.OPENING,
                    quantity_change=stock,
                    stock_after=stock,
                    reason="Opening stock (sample data)",
                    created_by=admin,
                )
