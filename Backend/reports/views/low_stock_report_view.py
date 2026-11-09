from rest_framework.response import Response
from rest_framework.views import APIView

from core.api import parse_int_param
from core.permissions import IsAdminRole
from products.models import Product
from products.serializers import ProductSerializer


class LowStockReportView(APIView):
    """GET /api/reports/low-stock/?threshold=10 - active products with stock below the threshold."""

    permission_classes = [IsAdminRole]

    def get(self, request):
        threshold = parse_int_param(request, "threshold", required=True, min_value=0)
        products = Product.objects.filter(is_active=True, stock_quantity__lt=threshold).order_by(
            "stock_quantity", "product_code"
        )
        return Response({"threshold": threshold, "results": ProductSerializer(products, many=True).data})
