from rest_framework import serializers

from products.models import Product


class ProductSalesSerializer(serializers.ModelSerializer):
    """A product row plus quantity sold and gross value (before order discount)."""

    quantity_sold = serializers.IntegerField(read_only=True)
    gross_sales = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = Product
        fields = ["id", "product_code", "name", "category", "quantity_sold", "gross_sales"]
        read_only_fields = fields
