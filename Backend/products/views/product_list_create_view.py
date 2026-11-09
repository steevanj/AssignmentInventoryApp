from django.db import transaction
from django.db.models import Q
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.api import apply_active_filter, paginated_response
from core.permissions import IsAdminOrReadOnly
from inventory.services import record_opening_stock
from products.models import Product
from products.serializers import ProductSerializer


class ProductListCreateView(APIView):
    """
    GET  /api/products/?search=&category=&status=&page=&page_size=
         Lists active products by default. Admin can pass status=inactive or all.
    POST /api/products/   create (Admin only)
    """

    permission_classes = [IsAdminOrReadOnly]

    def get(self, request):
        queryset = Product.objects.all()

        search = request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(Q(product_code__icontains=search) | Q(name__icontains=search))

        category = request.query_params.get("category", "").strip()
        if category:
            queryset = queryset.filter(category__iexact=category)

        queryset = apply_active_filter(queryset, request)
        return paginated_response(request, queryset, ProductSerializer, self)

    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            product = serializer.save()
            record_opening_stock(product, request.user)
        return Response(ProductSerializer(product).data, status=status.HTTP_201_CREATED)
