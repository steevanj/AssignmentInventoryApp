"""Small helpers that build test data. Used only by the test suites."""

from decimal import Decimal

from rest_framework.test import APIClient

from accounts.models import User
from customers.models import Customer
from products.models import Product

TEST_PASSWORD = "Test@Pass123"


def make_user(role=User.Role.SALES, email=None, name="Test User"):
    email = email or f"{role.lower()}{User.objects.count() + 1}@test.local"
    return User.objects.create_user(email, TEST_PASSWORD, name=name, role=role)


def make_admin(email=None):
    return make_user(User.Role.ADMIN, email=email, name="Test Admin")


def make_customer(name="Test Customer", is_active=True, **extra):
    return Customer.objects.create(name=name, is_active=is_active, **extra)


def make_product(code, price="100.00", stock=10, is_active=True, name=None, category="General"):
    return Product.objects.create(
        product_code=code,
        name=name or f"Product {code}",
        category=category,
        price=Decimal(price),
        stock_quantity=stock,
        is_active=is_active,
    )


def client_for(user):
    """An API client already logged in as the given user."""
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def order_payload(customer, lines, discount="0"):
    """lines: list of (product, quantity)."""
    return {
        "customer": customer.pk,
        "discount_percentage": discount,
        "items": [{"product": product.pk, "quantity": quantity} for product, quantity in lines],
    }
