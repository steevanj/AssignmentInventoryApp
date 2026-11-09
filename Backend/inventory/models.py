from django.conf import settings
from django.db import models


class StockMovement(models.Model):
    """
    Append-only ledger of every stock change. Product.stock_quantity is the
    running balance; this table records how it got there (who, why and
    which order).
    """

    class MovementType(models.TextChoices):
        OPENING = "OPENING", "Opening stock"
        ADJUSTMENT_IN = "ADJUSTMENT_IN", "Manual increase"
        ADJUSTMENT_OUT = "ADJUSTMENT_OUT", "Manual decrease"
        SALE = "SALE", "Order confirmed"
        SALE_REVERSAL = "SALE_REVERSAL", "Order cancelled"

    product = models.ForeignKey(
        "products.Product", on_delete=models.PROTECT, related_name="stock_movements"
    )
    movement_type = models.CharField(max_length=20, choices=MovementType.choices)
    quantity_change = models.IntegerField(help_text="Positive adds stock, negative removes stock.")
    stock_after = models.PositiveIntegerField(help_text="Product stock right after this movement.")
    related_order = models.ForeignKey(
        "orders.SalesOrder",
        on_delete=models.PROTECT,
        related_name="stock_movements",
        null=True,
        blank=True,
    )
    reason = models.CharField(max_length=255)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="stock_movements"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["product", "created_at"], name="movement_product_time_idx"),
            models.Index(fields=["movement_type"], name="movement_type_idx"),
        ]
        constraints = [
            models.CheckConstraint(check=~models.Q(quantity_change=0), name="movement_quantity_not_zero"),
        ]

    def __str__(self):
        sign = "+" if self.quantity_change > 0 else ""
        return f"{self.product.product_code} {sign}{self.quantity_change} ({self.get_movement_type_display()})"
