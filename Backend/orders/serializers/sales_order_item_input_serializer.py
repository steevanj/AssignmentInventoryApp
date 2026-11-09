from rest_framework import serializers

from orders.models import SalesOrderItem
from products.models import Product


class SalesOrderItemInputSerializer(serializers.ModelSerializer):
    """
    One line as sent by the browser: only product and quantity.
    rate and amount are deliberately not accepted - the server takes the
    rate from the product and calculates the amount itself.
    """

    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        error_messages={"does_not_exist": "Product {pk_value} does not exist."},
    )
    quantity = serializers.IntegerField(
        min_value=1,
        max_value=1_000_000,
        error_messages={
            "min_value": "Quantity must be at least 1.",
            "max_value": "Quantity is too large.",
            "invalid": "Quantity must be a whole number.",
            "required": "Quantity is required.",
        },
    )

    class Meta:
        model = SalesOrderItem
        fields = ["product", "quantity"]
