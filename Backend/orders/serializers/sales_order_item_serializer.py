from rest_framework import serializers

from orders.models import SalesOrderItem


class SalesOrderItemSerializer(serializers.ModelSerializer):
    """Read-only order line with the stored rate and amount."""

    product_code = serializers.CharField(source="product.product_code", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = SalesOrderItem
        fields = ["id", "product", "product_code", "product_name", "quantity", "rate", "amount"]
        read_only_fields = fields
