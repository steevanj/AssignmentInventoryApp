from rest_framework import serializers

from .product_serializer import ProductSerializer


class ProductUpdateSerializer(ProductSerializer):
    """
    Same as ProductSerializer, but stock_quantity is read-only.

    Stock may only change through a stock adjustment or an order, so that a
    StockMovement is always written. Editing the number directly would leave
    the stock ledger out of step with the product.
    """

    # Has to be re-declared here: Meta.read_only_fields is ignored for fields
    # that the parent serializer declares explicitly.
    stock_quantity = serializers.IntegerField(read_only=True)
