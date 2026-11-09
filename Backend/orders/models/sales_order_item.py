from django.core.validators import MinValueValidator
from django.db import models

from .sales_order import SalesOrder


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
