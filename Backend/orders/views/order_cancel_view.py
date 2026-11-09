from rest_framework.response import Response
from rest_framework.views import APIView

from orders.serializers import SalesOrderDetailSerializer
from orders.services import cancel_order


class OrderCancelView(APIView):
    """
    POST /api/orders/<id>/cancel/
    Draft -> Cancelled with no stock change; Confirmed -> Cancelled with the
    deducted stock put back. Cancelling twice returns 409.
    """

    def post(self, request, pk):
        order = cancel_order(order_id=pk, user=request.user)
        message = f"Order {order.order_number} cancelled."
        if order.confirmed_at:
            message += " Stock has been restored."
        return Response({"message": message, "order": SalesOrderDetailSerializer(order).data})
