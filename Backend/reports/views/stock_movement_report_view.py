from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView

from core.api import paginated_response, parse_date_range, parse_int_param
from core.permissions import IsAdminRole
from inventory.models import StockMovement
from inventory.serializers import StockMovementSerializer


class StockMovementReportView(APIView):
    """
    GET /api/reports/stock-movements/?product=&movement_type=&date_from=&date_to=&page=
    Newest first: product, type, quantity change, order, reason, user and time.
    """

    permission_classes = [IsAdminRole]

    def get(self, request):
        queryset = StockMovement.objects.select_related("product", "related_order", "created_by")

        product_id = parse_int_param(request, "product", min_value=1)
        if product_id:
            queryset = queryset.filter(product_id=product_id)

        movement_type = request.query_params.get("movement_type", "").strip().upper()
        if movement_type:
            if movement_type not in StockMovement.MovementType.values:
                raise ValidationError({"movement_type": "Use one of: " + ", ".join(StockMovement.MovementType.values)})
            queryset = queryset.filter(movement_type=movement_type)

        date_from, date_to = parse_date_range(request)
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)

        return paginated_response(request, queryset, StockMovementSerializer, self)
