from decimal import Decimal

from django.db.models import DecimalField, Q, Sum, Value
from django.db.models.functions import Coalesce
from rest_framework.response import Response
from rest_framework.views import APIView

from core.api import parse_date_range
from core.permissions import IsAdminRole
from orders.models import SalesOrder
from products.models import Product
from reports.serializers import ProductSalesSerializer


class ProductSalesReportView(APIView):
    """
    GET /api/reports/product-sales/?date_from=&date_to=

    Quantity sold and gross item value (sum of line amounts, before the
    order level discount) from Confirmed orders. Products never sold in
    the range are left out.
    """

    permission_classes = [IsAdminRole]

    def get(self, request):
        date_from, date_to = parse_date_range(request)

        confirmed = Q(order_items__order__status=SalesOrder.Status.CONFIRMED)
        if date_from:
            confirmed &= Q(order_items__order__order_date__gte=date_from)
        if date_to:
            confirmed &= Q(order_items__order__order_date__lte=date_to)

        products = (
            Product.objects
            .annotate(
                quantity_sold=Coalesce(Sum("order_items__quantity", filter=confirmed), Value(0)),
                gross_sales=Coalesce(Sum("order_items__amount", filter=confirmed), Value(Decimal("0.00")),
                                     output_field=DecimalField(max_digits=14, decimal_places=2)),
            )
            .filter(quantity_sold__gt=0)
            .order_by("-quantity_sold", "product_code")
        )

        return Response({
            "date_from": date_from,
            "date_to": date_to,
            "results": ProductSalesSerializer(products, many=True).data,
        })
