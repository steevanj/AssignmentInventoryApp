from rest_framework import serializers

from orders.models import SalesOrder

from .sales_order_item_serializer import SalesOrderItemSerializer
from .sales_order_list_serializer import SalesOrderListSerializer


class SalesOrderDetailSerializer(SalesOrderListSerializer):
    """Full order with its lines. is_editable tells the UI whether to show the edit form."""

    items = SalesOrderItemSerializer(many=True, read_only=True)
    is_editable = serializers.BooleanField(read_only=True)

    class Meta(SalesOrderListSerializer.Meta):
        model = SalesOrder
        fields = SalesOrderListSerializer.Meta.fields + ["confirmed_at", "cancelled_at", "is_editable", "items"]
        read_only_fields = fields
