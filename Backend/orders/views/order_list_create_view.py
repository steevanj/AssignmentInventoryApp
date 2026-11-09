from django.db.models import Q
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from core.api import paginated_response, parse_date_range
from orders.models import SalesOrder
from orders.serializers import SalesOrderDetailSerializer, SalesOrderListSerializer, SalesOrderWriteSerializer
from orders.services import orders_visible_to


class OrderListCreateView(APIView):
    """
    GET  /api/orders/?status=&search=&date_from=&date_to=&page=
         Admin sees all orders, a Sales User only their own.
    POST /api/orders/   create a Draft order
    """

    def get(self, request):
        queryset = orders_visible_to(request.user)

        order_status = request.query_params.get("status", "").strip().upper()
        if order_status:
            if order_status not in SalesOrder.Status.values:
                raise ValidationError({"status": "Use one of: DRAFT, CONFIRMED, CANCELLED."})
            queryset = queryset.filter(status=order_status)

        search = request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(Q(order_number__icontains=search) | Q(customer__name__icontains=search))

        date_from, date_to = parse_date_range(request)
        if date_from:
            queryset = queryset.filter(order_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(order_date__lte=date_to)

        return paginated_response(request, queryset, SalesOrderListSerializer, self)

    def post(self, request):
        serializer = SalesOrderWriteSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        return Response(SalesOrderDetailSerializer(order).data, status=status.HTTP_201_CREATED)
