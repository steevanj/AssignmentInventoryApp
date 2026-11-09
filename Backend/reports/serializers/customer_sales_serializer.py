from rest_framework import serializers

from customers.models import Customer


class CustomerSalesSerializer(serializers.ModelSerializer):
    """A customer row plus the two values annotated by the report query."""

    confirmed_order_count = serializers.IntegerField(read_only=True)
    total_sales = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = Customer
        fields = ["id", "name", "city", "is_active", "confirmed_order_count", "total_sales"]
        read_only_fields = fields
