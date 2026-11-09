from rest_framework.response import Response
from rest_framework.views import APIView

from orders.serializers import SalesOrderDetailSerializer, SalesOrderWriteSerializer
from orders.services import get_order_for_user


class OrderDetailView(APIView):
    """
    GET /api/orders/<id>/   the order with its items (404 if not yours)
    PUT /api/orders/<id>/   replace customer, discount and items (Draft only)
    """

    def get(self, request, pk):
        order = get_order_for_user(pk, request.user)
        return Response(SalesOrderDetailSerializer(order).data)

    def put(self, request, pk):
        order = get_order_for_user(pk, request.user)
        serializer = SalesOrderWriteSerializer(order, data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        order = serializer.save()  # the service re-checks Draft status under a row lock
        return Response(SalesOrderDetailSerializer(order).data)
