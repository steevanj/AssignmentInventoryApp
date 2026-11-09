from rest_framework.response import Response
from rest_framework.views import APIView

from orders.serializers import SalesOrderDetailSerializer
from orders.services import confirm_order


class OrderConfirmView(APIView):
    """
    POST /api/orders/<id>/confirm/
    Deducts stock for every line in one transaction. Returns 409 if the order
    is not Draft or any line has too little stock (nothing is changed then).
    """

    def post(self, request, pk):
        order = confirm_order(order_id=pk, user=request.user)
        return Response({
            "message": f"Order {order.order_number} confirmed and stock deducted.",
            "order": SalesOrderDetailSerializer(order).data,
        })
