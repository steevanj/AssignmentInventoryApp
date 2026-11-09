from decimal import Decimal

from django.db.models import Count, DecimalField, Q, Sum, Value
from django.db.models.functions import Coalesce
from rest_framework.response import Response
from rest_framework.views import APIView

from core.api import parse_date_range
from core.permissions import IsAdminRole
from customers.models import Customer
from orders.models import SalesOrder
from reports.serializers import CustomerSalesSerializer


class CustomerSalesReportView(APIView):
    """
    GET /api/reports/customer-sales/?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD

    Every customer is listed, including those with no Confirmed orders in
    the range (they show 0). The query joins customers to orders only -
    never to order items - so an order with many lines is still counted once
    and its grand_total is added once.
    """

    permission_classes = [IsAdminRole]

    def get(self, request):
        date_from, date_to = parse_date_range(request)

        confirmed = Q(orders__status=SalesOrder.Status.CONFIRMED)
        if date_from:
            confirmed &= Q(orders__order_date__gte=date_from)
        if date_to:
            confirmed &= Q(orders__order_date__lte=date_to)

        money = DecimalField(max_digits=14, decimal_places=2)
        customers = (
            Customer.objects
            .annotate(
                confirmed_order_count=Count("orders", filter=confirmed, distinct=True),
                total_sales=Coalesce(Sum("orders__grand_total", filter=confirmed),
                                     Value(Decimal("0.00")), output_field=money),
            )
            .order_by("-total_sales", "name")
        )

        rows = CustomerSalesSerializer(customers, many=True).data
        return Response({
            "date_from": date_from,
            "date_to": date_to,
            "total_orders": sum(row["confirmed_order_count"] for row in rows),
            # str() keeps money exact; a raw Decimal would be sent as a float
            "total_sales": str(sum((c.total_sales for c in customers), Decimal("0.00"))),
            "results": rows,
        })
