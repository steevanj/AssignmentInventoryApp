from rest_framework import serializers

from inventory.models import StockMovement


class StockMovementSerializer(serializers.ModelSerializer):
    """Read-only row of the stock ledger, used by the movement history report."""

    product_code = serializers.CharField(source="product.product_code", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)
    movement_type_display = serializers.CharField(source="get_movement_type_display", read_only=True)
    order_number = serializers.CharField(source="related_order.order_number", read_only=True, allow_null=True)
    created_by_name = serializers.CharField(source="created_by.name", read_only=True)

    class Meta:
        model = StockMovement
        fields = [
            "id", "product", "product_code", "product_name", "movement_type", "movement_type_display",
            "quantity_change", "stock_after", "related_order", "order_number", "reason",
            "created_by", "created_by_name", "created_at",
        ]
        read_only_fields = fields
