from decimal import Decimal

from rest_framework import serializers

from customers.models import Customer
from orders import services
from orders.models import MAX_DISCOUNT_PERCENTAGE, SalesOrder

from .sales_order_item_input_serializer import SalesOrderItemInputSerializer


class SalesOrderWriteSerializer(serializers.ModelSerializer):
    """
    Input for creating or editing a Draft order:

        {"customer": 1, "discount_percentage": "10", "items": [{"product": 1, "quantity": 2}, ...]}

    Only these three fields are accepted. Anything else the browser sends
    (rate, amounts, totals, status, created_by) is simply ignored; those
    values are always set on the server.
    """

    customer = serializers.PrimaryKeyRelatedField(
        queryset=Customer.objects.all(),
        error_messages={"does_not_exist": "Customer {pk_value} does not exist.",
                        "required": "Choose a customer.", "null": "Choose a customer."},
    )
    discount_percentage = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        min_value=Decimal("0"),
        max_value=MAX_DISCOUNT_PERCENTAGE,
        default=Decimal("0"),
        error_messages={
            # no literal percent sign here: Django formats validator messages with %
            "min_value": "Discount must be between 0 and 20.",
            "max_value": "Discount must be between 0 and 20.",
            "invalid": "Discount must be a number.",
        },
    )
    items = SalesOrderItemInputSerializer(many=True)

    class Meta:
        model = SalesOrder
        fields = ["customer", "discount_percentage", "items"]

    def validate_customer(self, customer):
        if not customer.is_active:
            raise serializers.ValidationError("This customer is inactive. Choose an active customer.")
        return customer

    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError("Add at least one item to the order.")

        seen_products = set()
        for item in items:
            product = item["product"]
            if product.pk in seen_products:
                raise serializers.ValidationError(
                    f"{product.product_code} is added more than once. Change its quantity instead."
                )
            seen_products.add(product.pk)
            if not product.is_active:
                raise serializers.ValidationError(
                    f"{product.product_code} ({product.name}) is inactive and cannot be ordered."
                )
        return items

    def create(self, validated_data):
        return services.create_order(user=self.context["request"].user, **validated_data)

    def update(self, instance, validated_data):
        return services.update_draft_order(
            order_id=instance.pk, user=self.context["request"].user, **validated_data
        )
