from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsAdminRole

from .serializers import StockAdjustmentSerializer, StockMovementSerializer
from .services import adjust_stock


class StockAdjustmentView(APIView):
    """
    POST /api/inventory/adjustments/
    {"product": 3, "quantity_change": -2, "reason": "Damaged in transit"}
    """

    permission_classes = [IsAdminRole]

    def post(self, request):
        serializer = StockAdjustmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        movement = adjust_stock(
            product_id=data["product"].pk,
            quantity_change=data["quantity_change"],
            reason=data["reason"],
            user=request.user,
        )
        return Response(
            {"message": "Stock updated.", "movement": StockMovementSerializer(movement).data},
            status=status.HTTP_201_CREATED,
        )
