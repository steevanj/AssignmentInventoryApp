from rest_framework import serializers

from inventory.models import StockMovement
from products.models import Product


class StockAdjustmentSerializer(serializers.ModelSerializer):
    """
    Input for a manual stock adjustment. Only the product, the signed
    change and the reason come from the user; movement type, resulting
    stock and created_by are worked out on the server.
    """

    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())

    class Meta:
        model = StockMovement
        fields = ["product", "quantity_change", "reason"]
        extra_kwargs = {
            "quantity_change": {"error_messages": {"invalid": "Quantity change must be a whole number."}},
            "reason": {"error_messages": {"blank": "A reason is required for every stock adjustment.",
                                          "required": "A reason is required for every stock adjustment."}},
        }

    def validate_quantity_change(self, value):
        if value == 0:
            raise serializers.ValidationError("Quantity change cannot be zero.")
        return value
