from django.core.validators import MinValueValidator
from django.db import models


class Product(models.Model):
    product_code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=150)
    category = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    stock_quantity = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["product_code"]
        indexes = [
            models.Index(fields=["name"], name="product_name_idx"),
            models.Index(fields=["category", "is_active"], name="product_category_active_idx"),
            models.Index(fields=["is_active"], name="product_active_idx"),
            models.Index(fields=["stock_quantity"], name="product_stock_idx"),
        ]
        constraints = [
            # last line of defence - the API validates these before saving
            models.CheckConstraint(check=models.Q(price__gte=0), name="product_price_not_negative"),
            models.CheckConstraint(check=models.Q(stock_quantity__gte=0), name="product_stock_not_negative"),
        ]

    def __str__(self):
        return f"{self.product_code} - {self.name}"
