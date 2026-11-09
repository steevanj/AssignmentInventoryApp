from decimal import Decimal

from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from products.models import Product


class ProductSerializer(serializers.ModelSerializer):
    """
    Used to list, view and create products. The CSV import reuses it row by
    row, so both paths share exactly the same validation rules.

    stock_quantity can only be set when the product is created; that value
    is recorded as an OPENING stock movement.
    """

    product_code = serializers.CharField(
        max_length=30,
        validators=[
            UniqueValidator(
                queryset=Product.objects.all(),
                lookup="iexact",
                message="A product with this code already exists.",
            )
        ],
    )
    price = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0"),
        error_messages={"min_value": "Price cannot be negative.", "invalid": "Price must be a number."},
    )
    stock_quantity = serializers.IntegerField(
        min_value=0,
        default=0,
        error_messages={
            "min_value": "Stock quantity cannot be negative.",
            "invalid": "Stock quantity must be a whole number.",
        },
    )

    class Meta:
        model = Product
        fields = [
            "id", "product_code", "name", "category", "price", "stock_quantity", "is_active",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_product_code(self, value):
        return value.strip().upper()

    def validate_category(self, value):
        return value.strip()
