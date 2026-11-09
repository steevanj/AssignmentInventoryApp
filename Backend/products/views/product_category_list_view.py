from rest_framework.response import Response
from rest_framework.views import APIView

from core.api import apply_active_filter
from products.models import Product


class ProductCategoryListView(APIView):
    """GET /api/products/categories/ returns the distinct categories for the filter dropdown."""

    def get(self, request):
        queryset = apply_active_filter(Product.objects.all(), request)
        categories = queryset.order_by("category").values_list("category", flat=True).distinct()
        return Response({"categories": list(categories)})
