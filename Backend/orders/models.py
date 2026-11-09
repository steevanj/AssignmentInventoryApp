from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

MAX_DISCOUNT_PERCENTAGE = Decimal("20")


class SalesOrder(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        CONFIRMED = "CONFIRMED", "Confirmed"
        CANCELLED = "CANCELLED", "Cancelled"

    order_number = models.CharField(max_length=30, unique=True, editable=False)
    customer = models.ForeignKey(
        "customers.Customer", on_delete=models.PROTECT, related_name="orders"
    )
    order_date = models.DateField(default=timezone.localdate)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0"),
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(MAX_DISCOUNT_PERCENTAGE)],
    )
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    discount_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    grand_total = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="sales_orders"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            # reports filter Confirmed orders by date range
            models.Index(fields=["status", "order_date"], name="order_status_date_idx"),
            # a Sales User's order list filters on created_by
            models.Index(fields=["created_by", "status"], name="order_owner_status_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(discount_percentage__gte=0) & models.Q(discount_percentage__lte=20),
                name="order_discount_between_0_and_20",
            ),
            models.CheckConstraint(
                check=models.Q(subtotal__gte=0) & models.Q(discount_amount__gte=0) & models.Q(grand_total__gte=0),
                name="order_amounts_not_negative",
            ),
        ]

    def __str__(self):
        return self.order_number

    @property
    def is_editable(self):
        """Only Draft orders can change; Confirmed and Cancelled orders are read-only."""
        return self.status == self.Status.DRAFT


class SalesOrderItem(models.Model):
    order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        "products.Product", on_delete=models.PROTECT, related_name="order_items"
    )
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    # The rate is copied from the product when the line is added, so a later
    # price change on the product never changes an existing order.
    rate = models.DecimalField(max_digits=12, decimal_places=2)
    amount = models.DecimalField(max_digits=14, decimal_places=2)

    class Meta:
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(fields=["order", "product"], name="unique_product_per_order"),
            models.CheckConstraint(check=models.Q(quantity__gt=0), name="order_item_quantity_positive"),
        ]

    def __str__(self):
        return f"{self.order.order_number}: {self.product.product_code} x {self.quantity}"
