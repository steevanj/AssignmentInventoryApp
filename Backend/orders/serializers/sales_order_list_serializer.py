from rest_framework import serializers

from orders.models import SalesOrder


class SalesOrderListSerializer(serializers.ModelSerializer):
    """Order header without its lines, used by the order list."""

    customer_name = serializers.CharField(source="customer.name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    created_by_name = serializers.CharField(source="created_by.name", read_only=True)

    class Meta:
        model = SalesOrder
        fields = [
            "id", "order_number", "customer", "customer_name", "order_date", "status", "status_display",
            "discount_percentage", "subtotal", "discount_amount", "grand_total",
            "created_by", "created_by_name", "created_at",
        ]
        read_only_fields = fields
